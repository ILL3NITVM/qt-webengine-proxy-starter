# QuadProxy - PyQt Integration Guide

QuadProxy seamlessly integrates authenticated HTTP proxies into existing PyQt5 and PyQt6 WebEngine applications.

---

## PyQt5 Integration Pattern

```python
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from quadproxy import ProxyConfig, configure_application_proxy

def main():
    # 1. Instantiate ProxyConfig
    config = ProxyConfig(
        host="proxy.example.net",
        port=8080,
        user="my_username",
        password="my_password"
    )

    # 2. Set global application proxy BEFORE QApplication creation
    configure_application_proxy(config)

    # 3. Create QApplication & QWebEngineView
    app = QApplication(sys.argv)
    view = QWebEngineView()
    def handle_proxy_auth(request_url, authenticator, proxy_host):
        authenticator.setUser(config.user)
        authenticator.setPassword(config.password)
    view.page().proxyAuthenticationRequired.connect(handle_proxy_auth)
    view.setWindowTitle("PyQt5 QuadProxy Integration")
    view.resize(1024, 768)
    view.load("https://api.ipify.org")
    view.show()

    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
```

---

## PyQt6 Integration Pattern

```python
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from quadproxy import ProxyConfig, configure_application_proxy

def main():
    config = ProxyConfig(
        host="proxy.example.net",
        port=8080,
        user="my_username",
        password="my_password"
    )

    # Global proxy setup works identically across PyQt5 and PyQt6
    configure_application_proxy(config)

    app = QApplication(sys.argv)
    view = QWebEngineView()
    def handle_proxy_auth(request_url, authenticator, proxy_host):
        authenticator.setUser(config.user)
        authenticator.setPassword(config.password)
    view.page().proxyAuthenticationRequired.connect(handle_proxy_auth)
    view.setWindowTitle("PyQt6 QuadProxy Integration")
    view.resize(1024, 768)
    view.load("https://api.ipify.org")
    view.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

---

## Environment Variable Auto-Loading

For production applications, load proxy configuration directly from environment variables:

```python
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from quadproxy import proxy_config_from_env, configure_application_proxy

config, onboarding_msg = proxy_config_from_env(no_proxy=False)
if onboarding_msg:
    print(onboarding_msg)
    sys.exit(1)

configure_application_proxy(config)

app = QApplication(sys.argv)
view = QWebEngineView()
def handle_proxy_auth(request_url, authenticator, proxy_host):
    if config:
        authenticator.setUser(config.user)
        authenticator.setPassword(config.password)
view.page().proxyAuthenticationRequired.connect(handle_proxy_auth)
view.load("https://example.com")
view.show()
sys.exit(app.exec_())
```

---

## Direct (No-Proxy) Troubleshooting Mode

Pass `None` or `no_proxy=True` to bypass proxy configuration for testing:

```python
from quadproxy import configure_application_proxy

# Reverts application proxy to direct connection (QNetworkProxy.NoProxy)
configure_application_proxy(None)
```
