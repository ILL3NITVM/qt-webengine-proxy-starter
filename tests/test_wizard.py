"""Unit tests for QuadProxy Desktop Configuration Wizard."""

from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

PRODUCT_DIR = Path(__file__).resolve().parents[1]
if str(PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(PRODUCT_DIR))

import quadproxy
from quadproxy.compatibility import QApplication, QT6
from quadproxy.config import ProxyConfig
from quadproxy.wizard import QuadProxyWizard, launch_wizard, main as wizard_main
from quadproxy.__main__ import build_parser, main as cli_main

# Set offscreen QPA platform for headless testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"


class QuadProxyWizardTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["-platform", "offscreen"])

    def setUp(self):
        self.wizard = QuadProxyWizard(target_url="https://example.com")

    def tearDown(self):
        if hasattr(self, "wizard") and self.wizard:
            self.wizard.close()
            self.wizard.deleteLater()

    def test_package_exports(self):
        """Verify QuadProxyWizard and launch_wizard are exported by quadproxy package."""
        self.assertTrue(hasattr(quadproxy, "QuadProxyWizard"))
        self.assertTrue(hasattr(quadproxy, "launch_wizard"))
        self.assertIn("QuadProxyWizard", quadproxy.__all__)
        self.assertIn("launch_wizard", quadproxy.__all__)

    def test_wizard_initialization_defaults(self):
        """Verify wizard initializes with correct default widgets and target URL."""
        self.assertEqual(self.wizard.target_url, "https://example.com")
        self.assertEqual(self.wizard.scheme_combo.currentText(), "HTTP")
        self.assertEqual(self.wizard.scheme_combo.count(), 1)
        self.assertEqual(self.wizard.scheme_combo.findText("SOCKS5"), -1)
        self.assertEqual(len(self.wizard.stage_widgets), 6)
        self.assertTrue(self.wizard.failure_box.isHidden())
        self.assertTrue(self.wizard.success_card.isHidden())

    def test_load_initial_values_from_config(self):
        """Verify wizard loads initial values from a provided ProxyConfig."""
        cfg = ProxyConfig(
            host="proxy.test.com",
            port=8080,
            user="user123",
            password="secret_password",
            scheme="http",
        )
        wiz = QuadProxyWizard(target_url="https://test.org", proxy_config=cfg)
        self.assertEqual(wiz.scheme_combo.currentText(), "HTTP")
        self.assertEqual(wiz.host_input.text(), "proxy.test.com")
        self.assertEqual(wiz.port_input.text(), "8080")
        self.assertEqual(wiz.user_input.text(), "user123")
        self.assertEqual(wiz.password_input.text(), "secret_password")

    def test_get_form_config_valid(self):
        """Verify get_form_config parses form input values into a ProxyConfig."""
        self.wizard.scheme_combo.setCurrentIndex(0)
        self.wizard.host_input.setText("1.2.3.4")
        self.wizard.port_input.setText("3128")
        self.wizard.user_input.setText("usr")
        self.wizard.password_input.setText("pwd")

        cfg, err = self.wizard.get_form_config()
        self.assertIsNone(err)
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg.host, "1.2.3.4")
        self.assertEqual(cfg.port, 3128)
        self.assertEqual(cfg.user, "usr")
        self.assertEqual(cfg.password, "pwd")
        self.assertEqual(cfg.scheme, "http")

    def test_get_form_config_missing_fields(self):
        """Verify get_form_config returns error message when fields are empty."""
        self.wizard.host_input.setText("1.2.3.4")

        cfg, err = self.wizard.get_form_config()
        self.assertIsNone(cfg)
        self.assertIsNotNone(err)
        self.assertIn("Missing required fields", err)

    def test_get_form_config_invalid_port(self):
        """Verify get_form_config returns error when port is non-integer."""
        self.wizard.host_input.setText("1.2.3.4")
        self.wizard.port_input.setText("invalid_port")
        self.wizard.user_input.setText("usr")
        self.wizard.password_input.setText("pwd")

        cfg, err = self.wizard.get_form_config()
        self.assertIsNone(cfg)
        self.assertIsNotNone(err)
        self.assertIn("Port must be a valid integer", err)

    def test_run_no_proxy_mode(self):
        """Verify direct mode execution updates stage badges and proof card correctly."""
        results = self.wizard.run_no_proxy_mode()
        self.assertEqual(len(results), 12)
        self.assertTrue(all(r.passed for r in results))
        self.assertEqual(self.wizard.lbl_proof_result.text(), "DIRECT CONNECTION — PROXY NOT ACTIVE")
        self.assertEqual(self.wizard.lbl_proxy_ip.text(), "PROXY IP: N/A (Direct Mode)")

    def test_run_wizard_headless(self):
        """Verify run_wizard_headless executes diagnostics programmatically."""
        self.wizard.no_proxy_mode = True
        results = self.wizard.run_wizard_headless()
        self.assertEqual(len(results), 12)
        self.assertTrue(all(r.passed for r in results))

    @patch("quadproxy.wizard.run_diagnostics")
    @patch("urllib.request.urlopen")
    def test_run_diagnostics_pipeline_success(self, mock_urlopen, mock_run_diag):
        """Verify successful diagnostic pipeline execution displays Customer Success Card."""
        from quadproxy.diagnostics import DiagnosticResult, DiagnosticResultList

        mock_resp = MagicMock()
        mock_resp.read.return_value = b"203.0.113.50"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        mock_results = DiagnosticResultList(
            [
                DiagnosticResult(1, "Configuration", True, "Configured HTTP proxy"),
                DiagnosticResult(2, "Proxy Reachable", True, "TCP socket opened"),
                DiagnosticResult(3, "Authentication Accepted", True, "Credentials accepted"),
                DiagnosticResult(4, "Qt WebEngine Initialized", True, "PyQt WebEngine ready"),
                DiagnosticResult(5, "Public IP Verification", True, "Verified public IP: 198.51.100.22"),
                DiagnosticResult(6, "Target Page", True, "Loaded target URL"),
            ]
        )
        mock_run_diag.return_value = mock_results

        self.wizard.host_input.setText("proxy.test.com")
        self.wizard.port_input.setText("8080")
        self.wizard.user_input.setText("testuser")
        self.wizard.password_input.setText("testpass")

        res = self.wizard.run_diagnostics_pipeline()
        self.assertFalse(self.wizard.success_card.isHidden())
        self.assertTrue(self.wizard.failure_box.isHidden())
        self.assertEqual(self.wizard.lbl_proof_result.text(), "RESULT: PROXY ROUTING VERIFIED")

    def test_failure_breakdown_explanations(self):
        """Verify stage failure explanation displays WHAT, WHY, and NEXT STEPS."""
        cfg = ProxyConfig("h", 8080, "u", "secret_pass")
        self.wizard._handle_stage_failure(2, "Connection refused on port 8080", cfg)

        self.assertFalse(self.wizard.failure_box.isHidden())
        self.assertIn("WHAT FAILED", self.wizard.lbl_what_failed.text())
        self.assertIn("WHY IT PROBABLY FAILED", self.wizard.lbl_why_failed.text())
        self.assertIn("WHAT THE CUSTOMER SHOULD DO NEXT", self.wizard.lbl_next_steps.text())
        self.assertNotIn("secret_pass", self.wizard.lbl_what_failed.text())

    def test_snippets_never_leak_password(self):
        """Verify PyQt6 and PyQt5 snippet copy functions never leak real password strings."""
        self.wizard.host_input.setText("myproxy.com")
        self.wizard.port_input.setText("9090")
        self.wizard.user_input.setText("myuser")
        self.wizard.password_input.setText("MY_TOP_SECRET_PASSWORD_999")

        with patch("quadproxy.compatibility.QApplication.clipboard") as mock_clip:
            mock_c = MagicMock()
            mock_clip.return_value = mock_c

            self.wizard.copy_pyqt6_snippet()
            self.wizard.copy_pyqt5_snippet()

            for call_args in mock_c.setText.call_args_list:
                snippet_text = call_args[0][0]
                self.assertNotIn("MY_TOP_SECRET_PASSWORD_999", snippet_text)
                self.assertIn("os.environ.get", snippet_text)
                self.assertIn("PROXY_PASSWORD", snippet_text)

    def test_export_env_template(self):
        """Verify export_env_template generates safe .env.example with placeholder passwords."""
        self.wizard.host_input.setText("myproxy.com")
        self.wizard.port_input.setText("9090")
        self.wizard.user_input.setText("myuser")
        self.wizard.password_input.setText("MY_TOP_SECRET_PASSWORD_999")

        with patch("quadproxy.compatibility.QApplication.clipboard") as mock_clip:
            mock_c = MagicMock()
            mock_clip.return_value = mock_c
            original_cwd = Path.cwd()
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                try:
                    self.wizard.export_env_template()
                    env_path = Path(tmp) / ".env.example"
                    self.assertTrue(env_path.exists())
                    content = env_path.read_text(encoding="utf-8")
                    self.assertNotIn("MY_TOP_SECRET_PASSWORD_999", content)
                    self.assertIn("your_proxy_password_here", content)
                finally:
                    os.chdir(original_cwd)

    def test_toggle_details_and_redaction(self):
        """Verify detail drawer toggles visibility and scrubs sensitive passwords."""
        self.wizard.password_input.setText("SUPER_SECRET_123")

        self.assertTrue(self.wizard.txt_details.isHidden())
        self.wizard.toggle_details()
        self.assertFalse(self.wizard.txt_details.isHidden())

        self.wizard._append_detail_log("Error connecting with password SUPER_SECRET_123!")
        log_text = self.wizard.txt_details.toPlainText()
        self.assertNotIn("SUPER_SECRET_123", log_text)
        self.assertIn("***", log_text)

    def test_cli_subcommands_wizard_and_gui(self):
        """Verify CLI parser handles 'wizard' and 'gui' subcommands."""
        parser = build_parser()
        args_wiz = parser.parse_args(["wizard", "--no-proxy"])
        self.assertEqual(args_wiz.command, "wizard")
        self.assertTrue(args_wiz.no_proxy)

        args_gui = parser.parse_args(["gui", "--url", "https://custom.com"])
        target_url = args_gui.url_flag or args_gui.url
        self.assertEqual(args_gui.command, "gui")
        self.assertEqual(target_url, "https://custom.com")

    @patch("quadproxy.__main__.launch_wizard", return_value=0)
    def test_cli_main_wizard_invocation(self, mock_launch):
        """Verify calling 'quadproxy wizard' delegates to launch_wizard."""
        ret = cli_main(["wizard", "--no-proxy"])
        self.assertEqual(ret, 0)
        mock_launch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
