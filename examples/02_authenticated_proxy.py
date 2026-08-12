"""Example B: Authenticated Proxy Integration.

Demonstrates initializing ProxyConfig with explicit credentials and running
the full diagnostic suite.
"""

from __future__ import annotations

import os
import sys
from quadproxy import ProxyConfig, run_diagnostics, format_diagnostic_table


def main() -> int:
    print("[QuadProxy Demo B] Running Authenticated Proxy Demonstration...")

    host = os.environ.get("PROXY_HOST", "proxy.example.net")
    port = int(os.environ.get("PROXY_PORT", "8080"))
    user = os.environ.get("PROXY_USER", "demo_user")
    password = os.environ.get("PROXY_PASSWORD", "demo_pass")

    config = ProxyConfig(host=host, port=port, user=user, password=password)
    print(f"Loaded config: {config}")

    results = run_diagnostics(target_url="https://example.com", proxy_config=config)
    print(format_diagnostic_table(results))
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
