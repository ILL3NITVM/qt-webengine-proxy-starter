"""Security utilities for password redaction and credential protection.

Ensures passwords and sensitive credentials never appear in logs, tracebacks,
__repr__ strings, or telemetry data.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

SENSITIVE_KEY_PATTERNS = re.compile(
    r"(pass|password|secret|token|key|auth|pwd|credential)", re.IGNORECASE
)

ENV_KV_REDACT_PATTERN = re.compile(
    r"((?:PROXY_PASSWORD|WEBSHARE_PROXY_PASSWORD|PASSWORD|SECRET|AUTH_TOKEN|API_KEY)=)([^\s;]+)",
    re.IGNORECASE,
)


def redact_password(password: Optional[str]) -> str:
    """Return a redacted placeholder for a password string.

    Args:
        password: Raw password string.

    Returns:
        Redacted string '***' or empty string if None or empty.
    """
    if not password:
        return ""
    return "***"


def redact_url(url: str) -> str:
    """Redact username and password credentials embedded in a URL string.

    Args:
        url: Full URL string potentially containing user credentials.

    Returns:
        URL string with password replaced by '***'.
    """
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        if parts.username or parts.password:
            netloc = parts.netloc
            if "@" in netloc:
                userinfo, hostport = netloc.rsplit("@", 1)
                if ":" in userinfo:
                    username, _ = userinfo.split(":", 1)
                    new_userinfo = f"{username}:***"
                else:
                    new_userinfo = userinfo
                new_netloc = f"{new_userinfo}@{hostport}"
                return urlunsplit(
                    (parts.scheme, new_netloc, parts.path, parts.query, parts.fragment)
                )
        return url
    except Exception:
        return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", url)


def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively copy a dictionary, masking values of sensitive keys.

    Args:
        data: Input dictionary.

    Returns:
        New dictionary with sensitive values redacted.
    """
    redacted: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(key, str) and SENSITIVE_KEY_PATTERNS.search(key):
            redacted[key] = "***" if value else value
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value)
        elif isinstance(value, list):
            redacted[key] = [
                redact_dict(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            redacted[key] = value
    return redacted


def redact_str(text: str, password: Optional[str] = None) -> str:
    """Scrub password strings and sensitive credential patterns from arbitrary text.

    Args:
        text: Target text string (e.g. log output, exception message, traceback).
        password: Optional explicit password string to scrub.

    Returns:
        Scrubbed string with sensitive values replaced by '***'.
    """
    if not text:
        return ""
    result = text
    if password:
        result = result.replace(password, "***")
    env_pwd = (
        os.environ.get("PROXY_PASSWORD", "").strip()
        or os.environ.get("WEBSHARE_PROXY_PASSWORD", "").strip()
    )
    if env_pwd:
        result = result.replace(env_pwd, "***")
    result = ENV_KV_REDACT_PATTERN.sub(r"\1***", result)
    return result

