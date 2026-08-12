# QuadProxy Technical Demonstration Plan

A concise, high-converting technical demonstration showing the exact failure mode of PyQt WebEngine proxies and how QuadProxy resolves it in 3 lines of Python.

---

## Technical Problem Statement

In PyQt5 and PyQt6, setting up an **authenticated HTTP proxy** for `QWebEngineView` frequently fails:
1. **Timing Bug**: Setting `QNetworkProxy.setApplicationProxy` *after* `QApplication` instantiation leaves Chromium WebEngine network sockets un-proxied or silently failing.
2. **Auth Challenge Loop**: Missing or un-handled `proxyAuthenticationRequired` signals cause infinite white screens or unhandled HTTP 407 Proxy Authentication Required errors.
3. **Unverified IP**: Developers assume the proxy works without verifying if WebEngine traffic is *actually* routing through the proxy IP versus the host's direct public IP.

---

## Killer Demo Walkthrough (Video/GIF Plan)

### Step 1: The Broken Attempt (15 seconds)
- Run a standard PyQt WebEngine script setting `QNetworkProxy` after `QApplication`.
- **Result**: The window displays a blank white screen, fails to respond to proxy authentication challenges, or direct public IP leaks.

### Step 2: The Root Cause Diagnosis (10 seconds)
- Run `python -m quadproxy doctor`.
- **Result**: Stage 7 (`Authentication Path`) or Stage 10 (`Direct/Proxy IP Comparison`) reports `FAIL [PUBLIC_IP_UNCHANGED]` or `FAIL [AUTHENTICATION_REJECTED]`.

### Step 3: QuadProxy 3-Line Fix (15 seconds)
- Add `configure_application_proxy(config)` BEFORE `QApplication(sys.argv)`.
- Re-run `python -m quadproxy doctor`.
- **Result**:
  ```
  +-------+------------------------------+--------+----------------------------------------------------+
  | Stage | Diagnostic Test              | Status | Details                                            |
  +-------+------------------------------+--------+----------------------------------------------------+
  | 8     | Direct Public IP Check       | PASS   | Direct public IP: 132.226.129.99                   |
  | 9     | Proxy Public IP Verification | PASS   | Proxy public IP: 185.220.101.5                     |
  | 10    | Direct/Proxy IP Comparison   | PASS   | Public IP changed successfully: 132.226... -> 185.220... |
  +-------+------------------------------+--------+----------------------------------------------------+
  FINAL DIAGNOSIS: PASS: QuadProxy diagnostic suite passed. Proxy is verified and ready.
  ```

### Step 4: Successful WebEngine Load (10 seconds)
- Launch application window. Target page loads instantly with verified proxy IP displayed.

---

## Code Comparison

### BEFORE (Broken / Unverified Setup)
```python
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QNetworkProxy
from PyQt5.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)  # ❌ ERROR: QApplication created before proxy set!

proxy = QNetworkProxy(QNetworkProxy.HttpProxy, "proxy.example.net", 8080)
proxy.setUser("user")
proxy.setPassword("pass")
QNetworkProxy.setApplicationProxy(proxy)  # ❌ Fails to apply to WebEngine sockets!

view = QWebEngineView()
view.load("https://api.ipify.org")  # ❌ Fails with white screen or direct IP leak
view.show()
sys.exit(app.exec_())
```

### AFTER (QuadProxy 3-Line Verified Setup)
```python
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from quadproxy import ProxyConfig, configure_application_proxy

# 1. Instantiate immutable configuration
config = ProxyConfig(host="proxy.example.net", port=8080, user="user", password="pass")

# 2. Configure global proxy BEFORE QApplication instantiation
configure_application_proxy(config)  # ✅ Contract timing satisfied

# 3. Launch application
app = QApplication(sys.argv)
view = QWebEngineView()
view.load("https://api.ipify.org")  # ✅ Verified routing & public IP changed
view.show()
sys.exit(app.exec_())
```

---

## Architectural Flow Diagram

```
STANDARD PYQT ATTEMPT (BROKEN):
  Script Start ➔ QApplication() ➔ QNetworkProxy() ➔ WebEngine View ➔ ❌ White Screen / Direct IP Leak

QUADPROXY PATTERN (VERIFIED):
  Script Start ➔ ProxyConfig() ➔ configure_application_proxy() ➔ QApplication() ➔ WebEngine View ➔ ✅ Proxy IP Verified
```
