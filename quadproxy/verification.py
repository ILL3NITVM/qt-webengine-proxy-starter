"""Preflight IP verification and validation utilities."""

from __future__ import annotations

import ipaddress
import time
import urllib.request
from typing import Optional, Sequence

from quadproxy.config import ProxyConfig
from quadproxy.security import redact_str

PROXY_CHECK_URL = "https://api.ipify.org"
RETRY_DELAYS_MS = (2000, 5000, 10000)
RETRY_DELAYS_SEC = (2.0, 5.0, 10.0)
TIMEOUT_MS = 75000
TIMEOUT_SEC = 75.0


def validate_ip_address(raw_ip: str) -> str:
    """Validate raw text input as an IPv4 or IPv6 address.

    Args:
        raw_ip: Text string containing IP address.

    Returns:
        Validated IP address string.

    Raises:
        ValueError: If input is not a valid IP address.
    """
    cleaned = str(raw_ip or "").strip()
    ip_obj = ipaddress.ip_address(cleaned)
    return str(ip_obj)


def verify_proxy_http(
    config: Optional[ProxyConfig],
    check_url: str = PROXY_CHECK_URL,
    retry_delays: Sequence[float] = RETRY_DELAYS_SEC,
    timeout_seconds: float = TIMEOUT_SEC,
) -> tuple[bool, str]:
    """Perform preflight HTTP IP verification with exponential backoff retries.

    Retries up to len(retry_delays) times with specified backoff delays (2s, 5s, 10s)
    and a timeout guard.

    Args:
        config: Optional ProxyConfig instance or None for direct connection.
        check_url: Verification target URL (default https://api.ipify.org).
        retry_delays: Sequence of retry delay durations in seconds.
        timeout_seconds: Timeout per connection attempt.

    Returns:
        tuple[bool, str]: (passed, ip_address_or_error_detail)
    """
    last_error = "Unknown failure"

    for attempt_idx, delay in enumerate(retry_delays):
        try:
            if config is not None:
                proxy_url = f"{config.scheme}://{config.user}:{config.password}@{config.host}:{config.port}"
                proxy_handler = urllib.request.ProxyHandler(
                    {"http": proxy_url, "https": proxy_url}
                )
                password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                password_mgr.add_password(
                    None, f"{config.host}:{config.port}", config.user, config.password
                )
                auth_handler = urllib.request.ProxyBasicAuthHandler(password_mgr)
                opener = urllib.request.build_opener(proxy_handler, auth_handler)
            else:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

            req = urllib.request.Request(
                check_url, headers={"User-Agent": "QuadProxy-Verifier/1.0"}
            )
            with opener.open(req, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace").strip()
                validated_ip = validate_ip_address(body)
                return True, validated_ip
        except Exception as exc:
            pwd = config.password if config else None
            last_error = redact_str(str(exc), pwd)
            if attempt_idx < len(retry_delays) - 1:
                time.sleep(delay)

    return False, f"Verification failed after {len(retry_delays)} attempts: {last_error}"
