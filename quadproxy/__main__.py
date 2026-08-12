"""CLI entry point for quadproxy package."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Sequence

from quadproxy import __version__
from quadproxy.activation import ActivationChecklist, format_checklist_cli
from quadproxy.config import proxy_config_from_env
from quadproxy.support_bundle import generate_support_bundle
from quadproxy.updater import format_update_report

QApplication = None
QTimer = None
exec_app = None
format_diagnostic_table = None
run_diagnostics = None
ProxyCheckingWindow = None
configure_application_proxy = None
launch_wizard = None


def ensure_runtime_modules() -> None:
    """Load Qt runtime objects only when a GUI run path needs them."""
    global QApplication, QTimer, exec_app, ProxyCheckingWindow, configure_application_proxy
    if QApplication is None or QTimer is None or exec_app is None:
        from quadproxy import compatibility

        if QApplication is None:
            QApplication = compatibility.QApplication
        if QTimer is None:
            QTimer = compatibility.QTimer
        if exec_app is None:
            exec_app = compatibility.exec_app
    if ProxyCheckingWindow is None or configure_application_proxy is None:
        from quadproxy import proxy

        if ProxyCheckingWindow is None:
            ProxyCheckingWindow = proxy.ProxyCheckingWindow
        if configure_application_proxy is None:
            configure_application_proxy = proxy.configure_application_proxy


def ensure_diagnostic_modules() -> None:
    """Load diagnostic objects only when doctor/check is executed."""
    global format_diagnostic_table, run_diagnostics
    if format_diagnostic_table is None or run_diagnostics is None:
        from quadproxy import diagnostics

        if format_diagnostic_table is None:
            format_diagnostic_table = diagnostics.format_diagnostic_table
        if run_diagnostics is None:
            run_diagnostics = diagnostics.run_diagnostics


def ensure_wizard_module() -> None:
    """Load the desktop wizard only when a wizard path needs it."""
    global launch_wizard
    if launch_wizard is None:
        from quadproxy import wizard

        launch_wizard = wizard.launch_wizard


def is_gui_environment() -> bool:
    """Check if current environment supports GUI application windows."""
    if sys.platform.startswith("linux"):
        display = os.environ.get("DISPLAY")
        wayland = os.environ.get("WAYLAND_DISPLAY")
        qpa = os.environ.get("QT_QPA_PLATFORM")
        if qpa == "offscreen":
            return False
        if not display and not wayland:
            return False
    return True


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser supporting doctor, check, support-bundle, checklist, version, update, run, wizard, gui.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="quadproxy",
        description="QuadProxy: Authenticated Proxy Integration & Diagnostics for PyQt WebEngine",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: wizard / gui
    for sub in ("wizard", "gui"):
        w_parser = subparsers.add_parser(
            sub, help="Launch QuadProxy Desktop Configuration Wizard"
        )
        w_parser.add_argument(
            "url", nargs="?", default="https://example.com", help="Target URL for testing"
        )
        w_parser.add_argument(
            "--url", dest="url_flag", default=None, help="Target URL for testing"
        )
        w_parser.add_argument(
            "--no-proxy", action="store_true", help="Start wizard in direct mode"
        )

    # Subcommand: doctor / check
    for sub in ("doctor", "check"):
        d_parser = subparsers.add_parser(
            sub, help="Run 12-stage diagnostic sequence and display result table"
        )
        d_parser.add_argument(
            "url", nargs="?", default="https://example.com", help="Target URL for testing"
        )
        d_parser.add_argument(
            "--url", dest="url_flag", default=None, help="Target URL for testing"
        )
        d_parser.add_argument(
            "--no-proxy", action="store_true", help="Run diagnostics in direct mode"
        )

    # Subcommand: support-bundle / support_bundle
    for sub in ("support-bundle", "support_bundle"):
        sb_parser = subparsers.add_parser(
            sub, help="Generate a safe, redacted support bundle ZIP archive"
        )
        sb_parser.add_argument(
            "--output", "-o", dest="output", default=None, help="Output zip file path"
        )
        sb_parser.add_argument(
            "url", nargs="?", default="https://example.com", help="Target URL for testing"
        )
        sb_parser.add_argument(
            "--url", dest="url_flag", default=None, help="Target URL for testing"
        )
        sb_parser.add_argument(
            "--no-proxy", action="store_true", help="Generate bundle in direct mode"
        )

    # Subcommand: checklist
    c_parser = subparsers.add_parser(
        "checklist", help="Display customer activation checklist progress"
    )
    c_parser.add_argument(
        "--no-proxy", action="store_true", help="Evaluate checklist in direct mode"
    )

    # Subcommand: version
    v_parser = subparsers.add_parser(
        "version", help="Display QuadProxy package version and release metadata"
    )

    # Subcommand: check-update / update
    for sub in ("check-update", "update"):
        u_parser = subparsers.add_parser(
            sub, help="Check for available updates without auto-downloading"
        )

    # Subcommand: run
    r_parser = subparsers.add_parser(
        "run", help="Launch PyQt WebEngine proxy checking window"
    )
    r_parser.add_argument(
        "url", nargs="?", default="https://example.com", help="Target URL to load after verification"
    )
    r_parser.add_argument(
        "--url", dest="url_flag", default=None, help="Target URL for testing"
    )
    r_parser.add_argument(
        "--no-proxy", action="store_true", help="Disable proxy setup"
    )

    # Global flags / positional fallback
    parser.add_argument(
        "url", nargs="?", default="https://example.com", help="Target URL to load"
    )
    parser.add_argument(
        "--url", dest="url_flag", default=None, help="Target URL for testing"
    )
    parser.add_argument(
        "--no-proxy", action="store_true", help="Disable proxy setup for troubleshooting"
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI entry point for quadproxy package.

    Args:
        argv: Optional command line argument list.

    Returns:
        Exit code integer.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    command = args.command
    no_proxy = getattr(args, "no_proxy", False)
    target_url = (
        getattr(args, "url_flag", None)
        or getattr(args, "url", None)
        or "https://example.com"
    )

    if command in ("wizard", "gui"):
        try:
            proxy_config, _ = proxy_config_from_env(no_proxy)
        except RuntimeError:
            proxy_config = None
        ensure_wizard_module()
        return launch_wizard(
            target_url=target_url, proxy_config=proxy_config, no_proxy=no_proxy
        )

    if command in ("doctor", "check"):
        ensure_diagnostic_modules()
        try:
            proxy_config, onboarding_msg = proxy_config_from_env(no_proxy=no_proxy)
        except RuntimeError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            return 2

        if onboarding_msg and not no_proxy:
            print(onboarding_msg, flush=True)

        results = run_diagnostics(
            target_url=target_url, proxy_config=proxy_config, no_proxy=no_proxy
        )
        print(format_diagnostic_table(results), flush=True)
        return 0 if all(r.passed for r in results) else 1

    if command in ("support-bundle", "support_bundle"):
        ensure_diagnostic_modules()
        try:
            proxy_config, _ = proxy_config_from_env(no_proxy=no_proxy)
        except RuntimeError:
            proxy_config = None

        output_path = getattr(args, "output", None)
        try:
            zip_path = generate_support_bundle(
                output_path=output_path,
                target_url=target_url,
                proxy_config=proxy_config,
                no_proxy=no_proxy,
            )
            print(
                "================================================================================"
            )
            print("QuadProxy Support Bundle Generated Successfully!")
            print("================================================================================")
            print(f"Bundle File Location : {zip_path}")
            print("Contains             : Redacted diagnostics, system info, error classifications")
            print("Guarantees           : ZERO secrets, passwords, Stripe tokens, or sensitive logs")
            print("================================================================================")
            return 0
        except Exception as exc:
            print(f"Failed to generate support bundle: {exc}", file=sys.stderr)
            return 1

    if command == "checklist":
        ensure_diagnostic_modules()
        try:
            proxy_config, _ = proxy_config_from_env(no_proxy=no_proxy)
        except RuntimeError:
            proxy_config = None

        doc_results = []
        if proxy_config is not None or no_proxy:
            doc_results = run_diagnostics(
                target_url=target_url, proxy_config=proxy_config, no_proxy=no_proxy
            )

        checklist = ActivationChecklist(
            proxy_config=proxy_config,
            no_proxy=no_proxy,
            doctor_results=doc_results,
        )
        print(format_checklist_cli(checklist.evaluate()), flush=True)
        return 0

    if command == "version":
        print(f"QuadProxy v{__version__}")
        print("Customer Activation & Support Completeness Release (Epoch 06)")
        return 0

    if command in ("check-update", "update"):
        print(format_update_report(), flush=True)
        return 0

    if command == "run":
        try:
            proxy_config, onboarding_msg = proxy_config_from_env(no_proxy)
        except RuntimeError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            return 2

        if onboarding_msg is not None:
            print(onboarding_msg, flush=True)
            return 0

        ensure_runtime_modules()
        configure_application_proxy(proxy_config)
        app = QApplication(sys.argv if argv is None else [sys.argv[0], *(argv or [])])
        window = ProxyCheckingWindow(target_url, proxy_config)
        window.show()
        QTimer.singleShot(0, window.start)
        return exec_app(app)

    # Positional fallback when no subcommand specified
    try:
        proxy_config, onboarding_msg = proxy_config_from_env(no_proxy)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if onboarding_msg is not None:
        if is_gui_environment():
            ensure_wizard_module()
            return launch_wizard(target_url=target_url, proxy_config=None, no_proxy=False)
        else:
            print(onboarding_msg, flush=True)
            return 0

    ensure_runtime_modules()
    configure_application_proxy(proxy_config)
    app = QApplication(sys.argv if argv is None else [sys.argv[0], *(argv or [])])
    window = ProxyCheckingWindow(target_url, proxy_config)
    window.show()
    QTimer.singleShot(0, window.start)
    return exec_app(app)


if __name__ == "__main__":
    sys.exit(main())
