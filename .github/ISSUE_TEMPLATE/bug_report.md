---
name: Proxy Setup Bug Report
about: Report a QWebEngineView proxy authentication or load failure
title: '[BUG]: '
labels: bug
assignees: ''

---

**Describe the Proxy Issue**
A clear and concise description of what fails (e.g. blank white screen, 407 authentication prompt popup, direct IP leak, or loadFinished(False)).

**Environment Information**
- OS: [e.g. Windows 11, Ubuntu 22.04, macOS Sonoma]
- Python Version: [e.g. 3.9, 3.11]
- Qt Binding: [e.g. PyQt5 5.15.9, PyQt6 6.5.0, PySide6 6.5.0]
- Proxy Type: [e.g. authenticated HTTP]

**Minimal Code Snippet**
```python
# Paste your QNetworkProxy / QWebEngineView initialization code here
```

**Security**

Never paste a real proxy hostname, username, password, token, checkout
session, or order token. Replace sensitive values with placeholders before
submitting.

**Output of CLI Diagnostic Tool**
Run `python -m quadproxy doctor` and paste sanitized output below (secrets are automatically masked):
```
[Paste output here]
```

---

For a setup question rather than a reproducible bug, use
[GitHub Discussions](https://github.com/ILL3NITVM/qt-webengine-proxy-starter/discussions).
