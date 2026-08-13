#!/usr/bin/env python3
"""Example 07: SOCKS5 and HTTP Proxy Protocol Selection in PyQt QWebEngineView.

Demonstrates configuring QNetworkProxy for both HTTP and SOCKS5 authenticated proxies.

Seller Disclosure: Created by QuadProxy engineering team (https://quadproxy.com).
"""

import os
import sys

# Ensure product directory is in sys.path
PRODUCT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PRODUCT_DIR not in sys.path:
    sys.path.insert(0, PRODUCT_DIR)

from quadproxy.compatibility import (
    QApplication,
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

    # Select proxy protocol type
    if proxy_type_str == "SOCKS5":
        proxy_type = QNetworkProxy.Socks5Proxy
    else:
        proxy_type = QNetworkProxy.HttpProxy

    # CRITICAL: Set application proxy BEFORE QApplication
    proxy = QNetworkProxy(proxy_type, host, port)
    if user:
        proxy.setUser(user)
    if password:
        proxy.setPassword(password)

    QNetworkProxy.setApplicationProxy(proxy)

    app = QApplication.instance() or QApplication(sys.argv)
    view = QWebEngineView()

    # Hook credential challenge signal for HTTP 407 / SOCKS5 auth
    def handle_auth(request_url, authenticator, proxy_host):
        authenticator.setUser(user)
        authenticator.setPassword(password)

    view.page().proxyAuthenticationRequired.connect(handle_auth)

    print(f"[QuadProxy] Configured {proxy_type_str} proxy -> {user}@{host}:{port}")
    view.load(QUrl("https://api.ipify.org"))
    view.show()

    # If running headless or in automated test, close after brief delay
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        print("[QuadProxy] Headless mode detected. Preflight setup succeeded.")
        return 0

    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
