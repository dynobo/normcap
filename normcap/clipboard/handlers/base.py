import abc
import logging
import os
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

    @abc.abstractmethod
    def _is_compatible(self) -> bool:
        ...  # pragma: no cover

    @staticmethod
    @abc.abstractmethod
    def _copy(text: str) -> None:
        ...  # pragma: no cover
