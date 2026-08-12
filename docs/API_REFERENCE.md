# QuadProxy API Reference

Complete Python API documentation for the `quadproxy` package, including core modules, classes, functions, and diagnostics utilities.

---

## Package Summary

```text
quadproxy
├── ProxyConfig                      (dataclass)
├── proxy_config_from_env()          (function)
├── configure_application_proxy()    (function)
├── ProxyCheckingWindow              (QMainWindow)
├── QT6                              (bool)
├── diagnostics                      (submodule)
│   ├── QuadProxyError               (Exception)
│   ├── ProxyConfigurationError      (QuadProxyError)
│   ├── ProxyConnectionError         (QuadProxyError)
│   ├── ProxyAuthenticationError     (QuadProxyError)
│   ├── ProxyVerificationError       (QuadProxyError)
│   ├── validate_environment()       (function)
│   ├── verify_proxy_connection()    (function)
│   ├── run_diagnostics()            (function)
│   └── doctor()                     (function)
└── cli                              (submodule)
    └── main()                       (function)
```

---

## 1. Core Module (`quadproxy`)

### `ProxyConfig`

Immutable dataclass holding proxy server connection parameters and credentials.

```python
@dataclass(frozen=True)
class ProxyConfig:
    host: str
    port: int
    user: str
    password: str
    scheme: str = "http"
```

#### Attributes

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `host` | `str` | Hostname or IP address of proxy server (e.g. `proxy.example.net`). |
| `port` | `int` | Port number of proxy server (e.g. `8080`). |
| `user` | `str` | Proxy authentication username. |
| `password` | `str` | Proxy authentication password. |
| `scheme` | `str` | Proxy scheme. QuadProxy v1.0 supports authenticated HTTP proxies only; use `http`. |

#### Security Representation Masking

`ProxyConfig` overrides `__repr__` and `__str__` to prevent accidental credential leakage in logs:
```python
repr(config)  # -> "ProxyConfig(host='proxy.example.net', port=8080, user='myuser', password='***')"
str(config)   # -> "ProxyConfig(myuser@proxy.example.net:8080)"
```

---

### `proxy_config_from_env()`

Resolves proxy configuration from active process environment variables.

```python
def proxy_config_from_env(no_proxy: bool = False) -> tuple[Optional[ProxyConfig], Optional[str]]
```

#### Parameters
- **`no_proxy`** (`bool`): If `True`, returns `(None, None)` to run in direct diagnostic mode without environment checks.

#### Returns
- **`tuple[Optional[ProxyConfig], Optional[str]]`**: `(config, onboarding_message)`
  - If `no_proxy` is `True`: `(None, None)`
  - If zero proxy environment variables are set: `(None, onboarding_guide_string)`
  - If all 4 proxy variables are set: `(ProxyConfig, None)`

#### Environment Variables Evaluated
- `PROXY_HOST` (required)
- `PROXY_PORT` (required integer)
- `PROXY_USER` (required)
- `PROXY_PASSWORD` (required; falls back to `WEBSHARE_PROXY_PASSWORD` if unset)
- `PROXY_SCHEME` (optional; only `http` is supported)

#### Exceptions Raised
- **`RuntimeError`**: Raised if proxy environment variables are partially specified (e.g., host and port set, but user missing).

---

### `configure_application_proxy()`

Configures global Qt application network proxy via `QNetworkProxy.setApplicationProxy()`.

```python
def configure_application_proxy(config: Optional[ProxyConfig]) -> None
```

#### Parameters
- **`config`** (`Optional[ProxyConfig]`): The `ProxyConfig` object to apply, or `None` to set `QNetworkProxy.NoProxy` (direct connection mode).

---

### `ProxyCheckingWindow`

PyQt `QMainWindow` component that runs automated preflight public IP verification via `api.ipify.org` before navigating to target URLs.

```python
class ProxyCheckingWindow(QMainWindow):
    def __init__(self, target_url: str, proxy_config: Optional[ProxyConfig]) -> None
    def start(self) -> None
```

#### Parameters
- **`target_url`** (`str`): The final application URL to load once proxy verification succeeds.
- **`proxy_config`** (`Optional[ProxyConfig]`): Active proxy configuration, or `None` for direct mode.

---

## 2. Diagnostics Submodule (`quadproxy.diagnostics`)

### Exception Hierarchy

```text
Exception
 └── QuadProxyError
      ├── ProxyConfigurationError
      ├── ProxyConnectionError
      ├── ProxyAuthenticationError
      └── ProxyVerificationError
```

---

### `validate_environment()`

Validates proxy environment variables and returns configuration or raises `ProxyConfigurationError`.

```python
def validate_environment(no_proxy: bool = False) -> Tuple[Optional[ProxyConfig], List[str]]
```

---

### `verify_proxy_connection()`

Tests TCP socket reachability and HTTP GET through proxy to `https://api.ipify.org`.

```python
def verify_proxy_connection(config: Optional[ProxyConfig] = None, timeout: float = 5.0) -> Dict[str, Any]
```

#### Returns Dictionary Format:
```json
{
  "status": "ok",
  "mode": "proxy",
  "host": "proxy.example.net",
  "port": 8080,
  "user": "myuser",
  "public_ip": "203.0.113.1",
  "message": "Proxy connection verified! Public IP: 203.0.113.1"
}
```

---

### `run_diagnostics()`

Runs the full six-stage diagnostic health check suite.

```python
def run_diagnostics(
    target_url: str = "https://example.com",
    proxy_config: Optional[ProxyConfig] = None,
    no_proxy: bool = False,
) -> DiagnosticResultList
```

`DiagnosticResultList` behaves like a list of `DiagnosticResult` objects and keeps a small dictionary-compatible metadata interface for older integrations.

---

### `doctor()`

CLI entry point helper for executing and displaying health check results to console.

```python
def doctor(no_proxy: bool = False) -> int
```

#### Returns
- **`0`**: Diagnostics passed successfully.
- **`1`**: One or more diagnostic stages failed.

---

## 3. CLI Submodule (`quadproxy.cli`)

### `main()`

CLI entry point for `quadproxy-doctor` executable.

```python
def main() -> int
```
