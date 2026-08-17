#!/usr/bin/env python3
"""Example 07: authenticated HTTP proxy scope validation.

QuadProxy v1.0 configures authenticated HTTP proxies only. SOCKS5 and HTTPS
proxy schemes are intentionally rejected rather than silently attempting an
unsupported configuration.
"""

import os
import sys

# Ensure product directory is in sys.path
PRODUCT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PRODUCT_DIR not in sys.path:
    sys.path.insert(0, PRODUCT_DIR)

from quadproxy.compatibility import (
    QApplication,
    QNETWORK_HTTP_PROXY,
    QNetworkProxy,
    QUrl,
    QWebEngineView,
)

def main():
    proxy_type_str = os.environ.get("PROXY_TYPE", "HTTP").upper()
    host = os.environ.get("PROXY_HOST", "proxy.example.com")
    port = int(os.environ.get("PROXY_PORT", "8080"))
    user = os.environ.get("PROXY_USER", "my_user")
    password = os.environ.get("PROXY_PASSWORD", "my_pass")

    if proxy_type_str != "HTTP":
        print(
            "QuadProxy v1.0 supports authenticated HTTP proxies only; "
            "SOCKS5 and HTTPS proxy schemes are not supported.",
            file=sys.stderr,
        )
        return 2

    # Set the application proxy before QApplication and all WebEngine objects.
    proxy = QNetworkProxy(QNETWORK_HTTP_PROXY, host, port)
    if user:
        proxy.setUser(user)
    if password:
        proxy.setPassword(password)

    QNetworkProxy.setApplicationProxy(proxy)

    app = QApplication.instance() or QApplication(sys.argv)
    view = QWebEngineView()

    # Handle the HTTP 407 authentication challenge.
    def handle_auth(request_url, authenticator, proxy_host):
        authenticator.setUser(user)
        authenticator.setPassword(password)

    view.page().proxyAuthenticationRequired.connect(handle_auth)

    print(f"[QuadProxy] Configured authenticated HTTP proxy -> {user}@{host}:{port}")
    view.load(QUrl("https://api.ipify.org"))
    view.show()

    # If running headless or in automated test, close after brief delay
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        print("[QuadProxy] Headless mode detected. Preflight setup succeeded.")
        return 0

    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
