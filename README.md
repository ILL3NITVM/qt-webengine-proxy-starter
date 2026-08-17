# Qt WebEngine Proxy Starter Kit (QuadProxy)

Production-grade starter kit and diagnostic CLI for running PyQt5 and PyQt6 `QWebEngineView` desktop applications through authenticated HTTP proxies.

* **Product Site & Storefront:** [https://quadproxy.com](https://quadproxy.com)
* **Commercial Kit:** $29.00 USD one-time download
* **Seller Disclosure:** Built by QuadProxy engineering team for Python desktop app developers.

> **Note:** This product does not include a proxy subscription or proxy IPs. Bring your own credentials from your HTTP proxy provider (e.g. Webshare, BrightData, Smartproxy, Oxylabs, etc.).

---

## The QWebEngineView Proxy Problem & Fix

If your `QWebEngineView` in PyQt fails to load pages when using an authenticated HTTP proxy (or drops back to your direct local IP), it comes down to two specific Qt WebEngine networking behaviors:

1. **Initialization Order Violation:** `QNetworkProxy.setApplicationProxy(proxy)` MUST be invoked **before** creating `QApplication(sys.argv)`. If invoked afterwards, Chromium's internal network process ignores the updated application proxy settings.
2. **Uncaught 407 Challenge:** Chromium does not automatically pass `QNetworkProxy` credentials to browser render tasks. When an HTTP proxy returns `407 Proxy Authentication Required`, Qt WebEngine emits `QWebEnginePage.proxyAuthenticationRequired`. If no slot handles this signal, Chromium cancels the request silently without throwing a Python exception.

### Minimal Working Solution (PyQt5 & PyQt6)

```python
import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkProxy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView

# STEP 1: Set global application proxy BEFORE QApplication
proxy = QNetworkProxy(QNetworkProxy.HttpProxy, "proxy.example.com", 8080)
proxy.setUser("my_username")
proxy.setPassword("my_password")
QNetworkProxy.setApplicationProxy(proxy)

# STEP 2: Create QApplication
app = QApplication(sys.argv)

# STEP 3: Connect proxy authentication callback
view = QWebEngineView()
def handle_proxy_auth(request_url, authenticator, proxy_host):
    authenticator.setUser("my_username")
    authenticator.setPassword("my_password")

view.page().proxyAuthenticationRequired.connect(handle_proxy_auth)

# STEP 4: Preflight public-IP verification & load
view.load(QUrl("https://api.ipify.org"))
view.show()
sys.exit(app.exec_())
```

---

## Quickstart Setup

Open a terminal inside `qt-webengine-proxy-starter`.

### 1. Create Virtual Environment

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 2. Install Local Package

PyQt6:
```bash
python -m pip install -e ".[pyqt6]"
```

PyQt5:
```bash
python -m pip install -e ".[pyqt5]"
```

### 3. Verify Install without Proxy (Direct Mode)

```bash
python -m quadproxy doctor --no-proxy
```

This confirms Python runtime, Qt WebEngine bindings, direct connectivity, public-IP lookup through `https://api.ipify.org`, and target URL loading.

### 4. Add Proxy Credentials & Run Diagnostics

Linux / macOS:
```bash
export PROXY_HOST="proxy.example.com"
export PROXY_PORT="8080"
export PROXY_USER="your_username"
export PROXY_PASSWORD="your_password"

python -m quadproxy doctor
python qt_proxy_starter.py --url https://example.com
```

Guided Setup UI (Desktop):
```bash
python -m quadproxy wizard
```

---

## Free Public Reference vs. $29 Commercial Download

The GitHub repository is a free technical reference for the Qt WebEngine
proxy lifecycle. The $29 purchase is a one-time digital delivery of the
QuadProxy starter kit under its commercial single-customer license. Neither
one is a proxy service, proxy subscription, or source of proxy IPs.

| | Free GitHub Reference | $29 at [quadproxy.com](https://quadproxy.com) |
|---|---|---|
| **Purpose** | Learn the initialization, 407 callback, and rendered-IP verification pattern. | Download the packaged starter kit for use in an application you own or operate. |
| **Material** | Lifecycle guide, troubleshooting, API documentation, and runnable reference examples. | ZIP delivery with the starter application, diagnostics, setup wizard, support-bundle workflow, and documentation. |
| **License / use** | Read the repository license before using or redistributing any source. It is not an open-source license grant. | A commercial single-customer license to use, modify, and deploy the kit in applications you own or operate; see `LICENSE.txt`. |
| **Proxy IPs, bandwidth, or accounts** | Not included. | Not included. Bring credentials from your own provider. |
| **Support path** | Public documentation, Issues, and Discussions for sanitized setup questions. | `support@quadproxy.com` for commercial-kit setup and defect reports; never send credentials. |

## What QuadProxy Does Not Provide

- A proxy service, proxy IPs, bandwidth, proxy accounts, or credentials.
- SOCKS5 or HTTPS proxy setup in the v1.0 workflow; the supported proxy scheme
  is authenticated HTTP.
- Per-tab or per-`QWebEngineView` proxy isolation in one running Qt WebEngine
  process. Use separate processes for separate proxy identities.
- Reliable proxy rotation after WebEngine starts. Restart the process after a
  proxy endpoint or credential change.
- Proof of DNS privacy, access to a particular target site, or immunity from a
  proxy provider's outage or target-site restrictions.

---

## Package Contents

- `quadproxy/`: Package with proxy configuration, authentication callbacks, diagnostics, and GUI wizard.
- `qt_proxy_starter.py`: Standalone starter app entry point.
- `examples/`: Eight runnable integration patterns for PyQt5 and PyQt6,
  including a minimal authenticated HTTP lifecycle and rendered public-IP
  check.
- `docs/`: Quickstart, lifecycle, integration, troubleshooting, and API
  references.

---

## Documentation

- `docs/README.md`: Documentation index.
- `docs/QUICKSTART.md`: Installation and first verification.
- `docs/QWEBENGINE_PROXY_LIFECYCLE.md`: Startup order, callback, verification,
  and scope limits.
- `docs/INTEGRATION_GUIDE.md`: Embedding QuadProxy into existing PyQt applications.
- `docs/TROUBLESHOOTING.md`: Common failure modes and resolution steps.
- `docs/API_REFERENCE.md`: Package API reference.

---

## Security Notes

- Proxy passwords are read from environment variables and are redacted in `ProxyConfig.__repr__`, logs, and diagnostic errors.
- Preflight checks verify the outward public IP before navigating to target URLs.
- Zero Stripe keys, webhook secrets, proxy passwords, or private data exist in this repository.

---

## License

Commercial single-customer starter-kit license. See `LICENSE.txt`.
