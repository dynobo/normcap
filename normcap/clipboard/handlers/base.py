import abc
import logging
import os
import re
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


class ClipboardHandlerBase(abc.ABC):
    def __init__(self) -> None:
        self.is_compatible = self._is_compatible()

    def copy(self, text: str) -> bool:
        """Wraps the method actually copying the text to the system clipboard.

        Should not be overridden. Overriding  _copy() should be enough.
        """
        if not self.is_compatible:
            logger.error(
                "%s.copy() called on incompatible system!",
                getattr(self, "__name__", ""),
            )
            return False

        try:
            self._copy(text)
        except Exception:
            logger.exception("%s.copy() failed!", getattr(self, "__name__", ""))
            return False
        else:
            return True

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @staticmethod
    def _os_has_wayland_display_manager() -> bool:
        if sys.platform != "linux":
            return False

        xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        has_wayland_display_env = bool(os.environ.get("WAYLAND_DISPLAY", ""))
        return "wayland" in xdg_session_type or has_wayland_display_env

    @staticmethod
    def _os_has_awesome_wm() -> bool:
        if sys.platform != "linux":
            return False

        return "awesome" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    @staticmethod
    def _get_gnome_version() -> str:
        """Detect Gnome version of current session.

        Returns:
            Version string or empty string if not detected.
        """
        if sys.platform != "linux":
            return ""

        if (
            not os.environ.get("GNOME_DESKTOP_SESSION_ID", "")
            and "gnome" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        ):
            return ""

        if not shutil.which("gnome-shell"):
            return ""

        try:
            output = subprocess.check_output(
                ["gnome-shell", "--version"],  # noqa: S607
                shell=False,  # noqa: S603
                text=True,
            )
            if result := re.search(r"\s+([\d.]+)", output.strip()):
                gnome_version = result.groups()[0]
        except Exception as e:
            logger.warning("Exception when trying to get gnome version from cli %s", e)
            return ""
        else:
            logger.debug("Detected Gnome Version: %s", gnome_version)
            return gnome_version

    @abc.abstractmethod
    def _is_compatible(self) -> bool:
        ...  # pragma: no cover

    @staticmethod
    @abc.abstractmethod
    def _copy(text: str) -> None:
        ...  # pragma: no cover
