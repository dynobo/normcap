"""NormCap Package."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("normcap")
except PackageNotFoundError:
    __version__ = "unknown"
