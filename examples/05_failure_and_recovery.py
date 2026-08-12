"""Example E: Diagnostic Failure + Actionable Recovery Playbook.

Demonstrates handling diagnostic failure classifications and generating
a safe support bundle for troubleshooting.
"""

from __future__ import annotations

import sys
from quadproxy import ProxyConfig, run_diagnostics, format_diagnostic_table, generate_support_bundle
from quadproxy.playbook import classify_failure


def main() -> int:
    print("[QuadProxy Demo E] Diagnostic Failure & Playbook Recovery Demo...")

    # Intentionally bad config to simulate authentication failure
    bad_config = ProxyConfig(
        host="127.0.0.1", port=9999, user="invalid_user", password="invalid_password"
    )

    results = run_diagnostics(target_url="https://example.com", proxy_config=bad_config)
    print(format_diagnostic_table(results))

    failed = [r for r in results if not r.passed]
    if failed:
        first = failed[0]
        rec = classify_failure(first.stage, first.message)
        print(f"\n[ACTIONABLE RECOVERY GUIDE]")
        print(f"Classification: {rec.title} ({rec.code})")
        print(f"Recommended Fix: {rec.recommendation}")
        print("Action Steps:")
        for step in rec.next_steps:
            print(f"  - {step}")

        print("\nGenerating diagnostic support bundle...")
        zip_path = generate_support_bundle(
            output_path="demo_failure_support_bundle.zip",
            proxy_config=bad_config,
        )
        print(f"Support bundle created at: {zip_path} (Secrets scrubbed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
