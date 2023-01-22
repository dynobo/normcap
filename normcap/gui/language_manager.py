"""Window for managing downloaded language files."""

import logging
from pathlib import Path
from typing import Optional, Union

from PySide6 import QtCore, QtWidgets

from normcap.gui import constants
from normcap.gui.downloader import Downloader
from normcap.gui.loading_indicator import LoadingIndicator

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """LanguagesWindow' communication bus."""

    on_open_url = QtCore.Signal(str)
    on_change_installed_languages = QtCore.Signal(list)


class LanguageManager(QtWidgets.QDialog):
    def __init__(
        self, tessdata_path: Path, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)
        # TODO: Avoid unnecessary properties

        self.setModal(True)
        self.setWindowTitle("Manage Languages (experimental)")
        self.setMinimumSize(800, 600)

        self.tessdata_path = tessdata_path

        self.com = Communicate()
        self.downloader = Downloader()
        self.downloader.com.on_download_failed.connect(self._on_download_error)
        self.downloader.com.on_download_finished.connect(self._on_download_finished)

        self.installed_layout = LanguageLayout(
            label_icon="SP_DialogApplyButton",
            label_text="Installed:",
            button_icon="SP_DialogDiscardButton",
            button_text="Delete",
        )
        self.installed_layout.button.pressed.connect(self._delete)

        self.available_layout = LanguageLayout(
            label_icon="SP_ArrowDown",
            label_text="Available:",
            button_icon="SP_ArrowDown",
            button_text="Download",
        )
        self.available_layout.button.pressed.connect(self._download)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addLayout(self.installed_layout)
        h_layout.addLayout(self.available_layout)

        self.close_button = QtWidgets.QPushButton("&Close")
        self.close_button.pressed.connect(self.close)

        self.tessdata_label = QtWidgets.QLabel(
            f"<a href='file:///{self.tessdata_path.resolve()}'>"
            "View tessdata folder in file manager...</a>"
        )
        self.tessdata_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.tessdata_label.linkActivated.connect(self.com.on_open_url)
        self.com.on_open_url.connect(self.close)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h_layout)
        layout.addWidget(self.close_button)
        layout.addWidget(self.tessdata_label)

        self.setLayout(layout)

        self.loading_indicator = LoadingIndicator(self, size=256)

        self._update_models()
        self.close_button.setFocus()

    @QtCore.Slot(str, str)
    def _on_download_error(self, reason: str, url: str) -> None:
        self._set_in_progress(False)
        QtWidgets.QMessageBox.critical(
            self, "Error", f"<b>Language download failed!</b><br><br>{reason}"
        )

    @QtCore.Slot(bytes, str)
    def _on_download_finished(self, data: bytes, url: str) -> None:
        """Save language to tessdata folder."""
        file_name = url.split("/")[-1]
        with open(self.tessdata_path / file_name, "wb") as fh:
            fh.write(data)
        self._update_models()
        self._set_in_progress(False)

    def _update_models(self) -> None:
        installed = self._get_installed_languages()
        self.installed_layout.model.languages = [
            lang for lang in constants.LANGUAGES if lang[0] in installed
        ]
        self.available_layout.model.languages = [
            lang for lang in constants.LANGUAGES if lang[0] not in installed
        ]
        self.installed_layout.model.layoutChanged.emit()
        self.installed_layout.view.clearSelection()
        self.available_layout.model.layoutChanged.emit()
        self.available_layout.view.clearSelection()
        self.com.on_change_installed_languages.emit(installed)

    def _get_installed_languages(self) -> list[str]:
        languages = [f.stem for f in self.tessdata_path.glob("*.traineddata")]
        return sorted(languages)

    def _download(self) -> None:
        indexes = self.available_layout.view.selectedIndexes()
        if indexes:
            self._set_in_progress(True)
            index = indexes[0]
            language = self.available_layout.model.languages[index.row()][0]
            self.downloader.get(constants.TESSDATA_BASE_URL + language + ".traineddata")

    def _delete(self) -> None:
        indexes = self.installed_layout.view.selectedIndexes()
        if not indexes:
            return

        if len(self.installed_layout.model.languages) <= 1:
            QtWidgets.QMessageBox.information(
                self,
                "Information",
                "It is not possible to delete all languages. "
                + "NormCap needs at least one to function correctly.",
            )
            return

        index = indexes[0]
        language = self.installed_layout.model.languages[index.row()][0]
        Path(self.tessdata_path / f"{language}.traineddata").unlink()
        self._update_models()

    def _set_in_progress(self, value: bool) -> None:
        self.available_layout.view.setEnabled(not value)
        self.installed_layout.view.setEnabled(not value)
        self.loading_indicator.setVisible(value)


class IconLabel(QtWidgets.QWidget):
    """Label with icon in front."""

    def __init__(self, icon: str, text: str) -> None:
        super().__init__()

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        icon_label = QtWidgets.QLabel()
        pixmapi = getattr(QtWidgets.QStyle, icon)
        icon_label.setPixmap(self.style().standardIcon(pixmapi).pixmap(16, 16))

        layout.addWidget(icon_label)
        layout.addSpacing(2)
        layout.addWidget(QtWidgets.QLabel(text))
        layout.addStretch()


class MinimalTableView(QtWidgets.QTableView):
    """TableView without grid, headers.

    - Only allows selection of rows.
    - Focus is disabled to avoid cells being focused. (Didn't found a better workaround)
    """

    def __init__(self, model: QtCore.QAbstractTableModel) -> None:
        super().__init__()
        self.setShowGrid(False)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.setModel(model)


class LanguageLayout(QtWidgets.QVBoxLayout):
    """Layout includes: Label, TableView with Model, Button."""

    def __init__(
        self, label_text: str, label_icon: str, button_text: str, button_icon: str
    ) -> None:
        super().__init__()
        label_text = IconLabel(label_icon, label_text)
        self.addWidget(label_text)

        self.model = LanguageModel()
        self.view = MinimalTableView(self.model)
        self.addWidget(self.view)

        self.button = QtWidgets.QPushButton(button_text)

        pixmapi = getattr(QtWidgets.QStyle.StandardPixmap, button_icon, None)
        self.button.setIcon(QtWidgets.QApplication.style().standardIcon(pixmapi))
        self.addWidget(self.button)


class LanguageModel(QtCore.QAbstractTableModel):
    def __init__(self, languages: Optional[list] = None) -> None:
        super().__init__()
        self.languages: list = languages if languages else []

    def data(
        self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole
    ) -> Union[str, QtCore.QSize, None]:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.languages[index.row()][index.column()]
        return None

    def rowCount(self, index: QtCore.QModelIndex) -> int:  # noqa: N802
        return len(self.languages)

    def columnCount(self, index: QtCore.QModelIndex) -> int:  # noqa: N802
        return len(self.languages[0]) if self.languages else 0
