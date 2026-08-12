# QuadProxy Actionable Failure Playbook & Troubleshooting

QuadProxy provides concrete, actionable remediation steps for every failure mode. Vague "something went wrong" errors are strictly avoided.

---

## Actionable Failure Playbook

### 1. PROXY HOST UNREACHABLE
- **Cause**: TCP connection to `PROXY_HOST:PROXY_PORT` timed out or was refused.
- **Remediation**:
  1. Verify proxy hostname spelling and port number in your provider dashboard.
  2. Check local firewall, VPN, or outbound router rules blocking outbound connections to proxy port.
  3. Test connectivity directly: `nc -zv proxy.example.net 8080`.

### 2. AUTHENTICATION REJECTED (HTTP 407)
- **Cause**: Proxy server rejected the provided username or password.
- **Remediation**:
  1. Double check `PROXY_USER` and `PROXY_PASSWORD` environment variables.
  2. Check if your proxy provider uses **IP Whitelisting** instead of Username/Password auth. If so, whitelist your server's IP address on the provider portal.
  3. Ensure special characters in passwords do not get mangled by shell environment variable parsing.

### 3. PUBLIC IP UNCHANGED
- **Cause**: Diagnostic tests succeeded, but direct public IP matches proxy public IP.
- **Remediation**:
  1. Ensure `configure_application_proxy(config)` is executed **BEFORE** creating the `QApplication` instance.
  2. Verify that custom `QNetworkAccessManager` or third-party web views do not override network proxy settings.

### 4. QT INITIALIZATION ORDER FAILURE
- **Cause**: `QNetworkProxy.setApplicationProxy` was invoked after `QApplication` initialization.
- **Remediation**:
  1. Move proxy configuration logic to the very beginning of script execution.
  2. Refer to `examples/03_pyqt5_integration.py` for exact initialization sequence.

### 5. TARGET PAGE LOAD FAILED
- **Cause**: Proxy connected and public IP changed, but target destination failed to load (e.g. HTTP 403 / 502 / timeout).
- **Remediation**:
  1. Destination website may block datacenter proxy IP ranges. Test with residential proxy pool.
  2. Verify target URL formatting and HTTPS SSL certificate status.
  3. Run doctor against another site: `python -m quadproxy doctor --url https://httpbin.org/get`.

### 6. PROXY DNS RESOLUTION FAILED
- **Cause**: Local DNS server could not resolve the proxy hostname.
- **Remediation**:
  1. Check local Internet DNS settings (`nslookup proxy.example.net`).
  2. Try substituting the numeric IPv4 address of the proxy host.

### 7. INVALID PROXY PORT
- **Cause**: `PROXY_PORT` environment variable is missing, non-numeric, or outside valid range (1–65535).
- **Remediation**:
  1. Ensure `PROXY_PORT` is a valid integer (e.g. `export PROXY_PORT=8080`).

---

## Support Contact & Escalation Path

If troubleshooting does not resolve your issue:

1. Generate a redacted support bundle:
   ```bash
   python -m quadproxy support-bundle
   ```
2. Email your support bundle ZIP file to: **support@quadproxy.com**
3. Include a description of your operating environment (OS, Python version, proxy provider name).

### Support Scope & Boundaries
- **In Scope**: Proxy configuration bugs, PyQt integration errors, credential redaction issues, diagnostic failures.
- **Out of Scope**: Third-party proxy provider outages, banned target website IPs, custom web scraping logic.
- **Refund Policy**: If QuadProxy fails to route traffic on a supported Python/PyQt environment due to a verified product defect, a full refund will be issued within 14 days of purchase.
