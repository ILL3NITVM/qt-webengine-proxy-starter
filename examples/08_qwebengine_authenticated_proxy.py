"""Minimal authenticated HTTP proxy lifecycle for a PyQt QWebEngineView.

Set PROXY_HOST, PROXY_PORT, PROXY_USER, and PROXY_PASSWORD before running.
The example keeps the Qt setup visible: configure the global QNetworkProxy
before QApplication, then handle the three-argument
proxyAuthenticationRequired signal on the page.
"""

from __future__ import annotations

import os
import sys

from quadproxy.compatibility import (
    QApplication,
    QNETWORK_HTTP_PROXY,
    QNetworkProxy,
    QUrl,
    QWebEngineView,
    exec_app,
)
from quadproxy.config import proxy_config_from_env

PUBLIC_IP_URL = "https://api.ipify.org"


def main() -> int:
    config, onboarding_message = proxy_config_from_env()
    if config is None:
        print(onboarding_message or "Set authenticated HTTP proxy environment variables.")
        return 0

    # This must happen before QApplication and all WebEngine objects.
    proxy = QNetworkProxy(QNETWORK_HTTP_PROXY, config.host, config.port)
    proxy.setUser(config.user)
    proxy.setPassword(config.password)
    QNetworkProxy.setApplicationProxy(proxy)

    app = QApplication(sys.argv)
    view = QWebEngineView()

    def handle_proxy_auth(request_url, authenticator, proxy_host):
        authenticator.setUser(config.user)
        authenticator.setPassword(config.password)

    view.page().proxyAuthenticationRequired.connect(handle_proxy_auth)

    def report_rendered_ip(loaded: bool) -> None:
        if not loaded:
            print("Public-IP page failed to load through the configured proxy.", file=sys.stderr)
            return
        view.page().runJavaScript(
            "(document.body && document.body.innerText || '').trim()",
            lambda value: print(f"Rendered public IP: {str(value or '').strip()}"),
        )

    view.loadFinished.connect(report_rendered_ip)
    view.setWindowTitle("QuadProxy Authenticated HTTP Proxy Lifecycle")
    view.resize(1024, 720)
    view.setUrl(QUrl(PUBLIC_IP_URL))
    view.show()

    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        print("Authenticated HTTP proxy lifecycle configured in offscreen mode.")
        return 0
    return exec_app(app)


if __name__ == "__main__":
    raise SystemExit(main())
