from pathlib import Path
import unittest

PACKAGE_DIR = Path(__file__).resolve().parents[1]
STARTER_SOURCE = PACKAGE_DIR / "qt_proxy_starter.py"
MAIN_SOURCE = PACKAGE_DIR / "quadproxy" / "__main__.py"
EXAMPLES_DIR = PACKAGE_DIR / "examples"
README = PACKAGE_DIR / "README.md"
QUICKSTART = PACKAGE_DIR / "docs" / "QUICKSTART.md"
API_REFERENCE = PACKAGE_DIR / "docs" / "API_REFERENCE.md"
FIRST_STEPS = PACKAGE_DIR / "FIRST_STEPS.md"


class StaticContractTests(unittest.TestCase):
    def test_proxy_setup_precedes_qapplication_in_main(self):
        """Verify configure_application_proxy is invoked before QApplication instantiation in main starter."""
        source = STARTER_SOURCE.read_text(encoding="utf-8")
        configure_index = source.index("configure_application_proxy(proxy_config)")
        app_index = source.index("app = QApplication")
        self.assertLess(configure_index, app_index)

    def test_proxy_setup_precedes_qapplication_in_cli_main(self):
        """Verify configure_application_proxy is invoked before QApplication in CLI __main__.py."""
        source = MAIN_SOURCE.read_text(encoding="utf-8")
        configure_index = source.index("configure_application_proxy(proxy_config)")
        app_index = source.index("app = QApplication")
        self.assertLess(configure_index, app_index)

    def test_proxy_setup_precedes_qapplication_in_examples(self):
        """Verify configure_application_proxy/attach_quadproxy precedes QApplication in all 5 examples."""
        for ex_path in sorted(EXAMPLES_DIR.glob("*.py")):
            source = ex_path.read_text(encoding="utf-8")
            if "app = QApplication" in source or "QApplication(" in source:
                config_pos = max(
                    source.find("configure_application_proxy"),
                    source.find("attach_quadproxy"),
                    source.find("setApplicationProxy"),
                )
                self.assertGreater(
                    config_pos,
                    -1,
                    f"Example {ex_path.name} must configure proxy before QApplication",
                )
                app_pos = source.find("app = QApplication")
                if app_pos == -1:
                    app_pos = source.find("QApplication(")
                self.assertLess(
                    config_pos,
                    app_pos,
                    f"Example {ex_path.name} must call configure_application_proxy before QApplication",
                )

    def test_no_domain_specific_terms_in_deliverable(self):
        """Verify ZERO proprietary or broker/seed terms exist anywhere in the deliverable package."""
        forbidden = [
            "pocket" + "option",
            "quadcom_" + "po",
            "bro" + "ker_account",
            "tra" + "ding_seed",
            "binary_" + "options",
            "po_browser_" + "automation",
        ]
        violations = []
        for file_path in sorted(PACKAGE_DIR.rglob("*")):
            if file_path.is_file() and not any(
                part in file_path.parts for part in ("__pycache__", ".git", ".pytest_cache")
            ):
                if file_path.suffix in (".py", ".md", ".txt", ".toml"):
                    text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                    for term in forbidden:
                        if term in text:
                            violations.append((file_path.relative_to(PACKAGE_DIR), term))

        self.assertEqual([], violations, f"Forbidden terms found in package files: {violations}")

    def test_customer_install_docs_match_zip_delivery(self):
        """Customer docs must install from the paid zip, not from an assumed PyPI package."""
        self.assertTrue(FIRST_STEPS.exists())
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (README, QUICKSTART, FIRST_STEPS)
        )
        self.assertIn('python -m pip install -e ".[pyqt6]"', combined)
        self.assertIn("python -m quadproxy doctor --no-proxy", combined)
        self.assertIn("python -m quadproxy doctor", combined)
        self.assertNotIn("pip install PyQt6 PyQt6-WebEngine quadproxy", combined)
        self.assertNotIn("pip install quadproxy", combined)
        shipped_docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [README, QUICKSTART, FIRST_STEPS, PACKAGE_DIR / "docs" / "TROUBLESHOOTING.md"]
        )
        self.assertNotIn("unittest discover tests", shipped_docs)

    def test_api_reference_matches_diagnostics_contract(self):
        api = API_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("target_url: str", api)
        self.assertIn("proxy_config: Optional[ProxyConfig]", api)
        self.assertIn(") -> DiagnosticResultList", api)
        self.assertIn("One or more diagnostic stages failed", api)
        self.assertNotIn("def run_diagnostics(no_proxy: bool = False) -> Dict", api)



if __name__ == "__main__":
    unittest.main()
