import logging
from typing import Any, cast

try:
    from PySide6 import QtGui

except ImportError:
    QtGui = cast(Any, None)

from .base import ClipboardHandlerBase

logger = logging.getLogger(__name__)


class QtCopyHandler(ClipboardHandlerBase):
    @staticmethod
    def _copy(text: str) -> None:
        """Use QtWidgets.QApplication.clipboard to copy text to system clipboard."""
        app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication()

        cb = app.clipboard()  # type: ignore  # Type hint wrong in PySide6?
        cb.setText(text)
        app.processEvents()

    def is_compatible(self) -> bool:
        if not QtGui:
            logger.debug("%s is not compatible on systems w/o PySide6", self.name)
            return False

        if self._os_has_wayland_display_manager():
            logger.debug("%s is not compatible with Wayland", self.name)
            return False

        logger.debug("%s is compatible", self.name)
        return True

    def is_installed(self) -> bool:
        logger.debug("%s requires no dependencies", self.name)
        return True
