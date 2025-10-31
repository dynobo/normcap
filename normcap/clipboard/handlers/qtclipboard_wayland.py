import logging
import time
from typing import Any, cast

from normcap.system import info

_dialog_reference: list = []
try:
    from PySide6 import QtCore, QtGui, QtWidgets

    class ClipboardDialog(QtWidgets.QDialog):
        def __init__(
            self,
            text: str,
            parent: "QtWidgets.QWidget | None" = None,
        ) -> None:
            super().__init__(parent=parent)

            # L10N: Introduction window title
            self.setWindowTitle("NormCap - Clipboard Helper")
            self.setWindowIcon(QtGui.QIcon(":normcap"))
            self.setMaximumSize(200, 200)
            self.setModal(False)
            QtCore.QTimer.singleShot(150, self._focus)
            self.text = text

            self.minimum_correct_reads = 3000
            self.timeout_s = 2.0
            self.correct_reads = 0

            self.app = QtGui.QGuiApplication.instance()
            self.start_time = time.time()

            self.copy_timer = QtCore.QTimer(self, interval=50)
            self.copy_timer.timeout.connect(self._copy)
            self.copy_timer.start()

            self.read_timer = QtCore.QTimer(self, interval=50)
            self.read_timer.timeout.connect(self._read)
            self.read_timer.start()

        def _focus(self) -> None:
            self.activateWindow()
            self.raise_()

        def _copy(self) -> None:
            cb = self.app.clipboard()  # type: ignore  # Type hint wrong in PySide6?
            cb.setText(self.text)
            self.app.processEvents()

        def _read(self) -> None:
            cb = self.app.clipboard()  # type: ignore  # Type hint wrong in PySide6?
            text = cb.text()
            if text == self.text:
                self.correct_reads += 1

            # At least two clipboard reads are necessary to confirm clipboard text was
            # reliably set. (Maybe the text got chached for the first read? Or it
            # requires some time to sync with system clipboard?)
            if self.correct_reads >= self.minimum_correct_reads:
                logger.debug(
                    "Correct reads: %s; Time passed: %s",
                    self.correct_reads,
                    time.time() - self.start_time,
                )
                self._close()

            if time.time() - self.start_time >= self.timeout_s:
                logger.warning(
                    "Copying to clipboard might have failed with handler 'qt_wayland'."
                )
                self._close()

        def _close(self) -> None:
            self.copy_timer.stop()
            self.read_timer.stop()
            self.close()


except ImportError:
    QtGui = cast(Any, None)

    class ClipboardDialog:  # type: ignore
        def __init__(self, text: str, parent: object = None) -> None:
            pass

        def exec(self) -> None:
            pass


logger = logging.getLogger(__name__)

install_instructions = (
    "Please install the Python package PySide6 with your preferred package manager."
)


def copy(text: str) -> None:
    """Use QtWidgets.QApplication.clipboard to copy text to system clipboard.

    Uses a helper window, as Wayland requires the application to have a visible window
    when accessing the clipboard.
    """
    if QtGui is None:
        return

    dialog = ClipboardDialog(text=text)

    # dialog.exec() leads to a nested event loop which for unknown reason result in a
    # segfault here.
    # By using dialog.show() we use the main event loop from the application, but to
    # avoid immediate garbage collection, we need to keep a reference to it.
    _dialog_reference.append(dialog)
    dialog.show()


def is_compatible() -> bool:
    return QtGui is not None and info.has_wayland_display_manager()


def is_installed() -> bool:
    return QtGui is not None
