# QuadProxy Documentation

This free technical reference helps PyQt5 and PyQt6 developers move from a
minimal `QWebEngineView` proxy setup to a verified application integration.

## Start Here

| Goal | Resource |
|---|---|
| Install and run the first direct-mode check | [Quickstart](QUICKSTART.md) |
| Understand startup order, the authentication callback, and the restart rule | [QWebEngine proxy lifecycle](QWEBENGINE_PROXY_LIFECYCLE.md) |
| Integrate into an existing desktop application | [Integration guide](INTEGRATION_GUIDE.md) |
| Run a minimal rendered public-IP check | [`examples/08_qwebengine_authenticated_proxy.py`](../examples/08_qwebengine_authenticated_proxy.py) |

## Diagnose and Verify

- [Doctor diagnostics](DOCTOR.md) explains the diagnostic output.
- [Troubleshooting](TROUBLESHOOTING.md) maps common HTTP 407, public-IP, and
  initialization failures to next steps.
- [Authentication callbacks](AUTHENTICATION_CALLBACKS.md) covers
  `QWebEnginePage.proxyAuthenticationRequired`.
- [FAQ](FAQ.md) documents scope limits, including per-view isolation and DNS
  verification boundaries.

## Reference and Safety

- [API reference](API_REFERENCE.md)
- [Security and credential handling](SECURITY.md)
- [Getting started](GETTING_STARTED.md)

QuadProxy supports authenticated HTTP proxies in its `doctor` and `wizard`
workflow. It does not include a proxy service, proxy IPs, SOCKS5 support, or
a claim of per-tab proxy isolation inside one running Qt WebEngine process.
