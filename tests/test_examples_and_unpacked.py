"""Unit tests for example scripts execution and zero-config unpacked zip execution."""

import ast
import importlib.util
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

PACKAGE_DIR = Path(__file__).resolve().parents[1]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from quadproxy.compatibility import QApplication, QWidget, QMainWindow
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


class MockWidget(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def _get_child_mock(self, **kw):
        return MagicMock(**kw)


class DummyWebEngineView(MockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._page = DummyPage()
        self.loadFinished = DummySignal()

    def setUrl(self, url):
        pass

    def page(self):
        return self._page


mock_webengine_module = MagicMock()
mock_webengine_module.QWebEngineView = DummyWebEngineView
sys.modules["PyQt5.QtWebEngineWidgets"] = mock_webengine_module
sys.modules["PyQt6.QtWebEngineWidgets"] = mock_webengine_module

ROOT_DIR = PACKAGE_DIR.parents[1]
EXAMPLES_DIR = PACKAGE_DIR / "examples"


def make_mock_app(*args, **kwargs):
    app = MagicMock()
    app.exec_.return_value = 0
    app.exec.return_value = 0
    return app




class ExampleScriptsTests(unittest.TestCase):
    def test_all_examples_syntax_valid(self):
        """Verify that all example scripts (01..05) are valid Python code and can be compiled."""
        example_files = sorted(EXAMPLES_DIR.glob("*.py"))
        self.assertGreaterEqual(len(example_files), 6, "Expected at least 6 example scripts")

        for ex_path in example_files:
            source = ex_path.read_text(encoding="utf-8")
            # 1. AST syntax check
            parsed = ast.parse(source, filename=str(ex_path))
            self.assertIsNotNone(parsed, f"Failed to parse AST for {ex_path.name}")

            # 2. Bytecode compilation check
            compiled = py_compile.compile(str(ex_path), doraise=True)
            self.assertIsNotNone(compiled, f"Failed to compile {ex_path.name}")

    def test_examples_importable_and_executable(self):
        """Verify that example scripts (01..05) can be imported and main() executes cleanly."""
        example_files = sorted(EXAMPLES_DIR.glob("*.py"))

        mock_widgets = MagicMock()
        mock_widgets.QApplication = make_mock_app
        mock_widgets.QMainWindow = MockWidget
        mock_widgets.QWidget = MockWidget
        mock_widgets.QLabel = MockWidget
        mock_widgets.QVBoxLayout = MockWidget

        mock_webengine = MagicMock()
        mock_webengine.QWebEngineView = DummyWebEngineView

        for ex_path in example_files:
            module_name = f"example_{ex_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, ex_path)
            self.assertIsNotNone(spec, f"Could not load spec for {ex_path.name}")
            mod = importlib.util.module_from_spec(spec)

            tmp_runtime = tempfile.mkdtemp(prefix="qt_runtime_")
            env_overrides = {
                "QT_QPA_PLATFORM": "offscreen",
                "HOME": tmp_runtime,
                "XDG_RUNTIME_DIR": tmp_runtime,
            }

            with patch.dict(os.environ, env_overrides), \
                 patch.dict(sys.modules, {
                     "PyQt5.QtWidgets": mock_widgets,
                     "PyQt6.QtWidgets": mock_widgets,
                     "PyQt5.QtWebEngineWidgets": mock_webengine,
                     "PyQt6.QtWebEngineWidgets": mock_webengine,
                 }), \
                 patch("sys.argv", [str(ex_path), "--no-proxy"]), \
                 patch("quadproxy.proxy.ProxyCheckingWindow", MockWidget), \
                 patch("quadproxy.ProxyCheckingWindow", MockWidget), \
                 patch("quadproxy.compatibility.exec_app", return_value=0), \
                 patch("quadproxy.diagnostics.run_diagnostics") as mock_diag:

                from quadproxy.diagnostics import DiagnosticResult, DiagnosticResultList
                mock_diag.return_value = DiagnosticResultList(
                    [DiagnosticResult(stage=1, name="Test", passed=True, message="OK")],
                    no_proxy=True,
                )

                assert spec.loader is not None
                spec.loader.exec_module(mod)
                self.assertTrue(hasattr(mod, "main"), f"Example {ex_path.name} missing main() function")

                try:
                    ret = mod.main()
                    self.assertIn(ret, (0, 1), f"Example {ex_path.name} main() returned unexpected code {ret}")
                except SystemExit as exc:
                    self.assertIn(exc.code, (0, None))


class UnpackedZipExecutionTests(unittest.TestCase):
    def test_clean_install_unpacked_zip_execution(self):
        """Build product zip, unpack in clean temp directory, and verify zero-config execution."""
        build_script = ROOT_DIR / "scripts" / "build_product.py"
        if os.environ.get("INSIDE_UNPACKED_TEST") == "1" or not build_script.exists():
            self.skipTest("Skipping recursive unpacked zip test inside extracted package")

        # 1. Build product zip
        sys.path.insert(0, str(ROOT_DIR))
        from scripts.build_product import build as build_product

        # 2. Extract into temporary workspace
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = build_product(Path(temp_dir) / "qt-webengine-proxy-starter.zip")
            self.assertTrue(zip_path.exists(), f"Product zip not found at {zip_path}")

            extracted_root = Path(temp_dir) / "unpacked"
            extracted_root.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extractall(extracted_root)

            unpacked_product = extracted_root / "qt-webengine-proxy-starter"
            self.assertTrue(
                unpacked_product.exists(),
                f"Unpacked product directory missing at {unpacked_product}",
            )
            self.assertFalse((unpacked_product / "tests").exists())

            # 3. Test qt_proxy_starter.py --help in unpacked dir
            tmp_rt = tempfile.mkdtemp(prefix="qt_runtime_")
            env_offscreen = {
                **os.environ,
                "QT_QPA_PLATFORM": "offscreen",
                "HOME": tmp_rt,
                "XDG_RUNTIME_DIR": tmp_rt,
            }

            # 3. Test qt_proxy_starter.py --help in unpacked dir
            starter_py = unpacked_product / "qt_proxy_starter.py"
            res_help = subprocess.run(
                [sys.executable, str(starter_py), "--help"],
                cwd=str(unpacked_product),
                env=env_offscreen,
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(res_help.returncode, 0)
            self.assertIn("usage:", res_help.stdout.lower() + res_help.stderr.lower())

            # 4. Test python -m quadproxy doctor --no-proxy in unpacked dir
            res_doctor = subprocess.run(
                [sys.executable, "-m", "quadproxy", "doctor", "--no-proxy"],
                cwd=str(unpacked_product),
                env=env_offscreen,
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(res_doctor.returncode, 0)
            self.assertIn("Stage", res_doctor.stdout)

            # 5. Test shipped source compilation in unpacked dir
            tmp_rt = tempfile.mkdtemp(prefix="qt_runtime_")
            env_offscreen = {
                **os.environ,
                "QT_QPA_PLATFORM": "offscreen",
                "HOME": tmp_rt,
                "XDG_RUNTIME_DIR": tmp_rt,
            }
            res_compile = subprocess.run(
                [sys.executable, "-m", "compileall", "qt_proxy_starter.py", "quadproxy", "examples"],
                cwd=str(unpacked_product),
                env=env_offscreen,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                res_compile.returncode,
                0,
                f"Unpacked product compile failed: {res_compile.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
