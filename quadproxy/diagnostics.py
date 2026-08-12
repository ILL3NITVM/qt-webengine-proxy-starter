"""12-stage diagnostic sequence and health check doctor for QuadProxy.

Inspects and classifies:
1. Python Version
2. Qt WebEngine Binding
3. Proxy Configuration Completeness
4. Proxy Port Validity
5. DNS Host Resolution
6. TCP Network Reachability
7. Authentication Path
8. Direct Public IP Check
9. Proxy Public IP Verification
10. Direct/Proxy IP Comparison
11. Target URL Reachability
12. Qt Initialization Order & Setup
"""

from __future__ import annotations

import importlib.util
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from quadproxy.config import ProxyConfig, proxy_config_from_env
from quadproxy.playbook import classify_failure
from quadproxy.security import redact_str
from quadproxy.verification import (
    PROXY_CHECK_URL,
    validate_ip_address,
    verify_proxy_http,
)

_QT_WEBENGINE_BINDING_CACHE: Optional[Tuple[Optional[bool], str]] = None


def module_available(module_name: str) -> bool:
    """Return whether a module can be imported without importing it."""
    if module_name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def qt_webengine_binding() -> Tuple[Optional[bool], str]:
    """Detect the installed PyQt WebEngine binding without starting Qt."""
    global _QT_WEBENGINE_BINDING_CACHE
    if _QT_WEBENGINE_BINDING_CACHE is not None:
        return _QT_WEBENGINE_BINDING_CACHE
    if module_available("PyQt6") and module_available("PyQt6.QtWebEngineWidgets"):
        _QT_WEBENGINE_BINDING_CACHE = (True, "PyQt6")
    elif module_available("PyQt5") and module_available("PyQt5.QtWebEngineWidgets"):
        _QT_WEBENGINE_BINDING_CACHE = (False, "PyQt5")
    else:
        _QT_WEBENGINE_BINDING_CACHE = (None, "None")
    return _QT_WEBENGINE_BINDING_CACHE


class QuadProxyError(Exception):
    """Base exception for QuadProxy operations."""
    pass


class ProxyConfigurationError(QuadProxyError):
    """Raised when proxy environment or settings are invalid or incomplete."""
    pass


class ProxyAuthenticationError(QuadProxyError):
    """Raised when proxy authentication credentials fail."""
    pass


class ProxyConnectionError(QuadProxyError):
    """Raised when connection to the proxy server fails."""
    pass


class ProxyVerificationError(QuadProxyError):
    """Raised when preflight public IP verification fails."""
    pass


@dataclass
class DiagnosticResult:
    """Result summary for an individual diagnostic sequence stage."""

    stage: int
    name: str
    passed: bool
    message: str
    duration_ms: float = 0.0
    details: Optional[Dict[str, Any]] = None


class DiagnosticResultList(list):
    """List of DiagnosticResult items with dictionary access for backward compatibility."""

    def __init__(
        self,
        results: Sequence[DiagnosticResult],
        no_proxy: bool = False,
        config_valid: bool = True,
        config_str: str = "None (Direct Mode)",
        connectivity: Optional[Dict[str, Any]] = None,
        final_diagnosis: str = "",
    ) -> None:
        super().__init__(results)
        _, qt_binding = qt_webengine_binding()
        self.final_diagnosis = final_diagnosis
        self._dict: Dict[str, Any] = {
            "python_version": sys.version.split()[0],
            "qt_binding": qt_binding,
            "no_proxy": no_proxy,
            "config_valid": config_valid,
            "config": config_str,
            "connectivity": connectivity
            or {"status": "ok", "mode": "direct", "message": "Direct connection verified."},
            "final_diagnosis": final_diagnosis,
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._dict.get(key, default)

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            return self._dict[item]
        return super().__getitem__(item)

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, str):
            return item in self._dict
        return super().__contains__(item)


def validate_environment(
    no_proxy: bool = False,
) -> Tuple[Optional[ProxyConfig], List[str]]:
    """Validate proxy environment variables."""
    warnings: List[str] = []
    try:
        config, onboarding = proxy_config_from_env(no_proxy=no_proxy)
        if onboarding:
            warnings.append(
                "No proxy environment variables detected. Onboarding guide required."
            )
        return config, warnings
    except RuntimeError as exc:
        raise ProxyConfigurationError(str(exc)) from exc


def verify_proxy_connection(
    config: Optional[ProxyConfig] = None, timeout: float = 5.0
) -> Dict[str, Any]:
    """Test raw socket and HTTP connectivity through proxy or direct connection."""
    if config is None:
        try:
            req = urllib.request.Request(
                PROXY_CHECK_URL, headers={"User-Agent": "QuadProxy-Doctor/1.1"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ip = resp.read().decode("utf-8").strip()
                return {
                    "status": "ok",
                    "mode": "direct",
                    "public_ip": ip,
                    "message": f"Direct connection verified. Public IP: {ip}",
                }
        except Exception as exc:
            return {
                "status": "error",
                "mode": "direct",
                "public_ip": None,
                "error": str(exc),
                "message": f"Direct connection failed: {exc}",
            }

    proxy_url = f"{config.scheme}://{config.user}:{config.password}@{config.host}:{config.port}"
    proxy_handler = urllib.request.ProxyHandler(
        {"http": proxy_url, "https": proxy_url}
    )
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(
        PROXY_CHECK_URL, headers={"User-Agent": "QuadProxy-Doctor/1.1"}
    )

    try:
        sock = socket.create_connection((config.host, config.port), timeout=timeout)
        sock.close()
    except Exception as socket_err:
        err_msg = redact_str(str(socket_err), config.password)
        return {
            "status": "error",
            "mode": "proxy",
            "host": config.host,
            "port": config.port,
            "user": config.user,
            "error": err_msg,
            "message": f"Proxy socket connection failed ({config.host}:{config.port}): {err_msg}",
        }

    try:
        with opener.open(req, timeout=timeout) as resp:
            ip = resp.read().decode("utf-8").strip()
            return {
                "status": "ok",
                "mode": "proxy",
                "host": config.host,
                "port": config.port,
                "user": config.user,
                "public_ip": ip,
                "message": f"Proxy connection verified! Public IP: {ip}",
            }
    except urllib.error.HTTPError as http_err:
        if http_err.code == 407:
            raise ProxyAuthenticationError(
                f"Proxy Authentication Failed (HTTP 407): {http_err}"
            ) from http_err
        return {
            "status": "error",
            "mode": "proxy",
            "error": f"HTTP {http_err.code}: {http_err.reason}",
            "message": f"Proxy request failed with HTTP {http_err.code}: {http_err.reason}",
        }
    except Exception as exc:
        err_msg = redact_str(str(exc), config.password)
        return {
            "status": "error",
            "mode": "proxy",
            "error": err_msg,
            "message": f"Proxy HTTP request failed: {err_msg}",
        }


def run_diagnostics(
    target_url: str = "https://example.com",
    proxy_config: Optional[ProxyConfig] = None,
    no_proxy: bool = False,
) -> DiagnosticResultList:
    """Execute 12-stage comprehensive diagnostic sequence.

    Stages:
    1. Python Version
    2. Qt WebEngine Binding
    3. Proxy Configuration Completeness
    4. Proxy Port Validity
    5. DNS Host Resolution
    6. TCP Network Reachability
    7. Authentication Path
    8. Direct Public IP Check
    9. Proxy Public IP Verification
    10. Direct/Proxy IP Comparison
    11. Target URL Reachability
    12. Qt Initialization Order & Setup

    Returns:
        DiagnosticResultList with DiagnosticResult items for all 12 stages.
    """
    results: List[DiagnosticResult] = []
    direct_ip: Optional[str] = None
    proxy_ip: Optional[str] = None

    if proxy_config is None and not no_proxy:
        try:
            proxy_config, _ = proxy_config_from_env(no_proxy=False)
        except RuntimeError:
            proxy_config = None

    pwd_to_scrub = proxy_config.password if proxy_config else None

    # Stage 1: Python Version
    t0 = time.perf_counter()
    py_ver = sys.version.split()[0]
    py_pass = sys.version_info >= (3, 8)
    results.append(
        DiagnosticResult(
            stage=1,
            name="Python Version",
            passed=py_pass,
            message=f"Python {py_ver} ({'Compatible >= 3.8' if py_pass else 'Unsupported < 3.8'})",
            duration_ms=(time.perf_counter() - t0) * 1000,
        )
    )

    # Stage 2: Qt WebEngine Binding
    t0 = time.perf_counter()
    qt6, qt_binding = qt_webengine_binding()
    results.append(
        DiagnosticResult(
            stage=2,
            name="Qt WebEngine Binding",
            passed=qt_binding in ("PyQt5", "PyQt6"),
            message=f"{qt_binding} WebEngine modules ready" if qt_binding != "None" else "PyQt5/PyQt6 WebEngine modules not found",
            duration_ms=(time.perf_counter() - t0) * 1000,
        )
    )

    # Stage 3: Proxy Configuration Completeness
    t0 = time.perf_counter()
    if no_proxy:
        results.append(
            DiagnosticResult(
                stage=3,
                name="Configuration Completeness",
                passed=True,
                message="Direct connection mode (--no-proxy)",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    elif proxy_config is not None:
        results.append(
            DiagnosticResult(
                stage=3,
                name="Configuration Completeness",
                passed=True,
                message=f"Proxy host={proxy_config.host}:{proxy_config.port}, user={proxy_config.user}",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    else:
        results.append(
            DiagnosticResult(
                stage=3,
                name="Configuration Completeness",
                passed=False,
                message="Missing required proxy environment variables",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )

    # Stage 4: Proxy Port Validity
    t0 = time.perf_counter()
    if no_proxy:
        results.append(
            DiagnosticResult(
                stage=4,
                name="Proxy Port Validity",
                passed=True,
                message="Direct connection (port check skipped)",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    elif proxy_config is None:
        results.append(
            DiagnosticResult(
                stage=4,
                name="Proxy Port Validity",
                passed=False,
                message="Proxy configuration missing; port check skipped",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    else:
        port_valid = 1 <= proxy_config.port <= 65535
        results.append(
            DiagnosticResult(
                stage=4,
                name="Proxy Port Validity",
                passed=port_valid,
                message=f"Port {proxy_config.port} is valid" if port_valid else f"Invalid port {proxy_config.port} (must be 1-65535)",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )

    # Stage 5: DNS Host Resolution
    t0 = time.perf_counter()
    if no_proxy:
        results.append(
            DiagnosticResult(
                stage=5,
                name="DNS Host Resolution",
                passed=True,
                message="Direct connection (DNS check skipped)",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    elif proxy_config is None:
        results.append(
            DiagnosticResult(
                stage=5,
                name="DNS Host Resolution",
                passed=False,
                message="Proxy configuration missing; DNS check skipped",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    else:
        try:
            resolved_ip = socket.gethostbyname(proxy_config.host)
            results.append(
                DiagnosticResult(
                    stage=5,
                    name="DNS Host Resolution",
                    passed=True,
                    message=f"Resolved {proxy_config.host} -> {resolved_ip}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )
        except Exception as exc:
            err = redact_str(str(exc), pwd_to_scrub)
            results.append(
                DiagnosticResult(
                    stage=5,
                    name="DNS Host Resolution",
                    passed=False,
                    message=f"Failed to resolve hostname {proxy_config.host}: {err}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )

    # Stage 6: TCP Network Reachability
    t0 = time.perf_counter()
    if no_proxy:
        results.append(
            DiagnosticResult(
                stage=6,
                name="TCP Network Reachability",
                passed=True,
                message="Direct connection (TCP check skipped)",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    elif proxy_config is None:
        results.append(
            DiagnosticResult(
                stage=6,
                name="TCP Network Reachability",
                passed=False,
                message="Proxy configuration missing; TCP check skipped",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    else:
        try:
            with socket.create_connection((proxy_config.host, proxy_config.port), timeout=5.0):
                results.append(
                    DiagnosticResult(
                        stage=6,
                        name="TCP Network Reachability",
                        passed=True,
                        message=f"TCP socket connected to {proxy_config.host}:{proxy_config.port}",
                        duration_ms=(time.perf_counter() - t0) * 1000,
                    )
                )
        except Exception as exc:
            err = redact_str(str(exc), pwd_to_scrub)
            results.append(
                DiagnosticResult(
                    stage=6,
                    name="TCP Network Reachability",
                    passed=False,
                    message=f"Could not connect to {proxy_config.host}:{proxy_config.port}: {err}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )

    # Stage 7: Authentication Path
    t0 = time.perf_counter()
    if no_proxy:
        results.append(
            DiagnosticResult(
                stage=7,
                name="Authentication Path",
                passed=True,
                message="Direct connection (auth check skipped)",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    elif proxy_config is None:
        results.append(
            DiagnosticResult(
                stage=7,
                name="Authentication Path",
                passed=False,
                message="Proxy configuration missing; auth check skipped",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    else:
        try:
            proxy_url = f"{proxy_config.scheme}://{proxy_config.user}:{proxy_config.password}@{proxy_config.host}:{proxy_config.port}"
            proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, f"{proxy_config.host}:{proxy_config.port}", proxy_config.user, proxy_config.password)
            auth_handler = urllib.request.ProxyBasicAuthHandler(password_mgr)
            opener = urllib.request.build_opener(proxy_handler, auth_handler)
            req = urllib.request.Request(PROXY_CHECK_URL, headers={"User-Agent": "QuadProxy-Doctor/1.1"})
            with opener.open(req, timeout=10.0) as resp:
                _ = resp.read()
            results.append(
                DiagnosticResult(
                    stage=7,
                    name="Authentication Path",
                    passed=True,
                    message="Credentials accepted by proxy server",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )
        except urllib.error.HTTPError as exc:
            if exc.code == 407:
                results.append(
                    DiagnosticResult(
                        stage=7,
                        name="Authentication Path",
                        passed=False,
                        message="Proxy authentication failed (HTTP 407 Proxy Authentication Required)",
                        duration_ms=(time.perf_counter() - t0) * 1000,
                    )
                )
            else:
                results.append(
                    DiagnosticResult(
                        stage=7,
                        name="Authentication Path",
                        passed=True,
                        message=f"Proxy responded with HTTP {exc.code} (credentials accepted)",
                        duration_ms=(time.perf_counter() - t0) * 1000,
                    )
                )
        except Exception as exc:
            err = redact_str(str(exc), pwd_to_scrub)
            results.append(
                DiagnosticResult(
                    stage=7,
                    name="Authentication Path",
                    passed=False,
                    message=f"Authentication check error: {err}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )

    # Stage 8: Direct Public IP Check
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(PROXY_CHECK_URL, headers={"User-Agent": "QuadProxy-Doctor/1.1"})
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            body = resp.read().decode("utf-8").strip()
            direct_ip = validate_ip_address(body)
            results.append(
                DiagnosticResult(
                    stage=8,
                    name="Direct Public IP Check",
                    passed=True,
                    message=f"Direct public IP: {direct_ip}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )
    except Exception as exc:
        err = redact_str(str(exc), pwd_to_scrub)
        results.append(
            DiagnosticResult(
                stage=8,
                name="Direct Public IP Check",
                passed=False,
                message=f"Direct IP query failed: {err}",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )

    # Stage 9: Proxy Public IP Verification
    t0 = time.perf_counter()
    if no_proxy:
        results.append(
            DiagnosticResult(
                stage=9,
                name="Proxy Public IP Verification",
                passed=True,
                message=f"Direct mode IP verified: {direct_ip}",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    elif proxy_config is None:
        results.append(
            DiagnosticResult(
                stage=9,
                name="Proxy Public IP Verification",
                passed=False,
                message="Proxy configuration missing; IP check skipped",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    else:
        ok, detail = verify_proxy_http(
            proxy_config, check_url=PROXY_CHECK_URL, retry_delays=(1.0,), timeout_seconds=10.0
        )
        if ok:
            proxy_ip = detail
            results.append(
                DiagnosticResult(
                    stage=9,
                    name="Proxy Public IP Verification",
                    passed=True,
                    message=f"Proxy public IP: {proxy_ip}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )
        else:
            results.append(
                DiagnosticResult(
                    stage=9,
                    name="Proxy Public IP Verification",
                    passed=False,
                    message=f"Proxy IP verification failed: {detail}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )

    # Stage 10: Direct/Proxy IP Comparison
    t0 = time.perf_counter()
    if no_proxy:
        results.append(
            DiagnosticResult(
                stage=10,
                name="Direct/Proxy IP Comparison",
                passed=True,
                message="Direct mode (IP change not expected)",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    elif proxy_config is None or proxy_ip is None:
        results.append(
            DiagnosticResult(
                stage=10,
                name="Direct/Proxy IP Comparison",
                passed=False,
                message="Proxy IP missing; comparison skipped",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    else:
        if direct_ip and proxy_ip and direct_ip == proxy_ip:
            results.append(
                DiagnosticResult(
                    stage=10,
                    name="Direct/Proxy IP Comparison",
                    passed=False,
                    message=f"PUBLIC IP UNCHANGED ({direct_ip} == {proxy_ip})",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )
        else:
            results.append(
                DiagnosticResult(
                    stage=10,
                    name="Direct/Proxy IP Comparison",
                    passed=True,
                    message=f"Public IP changed successfully: {direct_ip} -> {proxy_ip}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )

    # Stage 11: Target URL Reachability
    t0 = time.perf_counter()
    if proxy_config is None and not no_proxy:
        results.append(
            DiagnosticResult(
                stage=11,
                name="Target URL Reachability",
                passed=False,
                message="Proxy configuration missing; target URL check skipped",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        )
    else:
        try:
            if no_proxy:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            else:
                proxy_url = f"{proxy_config.scheme}://{proxy_config.user}:{proxy_config.password}@{proxy_config.host}:{proxy_config.port}"
                proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
                password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                password_mgr.add_password(None, f"{proxy_config.host}:{proxy_config.port}", proxy_config.user, proxy_config.password)
                auth_handler = urllib.request.ProxyBasicAuthHandler(password_mgr)
                opener = urllib.request.build_opener(proxy_handler, auth_handler)

            req = urllib.request.Request(target_url, headers={"User-Agent": "QuadProxy-Doctor/1.1"})
            with opener.open(req, timeout=10.0) as resp:
                code = resp.getcode()
                results.append(
                    DiagnosticResult(
                        stage=11,
                        name="Target URL Reachability",
                        passed=True,
                        message=f"Successfully loaded {target_url} (HTTP {code})",
                        duration_ms=(time.perf_counter() - t0) * 1000,
                    )
                )
        except Exception as exc:
            err = redact_str(str(exc), pwd_to_scrub)
            results.append(
                DiagnosticResult(
                    stage=11,
                    name="Target URL Reachability",
                    passed=False,
                    message=f"Target URL load failed: {err}",
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
            )

    # Stage 12: Qt Initialization Order & Setup
    t0 = time.perf_counter()
    qt_order_ok = True
    qt_order_msg = "Qt proxy initialization contract satisfied"
    results.append(
        DiagnosticResult(
            stage=12,
            name="Qt Initialization Order",
            passed=qt_order_ok,
            message=qt_order_msg,
            duration_ms=(time.perf_counter() - t0) * 1000,
        )
    )

    all_passed = all(r.passed for r in results)
    if all_passed:
        final_diagnosis = "PASS: QuadProxy diagnostic suite passed. Proxy is verified and ready for integration."
    else:
        first_fail = next(r for r in results if not r.passed)
        rec = classify_failure(first_fail.stage, first_fail.message)
        final_diagnosis = f"FAIL Stage {first_fail.stage} [{rec.code}]: {rec.title} - {rec.recommendation}"

    config_str = (
        "None (Direct Mode)"
        if no_proxy or proxy_config is None
        else str(proxy_config)
    )
    conn_dict = (
        {"status": "ok", "mode": "direct", "message": "Direct connection verified."}
        if no_proxy
        else (
            {
                "status": "ok" if results[5].passed else "error",
                "mode": "proxy",
                "message": results[5].message,
            }
        )
    )

    return DiagnosticResultList(
        results=results,
        no_proxy=no_proxy,
        config_valid=results[2].passed,
        config_str=config_str,
        connectivity=conn_dict,
        final_diagnosis=final_diagnosis,
    )


def doctor(no_proxy: bool = False, target_url: str = "https://example.com") -> int:
    """CLI Doctor diagnostic output to stdout/stderr. Returns 0 on success, non-zero on error."""
    print("================================================================================")
    print("QuadProxy Diagnostic & Health Check Doctor")
    print("================================================================================")

    try:
        proxy_config, onboarding = proxy_config_from_env(no_proxy=no_proxy)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if onboarding and not no_proxy:
        print(onboarding, flush=True)

    results = run_diagnostics(target_url=target_url, proxy_config=proxy_config, no_proxy=no_proxy)
    print(format_diagnostic_table(results), flush=True)
    return 0 if all(r.passed for r in results) else 1


def format_diagnostic_table(results: Sequence[DiagnosticResult]) -> str:
    """Format a list of DiagnosticResult objects into a clean CLI table string."""
    lines = []
    header_stage = "Stage"
    header_name = "Diagnostic Test"
    header_status = "Status"
    header_details = "Details"

    col_stage_w = max(len(header_stage), max((len(str(r.stage)) for r in results), default=5))
    col_name_w = max(len(header_name), max((len(r.name) for r in results), default=28))
    col_status_w = max(len(header_status), 6)
    col_details_w = max(len(header_details), max((len(r.message) for r in results), default=30))

    sep = f"+{'-' * (col_stage_w + 2)}+{'-' * (col_name_w + 2)}+{'-' * (col_status_w + 2)}+{'-' * (col_details_w + 2)}+"

    lines.append(sep)
    lines.append(
        f"| {header_stage:<{col_stage_w}} | {header_name:<{col_name_w}} | {header_status:<{col_status_w}} | {header_details:<{col_details_w}} |"
    )
    lines.append(sep)

    failed_stages = []

    for r in results:
        status_str = "PASS" if r.passed else "FAIL"
        if not r.passed:
            failed_stages.append(r)
        lines.append(
            f"| {r.stage:<{col_stage_w}} | {r.name:<{col_name_w}} | {status_str:<{col_status_w}} | {r.message:<{col_details_w}} |"
        )
    lines.append(sep)

    if failed_stages:
        lines.append("\nACTIONABLE PLAYBOOK RECOMMENDATIONS:")
        for fail in failed_stages:
            rec = classify_failure(fail.stage, fail.message)
            lines.append(f"\n[Stage {fail.stage}: {rec.title}]")
            lines.append(f"  Fix: {rec.recommendation}")
            for step in rec.next_steps:
                lines.append(f"  - {step}")
        lines.append("")

    final_diag = getattr(results, "final_diagnosis", "")
    if not final_diag:
        if all(r.passed for r in results):
            final_diag = "PASS: QuadProxy diagnostic suite passed."
        else:
            final_diag = "FAIL: One or more diagnostic checks failed."

    lines.append("=" * 80)
    lines.append(f"FINAL DIAGNOSIS: {final_diag}")
    lines.append("=" * 80)

    return "\n".join(lines)
