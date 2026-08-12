#!/usr/bin/env python3
"""Authenticated-proxy starter app for PyQt WebEngine (delegating to quadproxy package)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Sequence

from quadproxy.config import ProxyConfig, proxy_config_from_env


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
    """Build legacy CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Run a QWebEngineView through an authenticated proxy."
    )
    parser.add_argument(
        "--url",
        default="https://example.com",
        help="Target URL to load after proxy verification.",
    )
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="Disable proxy setup for troubleshooting.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Executable main entry point delegating to quadproxy package."""
    args = build_parser().parse_args(argv)
    from quadproxy.compatibility import QApplication, QTimer, exec_app
    from quadproxy.proxy import ProxyCheckingWindow, configure_application_proxy
    from quadproxy.wizard import launch_wizard

    try:
        proxy_config, onboarding_msg = proxy_config_from_env(args.no_proxy)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if onboarding_msg is not None:
        if is_gui_environment():
            return launch_wizard(target_url=args.url, proxy_config=None, no_proxy=False)
        else:
            print(onboarding_msg, flush=True)
            return 0

    configure_application_proxy(proxy_config)
    app = QApplication(sys.argv if argv is None else [sys.argv[0], *(argv or [])])
    window = ProxyCheckingWindow(args.url, proxy_config)
    window.show()
    QTimer.singleShot(0, window.start)
    return exec_app(app)


if __name__ == "__main__":
    sys.exit(main())
