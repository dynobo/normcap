import logging
from typing import Any, cast

from normcap.clipboard import system_info

try:
    from PySide6 import QtGui

except ImportError:
    QtGui = cast(Any, None)


logger = logging.getLogger(__name__)

install_instructions = (
    "Please install the Python package PySide6 with your preferred package manager."
)


def _create_helper_window(text: str) -> None:
    from PySide6 import QtCore, QtGui, QtWidgets

    class MainWindow(QtWidgets.QDialog):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.cb_text = text
            self.setWindowTitle("NormCap - Wayland Clipboard Helper")
            self.setModal(True)

            self.close_button = QtWidgets.QPushButton("close")
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(self.close_button)
            self.activateWindow()
            self.setLayout(layout)
            self.close_button.setFocus()

            # self.setMaximumSize(200, 100)
            # self.editfield = QtWidgets.QTextEdit(parent=self, placeholderText="test")
            # self.setCentralWidget(self.editfield)

            # self.setFixedSize(200, 200)
            # self.setWindowFlags(
            #     QtGui.Qt.WindowType.FramelessWindowHint
            #     | QtGui.Qt.WindowType.CustomizeWindowHint
            #     | QtGui.Qt.WindowType.WindowStaysOnTopHint
            # )
            # self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
            # self.setAnimated(False)
            # self.setEnabled(True)

        def _copy(self) -> None:
            logger.debug("Copy now: %s", self.cb_text)
            # self.editfield.setFocus()
            app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication()
            cb = app.clipboard()
            cb.setText(self.cb_text)
            app.processEvents()

        def _monitor(self) -> None:
            texts = []
            while self.isVisible():
                app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication()
                cb = app.clipboard()
                text = cb.text()
                if text == self.cb_text:
                    texts.append(text)
                if len(texts) > 5:
                    logger.debug("Clipboard: %s", texts)
                    break
                app.processEvents()

        def showEvent(self, event: QtGui.QShowEvent) -> None:  # noqa: N802
            """Update background image on show/reshow."""
            super().showEvent(event)
            logger.debug("showEvent. visible: %s", self.isVisible())
            # self.editfield.setFocus()
            timer = QtCore.QTimer(self, singleShot=True)
            timer.timeout.connect(self._monitor)
            timer.start(0)

            timer = QtCore.QTimer(self, singleShot=True)
            timer.timeout.connect(self._copy)
            timer.start(900)

    logger.debug("Open clipboard helper window...")

    win = MainWindow(text=text)
    win.show()
    loop = QtCore.QEventLoop()
    win.destroyed.connect(loop.quit)
    loop.exec()


def copy(text: str) -> None:
    """Use QtWidgets.QApplication.clipboard to copy text to system clipboard."""
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication()

    if system_info.has_wayland_display_manager():
        _create_helper_window(text=text)
    else:
        cb = app.clipboard()
        cb.setText(text)
        app.processEvents()


def is_compatible() -> bool:
    if not QtGui:
        return False

    return not system_info.has_wayland_display_manager()


def is_installed() -> bool:
    return True
