"""Actionable Failure Playbook for QuadProxy.

Maps diagnostic failures, exception types, and error codes to concrete customer recommendations.
Eliminates vague "something went wrong" messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, List, Any


@dataclass(frozen=True)
class PlaybookRecommendation:
    """Actionable remediation guidance for a specific failure classification."""

    code: str
    title: str
    description: str
    recommendation: str
    next_steps: List[str]


PLAYBOOK_REGISTRY: Dict[str, PlaybookRecommendation] = {
    "CONFIGURATION_MISSING": PlaybookRecommendation(
        code="CONFIGURATION_MISSING",
        title="PROXY CONFIGURATION INCOMPLETE",
        description="Required environment variables (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASSWORD) are missing.",
        recommendation="Set all 4 proxy environment variables or run in direct mode with --no-proxy.",
        next_steps=[
            "Export PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASSWORD in your terminal environment.",
            "Run 'python -m quadproxy wizard' to configure visually via Desktop GUI.",
            "Pass --no-proxy flag if testing local direct network connectivity.",
        ],
    ),
    "INVALID_PORT": PlaybookRecommendation(
        code="INVALID_PORT",
        title="INVALID PROXY PORT",
        description="The specified PROXY_PORT is not a valid integer within port range 1-65535.",
        recommendation="Verify and correct the PROXY_PORT value.",
        next_steps=[
            "Check your proxy provider dashboard for the exact HTTP/HTTPS proxy port number.",
            "Ensure PROXY_PORT contains numeric digits only (e.g. 8080 or 9000).",
        ],
    ),
    "DNS_RESOLUTION_FAILURE": PlaybookRecommendation(
        code="DNS_RESOLUTION_FAILURE",
        title="PROXY DNS RESOLUTION FAILED",
        description="The proxy host name could not be resolved by local DNS server.",
        recommendation="Verify provider hostname spelling and local DNS/network connectivity.",
        next_steps=[
            "Ping or lookup the proxy host (e.g. nslookup proxy.example.net).",
            "Check if an IP address can be used directly instead of host name.",
            "Verify your local Internet connection.",
        ],
    ),
    "PROXY_HOST_UNREACHABLE": PlaybookRecommendation(
        code="PROXY_HOST_UNREACHABLE",
        title="PROXY HOST UNREACHABLE",
        description="Failed to open TCP socket connection to proxy server host and port.",
        recommendation="Verify provider hostname, port, local firewall, and network routing.",
        next_steps=[
            "Check if outbound traffic to proxy port is blocked by firewall or VPN.",
            "Confirm the proxy server server status on provider dashboard.",
            "Test raw socket connection via telnet or nc (e.g. nc -zv proxy.example.net 8080).",
        ],
    ),
    "AUTHENTICATION_REJECTED": PlaybookRecommendation(
        code="AUTHENTICATION_REJECTED",
        title="AUTHENTICATION REJECTED (HTTP 407)",
        description="Proxy server rejected the provided username and password.",
        recommendation="Verify username/password credentials and provider authentication mode.",
        next_steps=[
            "Verify PROXY_USER and PROXY_PASSWORD credentials against your proxy dashboard.",
            "Check if your proxy provider uses IP Whitelisting instead of Username/Password authentication.",
            "Ensure password special characters are properly escaped in environment variables.",
        ],
    ),
    "PUBLIC_IP_UNCHANGED": PlaybookRecommendation(
        code="PUBLIC_IP_UNCHANGED",
        title="PUBLIC IP UNCHANGED",
        description="The detected public IP matches your direct public IP despite proxy configuration.",
        recommendation="Proxy configuration may not be applied to Qt WebEngine network traffic.",
        next_steps=[
            "Verify configure_application_proxy(config) is invoked BEFORE QApplication instance creation.",
            "Check if proxy configuration is overwritten or bypassed by custom QNetworkAccessManager.",
            "Re-run 'python -m quadproxy doctor' to re-test public IP verification.",
        ],
    ),
    "QT_INITIALIZATION_ORDER_FAILURE": PlaybookRecommendation(
        code="QT_INITIALIZATION_ORDER_FAILURE",
        title="QT INITIALIZATION ORDER FAILURE",
        description="Proxy settings were set after QApplication initialization or Qt WebEngine module import.",
        recommendation="Ensure configure_application_proxy(config) is called before creating QApplication.",
        next_steps=[
            "Move configure_application_proxy(config) to the top of your main script.",
            "Ensure QApplication is instantiated after setting QNetworkProxy.setApplicationProxy.",
            "Refer to examples/03_pyqt5_integration.py or examples/04_pyqt6_integration.py.",
        ],
    ),
    "TARGET_PAGE_FAILED": PlaybookRecommendation(
        code="TARGET_PAGE_FAILED",
        title="TARGET PAGE LOAD FAILED",
        description="Proxy connected and public IP verified, but target URL failed to load.",
        recommendation="Destination server may block proxy IP range or target site is temporarily down.",
        next_steps=[
            "Test loading a different target URL (e.g. python -m quadproxy doctor --url https://httpbin.org/get).",
            "Check if target web server blocks datacenter or residential proxy ranges.",
            "Verify target URL formatting and HTTPS SSL certificate status.",
        ],
    ),
    "QT_WEBENGINE_MISSING": PlaybookRecommendation(
        code="QT_WEBENGINE_MISSING",
        title="QT WEBENGINE MODULE MISSING",
        description="Neither PyQt5.QtWebEngineWidgets nor PyQt6.QtWebEngineWidgets is installed.",
        recommendation="Install PyQt WebEngine package for your Python environment.",
        next_steps=[
            "For PyQt5: run 'pip install PyQt5 PyQtWebEngine'",
            "For PyQt6: run 'pip install PyQt6 PyQt6-WebEngine'",
        ],
    ),
}


def classify_failure(
    stage: int,
    error_message: str,
    details: Optional[Dict[str, Any]] = None,
    direct_ip: Optional[str] = None,
    proxy_ip: Optional[str] = None,
) -> PlaybookRecommendation:
    """Classify a failure into a concrete PlaybookRecommendation."""
    msg = (error_message or "").lower()

    if stage == 1:
        if "incomplete" in msg or "missing" in msg:
            return PLAYBOOK_REGISTRY["CONFIGURATION_MISSING"]
        if "port" in msg:
            return PLAYBOOK_REGISTRY["INVALID_PORT"]

    if stage == 2:
        if "name or service not known" in msg or "gaierror" in msg or "dns" in msg:
            return PLAYBOOK_REGISTRY["DNS_RESOLUTION_FAILURE"]
        return PLAYBOOK_REGISTRY["PROXY_HOST_UNREACHABLE"]

    if stage == 3:
        if "407" in msg or "authentication" in msg or "denied" in msg:
            return PLAYBOOK_REGISTRY["AUTHENTICATION_REJECTED"]

    if stage == 4:
        if "not found" in msg or "missing" in msg:
            return PLAYBOOK_REGISTRY["QT_WEBENGINE_MISSING"]
        if "initialization" in msg or "order" in msg:
            return PLAYBOOK_REGISTRY["QT_INITIALIZATION_ORDER_FAILURE"]

    if stage == 5:
        if direct_ip and proxy_ip and direct_ip == proxy_ip:
            return PLAYBOOK_REGISTRY["PUBLIC_IP_UNCHANGED"]
        if "unchanged" in msg:
            return PLAYBOOK_REGISTRY["PUBLIC_IP_UNCHANGED"]

    if stage == 6:
        return PLAYBOOK_REGISTRY["TARGET_PAGE_FAILED"]

    # Fallback to general classification based on message keywords
    if "407" in msg:
        return PLAYBOOK_REGISTRY["AUTHENTICATION_REJECTED"]
    if "connect" in msg or "socket" in msg or "refused" in msg:
        return PLAYBOOK_REGISTRY["PROXY_HOST_UNREACHABLE"]
    if "dns" in msg or "resolution" in msg:
        return PLAYBOOK_REGISTRY["DNS_RESOLUTION_FAILURE"]
    if "unchanged" in msg:
        return PLAYBOOK_REGISTRY["PUBLIC_IP_UNCHANGED"]

    return PlaybookRecommendation(
        code="UNCLASSIFIED_FAILURE",
        title="DIAGNOSTIC STAGE FAILURE",
        description=f"Stage {stage} check failed: {error_message}",
        recommendation="Review diagnostic details and error trace for potential network or proxy issues.",
        next_steps=[
            "Run 'python -m quadproxy doctor' for detailed stage output.",
            "Generate a support bundle with 'python -m quadproxy support-bundle'.",
        ],
    )
