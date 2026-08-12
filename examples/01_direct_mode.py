"""Example A: Direct / No-Proxy Mode Demonstration.

Demonstrates running QuadProxy in direct mode (--no-proxy) for testing local
network connectivity and target URL reachability without proxy credentials.
"""

from __future__ import annotations

import sys
from quadproxy import run_diagnostics, format_diagnostic_table


def main() -> int:
    print("[QuadProxy Demo A] Running Direct / No-Proxy Mode Diagnostic Check...")
    results = run_diagnostics(target_url="https://example.com", no_proxy=True)
    print(format_diagnostic_table(results))
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
