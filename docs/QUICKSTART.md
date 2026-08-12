# 5 Minute Quickstart - QuadProxy

This guide assumes you have downloaded and unzipped `qt-webengine-proxy-starter.zip`.

QuadProxy supports PyQt6 and PyQt5. Install exactly one stack in a virtual environment.

> Important: QuadProxy is a starter package and integration pattern. It does not include a proxy service or proxy account.

## 1. Open The Unzipped Folder

```bash
cd qt-webengine-proxy-starter
```

## 2. Create A Virtual Environment

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

## 3. Install The Local Package

PyQt6:
```bash
python -m pip install -e ".[pyqt6]"
```

PyQt5:
```bash
python -m pip install -e ".[pyqt5]"
```

Do not install a public package for this paid zip. Install from the unzipped folder so your local copy, examples, and docs stay together.

## 4. First Verification Without A Proxy

```bash
python -m quadproxy doctor --no-proxy
```

Expected result:

- 6 diagnostic stages are printed.
- Configuration, Qt WebEngine import, public IP lookup, and target URL load pass.
- The command exits with status `0`.

If this fails, fix local Python/PyQt/network issues before adding proxy credentials.

## 5. Add Proxy Credentials

Windows PowerShell:
```powershell
$env:PROXY_HOST="proxy.example.net"
$env:PROXY_PORT="8080"
$env:PROXY_USER="your_username"
$env:PROXY_PASSWORD="your_password"
```

Linux / macOS:
```bash
export PROXY_HOST="proxy.example.net"
export PROXY_PORT="8080"
export PROXY_USER="your_username"
export PROXY_PASSWORD="your_password"
```

Optional:
```bash
export PROXY_SCHEME="http"
```

Only `http` is supported in QuadProxy v1.0. SOCKS proxy authentication is not enabled by this starter kit.

`WEBSHARE_PROXY_PASSWORD` is accepted as a fallback if `PROXY_PASSWORD` is not set.

## 6. Verify The Proxy

```bash
python -m quadproxy doctor
```

The public IP in the diagnostic output should be the proxy provider's outward IP, not your local network IP.

## 7. Launch The Starter App

```bash
python qt_proxy_starter.py --url https://example.com
```

For guided desktop setup:
```bash
python -m quadproxy wizard
```

For direct-mode troubleshooting:
```bash
python qt_proxy_starter.py --no-proxy --url https://example.com
```

## 8. Optional Local Self-Checks

```bash
python -m compileall qt_proxy_starter.py quadproxy examples
python -m quadproxy doctor --no-proxy
```

On Windows PowerShell:
```powershell
python -m compileall qt_proxy_starter.py quadproxy examples
python -m quadproxy doctor --no-proxy
```
