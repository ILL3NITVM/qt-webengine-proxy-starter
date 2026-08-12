# First Steps After Download

Run these commands from inside the unzipped `qt-webengine-proxy-starter` folder.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[pyqt6]"
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

Use `".[pyqt5]"` instead of `".[pyqt6]"` if your app uses PyQt5.

## First Verification

```bash
python -m quadproxy doctor --no-proxy
```

## Proxy Verification

Set your proxy environment variables:

```bash
export PROXY_HOST="proxy.example.net"
export PROXY_PORT="8080"
export PROXY_USER="your_username"
export PROXY_PASSWORD="your_password"
```

QuadProxy v1.0 supports authenticated HTTP proxies. Leave `PROXY_SCHEME` unset or set it to `http`.

Then run:

```bash
python -m quadproxy doctor
python qt_proxy_starter.py --url https://example.com
```

Open `docs/TROUBLESHOOTING.md` if any diagnostic stage fails.
