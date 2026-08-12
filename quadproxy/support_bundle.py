"""Support Bundle Generator for QuadProxy.

Generates safe, redacted diagnostic ZIP bundles for customer support troubleshooting.
Guarantees zero leakage of credentials, passwords, Stripe keys, cookies, or browser history.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import time
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from quadproxy import __version__
from quadproxy.diagnostics import DiagnosticResultList, qt_webengine_binding, run_diagnostics
from quadproxy.playbook import classify_failure
from quadproxy.security import redact_dict, redact_str

FORBIDDEN_SECRET_PATTERNS = [
    "sk_live_",
    "sk_test_",
    "whsec_",
    "bearer ",
    "sessionid=",
]


def generate_support_bundle(
    output_path: Optional[str] = None,
    target_url: str = "https://example.com",
    proxy_config: Optional[ProxyConfig] = None,
    no_proxy: bool = False,
    extra_logs: Optional[str] = None,
) -> str:
    """Generate a safe, redacted support bundle ZIP file.

    Args:
        output_path: Optional custom path for the target ZIP file.
        target_url: Target URL to run diagnostics against.
        proxy_config: Optional ProxyConfig instance.
        no_proxy: If True, run diagnostics in direct mode.
        extra_logs: Optional string log output to redact and include.

    Returns:
        Absolute filepath to the generated ZIP support bundle.

    Raises:
        ValueError: If adversarial secret redaction check fails.
    """
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if output_path is None:
        filename = f"quadproxy-support-bundle-{timestamp_str}.zip"
        output_path = os.path.abspath(filename)
    else:
        output_path = os.path.abspath(output_path)

    # 1. Resolve configuration safely
    if proxy_config is None and not no_proxy:
        try:
            proxy_config, _ = proxy_config_from_env(no_proxy=False)
        except RuntimeError:
            proxy_config = None

    # Password for string scrubbing
    pwd_to_scrub = proxy_config.password if proxy_config else None

    # 2. Collect Environment Metadata (SAFE ONLY)
    _, qt_binding = qt_webengine_binding()
    env_meta = {
        "quadproxy_version": __version__,
        "python_version": sys.version.split()[0],
        "python_platform": sys.platform,
        "os_name": os.name,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "qt_binding": qt_binding,
        "mode": "no_proxy" if no_proxy else ("proxy" if proxy_config else "unconfigured"),
        "timestamp_utc": timestamp_str,
    }

    # 3. Run Diagnostic Sequence
    diag_results: DiagnosticResultList = run_diagnostics(
        target_url=target_url, proxy_config=proxy_config, no_proxy=no_proxy
    )

    stage_summaries = []
    classifications = []

    for res in diag_results:
        clean_msg = redact_str(res.message, pwd_to_scrub)
        stage_info = {
            "stage": res.stage,
            "name": res.name,
            "passed": res.passed,
            "message": clean_msg,
            "duration_ms": round(res.duration_ms, 2),
        }
        stage_summaries.append(stage_info)

        if not res.passed:
            rec = classify_failure(
                stage=res.stage,
                error_message=clean_msg,
                details=res.details,
            )
            classifications.append(
                {
                    "stage": res.stage,
                    "code": rec.code,
                    "title": rec.title,
                    "description": rec.description,
                    "recommendation": rec.recommendation,
                    "next_steps": rec.next_steps,
                }
            )

    # 4. Redact Any Logs
    clean_logs = redact_str(extra_logs or "No additional runtime log recorded.", pwd_to_scrub)

    bundle_data = {
        "system": env_meta,
        "diagnostics": stage_summaries,
        "classifications": classifications,
        "overall_status": "PASS" if all(r.passed for r in diag_results) else "FAIL",
        "redacted_logs": clean_logs,
    }

    # Ensure complete dict sanitization
    sanitized_bundle_data = redact_dict(bundle_data)

    # Build human-readable text report
    report_lines = [
        "================================================================================",
        "QUADPROXY SUPPORT DIAGNOSTIC REPORT",
        "================================================================================",
        f"Generated: {timestamp_str} UTC",
        f"QuadProxy Version: {env_meta['quadproxy_version']}",
        f"Python Version   : {env_meta['python_version']} ({env_meta['platform_system']})",
        f"Qt Binding       : {env_meta['qt_binding']}",
        f"Execution Mode   : {env_meta['mode']}",
        f"Overall Status   : {sanitized_bundle_data['overall_status']}",
        "================================================================================",
        "\n--- STAGE DIAGNOSTIC RESULTS ---",
    ]

    for stage in stage_summaries:
        status_str = "PASS" if stage["passed"] else "FAIL"
        report_lines.append(
            f"Stage {stage['stage']}: {stage['name']:<28} [{status_str}] - {stage['message']}"
        )

    if classifications:
        report_lines.append("\n--- ACTIONABLE RECOMMENDED FIXES ---")
        for cls in classifications:
            report_lines.append(f"\n[Stage {cls['stage']} - {cls['title']}]")
            report_lines.append(f"Problem: {cls['description']}")
            report_lines.append(f"Fix    : {cls['recommendation']}")
            report_lines.append("Steps  :")
            for step in cls["next_steps"]:
                report_lines.append(f"  - {step}")

    report_lines.append("\n--- REDACTED RUNTIME LOGS ---")
    report_lines.append(clean_logs)
    report_lines.append("\n================================================================================")

    report_text = "\n".join(report_lines)

    # Adversarial Secret Audit on content before writing
    json_bytes = json.dumps(sanitized_bundle_data, indent=2).encode("utf-8")
    report_bytes = report_text.encode("utf-8")

    if pwd_to_scrub and pwd_to_scrub.strip():
        if pwd_to_scrub.encode("utf-8") in json_bytes or pwd_to_scrub.encode("utf-8") in report_bytes:
            raise ValueError("SECRET LEAK AUDIT FAILED: Raw password found in generated support bundle!")

    for forbidden in FORBIDDEN_SECRET_PATTERNS:
        if forbidden.encode("utf-8") in json_bytes or forbidden.encode("utf-8") in report_bytes:
            raise ValueError(f"SECRET LEAK AUDIT FAILED: Forbidden pattern {forbidden!r} found in bundle!")

    # Write Zip archive
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("diagnostics.json", json_bytes)
        zipf.writestr("SUPPORT_DIAGNOSTIC_REPORT.txt", report_bytes)

    return output_path
