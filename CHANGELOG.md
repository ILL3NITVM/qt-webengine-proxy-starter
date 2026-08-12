# Changelog

All notable changes to the QuadProxy Starter Kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.contentful.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-11

### Added
- Top-level `FIRST_STEPS.md` for zip customers, covering local install, no-proxy verification, proxy verification, and troubleshooting entry point.
- Core QuadProxy package (`quadproxy`) supporting PyQt6 and PyQt5 transparently.
- Preflight proxy verification window (`ProxyCheckingWindow`) with `api.ipify.org` IP validation.
- Exponential backoff retry logic (2s, 5s, 10s) for proxy connections.
- Environment variable configuration (`PROXY_HOST`, `PROXY_PORT`, `PROXY_USER`, `PROXY_PASSWORD`).
- Backward compatibility fallback for legacy `WEBSHARE_PROXY_PASSWORD`.
- Diagnostic CLI doctor command (`quadproxy-doctor` / `python -m quadproxy.cli`).
- Sensitive credential masking in logs, string representations (`ProxyConfig`), and error output.
- Zero-config first-run onboarding banner when environment variables are missing.
- Complete executable example suite in `examples/`:
  - `01_basic_browser.py`: Minimal direct browser example using `--no-proxy` or unauthenticated proxy.
  - `02_authenticated_proxy.py`: Authenticated proxy example with `ProxyConfig` and credential callback.
  - `03_existing_qapp.py`: Integrating quadproxy into an existing `QApplication` codebase.
  - `04_proxy_verification.py`: Running preflight public IP verification via `api.ipify.org`.
  - `05_error_handling.py`: Using `quadproxy.diagnostics` to catch and handle configuration and network proxy errors cleanly.
- Comprehensive documentation suite in `docs/`:
  - `QUICKSTART.md`: 5 Minute Quickstart guide for Windows PowerShell, Linux/bash, PyQt5, and PyQt6.
  - `INTEGRATION_GUIDE.md`: Step-by-step guide for embedding QuadProxy into existing PyQt applications.
  - `TROUBLESHOOTING.md`: Diagnostic guide covering common proxy errors, doctor command, and `--no-proxy` debugging.
  - `API_REFERENCE.md`: Complete Python API documentation for quadproxy modules and classes.
- Packaging configuration with standard setuptools/flit `pyproject.toml`.

### Changed
- Quickstart and README now install from the purchased zip with `python -m pip install -e ".[pyqt6]"` or `".[pyqt5]"` instead of implying a public package install.
- Unsupported proxy schemes now fail early with a clear HTTP-only message; the wizard exposes only the supported HTTP path.
- CLI help and direct-mode doctor startup now avoid unnecessary Qt/WebEngine imports, improving first-run reliability from a clean extracted zip.
