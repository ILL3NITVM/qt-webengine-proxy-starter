from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

# Insert product directory into python path for direct import
PRODUCT_DIR = Path(__file__).resolve().parents[1]
if str(PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(PRODUCT_DIR))

import qt_proxy_starter as starter
import quadproxy.config as config_mod


class OnboardingAndConfigTests(unittest.TestCase):
    def test_config_constants(self):
        """Verify environment variable configuration key constants."""
        self.assertEqual(config_mod.PROXY_HOST, "PROXY_HOST")
        self.assertEqual(config_mod.PROXY_PORT, "PROXY_PORT")
        self.assertEqual(config_mod.PROXY_USER, "PROXY_USER")
        self.assertEqual(config_mod.PROXY_PASSWORD, "PROXY_PASSWORD")
        self.assertEqual(config_mod.WEBSHARE_PROXY_PASSWORD, "WEBSHARE_PROXY_PASSWORD")
        self.assertEqual(config_mod.PROXY_SCHEME, "PROXY_SCHEME")

    def test_zero_config_first_run_returns_onboarding_guide(self):
        """Zero proxy environment variables must return onboarding guide instead of crashing."""
        with patch.dict(os.environ, {}, clear=True):
            config, onboarding_msg = starter.proxy_config_from_env(no_proxy=False)
            self.assertIsNone(config)
            self.assertIsNotNone(onboarding_msg)
            self.assertIn("First-Run Setup & Onboarding Guide", onboarding_msg)
            self.assertIn("THIS PRODUCT DOES NOT INCLUDE A BUILT-IN PROXY SERVICE", onboarding_msg)
            self.assertIn("$env:PROXY_HOST=", onboarding_msg)
            self.assertIn("export PROXY_HOST=", onboarding_msg)
            self.assertIn("--no-proxy", onboarding_msg)

    def test_no_proxy_flag_disables_proxy_without_onboarding_msg(self):
        """--no-proxy flag must return (None, None) allowing direct diagnostic execution."""
        with patch.dict(os.environ, {}, clear=True):
            config, onboarding_msg = starter.proxy_config_from_env(no_proxy=True)
            self.assertIsNone(config)
            self.assertIsNone(onboarding_msg)

    def test_generic_proxy_credentials(self):
        """Generic PROXY_PASSWORD environment variable resolves ProxyConfig correctly."""
        env = {
            "PROXY_HOST": "proxy.example.com",
            "PROXY_PORT": "8080",
            "PROXY_USER": "myuser",
            "PROXY_PASSWORD": "secret_generic_password",
        }
        with patch.dict(os.environ, env, clear=True):
            config, onboarding_msg = starter.proxy_config_from_env(no_proxy=False)
            self.assertIsNotNone(config)
            self.assertIsNone(onboarding_msg)
            self.assertEqual(config.host, "proxy.example.com")
            self.assertEqual(config.port, 8080)
            self.assertEqual(config.user, "myuser")
            self.assertEqual(config.password, "secret_generic_password")
            self.assertEqual(config.scheme, "http")

    def test_http_proxy_scheme_is_normalized(self):
        """Supported PROXY_SCHEME environment variable is normalized on ProxyConfig."""
        env = {
            "PROXY_HOST": "proxy.example.com",
            "PROXY_PORT": "8080",
            "PROXY_USER": "myuser",
            "PROXY_PASSWORD": "secret_generic_password",
            "PROXY_SCHEME": "HTTP",
        }
        with patch.dict(os.environ, env, clear=True):
            config, onboarding_msg = starter.proxy_config_from_env(no_proxy=False)
            self.assertIsNotNone(config)
            self.assertEqual(config.scheme, "http")

    def test_unsupported_proxy_scheme_is_rejected(self):
        """Unsupported schemes must fail early instead of silently using HTTP behavior."""
        env = {
            "PROXY_HOST": "proxy.example.com",
            "PROXY_PORT": "1080",
            "PROXY_USER": "myuser",
            "PROXY_PASSWORD": "secret_generic_password",
            "PROXY_SCHEME": "socks5",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                starter.proxy_config_from_env(no_proxy=False)
            self.assertIn("authenticated HTTP proxies only", str(ctx.exception))

    def test_legacy_webshare_password_fallback(self):
        """WEBSHARE_PROXY_PASSWORD resolves for backwards compatibility when PROXY_PASSWORD is unset."""
        env = {
            "PROXY_HOST": "proxy.webshare.io",
            "PROXY_PORT": "9999",
            "PROXY_USER": "webshare_user",
            "WEBSHARE_PROXY_PASSWORD": "secret_legacy_password",
        }
        with patch.dict(os.environ, env, clear=True):
            config, onboarding_msg = starter.proxy_config_from_env(no_proxy=False)
            self.assertIsNotNone(config)
            self.assertIsNone(onboarding_msg)
            self.assertEqual(config.user, "webshare_user")
            self.assertEqual(config.password, "secret_legacy_password")

    def test_missing_incomplete_credentials_raises_clean_error(self):
        """Incomplete credentials raise RuntimeError detailing missing variables without leaking data."""
        incomplete_envs = [
            {"PROXY_HOST": "proxy.example.com", "PROXY_PORT": "8080"},
            {"PROXY_USER": "u", "PROXY_PASSWORD": "p"},
            {"PROXY_HOST": "proxy.example.com", "PROXY_USER": "u", "PROXY_PASSWORD": "p"},
        ]
        for env in incomplete_envs:
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises(RuntimeError) as ctx:
                    starter.proxy_config_from_env(no_proxy=False)
                err_msg = str(ctx.exception)
                self.assertIn("Incomplete proxy configuration", err_msg)

    def test_invalid_port_raises_clean_error(self):
        """Non-integer PROXY_PORT raises a descriptive RuntimeError."""
        env = {
            "PROXY_HOST": "proxy.example.com",
            "PROXY_PORT": "invalid_port_number",
            "PROXY_USER": "myuser",
            "PROXY_PASSWORD": "mypassword",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                starter.proxy_config_from_env(no_proxy=False)
            self.assertIn("PROXY_PORT must be a valid integer", str(ctx.exception))

    def test_password_never_appears_in_logs_repr_or_str(self):
        """ProxyConfig string representation and error messages must mask password."""
        secret_pass = "ultra_sensitive_password_123"
        config = starter.ProxyConfig(
            host="proxy.example.com",
            port=8080,
            user="test_user",
            password=secret_pass,
        )
        repr_str = repr(config)
        str_str = str(config)

        self.assertNotIn(secret_pass, repr_str)
        self.assertNotIn(secret_pass, str_str)
        self.assertIn("password='***'", repr_str)
        self.assertIn("test_user@proxy.example.com:8080", str_str)


if __name__ == "__main__":
    unittest.main()
