"""QuadProxy Desktop Configuration Wizard GUI Application."""

from __future__ import annotations

import argparse
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Sequence, Tuple

from quadproxy.compatibility import (
    QT6,
    QPASSWORD_ECHO_MODE,
    QApplication,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    exec_app,
)
from quadproxy.config import (
    PROXY_HOST,
    PROXY_PASSWORD,
    PROXY_PORT,
    PROXY_SCHEME,
    PROXY_USER,
    WEBSHARE_PROXY_PASSWORD,
    ProxyConfig,
    SUPPORTED_PROXY_SCHEME,
    proxy_config_from_env,
)
from quadproxy.diagnostics import (
    DiagnosticResult,
    DiagnosticResultList,
    run_diagnostics,
)
from quadproxy.proxy import ProxyCheckingWindow, configure_application_proxy
from quadproxy.security import redact_str
from quadproxy.verification import PROXY_CHECK_URL, validate_ip_address, verify_proxy_http

STAGE_NAMES = [
    "Configuration",
    "Proxy Reachability",
    "Authentication",
    "Qt WebEngine Initialization",
    "Public IP Verification",
    "Target Page",
]


class QuadProxyWizard(QMainWindow):
    """Sleek Desktop Configuration Wizard for QuadProxy."""

    def __init__(
        self,
        target_url: str = "https://example.com",
        proxy_config: Optional[ProxyConfig] = None,
        no_proxy: bool = False,
    ) -> None:
        super().__init__()
        self.target_url = target_url
        self.initial_proxy_config = proxy_config
        self.no_proxy_mode = no_proxy
        self.direct_ip: Optional[str] = None
        self.proxy_ip: Optional[str] = None
        self.last_results: Optional[DiagnosticResultList] = None

        self.setWindowTitle("QuadProxy Desktop Configuration Wizard")
        self.resize(1024, 768)
        self.setMinimumSize(900, 650)

        self._init_ui()
        self._load_initial_values()

    def _init_ui(self) -> None:
        """Initialize all Qt widget layout and styling."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Scroll area container for smooth resizing
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame if QT6 else QFrame.NoFrame)

        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # 1. Intro / Header Banner
        intro_box = QFrame()
        intro_box.setObjectName("introBanner")
        intro_box.setStyleSheet(
            "#introBanner { background-color: #1e293b; border: 1px solid #3b82f6; "
            "border-radius: 8px; padding: 14px; }"
        )
        intro_layout = QVBoxLayout(intro_box)
        intro_layout.setSpacing(6)

        title_lbl = QLabel("QuadProxy Desktop Configuration Wizard")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #f8fafc;")

        desc_lbl = QLabel(
            "QuadProxy connects your Qt WebEngine application to a proxy you already have "
            "and verifies that traffic is actually using it."
        )
        desc_lbl.setStyleSheet("font-size: 13px; color: #cbd5e1;")

        notice_lbl = QLabel("NOTE: QuadProxy does not provide or sell proxy servers.")
        notice_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #f59e0b;")

        intro_layout.addWidget(title_lbl)
        intro_layout.addWidget(desc_lbl)
        intro_layout.addWidget(notice_lbl)
        content_layout.addWidget(intro_box)

        # 2. Form Fields Section
        form_group = QGroupBox("Proxy Configuration Settings")
        form_group.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #e2e8f0; font-size: 14px; margin-top: 6px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"
        )
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)

        self.scheme_combo = QComboBox()
        self.scheme_combo.addItems(["HTTP"])
        self.scheme_combo.setStyleSheet(
            "QComboBox { background-color: #334155; color: #f8fafc; padding: 6px; "
            "border: 1px solid #475569; border-radius: 4px; font-size: 13px; }"
        )

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("e.g. proxy.example.net")
        self.host_input.setStyleSheet(
            "QLineEdit { background-color: #334155; color: #f8fafc; padding: 6px; "
            "border: 1px solid #475569; border-radius: 4px; font-size: 13px; }"
        )

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("e.g. 8080")
        self.port_input.setStyleSheet(
            "QLineEdit { background-color: #334155; color: #f8fafc; padding: 6px; "
            "border: 1px solid #475569; border-radius: 4px; font-size: 13px; }"
        )

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("e.g. proxy_username")
        self.user_input.setStyleSheet(
            "QLineEdit { background-color: #334155; color: #f8fafc; padding: 6px; "
            "border: 1px solid #475569; border-radius: 4px; font-size: 13px; }"
        )

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QPASSWORD_ECHO_MODE)
        self.password_input.setPlaceholderText("e.g. proxy_password")
        self.password_input.setStyleSheet(
            "QLineEdit { background-color: #334155; color: #f8fafc; padding: 6px; "
            "border: 1px solid #475569; border-radius: 4px; font-size: 13px; }"
        )

        self.target_url_input = QLineEdit()
        self.target_url_input.setText(self.target_url)
        self.target_url_input.setPlaceholderText("https://example.com")
        self.target_url_input.setStyleSheet(
            "QLineEdit { background-color: #334155; color: #f8fafc; padding: 6px; "
            "border: 1px solid #475569; border-radius: 4px; font-size: 13px; }"
        )

        form_layout.addRow(self._make_label("Proxy Scheme:"), self.scheme_combo)
        form_layout.addRow(self._make_label("Proxy Host:"), self.host_input)
        form_layout.addRow(self._make_label("Proxy Port:"), self.port_input)
        form_layout.addRow(self._make_label("Proxy Username:"), self.user_input)
        form_layout.addRow(self._make_label("Proxy Password:"), self.password_input)
        form_layout.addRow(self._make_label("Target URL:"), self.target_url_input)

        content_layout.addWidget(form_group)

        # 3. Action Buttons Row
        btn_box = QFrame()
        btn_layout = QHBoxLayout(btn_box)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        self.btn_test = QPushButton("Test Proxy & Diagnostics")
        self.btn_test.setStyleSheet(
            "QPushButton { background-color: #2563eb; color: #ffffff; font-weight: bold; "
            "padding: 8px 14px; border-radius: 5px; font-size: 13px; } "
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        self.btn_test.clicked.connect(self.run_diagnostics_pipeline)

        self.btn_no_proxy = QPushButton("Try Without Proxy")
        self.btn_no_proxy.setStyleSheet(
            "QPushButton { background-color: #475569; color: #ffffff; font-weight: bold; "
            "padding: 8px 12px; border-radius: 5px; font-size: 12px; } "
            "QPushButton:hover { background-color: #64748b; }"
        )
        self.btn_no_proxy.clicked.connect(self.run_no_proxy_mode)

        self.btn_copy_qt6 = QPushButton("Copy PyQt6 Snippet")
        self.btn_copy_qt6.setStyleSheet(self._btn_style_secondary())
        self.btn_copy_qt6.clicked.connect(self.copy_pyqt6_snippet)

        self.btn_copy_qt5 = QPushButton("Copy PyQt5 Snippet")
        self.btn_copy_qt5.setStyleSheet(self._btn_style_secondary())
        self.btn_copy_qt5.clicked.connect(self.copy_pyqt5_snippet)

        self.btn_export_env = QPushButton("Export .env.example")
        self.btn_export_env.setStyleSheet(self._btn_style_secondary())
        self.btn_export_env.clicked.connect(self.export_env_template)

        self.btn_launch_browser = QPushButton("Launch Browser")
        self.btn_launch_browser.setStyleSheet(
            "QPushButton { background-color: #059669; color: #ffffff; font-weight: bold; "
            "padding: 8px 14px; border-radius: 5px; font-size: 13px; } "
            "QPushButton:hover { background-color: #047857; }"
        )
        self.btn_launch_browser.clicked.connect(self.launch_browser_window)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet(self._btn_style_secondary())
        self.btn_reset.clicked.connect(self.reset_form)

        btn_layout.addWidget(self.btn_test)
        btn_layout.addWidget(self.btn_no_proxy)
        btn_layout.addWidget(self.btn_copy_qt6)
        btn_layout.addWidget(self.btn_copy_qt5)
        btn_layout.addWidget(self.btn_export_env)
        btn_layout.addWidget(self.btn_launch_browser)
        btn_layout.addWidget(self.btn_reset)

        content_layout.addWidget(btn_box)

        # Status / Feedback Notification Label
        self.status_notification = QLabel("")
        self.status_notification.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #38bdf8; padding: 2px;"
        )
        content_layout.addWidget(self.status_notification)

        # 4. Customer Success Card ("QUADPROXY READY") & No-Proxy Banner
        self.success_card = QFrame()
        self.success_card.setObjectName("successCard")
        self.success_card.setStyleSheet(
            "#successCard { background-color: #065f46; border: 2px solid #10b981; "
            "border-radius: 8px; padding: 14px; }"
        )
        success_layout = QVBoxLayout(self.success_card)
        self.lbl_success_title = QLabel("QUADPROXY READY")
        self.lbl_success_title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #ffffff;"
        )
        self.lbl_success_body = QLabel(
            "Your PyQt WebEngine proxy configuration is fully verified and routing traffic securely."
        )
        self.lbl_success_body.setStyleSheet("font-size: 13px; color: #a7f3d0;")
        success_layout.addWidget(self.lbl_success_title)
        success_layout.addWidget(self.lbl_success_body)
        self.success_card.setVisible(False)
        content_layout.addWidget(self.success_card)

        # 5. Public IP Proof Card ("PROXY ROUTING VERIFIED" / "DIRECT CONNECTION — PROXY NOT ACTIVE")
        self.proof_card = QFrame()
        self.proof_card.setObjectName("proofCard")
        self.proof_card.setStyleSheet(
            "#proofCard { background-color: #1e293b; border: 1px solid #475569; "
            "border-radius: 8px; padding: 14px; }"
        )
        proof_layout = QVBoxLayout(self.proof_card)

        proof_header = QLabel("Public-IP Proof Card")
        proof_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc;")

        self.lbl_direct_ip = QLabel("DIRECT IP: Unknown")
        self.lbl_direct_ip.setStyleSheet("font-size: 13px; color: #cbd5e1;")

        self.lbl_proxy_ip = QLabel("PROXY IP: Unknown")
        self.lbl_proxy_ip.setStyleSheet("font-size: 13px; color: #cbd5e1;")

        self.lbl_proof_result = QLabel("RESULT: PENDING VERIFICATION")
        self.lbl_proof_result.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #94a3b8; margin-top: 4px;"
        )

        proof_layout.addWidget(proof_header)
        proof_layout.addWidget(self.lbl_direct_ip)
        proof_layout.addWidget(self.lbl_proxy_ip)
        proof_layout.addWidget(self.lbl_proof_result)
        content_layout.addWidget(self.proof_card)

        # 6. 6-Stage Visual Diagnostic Pipeline
        pipe_group = QGroupBox("6-Stage Visual Diagnostic Pipeline")
        pipe_group.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #e2e8f0; font-size: 14px; margin-top: 6px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"
        )
        pipe_layout = QVBoxLayout(pipe_group)
        pipe_layout.setSpacing(8)

        self.stage_widgets: List[Dict[str, QLabel]] = []
        for idx, name in enumerate(STAGE_NAMES, 1):
            row_frame = QFrame()
            row_frame.setStyleSheet(
                "QFrame { background-color: #0f172a; border: 1px solid #334155; "
                "border-radius: 6px; padding: 6px 10px; }"
            )
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(8, 6, 8, 6)

            stage_title = QLabel(f"[{idx}] {name}")
            stage_title.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #f1f5f9; min-width: 220px;"
            )

            badge = QLabel("WAITING")
            badge.setStyleSheet(self._badge_style("WAITING"))

            msg_lbl = QLabel("Pending diagnostic check")
            msg_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")

            row_layout.addWidget(stage_title)
            row_layout.addWidget(badge)
            row_layout.addWidget(msg_lbl, 1)

            pipe_layout.addWidget(row_frame)

            self.stage_widgets.append(
                {"title": stage_title, "badge": badge, "message": msg_lbl}
            )

        content_layout.addWidget(pipe_group)

        # 7. Layer Error Explanation Box (Shown on Failure)
        self.failure_box = QFrame()
        self.failure_box.setObjectName("failureBox")
        self.failure_box.setStyleSheet(
            "#failureBox { background-color: #450a0a; border: 2px solid #ef4444; "
            "border-radius: 8px; padding: 14px; }"
        )
        fail_layout = QVBoxLayout(self.failure_box)
        fail_layout.setSpacing(6)

        fail_header = QLabel("Diagnostic Stage Failure Breakdown")
        fail_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #fca5a5;")

        self.lbl_what_failed = QLabel("")
        self.lbl_what_failed.setStyleSheet("font-size: 13px; color: #fecaca;")
        self.lbl_what_failed.setWordWrap(True)

        self.lbl_why_failed = QLabel("")
        self.lbl_why_failed.setStyleSheet("font-size: 13px; color: #fecaca;")
        self.lbl_why_failed.setWordWrap(True)

        self.lbl_next_steps = QLabel("")
        self.lbl_next_steps.setStyleSheet("font-size: 13px; color: #fef08a;")
        self.lbl_next_steps.setWordWrap(True)

        fail_layout.addWidget(fail_header)
        fail_layout.addWidget(self.lbl_what_failed)
        fail_layout.addWidget(self.lbl_why_failed)
        fail_layout.addWidget(self.lbl_next_steps)
        self.failure_box.setVisible(False)
        content_layout.addWidget(self.failure_box)

        # 8. Error Experience & "SHOW DETAILS" Text Drawer
        details_box = QFrame()
        details_layout = QVBoxLayout(details_box)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(6)

        self.btn_toggle_details = QPushButton("SHOW DETAILS")
        self.btn_toggle_details.setStyleSheet(self._btn_style_secondary())
        self.btn_toggle_details.clicked.connect(self.toggle_details)

        self.txt_details = QTextEdit()
        self.txt_details.setReadOnly(True)
        self.txt_details.setMaximumHeight(160)
        self.txt_details.setStyleSheet(
            "QTextEdit { background-color: #090d16; color: #38bdf8; font-family: monospace; "
            "font-size: 12px; border: 1px solid #334155; border-radius: 4px; padding: 6px; }"
        )
        self.txt_details.setVisible(False)

        details_layout.addWidget(self.btn_toggle_details)
        details_layout.addWidget(self.txt_details)
        content_layout.addWidget(details_box)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 13px; color: #cbd5e1; font-weight: bold;")
        return lbl

    def _btn_style_secondary(self) -> str:
        return (
            "QPushButton { background-color: #334155; color: #f1f5f9; "
            "padding: 7px 10px; border: 1px solid #475569; border-radius: 4px; font-size: 12px; } "
            "QPushButton:hover { background-color: #475569; }"
        )

    def _badge_style(self, status: str) -> str:
        colors = {
            "WAITING": ("#64748b", "#0f172a"),
            "RUNNING": ("#3b82f6", "#1e3a8a"),
            "PASS": ("#22c55e", "#064e3b"),
            "FAIL": ("#ef4444", "#7f1d1d"),
        }
        fg, bg = colors.get(status, ("#64748b", "#0f172a"))
        return (
            f"QLabel {{ background-color: {bg}; color: {fg}; font-weight: bold; "
            f"border: 1px solid {fg}; border-radius: 4px; padding: 2px 8px; font-size: 11px; }}"
        )

    def _load_initial_values(self) -> None:
        """Populate initial form values from provided ProxyConfig or environment."""
        if self.initial_proxy_config is not None:
            cfg = self.initial_proxy_config
            idx = self.scheme_combo.findText(cfg.scheme.upper())
            if idx >= 0:
                self.scheme_combo.setCurrentIndex(idx)
            self.host_input.setText(cfg.host)
            self.port_input.setText(str(cfg.port))
            self.user_input.setText(cfg.user)
            self.password_input.setText(cfg.password)
        else:
            host = os.environ.get(PROXY_HOST, "").strip()
            port = os.environ.get(PROXY_PORT, "").strip()
            user = os.environ.get(PROXY_USER, "").strip()
            pwd = (
                os.environ.get(PROXY_PASSWORD, "").strip()
                or os.environ.get(WEBSHARE_PROXY_PASSWORD, "").strip()
            )
            scheme = os.environ.get(PROXY_SCHEME, SUPPORTED_PROXY_SCHEME).strip().upper()

            if scheme:
                idx = self.scheme_combo.findText(scheme)
                if idx >= 0:
                    self.scheme_combo.setCurrentIndex(idx)
            if host:
                self.host_input.setText(host)
            if port:
                self.port_input.setText(port)
            if user:
                self.user_input.setText(user)
            if pwd:
                self.password_input.setText(pwd)

    def get_form_config(self) -> Tuple[Optional[ProxyConfig], Optional[str]]:
        """Construct ProxyConfig from user inputs or return validation error."""
        if self.no_proxy_mode:
            return None, None

        host = self.host_input.text().strip()
        port_raw = self.port_input.text().strip()
        user = self.user_input.text().strip()
        password = self.password_input.text().strip()
        scheme = self.scheme_combo.currentText().strip().lower() or SUPPORTED_PROXY_SCHEME

        missing = []
        if not host:
            missing.append("Host")
        if not port_raw:
            missing.append("Port")
        if not user:
            missing.append("User")
        if not password:
            missing.append("Password")

        if missing:
            return None, f"Missing required fields: {', '.join(missing)}"

        try:
            port = int(port_raw)
        except ValueError:
            return None, "Port must be a valid integer"

        try:
            return (
                ProxyConfig(
                    host=host, port=port, user=user, password=password, scheme=scheme
                ),
                None,
            )
        except ValueError as exc:
            return None, str(exc)

    def set_stage_status(
        self, stage_idx: int, status: str, message: str
    ) -> None:
        """Update visual badge and message for a specific diagnostic stage (1-indexed)."""
        if 1 <= stage_idx <= len(self.stage_widgets):
            widget = self.stage_widgets[stage_idx - 1]
            widget["badge"].setText(status)
            widget["badge"].setStyleSheet(self._badge_style(status))
            widget["message"].setText(message)
            QApplication.processEvents()

    def run_diagnostics_pipeline(self) -> DiagnosticResultList:
        """Execute 6-stage visual diagnostic pipeline with proxy settings."""
        self.no_proxy_mode = False
        self.status_notification.setText("Running diagnostic pipeline...")
        self.failure_box.setVisible(False)
        self.success_card.setVisible(False)
        self.txt_details.clear()

        # Reset all badges to WAITING
        for i in range(1, 7):
            self.set_stage_status(i, "WAITING", "Pending diagnostic check")

        config, err_msg = self.get_form_config()
        if err_msg or config is None:
            self.set_stage_status(1, "FAIL", err_msg or "Configuration invalid")
            self._handle_stage_failure(1, err_msg or "Configuration error", config)
            results = DiagnosticResultList(
                [
                    DiagnosticResult(
                        stage=1,
                        name="Configuration",
                        passed=False,
                        message=err_msg or "Configuration error",
                    )
                ]
            )
            self.last_results = results
            return results

        # Run Stage 1
        self.set_stage_status(1, "RUNNING", "Validating configuration...")
        time.sleep(0.05)
        self.set_stage_status(
            1,
            "PASS",
            f"Configured {config.scheme.upper()} proxy {config.user}@{config.host}:{config.port}",
        )

        # Run 6-stage diagnostics engine
        self._append_detail_log(f"Starting 6-stage diagnostic sequence for {config}...")
        results = run_diagnostics(
            target_url=self.target_url_input.text().strip() or "https://example.com",
            proxy_config=config,
            no_proxy=False,
        )
        self.last_results = results

        # Fetch Direct IP for proof card comparison
        try:
            req = urllib.request.Request(
                PROXY_CHECK_URL, headers={"User-Agent": "QuadProxy-Wizard/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                self.direct_ip = resp.read().decode("utf-8").strip()
        except Exception as exc:
            self.direct_ip = "Unavailable"
            self._append_detail_log(f"Direct IP check error: {exc}")

        # Update Stage Badges 2 to 6 based on diagnostic results
        failed_stage = None
        for res in results:
            if res.stage == 1:
                continue
            stage_idx = res.stage
            if res.passed:
                self.set_stage_status(stage_idx, "PASS", res.message)
                self._append_detail_log(f"Stage {stage_idx} [{res.name}]: PASS - {res.message}")
            else:
                self.set_stage_status(stage_idx, "FAIL", res.message)
                self._append_detail_log(f"Stage {stage_idx} [{res.name}]: FAIL - {res.message}")
                if failed_stage is None:
                    failed_stage = (res.stage, res.message)

        # Update Proof Card & Success/Failure Screens
        stage5_res = results[4] if len(results) >= 5 else None
        if stage5_res and stage5_res.passed:
            # Extract IP from message
            parts = stage5_res.message.split("Verified public IP: ")
            self.proxy_ip = parts[-1].strip() if len(parts) > 1 else stage5_res.message
        else:
            self.proxy_ip = "Verification Failed"

        self.lbl_direct_ip.setText(f"DIRECT IP: {self.direct_ip}")
        self.lbl_proxy_ip.setText(f"PROXY IP: {self.proxy_ip}")

        all_passed = all(r.passed for r in results)
        if all_passed:
            self.lbl_proof_result.setText("RESULT: PROXY ROUTING VERIFIED")
            self.lbl_proof_result.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #10b981; margin-top: 4px;"
            )
            self.success_card.setVisible(True)
            self.failure_box.setVisible(False)
            self.status_notification.setText("QuadProxy Diagnostics Passed (6/6 stages)")
        else:
            self.lbl_proof_result.setText("RESULT: PROXY VERIFICATION FAILED")
            self.lbl_proof_result.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #ef4444; margin-top: 4px;"
            )
            self.success_card.setVisible(False)
            if failed_stage:
                self._handle_stage_failure(failed_stage[0], failed_stage[1], config)
            self.status_notification.setText("Diagnostic pipeline completed with errors.")

        return results

    def run_no_proxy_mode(self) -> DiagnosticResultList:
        """Run wizard diagnostics in Direct Connection / No-Proxy mode."""
        self.no_proxy_mode = True
        self.status_notification.setText("Running in Direct Connection / No-Proxy Mode...")
        self.failure_box.setVisible(False)
        self.success_card.setVisible(False)
        self.txt_details.clear()

        self._append_detail_log("Executing direct connection diagnostics (--no-proxy)...")

        results = run_diagnostics(
            target_url=self.target_url_input.text().strip() or "https://example.com",
            proxy_config=None,
            no_proxy=True,
        )
        self.last_results = results

        for res in results:
            self.set_stage_status(res.stage, "PASS", res.message)
            self._append_detail_log(f"Stage {res.stage} [{res.name}]: PASS - {res.message}")

        # Update Proof Card for Direct Mode
        direct_ip_res = results[4] if len(results) >= 5 else None
        if direct_ip_res and direct_ip_res.passed:
            ip_str = direct_ip_res.message.replace("Direct public IP verified: ", "").strip()
            self.direct_ip = ip_str
        else:
            self.direct_ip = "Unknown"

        self.proxy_ip = "N/A (Direct Mode)"
        self.lbl_direct_ip.setText(f"DIRECT IP: {self.direct_ip}")
        self.lbl_proxy_ip.setText(f"PROXY IP: {self.proxy_ip}")
        self.lbl_proof_result.setText("DIRECT CONNECTION — PROXY NOT ACTIVE")
        self.lbl_proof_result.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #f59e0b; margin-top: 4px;"
        )

        self.status_notification.setText("Direct connection verified successfully.")
        return results

    def run_wizard_headless(self) -> DiagnosticResultList:
        """Programmatic headless execution method for automated testing."""
        if self.no_proxy_mode:
            return self.run_no_proxy_mode()

        # Check if form is unpopulated and env vars exist
        host = self.host_input.text().strip()
        if not host and os.environ.get(PROXY_HOST):
            self._load_initial_values()

        return self.run_diagnostics_pipeline()

    def _handle_stage_failure(
        self, stage_idx: int, error_msg: str, config: Optional[ProxyConfig]
    ) -> None:
        """Display clear explanation breakdown for failed diagnostic stage."""
        self.failure_box.setVisible(True)

        pwd = config.password if config else None
        clean_err = redact_str(error_msg, pwd)

        host_str = config.host if config else "proxy_host"
        port_str = str(config.port) if config else "proxy_port"
        target_str = self.target_url_input.text().strip() or "https://example.com"

        explanations = {
            1: (
                f"WHAT FAILED: Proxy configuration parameters invalid or incomplete ({clean_err}).",
                "WHY IT PROBABLY FAILED: One or more required fields (Host, Port, User, Password) are blank or Port is non-integer.",
                "WHAT THE CUSTOMER SHOULD DO NEXT: Complete all configuration fields or click 'Try Without Proxy'.",
            ),
            2: (
                f"WHAT FAILED: Cannot open raw TCP socket to proxy server at {host_str}:{port_str} ({clean_err}).",
                "WHY IT PROBABLY FAILED: Proxy server is offline, host/port is incorrect, or a local/network firewall is blocking outbound TCP traffic.",
                "WHAT THE CUSTOMER SHOULD DO NEXT: Verify host IP and port with your proxy provider. Ensure outbound connection to this port is allowed.",
            ),
            3: (
                f"WHAT FAILED: Proxy authentication rejected credentials ({clean_err}).",
                "WHY IT PROBABLY FAILED: Username or password is wrong, or your client IP is not whitelisted in provider dashboard.",
                "WHAT THE CUSTOMER SHOULD DO NEXT: Double check your proxy username and password in the fields above, or whitelist your IP address.",
            ),
            4: (
                f"WHAT FAILED: Qt WebEngine bindings failed to initialize ({clean_err}).",
                "WHY IT PROBABLY FAILED: Missing PyQt5/PyQt6 WebEngine package or display driver issue.",
                "WHAT THE CUSTOMER SHOULD DO NEXT: Ensure PyQt WebEngine module is installed (e.g. `pip install PyQt6-WebEngine`).",
            ),
            5: (
                f"WHAT FAILED: Preflight public IP verification via api.ipify.org failed ({clean_err}).",
                "WHY IT PROBABLY FAILED: Proxy connected but failed to route HTTP traffic to the IP check endpoint.",
                "WHAT THE CUSTOMER SHOULD DO NEXT: Check proxy provider bandwidth, active subnets, and server health.",
            ),
            6: (
                f"WHAT FAILED: Failed to load target URL {target_str} through proxy ({clean_err}).",
                "WHY IT PROBABLY FAILED: Target website is down, URL is malformed, or proxy blocks requests to destination domain.",
                "WHAT THE CUSTOMER SHOULD DO NEXT: Test loading target URL in a standard browser and check proxy domain ACL rules.",
            ),
        }

        what, why, next_steps = explanations.get(
            stage_idx,
            (
                f"WHAT FAILED: Diagnostic Stage {stage_idx} failed ({clean_err}).",
                "WHY IT PROBABLY FAILED: Network or proxy connection error.",
                "WHAT THE CUSTOMER SHOULD DO NEXT: Check network settings and credentials.",
            ),
        )

        self.lbl_what_failed.setText(what)
        self.lbl_why_failed.setText(why)
        self.lbl_next_steps.setText(next_steps)

    def _append_detail_log(self, text: str) -> None:
        """Append log line to details drawer with password masking."""
        pwd = self.password_input.text().strip()
        redacted = redact_str(text, pwd)
        self.txt_details.append(redacted)

    def toggle_details(self) -> None:
        """Toggle visibility of expandable text drawer."""
        visible = not self.txt_details.isVisible()
        self.txt_details.setVisible(visible)
        self.btn_toggle_details.setText("HIDE DETAILS" if visible else "SHOW DETAILS")

    def copy_pyqt6_snippet(self) -> None:
        """Copy PyQt6 integration code snippet using os.environ references."""
        host = self.host_input.text().strip() or "proxy.example.net"
        port = self.port_input.text().strip() or "8080"
        user = self.user_input.text().strip() or "your_user"
        scheme = self.scheme_combo.currentText().strip().lower() or "http"
        target_url = self.target_url_input.text().strip() or "https://example.com"

        snippet = (
            "import os\n"
            "import sys\n"
            "from PyQt6.QtCore import QUrl\n"
            "from PyQt6.QtWidgets import QApplication\n"
            "from PyQt6.QtWebEngineWidgets import QWebEngineView\n"
            "from quadproxy import configure_application_proxy, ProxyConfig\n\n"
            "# Read credentials securely from environment variables (never hardcode real passwords)\n"
            "proxy_config = ProxyConfig(\n"
            f'    host=os.environ.get("PROXY_HOST", "{host}"),\n'
            f'    port=int(os.environ.get("PROXY_PORT", "{port}")),\n'
            f'    user=os.environ.get("PROXY_USER", "{user}"),\n'
            '    password=os.environ.get("PROXY_PASSWORD", ""),\n'
            f'    scheme=os.environ.get("PROXY_SCHEME", "{scheme}"),\n'
            ")\n\n"
            "configure_application_proxy(proxy_config)\n\n"
            "app = QApplication(sys.argv)\n"
            "view = QWebEngineView()\n"
            f'view.setUrl(QUrl("{target_url}"))\n'
            "view.show()\n"
            "sys.exit(app.exec())\n"
        )

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(snippet)
        self.status_notification.setText("PyQt6 integration snippet copied to clipboard!")

    def copy_pyqt5_snippet(self) -> None:
        """Copy PyQt5 integration code snippet using os.environ references."""
        host = self.host_input.text().strip() or "proxy.example.net"
        port = self.port_input.text().strip() or "8080"
        user = self.user_input.text().strip() or "your_user"
        scheme = self.scheme_combo.currentText().strip().lower() or "http"
        target_url = self.target_url_input.text().strip() or "https://example.com"

        snippet = (
            "import os\n"
            "import sys\n"
            "from PyQt5.QtCore import QUrl\n"
            "from PyQt5.QtWidgets import QApplication\n"
            "from PyQt5.QtWebEngineWidgets import QWebEngineView\n"
            "from quadproxy import configure_application_proxy, ProxyConfig\n\n"
            "# Read credentials securely from environment variables (never hardcode real passwords)\n"
            "proxy_config = ProxyConfig(\n"
            f'    host=os.environ.get("PROXY_HOST", "{host}"),\n'
            f'    port=int(os.environ.get("PROXY_PORT", "{port}")),\n'
            f'    user=os.environ.get("PROXY_USER", "{user}"),\n'
            '    password=os.environ.get("PROXY_PASSWORD", ""),\n'
            f'    scheme=os.environ.get("PROXY_SCHEME", "{scheme}"),\n'
            ")\n\n"
            "configure_application_proxy(proxy_config)\n\n"
            "app = QApplication(sys.argv)\n"
            "view = QWebEngineView()\n"
            f'view.setUrl(QUrl("{target_url}"))\n'
            "view.show()\n"
            "sys.exit(app.exec_())\n"
        )

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(snippet)
        self.status_notification.setText("PyQt5 integration snippet copied to clipboard!")

    def export_env_template(self) -> None:
        """Generate safe .env.example template with unpopulated passwords."""
        host = self.host_input.text().strip() or "proxy.example.net"
        port = self.port_input.text().strip() or "8080"
        user = self.user_input.text().strip() or "your_user"
        scheme = self.scheme_combo.currentText().strip().lower() or "http"

        content = (
            "# QuadProxy Environment Variables Template (.env.example)\n"
            f"PROXY_SCHEME={scheme}\n"
            f"PROXY_HOST={host}\n"
            f"PROXY_PORT={port}\n"
            f"PROXY_USER={user}\n"
            "PROXY_PASSWORD=your_proxy_password_here\n"
        )

        env_path = os.path.join(os.getcwd(), ".env.example")
        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
            msg = f"Exported safe .env.example template to {env_path} and copied to clipboard!"
        except Exception as exc:
            msg = f"Failed to save .env.example: {exc}. Template copied to clipboard."

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(content)
        self.status_notification.setText(msg)

    def launch_browser_window(self) -> None:
        """Launch ProxyCheckingWindow or browser view with configured settings."""
        config, err = self.get_form_config()
        if not self.no_proxy_mode and (err or config is None):
            self.status_notification.setText(f"Cannot launch browser: {err}")
            return

        target_url = self.target_url_input.text().strip() or "https://example.com"
        configure_application_proxy(config if not self.no_proxy_mode else None)

        self.browser_window = ProxyCheckingWindow(
            target_url, config if not self.no_proxy_mode else None
        )
        self.browser_window.show()
        self.browser_window.start()
        self.status_notification.setText("Launched browser verification window.")

    def reset_form(self) -> None:
        """Reset form fields and diagnostic state."""
        self.host_input.clear()
        self.port_input.clear()
        self.user_input.clear()
        self.password_input.clear()
        self.target_url_input.setText("https://example.com")
        self.scheme_combo.setCurrentIndex(0)

        self.no_proxy_mode = False
        self.direct_ip = None
        self.proxy_ip = None
        self.status_notification.setText("Reset all fields to defaults.")

        self.failure_box.setVisible(False)
        self.success_card.setVisible(False)
        self.txt_details.clear()

        self.lbl_direct_ip.setText("DIRECT IP: Unknown")
        self.lbl_proxy_ip.setText("PROXY IP: Unknown")
        self.lbl_proof_result.setText("RESULT: PENDING VERIFICATION")
        self.lbl_proof_result.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #94a3b8; margin-top: 4px;"
        )

        for i in range(1, 7):
            self.set_stage_status(i, "WAITING", "Pending diagnostic check")


def launch_wizard(
    target_url: str = "https://example.com",
    proxy_config: Optional[ProxyConfig] = None,
    no_proxy: bool = False,
) -> int:
    """Launch QuadProxy Desktop Configuration Wizard GUI app.

    Args:
        target_url: Target URL for verification.
        proxy_config: Optional initial ProxyConfig.
        no_proxy: If True, open wizard in direct connection mode.

    Returns:
        Exit code from Qt application event loop.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    wizard = QuadProxyWizard(
        target_url=target_url, proxy_config=proxy_config, no_proxy=no_proxy
    )
    wizard.show()

    # Headless support for offscreen automated testing
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        wizard.run_wizard_headless()

    return exec_app(app)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI entry point for quadproxy-wizard command."""
    parser = argparse.ArgumentParser(
        prog="quadproxy-wizard",
        description="QuadProxy Desktop Configuration Wizard",
    )
    parser.add_argument(
        "--url", default="https://example.com", help="Target URL for testing"
    )
    parser.add_argument(
        "--no-proxy", action="store_true", help="Start wizard in direct connection mode"
    )
    args = parser.parse_args(argv)

    try:
        config, _ = proxy_config_from_env(no_proxy=args.no_proxy)
    except RuntimeError:
        config = None

    return launch_wizard(
        target_url=args.url, proxy_config=config, no_proxy=args.no_proxy
    )


if __name__ == "__main__":
    sys.exit(main())
