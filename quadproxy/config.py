"""Proxy configuration dataclass and environment variable resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

PROXY_HOST = "PROXY_HOST"
PROXY_PORT = "PROXY_PORT"
PROXY_USER = "PROXY_USER"
PROXY_PASSWORD = "PROXY_PASSWORD"
WEBSHARE_PROXY_PASSWORD = "WEBSHARE_PROXY_PASSWORD"
PROXY_SCHEME = "PROXY_SCHEME"
SUPPORTED_PROXY_SCHEME = "http"


ONBOARDING_GUIDE = (
    "================================================================================\n"
    "Qt WebEngine Proxy Starter — First-Run Setup & Onboarding Guide\n"
    "================================================================================\n"
    "Welcome! This starter kit demonstrates authenticated proxy setup in PyQt.\n\n"
    "NOTE: THIS PRODUCT DOES NOT INCLUDE A BUILT-IN PROXY SERVICE OR ACCOUNT.\n"
    "You must supply proxy credentials from your own proxy provider (e.g. Webshare,\n"
    "BrightData, Oxylabs, Smartproxy, etc.).\n\n"
    "QUICKSTART OPTIONS:\n\n"
    "1. Run with your Proxy Credentials (Windows PowerShell):\n"
    '   $env:PROXY_HOST="proxy.example.net"\n'
    '   $env:PROXY_PORT="8080"\n'
    '   $env:PROXY_USER="your_user"\n'
    '   $env:PROXY_PASSWORD="your_password"\n'
    "   python qt_proxy_starter.py --url https://example.com\n\n"
    "2. Run with your Proxy Credentials (Linux / macOS bash):\n"
    '   export PROXY_HOST="proxy.example.net"\n'
    '   export PROXY_PORT="8080"\n'
    '   export PROXY_USER="your_user"\n'
    '   export PROXY_PASSWORD="your_password"\n'
    "   python3 qt_proxy_starter.py --url https://example.com\n\n"
    "3. Run in Direct / No-Proxy Mode (Diagnostic / Demo):\n"
    "   python3 qt_proxy_starter.py --no-proxy --url https://example.com\n\n"
    "For full instructions and details, see README.md in this package.\n"
    "================================================================================\n"
)


@dataclass(frozen=True)
class ProxyConfig:
    """Immutable container for proxy connection parameters and credentials."""

    host: str
    port: int
    user: str
    password: str
    scheme: str = SUPPORTED_PROXY_SCHEME

    def __post_init__(self) -> None:
        object.__setattr__(self, "scheme", normalize_proxy_scheme(self.scheme))

    def __repr__(self) -> str:
        return f"ProxyConfig(host={self.host!r}, port={self.port!r}, user={self.user!r}, password='***')"

    def __str__(self) -> str:
        return f"ProxyConfig({self.user}@{self.host}:{self.port})"


def normalize_proxy_scheme(raw_scheme: str | None) -> str:
    """Return a supported normalized proxy scheme or raise a clear error."""
    scheme = str(raw_scheme or SUPPORTED_PROXY_SCHEME).strip().lower() or SUPPORTED_PROXY_SCHEME
    if scheme != SUPPORTED_PROXY_SCHEME:
        raise ValueError(
            "Unsupported PROXY_SCHEME "
            f"{scheme!r}. QuadProxy v1.0 supports authenticated HTTP proxies only; "
            "set PROXY_SCHEME=http or leave it unset."
        )
    return scheme


def proxy_config_from_env(
    no_proxy: bool = False,
) -> tuple[Optional[ProxyConfig], Optional[str]]:
    """Resolve proxy configuration from environment variables.

    Args:
        no_proxy: If True, bypass proxy configuration and return (None, None).

    Returns:
        tuple[Optional[ProxyConfig], Optional[str]]: (config, onboarding_message)
        - If no_proxy is True: (None, None)
        - If zero proxy env vars set: (None, onboarding_guide)
        - If all 4 env vars set: (ProxyConfig, None)
        - If partially set: raises RuntimeError (with password masked)
    """
    if no_proxy:
        return None, None

    host = os.environ.get(PROXY_HOST, "").strip()
    port_raw = os.environ.get(PROXY_PORT, "").strip()
    user = os.environ.get(PROXY_USER, "").strip()
    password = (
        os.environ.get(PROXY_PASSWORD, "").strip()
        or os.environ.get(WEBSHARE_PROXY_PASSWORD, "").strip()
    )
    try:
        scheme = normalize_proxy_scheme(os.environ.get(PROXY_SCHEME, SUPPORTED_PROXY_SCHEME))
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    env_pairs = [
        (PROXY_HOST, host),
        (PROXY_PORT, port_raw),
        (PROXY_USER, user),
        (PROXY_PASSWORD, password),
    ]
    present_count = sum(1 for _, val in env_pairs if val)

    if present_count == 0:
        return None, ONBOARDING_GUIDE

    missing = [name for name, val in env_pairs if not val]
    if missing:
        raise RuntimeError(
            "Incomplete proxy configuration. Missing required variable(s): "
            + ", ".join(missing)
            + ". Provide all 4 proxy variables or run with --no-proxy for direct mode."
        )

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise RuntimeError("PROXY_PORT must be a valid integer") from exc

    return (
        ProxyConfig(
            host=host, port=port, user=user, password=password, scheme=scheme
        ),
        None,
    )
