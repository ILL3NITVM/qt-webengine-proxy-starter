"""Proxy authentication handler for Qt WebEngine pages."""

from __future__ import annotations

from typing import Any, Optional

from quadproxy.compatibility import QUrl
from quadproxy.config import ProxyConfig


class ProxyAuthenticator:
    """Manages proxy authentication requests for Qt WebEngine network requests."""

    def __init__(self, config: Optional[ProxyConfig]) -> None:
        """Initialize proxy authenticator with optional ProxyConfig.

        Args:
            config: ProxyConfig instance or None.
        """
        self.config = config

    def handle_authentication(
        self, request_url: QUrl, authenticator: Any, *args: Any
    ) -> None:
        """Slot for QWebEnginePage.proxyAuthenticationRequired signal.

        Supplies credentials quietly to the authenticator without printing
        passwords or emitting logs containing secret credentials.

        Args:
            request_url: QUrl requesting proxy authentication.
            authenticator: QAuthenticator instance supplied by Qt.
            *args: Additional positional arguments from signal emission.
        """
        if self.config is None:
            return
        authenticator.setUser(self.config.user)
        authenticator.setPassword(self.config.password)

    def attach_to_page(self, page: Any) -> None:
        """Connect this authenticator to a QWebEnginePage's proxyAuthenticationRequired signal.

        Args:
            page: QWebEnginePage instance.
        """
        if hasattr(page, "proxyAuthenticationRequired"):
            page.proxyAuthenticationRequired.connect(self.handle_authentication)
