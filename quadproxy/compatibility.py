"""PyQt6 and PyQt5 cross-compatibility module."""

from __future__ import annotations

import sys
from typing import Any

try:
    from PyQt6.QtCore import QTimer, QUrl
    from PyQt6.QtNetwork import QAuthenticator, QNetworkProxy
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QScrollArea,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    QT6 = True
except ImportError:
    from PyQt5.QtCore import QTimer, QUrl
    from PyQt5.QtNetwork import QAuthenticator, QNetworkProxy
    from PyQt5.QtWidgets import (
        QApplication,
        QComboBox,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QScrollArea,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    from PyQt5.QtWebEngineWidgets import QWebEngineView

    QT6 = False


QNETWORK_HTTP_PROXY = (
    QNetworkProxy.ProxyType.HttpProxy if QT6 else QNetworkProxy.HttpProxy
)
QNETWORK_NO_PROXY = (
    QNetworkProxy.ProxyType.NoProxy if QT6 else QNetworkProxy.NoProxy
)

QPASSWORD_ECHO_MODE = (
    QLineEdit.EchoMode.Password if QT6 else QLineEdit.Password
)


def exec_app(app: QApplication) -> int:
    """Execute Qt application event loop in a cross-compatible manner across PyQt5/PyQt6.

    Args:
        app: QApplication instance.

    Returns:
        Exit code returned by Qt event loop execution.
    """
    return app.exec() if QT6 else app.exec_()

