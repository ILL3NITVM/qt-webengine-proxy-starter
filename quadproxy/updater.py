"""Safe, non-forced update checker for QuadProxy.

Enforces:
- No automatic code execution
- No silent download or installation
- No secret or credential transmission
- No intrusive telemetry
- Transparent customer reporting and manual download instructions
"""

from __future__ import annotations

import json
import os
from typing import Dict, Any, Tuple

from quadproxy import __version__

LATEST_RELEASE_VERSION = "1.1.0"
CUSTOMER_PORTAL_URL = "https://quadproxy.com/portal/downloads"
CHANGELOG_URL = "https://quadproxy.com/changelog"


def check_for_updates() -> Dict[str, Any]:
    """Return update status safely without sending telemetry or credentials."""
    current = __version__
    latest = LATEST_RELEASE_VERSION

    is_newer = _version_tuple(latest) > _version_tuple(current)

    return {
        "current_version": current,
        "latest_version": latest,
        "update_available": is_newer,
        "message": (
            f"QuadProxy {latest} available (Current: {current})."
            if is_newer
            else f"QuadProxy is up to date (Version {current})."
        ),
        "download_url": CUSTOMER_PORTAL_URL if is_newer else None,
        "changelog_url": CHANGELOG_URL,
    }


def format_update_report() -> str:
    """Format update status into clear customer instructions."""
    info = check_for_updates()
    lines = [
        "================================================================================",
        "QuadProxy Update Check",
        "================================================================================",
        f"Current Installed Version : {info['current_version']}",
        f"Latest Available Version  : {info['latest_version']}",
    ]

    if info["update_available"]:
        lines.extend([
            "\n[UPDATE AVAILABLE]",
            f"A newer release ({info['latest_version']}) is available in your customer portal.",
            "\nTo update safely:",
            "1. Visit your secure download portal: " + CUSTOMER_PORTAL_URL,
            "2. Download the updated ZIP package (qt-webengine-proxy-starter.zip).",
            "3. Extract and replace your local quadproxy module files.",
            "4. Run 'python -m quadproxy doctor' to verify.",
            "\nNote: QuadProxy NEVER automatically downloads or executes code updates.",
        ])
    else:
        lines.extend([
            "\n[UP TO DATE]",
            f"You possess the latest release of QuadProxy ({info['current_version']}).",
        ])

    lines.append("================================================================================")
    return "\n".join(lines)


def _version_tuple(ver_str: str) -> Tuple[int, ...]:
    """Parse version string into integer tuple for comparison."""
    try:
        return tuple(int(x) for x in ver_str.strip().split("."))
    except Exception:
        return (1, 0, 0)
