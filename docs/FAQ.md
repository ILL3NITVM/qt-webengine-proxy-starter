# QuadProxy - Frequently Asked Questions (FAQ)

---

### Q1: Does QuadProxy include proxy servers or proxy bandwidth?
**No.** QuadProxy is a commercial software integration kit for PyQt WebEngine developers. You must supply HTTP proxy credentials from your own proxy provider (e.g. Webshare, BrightData, Oxylabs, Smartproxy, IPRoyal, etc.).

---

### Q2: Does QuadProxy support PyQt5 and PyQt6?
**Yes.** QuadProxy automatically detects whether `PyQt5` or `PyQt6` is installed in your Python environment and uses the correct Qt WebEngine binding seamlessly.

---

### Q3: How do I test QuadProxy if I don't have proxy credentials ready yet?
Run QuadProxy in **direct mode**:
```bash
python -m quadproxy doctor --no-proxy
```
This tests your Python environment, PyQt installation, network connectivity, and target site reachability without requiring proxy credentials.

---

### Q4: Why does my public IP remain unchanged after setting proxy settings?
In Qt WebEngine applications, `configure_application_proxy(config)` must be called **BEFORE** creating the `QApplication` instance. If `QApplication` is initialized first, Qt network proxy settings will not be applied to WebEngine network sockets.

---

### Q5: How do I generate a support bundle to report a problem?
Run:
```bash
python -m quadproxy support-bundle
```
This creates a redacted ZIP archive (`quadproxy-support-bundle-YYYYMMDD_HHMMSS.zip`) containing diagnostic results, system metadata, and failure classifications with **zero passwords or secrets**. Send this ZIP to `support@quadproxy.com`.

---

### Q6: Does QuadProxy send telemetry or automatically execute code updates?
**No.** QuadProxy does not collect telemetry, send tracking events, or automatically download/execute code. All update checks are manual and non-intrusive (`python -m quadproxy check-update`).

---

### Q7: What is the refund policy?
If QuadProxy fails to route traffic on a supported Python/PyQt platform due to a verified product defect, contact `support@quadproxy.com` within 14 days of purchase for a full refund.
