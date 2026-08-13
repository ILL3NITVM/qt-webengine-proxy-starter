# PyQt5 & PyQt6 QWebEngineView Authentication Callback Architecture

This guide details the internal mechanism of handling HTTP 407 (`Proxy Authentication Required`) challenges in Qt WebEngine.

---

## The Core Technical Mismatch

In standard Python `requests` or `urllib3`, proxy credentials passed in the proxy URL (`http://user:pass@host:port`) are automatically formatted into `Proxy-Authorization: Basic ...` HTTP headers.

In Qt WebEngine, however:
1. `QNetworkProxy.setUser("user")` and `setPassword("pass")` are used ONLY for standard Qt socket operations (`QNetworkAccessManager`, `QTcpSocket`).
2. Chromium (`QtWebEngineProcess`) manages its own independent HTTP connection pool.
3. When an HTTP proxy demands authentication, Chromium emits a `407 Proxy Authentication Required` challenge to the main process via IPC.
4. Qt WebEngine wraps this challenge in the signal `QWebEnginePage.proxyAuthenticationRequired(QUrl, QAuthenticator, QString)`.

---

## Signal Callback Implementation

### PyQt5
```python
from PyQt5.QtWebEngineWidgets import QWebEngineView

view = QWebEngineView()

def handle_proxy_challenge(request_url, authenticator, proxy_host):
    authenticator.setUser("your_proxy_username")
    authenticator.setPassword("your_proxy_password")

view.page().proxyAuthenticationRequired.connect(handle_proxy_challenge)
```

### PyQt6
```python
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView

view = QWebEngineView()

def handle_proxy_challenge(request_url, authenticator, proxy_host):
    authenticator.setUser("your_proxy_username")
    authenticator.setPassword("your_proxy_password")

view.page().proxyAuthenticationRequired.connect(handle_proxy_challenge)
```

---

## Preflight Verification Pattern

Before navigating to sensitive web targets, always execute a preflight verification request to `https://api.ipify.org` to confirm that:
1. `loadFinished(True)` is received.
2. The rendered page text matches your expected proxy egress IP.

---

## Commercial QuadProxy Starter Kit

If you require a production-grade starter kit that automates preflight checks, environment variable loading, CLI diagnostic suites (`python -m quadproxy doctor`), and GUI setup wizards:

- **Storefront:** [https://quadproxy.com](https://quadproxy.com)
- **Price:** $29.00 USD one-time purchase
- **Seller Disclosure:** Built by QuadProxy engineering team for Python desktop app developers.
