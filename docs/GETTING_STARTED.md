# QuadProxy - Getting Started Guide

Welcome to **QuadProxy**! This guide takes you from purchase to successful proxy integration in your PyQt WebEngine application.

---

## The 9-Stage Customer Activation Journey

```
PURCHASE ➔ DOWNLOAD ➔ EXTRACT ➔ LAUNCH ➔ CONFIGURE ➔ TEST ➔ VERIFIED ➔ INTEGRATE ➔ SUCCESS
```

Every step is supported by QuadProxy CLI diagnostics and Desktop GUI Wizard.

---

## 1. Prerequisites

- **Python**: 3.8, 3.9, 3.10, 3.11, or 3.12
- **PyQt**: PyQt5 (`PyQt5` + `PyQtWebEngine`) or PyQt6 (`PyQt6` + `PyQt6-WebEngine`)
- **Proxy Credentials**: HTTP authenticated proxy (Host, Port, Username, Password) from your proxy provider (Webshare, BrightData, Oxylabs, Smartproxy, etc.).

> **NOTE**: QuadProxy is an integration engine and developer kit. It does not sell or bundle proxy bandwidth/servers.

---

## 2. Installation

1. Download `qt-webengine-proxy-starter.zip` from your customer delivery link.
2. Extract the ZIP archive:
   ```bash
   unzip qt-webengine-proxy-starter.zip -d quadproxy-app
   cd quadproxy-app
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. First-Run Setup & Diagnostics

Choose one of two quickstart methods:

### Option A: Desktop GUI Wizard (Recommended)
Launch the interactive configuration wizard:
```bash
python -m quadproxy wizard
```
Features:
- Live proxy testing and public IP verification
- Interactive Activation Checklist
- One-click Python integration code generator
- Direct mode toggle for troubleshooting

### Option B: Command-Line Diagnostics
Configure your environment variables:

**Linux / macOS (Bash):**
```bash
export PROXY_HOST="proxy.example.net"
export PROXY_PORT="8080"
export PROXY_USER="your_username"
export PROXY_PASSWORD="your_password"

python -m quadproxy doctor
```

**Windows (PowerShell):**
```powershell
$env:PROXY_HOST="proxy.example.net"
$env:PROXY_PORT="8080"
$env:PROXY_USER="your_username"
$env:PROXY_PASSWORD="your_password"

python -m quadproxy doctor
```

---

## 4. Activation Checklist

Track your onboarding progress anytime with:
```bash
python -m quadproxy checklist
```

Checklist Items:
- [x] Python environment ready
- [x] PyQt5 or PyQt6 available
- [x] Proxy credentials entered
- [x] Proxy reachable
- [x] Authentication successful
- [x] Public IP changed
- [x] Target URL loaded
- [ ] Integration snippet copied
- [ ] Existing application tested

---

## 5. Integrating into Your Application

To enable proxying across all Qt WebEngine views in your application, call `configure_application_proxy(config)` **BEFORE** creating your `QApplication` instance:

```python
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from quadproxy import ProxyConfig, configure_application_proxy

# 1. Load credentials from environment or config
config = ProxyConfig(
    host="proxy.example.net",
    port=8080,
    user="your_username",
    password="your_password"
)

# 2. Configure proxy BEFORE QApplication creation
configure_application_proxy(config)

# 3. Create QApplication & load target page
app = QApplication(sys.argv)
view = QWebEngineView()
view.load("https://api.ipify.org")
view.show()
sys.exit(app.exec_())
```

---

## Next Steps

- View [DOCTOR.md](DOCTOR.md) for full diagnostic command options.
- View [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for actionable failure resolutions.
- View [INTEGRATION.md](INTEGRATION.md) for advanced PyQt5 / PyQt6 code snippets.
