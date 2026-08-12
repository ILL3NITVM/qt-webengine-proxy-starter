"""CLI adapter module for quadproxy-doctor script entry point."""

from __future__ import annotations

import sys
from typing import Optional, Sequence

from quadproxy.__main__ import main as quadproxy_main


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in {
        "doctor",
        "check",
        "support-bundle",
        "support_bundle",
        "checklist",
        "version",
        "update",
        "check-update",
        "wizard",
        "gui",
        "run",
    }:
        args = ["doctor", *args]
    return quadproxy_main(args)


__all__ = ["main"]
