"""Example D: Existing PyQt6 Application Integration.

Demonstrates integrating QuadProxy into an existing PyQt6 codebase.
"""

from __future__ import annotations

import os
import sys

from quadproxy import ProxyConfig, configure_application_proxy


def main() -> int:
    print("[QuadProxy Demo D] Running Existing PyQt6 Integration...")

    no_proxy = os.environ.get("NO_PROXY", "0") == "1"
    config = None
    if not no_proxy:
        host = os.environ.get("PROXY_HOST", "")
        port_raw = os.environ.get("PROXY_PORT", "")
        user = os.environ.get("PROXY_USER", "")
        password = os.environ.get("PROXY_PASSWORD", "")
        if host and port_raw and user and password:
            config = ProxyConfig(host=host, port=int(port_raw), user=user, password=password)

    configure_application_proxy(config)
    print("PyQt6 application proxy contract configured successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
