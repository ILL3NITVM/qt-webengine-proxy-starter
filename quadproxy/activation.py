"""Customer Activation Journey & Checklist module for QuadProxy.

Tracks and formats the 9-stage post-purchase customer activation checklist:
1. Python environment ready
2. PyQt5 or PyQt6 available
3. Proxy credentials entered
4. Proxy reachable
5. Authentication successful
6. Public IP changed
7. Target URL loaded
8. Integration snippet copied
9. Existing application tested
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any

from quadproxy.diagnostics import qt_webengine_binding
from quadproxy.config import ProxyConfig


@dataclass
class ChecklistItem:
    """Represents a single customer activation checklist item."""

    key: str
    label: str
    passed: bool
    details: str
    next_action: str


class ActivationChecklist:
    """Evaluates and holds customer activation checklist progress."""

    ACTIVATION_STAGES = [
        ("PURCHASE", "Download QuadProxy ZIP package after Stripe checkout."),
        ("DOWNLOAD", "Extract package to local working directory."),
        ("EXTRACT", "Install dependencies via pip install -r requirements.txt."),
        ("LAUNCH", "Run python -m quadproxy doctor or desktop wizard."),
        ("CONFIGURE", "Provide PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASSWORD."),
        ("TEST", "Execute quadproxy diagnostic suite."),
        ("VERIFIED", "Confirm public IP changed and target URL loaded successfully."),
        ("INTEGRATE", "Copy integration code snippet into your application."),
        ("SUCCESS", "Verify your existing PyQt application with proxy enabled."),
    ]

    def __init__(
        self,
        proxy_config: Optional[ProxyConfig] = None,
        no_proxy: bool = False,
        doctor_results: Optional[List[Any]] = None,
        snippet_copied: bool = False,
        app_tested: bool = False,
    ) -> None:
        self.proxy_config = proxy_config
        self.no_proxy = no_proxy
        self.doctor_results = doctor_results or []
        self.snippet_copied = snippet_copied
        self.app_tested = app_tested

    def evaluate(self) -> List[ChecklistItem]:
        """Evaluate all 9 checklist items against current environment and results."""
        items: List[ChecklistItem] = []

        # 1. Python environment ready
        py_ver = sys.version.split()[0]
        py_ok = sys.version_info >= (3, 8)
        items.append(
            ChecklistItem(
                key="python_env",
                label="Python environment ready",
                passed=py_ok,
                details=f"Python {py_ver} ({'>=3.8' if py_ok else '<3.8 Unsupported'})",
                next_action="Use Python 3.8 or newer." if not py_ok else "Environment ready.",
            )
        )

        # 2. PyQt5 or PyQt6 available
        _, qt_binding = qt_webengine_binding()
        qt_ok = qt_binding in ("PyQt5", "PyQt6")
        items.append(
            ChecklistItem(
                key="pyqt_available",
                label="PyQt5 or PyQt6 available",
                passed=qt_ok,
                details=f"Detected Qt binding: {qt_binding}",
                next_action=(
                    "Install PyQt5/PyQt6 via 'pip install PyQt5 PyQtWebEngine' or 'pip install PyQt6 PyQt6-WebEngine'."
                    if not qt_ok
                    else "Qt WebEngine binding present."
                ),
            )
        )

        # 3. Proxy credentials entered
        if self.no_proxy:
            config_ok = True
            config_msg = "Direct mode enabled (--no-proxy)"
            config_next = "Proceed with direct connection diagnostics."
        elif self.proxy_config is not None:
            config_ok = True
            config_msg = f"Host={self.proxy_config.host}:{self.proxy_config.port}, User={self.proxy_config.user}"
            config_next = "Credentials loaded from environment."
        else:
            config_ok = False
            config_msg = "Missing proxy environment variables (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASSWORD)"
            config_next = "Set proxy environment variables or launch 'python -m quadproxy wizard'."

        items.append(
            ChecklistItem(
                key="proxy_credentials",
                label="Proxy credentials entered",
                passed=config_ok,
                details=config_msg,
                next_action=config_next,
            )
        )

        # Helper to retrieve doctor stage result
        stage_map = {getattr(r, "stage", idx + 1): r for idx, r in enumerate(self.doctor_results)}

        # 4. Proxy reachable
        stage2 = stage_map.get(2)
        stage2_ok = stage2.passed if stage2 else False
        stage2_msg = stage2.message if stage2 else ("Direct mode skipped" if self.no_proxy else "Not run yet")
        if self.no_proxy:
            stage2_ok = True
            stage2_msg = "Direct connection (socket check skipped)"
        items.append(
            ChecklistItem(
                key="proxy_reachable",
                label="Proxy reachable",
                passed=stage2_ok,
                details=stage2_msg,
                next_action="Verify proxy hostname, port, and network/firewall." if not stage2_ok else "Socket reachable.",
            )
        )

        # 5. Authentication successful
        stage3 = stage_map.get(3)
        stage3_ok = stage3.passed if stage3 else False
        stage3_msg = stage3.message if stage3 else ("Direct mode skipped" if self.no_proxy else "Not run yet")
        if self.no_proxy:
            stage3_ok = True
            stage3_msg = "Direct connection (auth check skipped)"
        items.append(
            ChecklistItem(
                key="auth_successful",
                label="Authentication successful",
                passed=stage3_ok,
                details=stage3_msg,
                next_action="Check username, password, and provider IP whitelist." if not stage3_ok else "Authentication accepted.",
            )
        )

        # 6. Public IP changed
        stage5 = stage_map.get(5)
        stage5_ok = stage5.passed if stage5 else False
        stage5_msg = stage5.message if stage5 else "Not run yet"
        items.append(
            ChecklistItem(
                key="public_ip_changed",
                label="Public IP changed",
                passed=stage5_ok,
                details=stage5_msg,
                next_action="Run 'python -m quadproxy doctor' to verify public IP." if not stage5_ok else "Public IP verified.",
            )
        )

        # 7. Target URL loaded
        stage6 = stage_map.get(6)
        stage6_ok = stage6.passed if stage6 else False
        stage6_msg = stage6.message if stage6 else "Not run yet"
        items.append(
            ChecklistItem(
                key="target_url_loaded",
                label="Target URL loaded",
                passed=stage6_ok,
                details=stage6_msg,
                next_action="Check target URL reachability or destination restrictions." if not stage6_ok else "Target URL loaded.",
            )
        )

        # 8. Integration snippet copied
        items.append(
            ChecklistItem(
                key="snippet_copied",
                label="Integration snippet copied",
                passed=self.snippet_copied,
                details="Snippet copied to clipboard / exported" if self.snippet_copied else "Snippet not yet copied",
                next_action="Copy integration snippet from wizard or docs/INTEGRATION.md." if not self.snippet_copied else "Snippet ready.",
            )
        )

        # 9. Existing application tested
        items.append(
            ChecklistItem(
                key="app_tested",
                label="Existing application tested",
                passed=self.app_tested,
                details="Application integration verified" if self.app_tested else "Integration test pending",
                next_action="Run your PyQt application with configure_application_proxy(config)." if not self.app_tested else "Integration verified.",
            )
        )

        return items


def format_checklist_cli(items: List[ChecklistItem]) -> str:
    """Format activation checklist items into a clean CLI string."""
    lines = [
        "================================================================================",
        "QuadProxy Customer Activation Checklist",
        "================================================================================",
    ]
    completed_count = sum(1 for item in items if item.passed)
    total_count = len(items)
    percentage = int((completed_count / total_count) * 100)

    lines.append(f"Progress: [{completed_count}/{total_count}] ({percentage}% Complete)\n")

    for item in items:
        mark = "[X]" if item.passed else "[ ]"
        lines.append(f"{mark} {item.label:<32} - {item.details}")
        if not item.passed:
            lines.append(f"    -> Next Action: {item.next_action}")

    lines.append("================================================================================")
    return "\n".join(lines)
