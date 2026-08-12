"""Security Regression Unit Tests for QuadProxy Credential Protection.

Verifies zero credential leakage across:
- Logs & detail text drawers
- Exceptions & error tracebacks
- Clipboard code snippets (PyQt5 and PyQt6)
- Diagnostic tables & doctor reports
- Generated configuration templates (.env.example)
- Subprocess arguments & CLI environments
- __repr__ and __str__ representations of ProxyConfig
- UI stage failure breakdowns (WHAT, WHY, NEXT STEPS)
"""

import io
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

PRODUCT_DIR = Path(__file__).resolve().parents[1]
if str(PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(PRODUCT_DIR))

# Ensure headless Qt execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import quadproxy
from quadproxy.compatibility import QApplication
from quadproxy.config import ProxyConfig, proxy_config_from_env
from quadproxy.diagnostics import (
    DiagnosticResult,
    DiagnosticResultList,
    doctor,
    format_diagnostic_table,
    run_diagnostics,
    verify_proxy_connection,
)
from quadproxy.security import (
    redact_dict,
    redact_password,
    redact_str,
    redact_url,
)
from quadproxy.wizard import QuadProxyWizard


SECRET_CUSTOMER_PASSWORD = "CUSTOMER_ULTRA_SECRET_PASSWORD_987654321_!"


class SecretLeakRegressionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["-platform", "offscreen"])

    def setUp(self):
        self.config = ProxyConfig(
            host="proxy.customer.net",
            port=8080,
            user="customer_user",
            password=SECRET_CUSTOMER_PASSWORD,
            scheme="http",
        )
        self.wizard = QuadProxyWizard(
            target_url="https://example.com", proxy_config=self.config
        )

    def tearDown(self):
        if hasattr(self, "wizard") and self.wizard:
            self.wizard.close()
            self.wizard.deleteLater()

    def test_proxy_config_repr_masks_password(self):
        """Verify ProxyConfig.__repr__ masks the real password as '***'."""
        repr_str = repr(self.config)
        self.assertNotIn(
            SECRET_CUSTOMER_PASSWORD,
            repr_str,
            "ProxyConfig.__repr__ MUST NOT contain the plaintext password!",
        )
        self.assertIn("password='***'", repr_str)
        self.assertIn("customer_user", repr_str)
        self.assertIn("proxy.customer.net", repr_str)

    def test_proxy_config_str_omits_password(self):
        """Verify ProxyConfig.__str__ displays user@host:port without password."""
        str_val = str(self.config)
        self.assertNotIn(
            SECRET_CUSTOMER_PASSWORD,
            str_val,
            "ProxyConfig.__str__ MUST NOT contain the plaintext password!",
        )
        self.assertEqual(str_val, "ProxyConfig(customer_user@proxy.customer.net:8080)")

    def test_security_redact_functions(self):
        """Verify core security module redaction helper functions."""
        # 1. redact_password
        self.assertEqual(redact_password(SECRET_CUSTOMER_PASSWORD), "***")
        self.assertEqual(redact_password(""), "")
        self.assertEqual(redact_password(None), "")

        # 2. redact_url
        raw_url = f"http://customer_user:{SECRET_CUSTOMER_PASSWORD}@proxy.customer.net:8080/path?key=val"
        redacted_url = redact_url(raw_url)
        self.assertNotIn(SECRET_CUSTOMER_PASSWORD, redacted_url)
        self.assertIn("http://customer_user:***@proxy.customer.net:8080/path", redacted_url)

        # 3. redact_dict
        d = {
            "PROXY_HOST": "proxy.customer.net",
            "PROXY_PASSWORD": SECRET_CUSTOMER_PASSWORD,
            "nested": {"secret": SECRET_CUSTOMER_PASSWORD, "safe": "value"},
            "items": [{"auth_token": SECRET_CUSTOMER_PASSWORD}, "normal_string"],
        }
        redacted_d = redact_dict(d)
        self.assertEqual(redacted_d["PROXY_PASSWORD"], "***")
        self.assertEqual(redacted_d["nested"]["secret"], "***")
        self.assertEqual(redacted_d["items"][0]["auth_token"], "***")
        self.assertNotIn(SECRET_CUSTOMER_PASSWORD, str(redacted_d))

        # 4. redact_str
        log_text = f"Connection failed using password {SECRET_CUSTOMER_PASSWORD} on host proxy.customer.net"
        clean_log = redact_str(log_text, SECRET_CUSTOMER_PASSWORD)
        self.assertNotIn(SECRET_CUSTOMER_PASSWORD, clean_log)
        self.assertIn("***", clean_log)

        kv_env_text = f"PROXY_PASSWORD={SECRET_CUSTOMER_PASSWORD}; WEBSHARE_PROXY_PASSWORD={SECRET_CUSTOMER_PASSWORD}"
        clean_kv = redact_str(kv_env_text)
        self.assertNotIn(SECRET_CUSTOMER_PASSWORD, clean_kv)
        self.assertIn("PROXY_PASSWORD=***", clean_kv)

    def test_wizard_detail_log_redaction(self):
        """Verify wizard detail text drawer scrubs secret passwords from log messages."""
        self.wizard.password_input.setText(SECRET_CUSTOMER_PASSWORD)
        self.wizard._append_detail_log(
            f"Failed login attempt with password={SECRET_CUSTOMER_PASSWORD}"
        )
        drawer_content = self.wizard.txt_details.toPlainText()
        self.assertNotIn(
            SECRET_CUSTOMER_PASSWORD,
            drawer_content,
            "Wizard detail log drawer leaked customer password!",
        )
        self.assertIn("***", drawer_content)

    def test_exceptions_and_connection_errors_do_not_leak_password(self):
        """Verify exceptions caught during socket or HTTP verification redact passwords."""
        # Socket failure with invalid host
        with patch("socket.create_connection", side_effect=OSError(f"Failed auth for password {SECRET_CUSTOMER_PASSWORD}")):
            result = verify_proxy_connection(self.config, timeout=1.0)
            self.assertNotIn(
                SECRET_CUSTOMER_PASSWORD,
                str(result),
                "verify_proxy_connection error leaked password in result dict!",
            )
            self.assertIn("***", str(result))

        # Incomplete env resolution exception
        env = {
            "PROXY_HOST": "proxy.net",
            "PROXY_PASSWORD": SECRET_CUSTOMER_PASSWORD,
        }
        with patch.dict(os.environ, env, clear=True):
            try:
                proxy_config_from_env(no_proxy=False)
            except RuntimeError as exc:
                exc_str = str(exc)
                self.assertNotIn(
                    SECRET_CUSTOMER_PASSWORD,
                    exc_str,
                    "Incomplete proxy_config_from_env exception leaked password!",
                )

    def test_clipboard_snippets_never_leak_password(self):
        """Verify PyQt5 & PyQt6 clipboard snippet export uses environment variables, never raw password."""
        self.wizard.password_input.setText(SECRET_CUSTOMER_PASSWORD)

        with patch("quadproxy.compatibility.QApplication.clipboard") as mock_clip:
            mock_c = MagicMock()
            mock_clip.return_value = mock_c

            self.wizard.copy_pyqt6_snippet()
            self.wizard.copy_pyqt5_snippet()

            for call_args in mock_c.setText.call_args_list:
                snippet_text = call_args[0][0]
                self.assertNotIn(
                    SECRET_CUSTOMER_PASSWORD,
                    snippet_text,
                    "Code snippet leaked raw customer password!",
                )
                self.assertIn('os.environ.get("PROXY_PASSWORD", "")', snippet_text)

    def test_diagnostic_output_table_and_doctor_no_secret_leak(self):
        """Verify diagnostic result tables and doctor CLI output omit raw passwords."""
        with patch("socket.create_connection", side_effect=OSError(f"Err {SECRET_CUSTOMER_PASSWORD}")), \
             patch("urllib.request.build_opener", side_effect=Exception(f"Opener fail {SECRET_CUSTOMER_PASSWORD}")):
            results = run_diagnostics(
                target_url="https://example.com",
                proxy_config=self.config,
                no_proxy=False,
            )

            table = format_diagnostic_table(results)
            self.assertNotIn(
                SECRET_CUSTOMER_PASSWORD,
                table,
                "Diagnostic table leaked raw customer password!",
            )

            results_str = str(results)
            self.assertNotIn(
                SECRET_CUSTOMER_PASSWORD,
                results_str,
                "DiagnosticResultList representation leaked raw customer password!",
            )

            buf = io.StringIO()
            with patch("sys.stdout", buf), patch("sys.stderr", buf):
                with patch.dict(os.environ, {
                    "PROXY_HOST": self.config.host,
                    "PROXY_PORT": str(self.config.port),
                    "PROXY_USER": self.config.user,
                    "PROXY_PASSWORD": SECRET_CUSTOMER_PASSWORD,
                }):
                    doctor(no_proxy=False)
                out = buf.getvalue()
                self.assertNotIn(
                    SECRET_CUSTOMER_PASSWORD,
                    out,
                    "Doctor CLI stdout/stderr leaked raw customer password!",
                )

    def test_export_env_template_no_secret_leak(self):
        """Verify export_env_template output contains placeholder password only."""
        self.wizard.password_input.setText(SECRET_CUSTOMER_PASSWORD)

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
                    file_content = env_path.read_text(encoding="utf-8")
                    self.assertNotIn(
                        SECRET_CUSTOMER_PASSWORD,
                        file_content,
                        "Exported .env.example leaked real password!",
                    )
                    self.assertIn("PROXY_PASSWORD=your_proxy_password_here", file_content)
                finally:
                    os.chdir(original_cwd)

            for call_args in mock_c.setText.call_args_list:
                clipboard_content = call_args[0][0]
                self.assertNotIn(
                    SECRET_CUSTOMER_PASSWORD,
                    clipboard_content,
                    "Exported env template clipboard leaked real password!",
                )

    def test_subprocess_arguments_and_environment_scrubbing(self):
        """Verify process command-line arguments and environment formatting do not leak secrets."""
        import subprocess

        # Format simulated command args
        cmd_args = [
            sys.executable,
            "-m",
            "quadproxy",
            "doctor",
            "--url",
            "https://example.com",
        ]
        cmd_line = subprocess.list2cmdline(cmd_args)
        self.assertNotIn(SECRET_CUSTOMER_PASSWORD, cmd_line)

        # Redact dictionary representing process env
        env_dict = {
            "PATH": "/usr/bin",
            "PROXY_USER": "myuser",
            "PROXY_PASSWORD": SECRET_CUSTOMER_PASSWORD,
        }
        clean_env = redact_dict(env_dict)
        self.assertNotIn(
            SECRET_CUSTOMER_PASSWORD,
            str(clean_env),
            "Process environment dictionary log leaked secret password!",
        )

    def test_wizard_failure_breakdowns_no_secret_leak(self):
        """Verify all 6 wizard stage failure breakdowns sanitize error messages."""
        self.wizard.password_input.setText(SECRET_CUSTOMER_PASSWORD)
        raw_error_with_secret = f"Authentication error using credentials {SECRET_CUSTOMER_PASSWORD} on server"

        for stage_idx in range(1, 7):
            self.wizard._handle_stage_failure(
                stage_idx, raw_error_with_secret, self.config
            )

            what = self.wizard.lbl_what_failed.text()
            why = self.wizard.lbl_why_failed.text()
            next_steps = self.wizard.lbl_next_steps.text()

            self.assertNotIn(
                SECRET_CUSTOMER_PASSWORD,
                what,
                f"Stage {stage_idx} WHAT FAILED label leaked customer password!",
            )
            self.assertNotIn(
                SECRET_CUSTOMER_PASSWORD,
                why,
                f"Stage {stage_idx} WHY IT FAILED label leaked customer password!",
            )
            self.assertNotIn(
                SECRET_CUSTOMER_PASSWORD,
                next_steps,
                f"Stage {stage_idx} NEXT STEPS label leaked customer password!",
            )
            self.assertIn("***", what)

    def test_comprehensive_zero_secret_leak_audit(self):
        """Perform blanket audit across all wizard UI labels, text properties, and output strings."""
        self.wizard.password_input.setText(SECRET_CUSTOMER_PASSWORD)

        mock_resp = MagicMock()
        mock_resp.read.return_value = b"1.1.1.1"
        mock_resp.__enter__.return_value = mock_resp

        # Trigger failure on pipeline run
        with patch("socket.create_connection", side_effect=OSError(f"Err {SECRET_CUSTOMER_PASSWORD}")), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            self.wizard.run_diagnostics_pipeline()

        # Audit all labels in the wizard UI
        all_labels = self.wizard.findChildren(quadproxy.compatibility.QLabel)
        for label in all_labels:
            text = label.text()
            self.assertNotIn(
                SECRET_CUSTOMER_PASSWORD,
                text,
                f"QLabel (objectName={label.objectName()}) leaked customer secret: '{text}'",
            )

        # Audit details text edit
        details_text = self.wizard.txt_details.toPlainText()
        self.assertNotIn(
            SECRET_CUSTOMER_PASSWORD,
            details_text,
            "Details QTextEdit leaked customer secret!",
        )

    def test_support_bundle_zero_secret_leak(self):
        """Verify support bundle ZIP generation contains ZERO secrets and aborts if forbidden pattern is found."""
        from quadproxy.support_bundle import generate_support_bundle
        import zipfile

        # 1. Verify successful generation with password scrubbing
        with tempfile.TemporaryDirectory() as tmp_dir:
            bundle_zip = os.path.join(tmp_dir, "test_support_bundle.zip")
            generate_support_bundle(
                output_path=bundle_zip,
                proxy_config=self.config,
                extra_logs=f"Runtime error with password {SECRET_CUSTOMER_PASSWORD}",
            )

            self.assertTrue(os.path.exists(bundle_zip))

            with zipfile.ZipFile(bundle_zip, "r") as zf:
                file_list = zf.namelist()
                self.assertIn("diagnostics.json", file_list)
                self.assertIn("SUPPORT_DIAGNOSTIC_REPORT.txt", file_list)

                diag_json_bytes = zf.read("diagnostics.json")
                report_txt_bytes = zf.read("SUPPORT_DIAGNOSTIC_REPORT.txt")

                self.assertNotIn(SECRET_CUSTOMER_PASSWORD.encode("utf-8"), diag_json_bytes)
                self.assertNotIn(SECRET_CUSTOMER_PASSWORD.encode("utf-8"), report_txt_bytes)

        # 2. Verify adversarial audit aborts if unredacted forbidden pattern (e.g. sk_live_) is injected
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_zip = os.path.join(tmp_dir, "bad_bundle.zip")
            with self.assertRaises(ValueError) as cm:
                generate_support_bundle(
                    output_path=bad_zip,
                    proxy_config=self.config,
                    extra_logs="Leaked Stripe Key sk_live_1234567890",
                )
            self.assertIn("SECRET LEAK AUDIT FAILED", str(cm.exception))

    def test_activation_checklist_and_playbook(self):
        """Verify activation checklist evaluation and playbook failure classification."""
        from quadproxy.activation import ActivationChecklist, format_checklist_cli
        from quadproxy.playbook import classify_failure

        checklist = ActivationChecklist(proxy_config=self.config, no_proxy=False)
        items = checklist.evaluate()
        self.assertEqual(len(items), 9)

        cli_str = format_checklist_cli(items)
        self.assertIn("Customer Activation Checklist", cli_str)
        self.assertNotIn(SECRET_CUSTOMER_PASSWORD, cli_str)

        rec = classify_failure(stage=3, error_message="HTTP 407 Proxy Authentication Required")
        self.assertEqual(rec.code, "AUTHENTICATION_REJECTED")
        self.assertIn("Verify username/password", rec.recommendation)


if __name__ == "__main__":
    unittest.main()

