"""QuadProxy package for PyQt WebEngine authenticated proxy integration."""

from quadproxy.config import ProxyConfig, proxy_config_from_env

__version__ = "1.1.0"

__all__ = [
    "__version__",
    "QT6",
    "ProxyConfig",
    "configure_application_proxy",
    "ProxyCheckingWindow",
    "run_diagnostics",
    "format_diagnostic_table",
    "proxy_config_from_env",
    "DiagnosticResult",
    "QuadProxyWizard",
    "launch_wizard",
    "ActivationChecklist",
    "generate_support_bundle",
    "classify_failure",
]


def __getattr__(name: str):
    """Lazily expose Qt-backed and support helpers without slowing simple CLI help/imports."""
    if name == "QT6":
        from quadproxy.compatibility import QT6

        globals()[name] = QT6
        return QT6
    if name in {"DiagnosticResult", "run_diagnostics", "format_diagnostic_table"}:
        from quadproxy.diagnostics import DiagnosticResult, run_diagnostics, format_diagnostic_table

        values = {
            "DiagnosticResult": DiagnosticResult,
            "run_diagnostics": run_diagnostics,
            "format_diagnostic_table": format_diagnostic_table,
        }
    elif name in {"ProxyCheckingWindow", "configure_application_proxy"}:
        from quadproxy.proxy import ProxyCheckingWindow, configure_application_proxy

        values = {
            "ProxyCheckingWindow": ProxyCheckingWindow,
            "configure_application_proxy": configure_application_proxy,
        }
    elif name in {"QuadProxyWizard", "launch_wizard"}:
        from quadproxy.wizard import QuadProxyWizard, launch_wizard

        values = {
            "QuadProxyWizard": QuadProxyWizard,
            "launch_wizard": launch_wizard,
        }
    elif name == "ActivationChecklist":
        from quadproxy.activation import ActivationChecklist

        values = {"ActivationChecklist": ActivationChecklist}
    elif name == "generate_support_bundle":
        from quadproxy.support_bundle import generate_support_bundle

        values = {"generate_support_bundle": generate_support_bundle}
    elif name == "classify_failure":
        from quadproxy.playbook import classify_failure

        values = {"classify_failure": classify_failure}
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals().update(values)
    return values[name]
