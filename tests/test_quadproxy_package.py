"""Comprehensive unit test suite for the quadproxy package."""

from pathlib import Path
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

PRODUCT_DIR = Path(__file__).resolve().parents[1]
if str(PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(PRODUCT_DIR))

import quadproxy
from quadproxy.security import (
    redact_dict,
    redact_password,
    redact_str,
    redact_url,
)
from quadproxy.compatibility import (
    QT6,
    QNETWORK_HTTP_PROXY,
    QNETWORK_NO_PROXY,
    exec_app,
)
from quadproxy.config import (
    PROXY_HOST,
    PROXY_PASSWORD,
    PROXY_PORT,
    PROXY_SCHEME,
    PROXY_USER,
    SUPPORTED_PROXY_SCHEME,
    WEBSHARE_PROXY_PASSWORD,
    ProxyConfig,
    normalize_proxy_scheme,
    proxy_config_from_env,
)
from quadproxy.authentication import ProxyAuthenticator
from quadproxy.verification import (
    PROXY_CHECK_URL,
    RETRY_DELAYS_MS,
    RETRY_DELAYS_SEC,
    TIMEOUT_MS,
    TIMEOUT_SEC,
    validate_ip_address,
    verify_proxy_http,
)
from quadproxy.diagnostics import (
    DiagnosticResult,
    DiagnosticResultList,
    ProxyAuthenticationError,
    ProxyConfigurationError,
    doctor,
    format_diagnostic_table,
    run_diagnostics,
    validate_environment,
    verify_proxy_connection,
)
from quadproxy.proxy import ProxyCheckingWindow, configure_application_proxy
from quadproxy.cli import main as doctor_script_main
from quadproxy.__main__ import build_parser, main as cli_main


class SecurityModuleTests(unittest.TestCase):
    def test_redact_password(self):
        self.assertEqual(redact_password("secret"), "***")
        self.assertEqual(redact_password(""), "")
        self.assertEqual(redact_password(None), "")

    def test_redact_url(self):
        url = "http://user:my_secret_pass@proxy.example.com:8080/path?arg=val"
        redacted = redact_url(url)
        self.assertNotIn("my_secret_pass", redacted)
        self.assertIn("user:***", redacted)
        self.assertEqual(redact_url(""), "")

        url_no_cred = "http://proxy.example.com:8080/path"
        self.assertEqual(redact_url(url_no_cred), url_no_cred)

        # Malformed URL fallback regex branch
        malformed = "http://user:secret_pass@invalid host/path"
        redacted_mal = redact_url(malformed)
        self.assertNotIn("secret_pass", redacted_mal)

    def test_redact_dict(self):
        data = {
            "user": "alice",
            "password": "secret_password",
            "nested": {
                "api_key": "12345-secret",
                "normal": "value",
                "auth_cred": "my_cred",
            },
            "list": [{"token": "abc-xyz", "pwd": "p1"}, "normal_elem"],
        }
        redacted = redact_dict(data)
        self.assertEqual(redacted["user"], "alice")
        self.assertEqual(redacted["password"], "***")
        self.assertEqual(redacted["nested"]["api_key"], "***")
        self.assertEqual(redacted["nested"]["normal"], "value")
        self.assertEqual(redacted["nested"]["auth_cred"], "***")
        self.assertEqual(redacted["list"][0]["token"], "***")
        self.assertEqual(redacted["list"][0]["pwd"], "***")

    def test_redact_str(self):
        text = "Error in PROXY_PASSWORD=my_secret_pass during connection"
        scrubbed = redact_str(text, password="my_secret_pass")
        self.assertNotIn("my_secret_pass", scrubbed)
        self.assertIn("***", scrubbed)
        self.assertEqual(redact_str(""), "")

        # Test pattern-based key-value redaction
        text2 = "WEBSHARE_PROXY_PASSWORD=sec123 PASSWORD=pass456 API_KEY=key789"
        scrubbed2 = redact_str(text2)
        self.assertNotIn("sec123", scrubbed2)
        self.assertNotIn("pass456", scrubbed2)
        self.assertNotIn("key789", scrubbed2)


class CompatibilityModuleTests(unittest.TestCase):
    def test_constants_and_types(self):
        self.assertIsInstance(QT6, bool)
        self.assertIsNotNone(QNETWORK_HTTP_PROXY)
        self.assertIsNotNone(QNETWORK_NO_PROXY)

    def test_exec_app_calls_correct_method(self):
        mock_app = MagicMock()
        mock_app.exec.return_value = 0
        mock_app.exec_.return_value = 0
        ret = exec_app(mock_app)
        self.assertEqual(ret, 0)


class ConfigModuleTests(unittest.TestCase):
    def test_package_exports(self):
        self.assertEqual(quadproxy.__version__, "1.1.0")
        self.assertIn("ProxyConfig", quadproxy.__all__)

    def test_env_constants(self):
        self.assertEqual(PROXY_HOST, "PROXY_HOST")
        self.assertEqual(PROXY_PORT, "PROXY_PORT")
        self.assertEqual(PROXY_USER, "PROXY_USER")
        self.assertEqual(PROXY_PASSWORD, "PROXY_PASSWORD")
        self.assertEqual(WEBSHARE_PROXY_PASSWORD, "WEBSHARE_PROXY_PASSWORD")
        self.assertEqual(PROXY_SCHEME, "PROXY_SCHEME")
        self.assertEqual(SUPPORTED_PROXY_SCHEME, "http")

    def test_proxy_config_representation(self):
        cfg = ProxyConfig(host="h", port=80, user="u", password="secret_password_123", scheme="http")
        self.assertNotIn("secret_password_123", repr(cfg))
        self.assertNotIn("secret_password_123", str(cfg))
        self.assertIn("password='***'", repr(cfg))
        self.assertEqual(str(cfg), "ProxyConfig(u@h:80)")

    def test_proxy_scheme_validation(self):
        self.assertEqual(normalize_proxy_scheme("HTTP"), "http")
        with self.assertRaises(ValueError):
            ProxyConfig(host="h", port=1080, user="u", password="p", scheme="socks5")


class AuthenticationModuleTests(unittest.TestCase):
    def test_proxy_authenticator_sets_credentials(self):
        cfg = ProxyConfig(host="h", port=80, user="user1", password="pass1")
        auth = ProxyAuthenticator(cfg)
        mock_qauth = MagicMock()
        auth.handle_authentication(MagicMock(), mock_qauth)
        mock_qauth.setUser.assert_called_once_with("user1")
        mock_qauth.setPassword.assert_called_once_with("pass1")

    def test_proxy_authenticator_none_config(self):
        auth = ProxyAuthenticator(None)
        mock_qauth = MagicMock()
        auth.handle_authentication(MagicMock(), mock_qauth)
        mock_qauth.setUser.assert_not_called()
        mock_qauth.setPassword.assert_not_called()

    def test_attach_to_page(self):
        cfg = ProxyConfig(host="h", port=80, user="user1", password="pass1")
        auth = ProxyAuthenticator(cfg)
        mock_page = MagicMock()
        auth.attach_to_page(mock_page)
        mock_page.proxyAuthenticationRequired.connect.assert_called_once_with(
            auth.handle_authentication
        )

        # Attach to page without signal attribute should not raise error
        auth.attach_to_page(object())


class VerificationModuleTests(unittest.TestCase):
    def test_validate_ip_address(self):
        self.assertEqual(validate_ip_address("1.1.1.1"), "1.1.1.1")
        self.assertEqual(validate_ip_address(" ::1 "), "::1")
        with self.assertRaises(ValueError):
            validate_ip_address("invalid-ip")
        with self.assertRaises(ValueError):
            validate_ip_address("")

    def test_verification_constants(self):
        self.assertEqual(PROXY_CHECK_URL, "https://api.ipify.org")
        self.assertEqual(RETRY_DELAYS_MS, (2000, 5000, 10000))
        self.assertEqual(RETRY_DELAYS_SEC, (2.0, 5.0, 10.0))
        self.assertEqual(TIMEOUT_MS, 75000)
        self.assertEqual(TIMEOUT_SEC, 75.0)

    @patch("urllib.request.build_opener")
    def test_verify_proxy_http_success(self, mock_build_opener):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"203.0.113.195\n"
        mock_resp.__enter__.return_value = mock_resp
        mock_build_opener.return_value.open.return_value = mock_resp

        ok, ip = verify_proxy_http(None, retry_delays=(0.01,))
        self.assertTrue(ok)
        self.assertEqual(ip, "203.0.113.195")

    @patch("urllib.request.build_opener")
    def test_verify_proxy_http_failure(self, mock_build_opener):
        mock_build_opener.return_value.open.side_effect = RuntimeError("Connection failed")
        ok, err = verify_proxy_http(None, retry_delays=(0.01,))
        self.assertFalse(ok)
        self.assertIn("Verification failed", err)


class DiagnosticsModuleTests(unittest.TestCase):
    def test_run_diagnostics_no_proxy(self):
        results = run_diagnostics(no_proxy=True)
        self.assertEqual(len(results), 12)
        self.assertTrue(all(r.passed for r in results))
        table = format_diagnostic_table(results)
        self.assertIn("Stage", table)
        self.assertIn("Status", table)

    def test_run_diagnostics_with_config(self):
        cfg = ProxyConfig(host="127.0.0.1", port=9999, user="u", password="p")
        results = run_diagnostics(proxy_config=cfg)
        self.assertEqual(len(results), 12)
        self.assertEqual(results[0].stage, 1)
        self.assertTrue(results[0].passed)

    def test_run_diagnostics_missing_env(self):
        results = run_diagnostics(proxy_config=None, no_proxy=False)
        self.assertEqual(len(results), 12)
        self.assertFalse(results[2].passed)
        self.assertIn("Missing required proxy environment variables", results[2].message)
        self.assertFalse(results[3].passed)
        self.assertFalse(results[4].passed)
        self.assertFalse(results[5].passed)
        self.assertFalse(results[10].passed)

    def test_diagnostic_result_list_dict_interface(self):
        res_list = DiagnosticResultList(
            [DiagnosticResult(stage=1, name="Test", passed=True, message="OK")],
            no_proxy=True,
        )
        self.assertEqual(res_list.get("no_proxy"), True)
        self.assertTrue(res_list.get("config_valid"))
        self.assertEqual(res_list["no_proxy"], True)
        self.assertIn("connectivity", res_list)
        self.assertEqual(res_list[0].stage, 1)

    def test_validate_environment(self):
        with patch.dict(os.environ, {}, clear=True):
            cfg, warnings = validate_environment(no_proxy=True)
            self.assertIsNone(cfg)
            self.assertEqual(warnings, [])

            cfg2, warnings2 = validate_environment(no_proxy=False)
            self.assertIsNone(cfg2)
            self.assertEqual(len(warnings2), 1)

        with patch.dict(os.environ, {"PROXY_HOST": "h"}, clear=True):
            with self.assertRaises(ProxyConfigurationError):
                validate_environment(no_proxy=False)

    def test_verify_proxy_connection_direct(self):
        res = verify_proxy_connection(config=None, timeout=2.0)
        self.assertIn(res["status"], ("ok", "error"))

    @patch("socket.create_connection")
    def test_verify_proxy_connection_socket_failure(self, mock_socket):
        mock_socket.side_effect = OSError("Connection refused")
        cfg = ProxyConfig(host="127.0.0.1", port=9999, user="u", password="p")
        res = verify_proxy_connection(config=cfg, timeout=1.0)
        self.assertEqual(res["status"], "error")
        self.assertIn("failed", res["message"])


class MainCLITests(unittest.TestCase):
    def test_parser(self):
        parser = build_parser()
        args = parser.parse_args(["doctor"])
        self.assertEqual(args.command, "doctor")

        args_check = parser.parse_args(["check", "--no-proxy"])
        self.assertEqual(args_check.command, "check")
        self.assertTrue(args_check.no_proxy)

        args_run = parser.parse_args(["run", "--no-proxy"])
        self.assertEqual(args_run.command, "run")
        self.assertTrue(args_run.no_proxy)


    def test_cli_doctor_no_proxy(self):
        ret = cli_main(["doctor", "--no-proxy"])
        self.assertEqual(ret, 0)

    def test_cli_check_no_proxy(self):
        ret = cli_main(["check", "--no-proxy"])
        self.assertEqual(ret, 0)

    def test_quadproxy_doctor_script_defaults_to_doctor(self):
        ret = doctor_script_main(["--no-proxy"])
        self.assertEqual(ret, 0)

    @patch("quadproxy.__main__.exec_app", return_value=0)
    @patch("quadproxy.__main__.ProxyCheckingWindow")
    @patch("quadproxy.__main__.QApplication")
    def test_cli_run_no_proxy(self, mock_qapp, mock_window, mock_exec):
        ret = cli_main(["run", "--no-proxy"])
        self.assertEqual(ret, 0)


    def test_cli_zero_config_onboarding(self):
        with patch.dict(os.environ, {}, clear=True):
            ret = cli_main([])
            self.assertEqual(ret, 0)

    def test_cli_config_error(self):
        with patch.dict(os.environ, {"PROXY_HOST": "h"}, clear=True):
            ret = cli_main(["doctor"])
            self.assertEqual(ret, 2)


class ProxyModuleTests(unittest.TestCase):
    @patch("quadproxy.proxy.QNetworkProxy.setApplicationProxy")
    def test_configure_application_proxy(self, mock_set_proxy):
        configure_application_proxy(None)
        mock_set_proxy.assert_called_once()

        mock_set_proxy.reset_mock()
        cfg = ProxyConfig(host="proxy.com", port=8080, user="u", password="p")
        configure_application_proxy(cfg)
        mock_set_proxy.assert_called_once()

    @patch("quadproxy.proxy.QTimer.singleShot")
    def test_proxy_checking_window_flow(self, mock_timer):
        from quadproxy.compatibility import QApplication, QWidget

        _app = QApplication.instance() or QApplication(["-platform", "offscreen"])

        class DummySignal(MagicMock):
            def connect(self, slot):
                pass

        class DummyPage(MagicMock):
            def __init__(self):
                super().__init__()
                self.proxyAuthenticationRequired = DummySignal()
            def runJavaScript(self, script, callback):
                callback("1.2.3.4")

        class DummyView(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self._page = DummyPage()
                self.loadFinished = DummySignal()
            def setUrl(self, url):
                pass
            def page(self):
                return self._page

        with patch("quadproxy.proxy.QWebEngineView", DummyView):
            cfg = ProxyConfig(host="proxy.com", port=8080, user="u", password="p")
            window = ProxyCheckingWindow("https://target.com", cfg)
            self.assertEqual(window.target_url, "https://target.com")

            # Test start
            window.start()
            mock_timer.assert_called()

            # Test _start_attempt
            window._start_attempt()
            self.assertEqual(window.attempt, 1)

            # Test _load_finished error
            window._load_finished(False)

            # Test _validate_ip
            window.finished = False
            window._validate_ip("1.2.3.4")
            self.assertTrue(window.finished)
            self.assertIn("Proxy verified", window.status.text())




if __name__ == "__main__":
    unittest.main()
