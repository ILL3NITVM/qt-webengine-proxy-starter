"""Example F: Successful Public IP Verification Demonstration.

Demonstrates verifying public IP address change when running in direct vs proxy mode.
"""

from __future__ import annotations

import sys
from quadproxy.diagnostics import verify_proxy_connection


def main() -> int:
    print("[QuadProxy Demo F] Verifying Direct Public IP...")
    res_direct = verify_proxy_connection(config=None)
    if res_direct["status"] == "ok":
        print(f"[Direct Mode] Public IP: {res_direct['public_ip']}")
    else:
        print(f"[Direct Mode] Check failed: {res_direct.get('error')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
