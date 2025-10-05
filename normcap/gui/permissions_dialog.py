"""Permission Dialog window for NormCap.

This dialog is used to inform the user about required permissions.
"""

import logging
from collections.abc import Callable

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import constants
from normcap.gui.constants import OPEN_ISSUE_TEXT
from normcap.gui.localization import _

logger = logging.getLogger(__name__)


class MissingPermissionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        text: str,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        # L10N: Permission dialog window title
        self.setWindowTitle(_("NormCap - Missing Permissions!"))
        self.setWindowIcon(QtGui.QIcon(":normcap"))
        self.setMinimumSize(600, 300)
        self.setModal(True)

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.addWidget(self._create_message(text))
        main_vbox.addStretch()
        main_vbox.addLayout(self._create_footer())
        self.setLayout(main_vbox)

    @staticmethod
    def _create_message(text: str) -> QtWidgets.QLabel:
        message = QtWidgets.QLabel(text)
        message.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
            | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard
            | QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        message.setWordWrap(True)
        return message

    def _create_footer(self) -> QtWidgets.QLayout:
        footer_hbox = QtWidgets.QHBoxLayout()
        footer_hbox.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        footer_hbox.setContentsMargins(0, 0, 2, 0)

        open_issue_text = QtWidgets.QLabel(constants.OPEN_ISSUE_TEXT)

        # L10N: Permission dialog button
        ok_button = QtWidgets.QPushButton(_("Exit"))
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)

        footer_hbox.addWidget(open_issue_text)
        footer_hbox.addStretch()
        footer_hbox.addWidget(ok_button)
        return footer_hbox


class RequestDbusPermissionDialog(QtWidgets.QDialog):
    def __init__(self, capture_func: Callable) -> None:
        super().__init__()
        # L10N: Title of screenshot permission dialog only shown on Linux + Wayland.
        title = _("NormCap - Screenshot Permission")
        # L10N: Text of screenshot permission dialog only shown on Linux + Wayland.
        text = _(
            "<h3>Request screenshot permission?</h3>"
            "<p>NormCap needs permission to take screenshots, which is essential"
            "<br> for its functionality. It appears these permissions are "
            "currently missing.</p>"
            "<p>Click 'OK' to trigger a system prompt requesting access.<br>"
            "Please allow this, otherwise NormCap may not work properly.</p>"
        )
        self.capture_func = capture_func

        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon(":normcap"))
        self.setMinimumSize(600, 300)
        self.setModal(True)

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.addWidget(self._create_message(text))
        main_vbox.addStretch()
        main_vbox.addLayout(self._create_footer())
        self.setLayout(main_vbox)

    @staticmethod
    def _create_message(text: str) -> QtWidgets.QLabel:
        message = QtWidgets.QLabel(text)
        message.setWordWrap(True)
        return message

    def _create_footer(self) -> QtWidgets.QLayout:
        footer_hbox = QtWidgets.QHBoxLayout()
        footer_hbox.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        footer_hbox.setContentsMargins(0, 0, 2, 0)

        open_issue_text = QtWidgets.QLabel(OPEN_ISSUE_TEXT)

        # L10N: Permission request dialog button
        ok_button = QtWidgets.QPushButton(_("Ok"))
        ok_button.clicked.connect(self.accept_button_pressed)
        ok_button.setDefault(True)

        # L10N: Permission request dialog button
        cancle_button = QtWidgets.QPushButton(_("Cancel"))
        cancle_button.clicked.connect(self.reject_button_pressed)

        footer_hbox.addWidget(open_issue_text)
        footer_hbox.addStretch()
        footer_hbox.addWidget(ok_button)
        footer_hbox.addWidget(cancle_button)
        return footer_hbox

    def accept_button_pressed(self) -> None:
        self.setEnabled(False)

        screenshots = []
        try:
            logger.debug("Request screenshot.")
            screenshots = self.capture_func()
        except TimeoutError:
            logger.warning("Timeout when taking screenshot!")
        except PermissionError:
            logger.warning("Missing permission for taking screenshot!")

        self.setEnabled(True)
        self.setResult(len(screenshots) > 0)
        self.hide()

    def reject_button_pressed(self) -> None:
        logger.warning("Screenshot permission dialog was canceled!")
        self.setResult(False)
        self.hide()
