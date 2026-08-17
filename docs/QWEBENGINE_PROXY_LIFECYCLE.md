# QWebEngineView Authenticated HTTP Proxy Lifecycle

This free reference explains the smallest reliable lifecycle for routing a
PyQt5 or PyQt6 `QWebEngineView` through an authenticated HTTP proxy.

## The Lifecycle

1. Read and validate the proxy configuration before creating Qt objects.
2. Call `QNetworkProxy.setApplicationProxy()` before `QApplication` and before
   every WebEngine object is created.
3. Create `QApplication`, then create each `QWebEngineView` or
   `QWebEnginePage`.
4. Connect a handler for
   `proxyAuthenticationRequired(request_url, authenticator, proxy_host)` on
   every page that can make authenticated proxy requests.
5. Load a neutral public-IP endpoint and read the rendered page value before
   navigating to a target page.
6. Restart the process if the proxy endpoint or credentials change.

Qt WebEngine uses an application/browser-process-scoped proxy. It does not
offer reliable per-tab or per-`QWebEngineView` proxy isolation inside one
running process.

## Minimal Reference

The included
[`examples/08_qwebengine_authenticated_proxy.py`](../examples/08_qwebengine_authenticated_proxy.py)
is directly runnable after setting `PROXY_HOST`, `PROXY_PORT`, `PROXY_USER`,
and `PROXY_PASSWORD`. Its core is:

```python
proxy = QNetworkProxy(QNETWORK_HTTP_PROXY, config.host, config.port)
proxy.setUser(config.user)
proxy.setPassword(config.password)
QNetworkProxy.setApplicationProxy(proxy)  # Before QApplication

app = QApplication(sys.argv)
view = QWebEngineView()

def handle_proxy_auth(request_url, authenticator, proxy_host):
    authenticator.setUser(config.user)
    authenticator.setPassword(config.password)

view.page().proxyAuthenticationRequired.connect(handle_proxy_auth)
view.setUrl(QUrl("https://api.ipify.org"))
```

For PyQt6, `QNetworkProxy.ProxyType.HttpProxy` is the enum value; for PyQt5 it
is `QNetworkProxy.HttpProxy`. The example imports QuadProxy's compatibility
constant so the same source runs with either binding.

## What Public-IP Verification Proves

When the rendered IP endpoint finishes successfully and shows the proxy
provider's egress address, it verifies the WebEngine request used for that
check traveled through the expected proxy route. It does not independently
prove DNS privacy, all future target requests, or isolation between tabs.
Validate those properties separately when they matter.

## Common Failure Modes

| Symptom | First check |
|---|---|
| `loadFinished(False)` or a blank page | Confirm the proxy was set before `QApplication` and that the page callback is connected. |
| HTTP 407 | Check the callback accepts all three arguments and sets the credential fields. |
| Direct IP appears | Restart the application after moving proxy setup before WebEngine initialization. |
| Different proxy required for another tab | Run a separate process for that proxy identity. |

Continue with the [integration guide](INTEGRATION_GUIDE.md) for multi-window
applications or [troubleshooting](TROUBLESHOOTING.md) for diagnostic steps.
