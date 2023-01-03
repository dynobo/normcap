"""Window for managing downloaded language files."""

import logging
from typing import Optional, Union

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import constants, system_info, utils

logger = logging.getLogger(__name__)


class LanguagesWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlags(QtCore.Qt.WindowType.Popup)
        list_font = QtGui.QFont("monospace")
        layout = QtWidgets.QVBoxLayout()

        self.h_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(self.h_layout)

        self.all_languages = constants.LANGUAGES

        self.installed_layout = QtWidgets.QVBoxLayout()
        self.h_layout.addLayout(self.installed_layout)

        self.installed_label = QtWidgets.QLabel("Installed languages:")
        self.installed_layout.addWidget(self.installed_label)

        self.installed_view = QtWidgets.QListView()
        self.installed_view.setFont(list_font)
        self.installed_layout.addWidget(self.installed_view)
        self.installed_model = LanguageModel(self.all_languages)
        self.installed_view.setModel(self.installed_model)

        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.setIcon(utils.get_icon("", "delete"))
        self.installed_layout.addWidget(self.delete_button)

        self.available_layout = QtWidgets.QVBoxLayout()
        self.h_layout.addLayout(self.available_layout)

        self.available_label = QtWidgets.QLabel("Available languages:")
        self.available_layout.addWidget(self.available_label)

        self.available_view = QtWidgets.QListView()
        self.available_view.setFont(list_font)
        self.available_layout.addWidget(self.available_view)
        self.available_model = LanguageModel(self.all_languages)
        self.available_view.setModel(self.available_model)

        self.download_button = QtWidgets.QPushButton("Download")
        self.download_button.setIcon(utils.get_icon("", "download"))
        self.available_layout.addWidget(self.download_button)

        self.close_button = QtWidgets.QPushButton("Close")
        layout.addWidget(self.close_button)

        self.setLayout(layout)

        self.download_button.pressed.connect(self.download)
        self.delete_button.pressed.connect(self.delete)

    def download(self) -> None:
        ...

    def delete(self) -> None:
        indexes = self.available_view.selectedIndexes()
        if indexes:
            index = indexes[0]
            del self.model.languages[index.row()]
            self.model.layoutChanged.emit()
            self.available_view.clearSelection()


class LanguageModel(QtCore.QAbstractListModel):
    def __init__(self, languages: Optional[list]) -> None:
        super().__init__()
        self.languages: list = languages if languages else []
        self.download_icon = QtGui.QImage(
            system_info.get_resources_path() / "parse.svg"
        )
        self.download_icon = self.download_icon.scaledToHeight(
            int(QtGui.QFont("monospace").pointSize() * 4)
        )

    def data(
        self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole
    ) -> Union[str, QtCore.QSize, None]:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            lang = self.languages[index.row()]
            return f"{lang['abbrev']: <13} {lang['name']: <31} {lang['native']}"
        return None

    def rowCount(self, index: QtCore.QModelIndex) -> int:  # noqa: N802
        return len(self.languages)
