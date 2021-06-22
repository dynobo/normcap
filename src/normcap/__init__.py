"""Normcap Package."""

from importlib_metadata import version

try:
    __version__ = version(__package__)
except:  # pylint: disable=bare-except
    __version__ = "unknown"
