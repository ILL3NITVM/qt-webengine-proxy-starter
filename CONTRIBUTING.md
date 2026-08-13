# Contributing to Qt WebEngine Proxy Starter

Thank you for your interest in contributing to QuadProxy!

## Guidelines
1. **Security & Zero Secret Leakage:** Never commit passwords, proxy credentials, or Stripe keys. All diagnostic tests must use environment variable placeholders (`os.environ.get("PROXY_PASSWORD", "")`).
2. **PyQt5 & PyQt6 Backward Compatibility:** All features and examples must support both PyQt5 and PyQt6.
3. **Headless Testing:** Unit tests must execute in offscreen mode (`os.environ["QT_QPA_PLATFORM"] = "offscreen"`).

## Running Tests Locally
```bash
python -m unittest discover -s tests
```

---

*Product Storefront:* [https://quadproxy.com](https://quadproxy.com)  
*Seller Disclosure:* Built by QuadProxy engineering team for Python desktop app developers.
