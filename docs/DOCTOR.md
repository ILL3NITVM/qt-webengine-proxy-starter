# QuadProxy Doctor - Diagnostic & Support Tool

`python -m quadproxy doctor` is the built-in diagnostic and health-checking engine for QuadProxy. It performs a 12-stage inspection sequence to verify network routing, credentials, Qt bindings, and public IP changes.

---

## Command Usage

```bash
# Run full 12-stage diagnostics using environment variables
python -m quadproxy doctor

# Run diagnostics against a custom target URL
python -m quadproxy doctor --url https://httpbin.org/ip

# Run in direct mode (bypassing proxy) to test base network connectivity
python -m quadproxy doctor --no-proxy
```

---

## 12-Stage Inspection Sequence

| Stage | Inspection Name | Description |
|---|---|---|
| **1** | **Python Version** | Validates Python 3.8+ compatibility. |
| **2** | **Qt WebEngine Binding** | Detects installed PyQt5 / PyQt6 WebEngine modules. |
| **3** | **Configuration Completeness** | Verifies presence of PROXY_HOST, PORT, USER, PASSWORD. |
| **4** | **Proxy Port Validity** | Verifies integer port within valid range (1–65535). |
| **5** | **DNS Host Resolution** | Resolves proxy host IP via local DNS. |
| **6** | **TCP Network Reachability** | Tests raw TCP socket connectivity to host:port. |
| **7** | **Authentication Path** | Sends authenticated HTTP request, testing for 407 errors. |
| **8** | **Direct Public IP Check** | Queries direct public IP address without proxy. |
| **9** | **Proxy Public IP Verification** | Queries public IP address through the configured proxy. |
| **10** | **Direct/Proxy IP Comparison** | Compares direct vs proxy IP to confirm public IP CHANGED. |
| **11** | **Target URL Reachability** | Loads target webpage via proxy and checks HTTP 200 status. |
| **12** | **Qt Initialization Order** | Audits Qt application proxy setup contract timing. |

---

## Concise Final Diagnosis

At the end of every run, Doctor outputs a clear, single-line final summary:

```
================================================================================
FINAL DIAGNOSIS: PASS: QuadProxy diagnostic suite passed. Proxy is verified and ready for integration.
================================================================================
```

Or on failure:

```
================================================================================
FINAL DIAGNOSIS: FAIL Stage 7 [AUTHENTICATION_REJECTED]: AUTHENTICATION REJECTED (HTTP 407) - Verify username/password and provider authentication mode.
================================================================================
```

---

## Diagnostic Support Bundle

When seeking customer support, generate a safe diagnostic bundle ZIP containing redacted logs and test results:

```bash
python -m quadproxy support-bundle
```

Generated file: `quadproxy-support-bundle-YYYYMMDD_HHMMSS.zip`

Guarantees:
- **Scrubbed Credentials**: Passwords, secrets, and auth tokens are replaced with `***`.
- **Zero Privacy Leaks**: Excludes cookies, browser history, internal databases, or Stripe data.
