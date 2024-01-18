"""Dialog window with basic instructions for using NormCap.

Some users are confused about how NormCap works or where to find the settings menu.
This dialog should be shown at least once on the very first start to explain those
basic features.

By toggling a checkbox, the user can opt out of showing the screen on startup.
"""

import enum
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui.localization import _


@dataclass
class Section:
    title: str
    text: str
    image: Path


class Choice(enum.IntEnum):
    """Return codes of the Dialog.

    As 0 is default for closing the Dialog (through X or shortcut), we use different
    values to distinguish between closing the dialog w/ or w/o having the dont show
    checkbox selected.
    """

    REJECTED = 0
    ACCEPTED = 1
    SHOW = 10
    DONT_SHOW = 11


class IntroductionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        show_on_startup: bool,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)

        # L10N: Introduction window title
        self.setWindowTitle(_("Introduction to NormCap"))
        self.setWindowIcon(QtGui.QIcon(":normcap"))
        self.setMinimumSize(1024, 650)
        self.setModal(True)

        # L10N: Introduction window checkbox
        self.show_on_startup_checkbox = QtWidgets.QCheckBox(_("Show on startup"))
        self.show_on_startup_checkbox.setChecked(show_on_startup)
        # L10N: Introduction window button
        self.ok_button = QtWidgets.QPushButton(_("Ok"))
        self.ok_button.clicked.connect(self._on_button_clicked)
        self.ok_button.setDefault(True)

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.addStretch()
        main_vbox.addWidget(self._create_header())
        main_vbox.addWidget(self._create_content())
        main_vbox.addLayout(self._create_footer())
        main_vbox.addStretch()
        self.setLayout(main_vbox)

    @property
    def sections_data(self) -> list[Section]:
        prefix = sys.platform
        img_path = Path(__file__).parent.parent / "resources" / "images"
        # L10N: Introduction window shortcut for pasting on Linux and Windows
        paste_shortcut_win32_linux = _("Ctrl + v")
        # L10N: Introduction window shortcut for pasting on macOS
        paste_shortcut_darwin = _("Cmd + v")
        return [
            Section(
                # L10N: Introduction window step title
                title=_("1. Select area"),
                # L10N: Introduction window step description
                text=_(
                    "Wait until a pink border appears around your screen, then select "
                    "the desired capture area."
                ),
                image=img_path / f"{prefix}-intro-1.png",
            ),
            Section(
                # L10N: Introduction window step title
                title=_("2. Wait for detection"),
                # L10N: Introduction window step description
                text=_(
                    "Processing takes time. Wait for a notification or a color "
                    "change of the system tray icon."
                ),
                image=img_path / f"{prefix}-intro-2.png",
            ),
            Section(
                # L10N: Introduction window step title
                title=_("3. Paste from clipboard"),
                # L10N: Introduction window step description
                text=_(
                    "The detection result will be copied to your system's clipboard. "
                    "Paste it into any application ({shortcut})."
                ).format(
                    shortcut=paste_shortcut_darwin
                    if sys.platform == "darwin"
                    else paste_shortcut_win32_linux
                ),
                image=img_path / f"{prefix}-intro-3.png",
            ),
            Section(
                # L10N: Introduction window step title
                title=_("Settings & more"),
                # L10N: Introduction window step description
                text=_(
                    "Open the menu using the gear icon in the upper right corner of "
                    "corner your screen."
                ),
                image=img_path / f"{prefix}-intro-4.png",
            ),
        ]

    @staticmethod
    def _create_header() -> QtWidgets.QLabel:
        # L10N: Introduction window headline
        header = QtWidgets.QLabel(_("Basic Usage"))
        header_font = QtGui.QFont(QtGui.QFont().family(), pointSize=18, weight=300)
        header.setFont(header_font)
        return header

    def _create_content(self) -> QtWidgets.QWidget:
        sections_hbox = QtWidgets.QHBoxLayout()
        sections_hbox.setSpacing(15)
        sections_hbox.setContentsMargins(0, 15, 0, 15)

        for section in self.sections_data:
            section_layout = self._create_content_section(
                title=section.title, image=section.image, text=section.text
            )
            sections_hbox.addLayout(section_layout, 1)

        sections_container = QtWidgets.QWidget()
        sections_container.setLayout(sections_hbox)
        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(sections_container)
        scroll.setFixedHeight(sections_container.height())
        return scroll

    @staticmethod
    def _create_content_section(
        title: str, text: str, image: Path
    ) -> QtWidgets.QLayout:
        vbox = QtWidgets.QVBoxLayout()

        section_title = QtWidgets.QLabel(title)
        section_title.setFont(QtGui.QFont(QtGui.QFont().family(), weight=600))
        section_title.setWordWrap(True)
        vbox.addWidget(section_title)

        section_text = QtWidgets.QLabel(text)
        section_text.setWordWrap(True)
        vbox.addWidget(section_text)

        vbox.addStretch()

        image_label = QtWidgets.QLabel()
        image_label.setPixmap(QtGui.QPixmap(str(image.resolve())))
        image_label.setFixedWidth(230)
        image_label.setFixedHeight(400)
        image_label.setScaledContents(True)
        vbox.addWidget(image_label)

        return vbox

    def _create_footer(self) -> QtWidgets.QLayout:
        footer_hbox = QtWidgets.QHBoxLayout()
        footer_hbox.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        footer_hbox.setContentsMargins(0, 0, 2, 0)

        # L10N: Introduction window checkbox
        footer_hbox.addWidget(self.show_on_startup_checkbox)
        footer_hbox.addWidget(self.ok_button)
        return footer_hbox

    def _on_button_clicked(self) -> None:
        return_code = (
            Choice.SHOW
            if self.show_on_startup_checkbox.isChecked()
            else Choice.DONT_SHOW
        )
        self.done(return_code)
