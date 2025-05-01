"""Permission Dialog window for NormCap.

This dialog is used to inform the user about required permissions.
"""

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import constants
from normcap.gui.localization import _


# FIXME: Checks for permission, but it should be stored in settings!
class PermissionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        text: str,
        parent: Optional[QtWidgets.QWidget] = None,
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
