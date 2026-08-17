from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="quadproxy-starter",
    version="1.0.0",
    description="PyQt5 & PyQt6 QWebEngineView Authenticated Proxy Starter Kit & CLI Diagnostics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="QuadProxy Team",
    author_email="support@quadproxy.com",
    url="https://quadproxy.com",
    project_urls={
        "Homepage": "https://quadproxy.com",
        "Documentation": "https://github.com/ILL3NITVM/qt-webengine-proxy-starter#readme",
        "Source": "https://github.com/ILL3NITVM/qt-webengine-proxy-starter",
        "Tracker": "https://github.com/ILL3NITVM/qt-webengine-proxy-starter/issues",
    },
    packages=find_packages(exclude=["tests*", "examples*"]),
    py_modules=["qt_proxy_starter"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "quadproxy=quadproxy.cli:main",
        ],
    },
)
