# QuadProxy Security Policy & Credential Protection

Security and secret protection are core engineering requirements in QuadProxy. QuadProxy guarantees that proxy passwords, authentication tokens, API keys, and sensitive customer data never leak into logs, exception tracebacks, CLI output, or support bundles.

---

## Redaction Guarantee & Architecture

### 1. ProxyConfig Immutability & Masking
`ProxyConfig` is an immutable dataclass (`@dataclass(frozen=True)`).
- `repr(config)` masks passwords automatically:
  `ProxyConfig(host='proxy.net', port=8080, user='usr', password='***')`
- `str(config)` outputs masked user@host format.

### 2. Exception & Traceback Scrubbing
All internal exception handlers wrap error messages through `quadproxy.security.redact_str(text, password)`.
Even if a lower-level library (urllib, socket, SSL) includes full URLs or proxy headers in exception strings, QuadProxy scrubs raw password strings before printing or logging.

### 3. Support Bundle Privacy Guarantee
The support bundle generator (`python -m quadproxy support-bundle`) executes mandatory adversarial secret audits before packaging ZIP contents:
- Passwords, secrets, and auth tokens are replaced with `***`.
- Stripe API keys, customer session cookies, browser history, and unrelated environment variables are strictly excluded.
- If a raw secret is detected during zip construction, bundle generation immediately aborts with `ValueError("SECRET LEAK AUDIT FAILED")`.

### 4. Clipboard & Export Sanitization
Desktop GUI Wizard snippet generators mask password fields (`"***"`) or instruct users to load from environment variables (`os.environ["PROXY_PASSWORD"]`).

---

## Adversarial Secret Auditing

Run automated secret redaction tests anytime:
```bash
python -m unittest tests/test_secret_leak_regression.py
```
This suite verifies credential scrubbing across:
- Environment variable inspection
- Exception tracebacks and error strings
- Support bundle ZIP output
- Log messages
- Config exports and CLI output
