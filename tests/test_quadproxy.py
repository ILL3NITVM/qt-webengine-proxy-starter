from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

PRODUCT_DIR = Path(__file__).resolve().parents[1]
if str(PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(PRODUCT_DIR))

import quadproxy
from quadproxy.diagnostics import (
    ProxyConfigurationError,
    ProxyAuthenticationError,
    doctor,
    run_diagnostics,
    validate_environment,
    verify_proxy_connection,
)


class QuadProxyPackageTests(unittest.TestCase):
    def test_imports_and_version(self):
        self.assertEqual(quadproxy.__version__, "1.1.0")
        self.assertTrue(hasattr(quadproxy, "ProxyConfig"))
        self.assertTrue(hasattr(quadproxy, "configure_application_proxy"))
        self.assertTrue(hasattr(quadproxy, "proxy_config_from_env"))

    def test_diagnostics_validate_environment_success(self):
        env = {
            "PROXY_HOST": "127.0.0.1",
            "PROXY_PORT": "8080",
            "PROXY_USER": "testuser",
            "PROXY_PASSWORD": "testpassword",
        }
        with patch.dict(os.environ, env, clear=True):
            config, warnings = validate_environment(no_proxy=False)
            self.assertIsNotNone(config)
            self.assertEqual(config.host, "127.0.0.1")
            self.assertEqual(warnings, [])

    def test_diagnostics_validate_environment_error(self):
        env = {"PROXY_HOST": "127.0.0.1"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ProxyConfigurationError):
                validate_environment(no_proxy=False)

    def test_run_diagnostics_direct_mode(self):
        report = run_diagnostics(no_proxy=True)
        self.assertTrue(report.get("no_proxy"))
        self.assertTrue(report.get("config_valid"))
        self.assertEqual(report.get("config"), "None (Direct Mode)")
        self.assertIn("connectivity", report)

    def test_doctor_cli_direct(self):
        exit_code = doctor(no_proxy=True)
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
