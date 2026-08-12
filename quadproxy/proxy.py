"""Application proxy configuration and main window widget."""

from __future__ import annotations

import sys
from typing import Any, Optional

from quadproxy.authentication import ProxyAuthenticator
from quadproxy.compatibility import (
    QNETWORK_HTTP_PROXY,
    QNETWORK_NO_PROXY,
    QLabel,
    QMainWindow,
    QNetworkProxy,
    QTimer,
    QUrl,
    QVBoxLayout,
    QWidget,
    QWebEngineView,
)
from quadproxy.config import ProxyConfig
from quadproxy.verification import (
    PROXY_CHECK_URL,
    RETRY_DELAYS_MS,
    TIMEOUT_MS,
    validate_ip_address,
)


def configure_application_proxy(config: Optional[ProxyConfig]) -> None:
    """Configure global authenticated HTTP proxy in Qt before QApplication.

    Args:
        config: ProxyConfig instance or None for direct (no-proxy) mode.
    """
    if config is None:
        QNetworkProxy.setApplicationProxy(QNetworkProxy(QNETWORK_NO_PROXY))
        return
    proxy = QNetworkProxy(QNETWORK_HTTP_PROXY, config.host, config.port)
    proxy.setUser(config.user)
    proxy.setPassword(config.password)
    QNetworkProxy.setApplicationProxy(proxy)


class ProxyCheckingWindow(QMainWindow):
    """Main window displaying preflight IP verification before loading target URL."""

    def __init__(self, target_url: str, proxy_config: Optional[ProxyConfig]) -> None:
        super().__init__()
        self.target_url = target_url
        self.proxy_config = proxy_config
        self.attempt = 0
        self.load_generation = 0
        self.finished = False

        self.setWindowTitle("Qt WebEngine Proxy Starter")
        self.resize(1100, 720)

        self.status = QLabel("Starting", self)
        self.browser = QWebEngineView(self)

        self.authenticator = ProxyAuthenticator(self.proxy_config)
        if self.proxy_config is not None:
            self.authenticator.attach_to_page(self.browser.page())

        layout = QVBoxLayout()
        layout.addWidget(self.status)
        layout.addWidget(self.browser, 1)
        container = QWidget(self)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.browser.loadFinished.connect(self._load_finished)

    def start(self) -> None:
        if self.proxy_config is None:
            self.status.setText("Proxy disabled; loading target URL")
            self.browser.setUrl(QUrl(self.target_url))
            return
        self._schedule_attempt(0)

    def _schedule_attempt(self, delay_ms: int) -> None:
        QTimer.singleShot(delay_ms, self._start_attempt)

    def _start_attempt(self) -> None:
        if self.finished or self.attempt >= 3:
            return
        self.attempt += 1
        self.load_generation += 1
        generation = self.load_generation
        delay_label = RETRY_DELAYS_MS[self.attempt - 1] // 1000
        self.status.setText(
            f"Proxy check attempt {self.attempt}/3 after {delay_label}s retry window"
        )
        self.browser.setUrl(QUrl(PROXY_CHECK_URL))
        QTimer.singleShot(TIMEOUT_MS, lambda: self._timeout(generation))

    def _timeout(self, generation: int) -> None:
        if self.finished or generation != self.load_generation:
            return
        self._record_failure(f"timeout loading {PROXY_CHECK_URL}")

    def _load_finished(self, ok: bool) -> None:
        if self.finished or self.proxy_config is None:
            return
        if not ok:
            self._record_failure("page load failed during proxy verification")
            return
        self.browser.page().runJavaScript(
            "(document.body && document.body.innerText || '').trim()",
            self._validate_ip,
        )

    def _validate_ip(self, raw: Any) -> None:
        if self.finished:
            return
        public_ip = str(raw or "").strip()
        try:
            validate_ip_address(public_ip)
        except ValueError:
            self._record_failure("invalid response from api.ipify.org")
            return
        self.finished = True
        self.status.setText(
            f"Proxy verified; public IP {public_ip}; loading target URL"
        )
        print(f"Proxy verified public IP: {public_ip}", flush=True)
        self.browser.setUrl(QUrl(self.target_url))

    def _record_failure(self, detail: str) -> None:
        if self.attempt >= 3:
            self.finished = True
            self.status.setText(f"Proxy verification failed: {detail}")
            print(
                f"Proxy verification failed after 3 attempts: {detail}", file=sys.stderr
            )
            return
        delay_ms = RETRY_DELAYS_MS[self.attempt - 1]
        self.status.setText(
            f"Proxy check failed: {detail}; retrying in {delay_ms // 1000}s"
        )
        self._schedule_attempt(delay_ms)
