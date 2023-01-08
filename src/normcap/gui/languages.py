"""Window for managing downloaded language files."""

import logging
from functools import partial
from pathlib import Path
from typing import Optional, Union

from PySide6 import QtCore, QtWidgets

from normcap.gui import constants, system_info, utils
from normcap.gui.downloader import Downloader

logger = logging.getLogger(__name__)


class IconLabel(QtWidgets.QWidget):
    """Label with icon in front."""

    IconSize = QtCore.QSize(16, 16)

    def __init__(self, icon: str, text: str, final_stretch: bool = True) -> None:
        super().__init__()

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        icon_label = QtWidgets.QLabel()
        pixmapi = getattr(QtWidgets.QStyle, icon)
        icon_label.setPixmap(self.style().standardIcon(pixmapi).pixmap(self.IconSize))

        layout.addWidget(icon_label)
        layout.addSpacing(2)
        layout.addWidget(QtWidgets.QLabel(text))

        if final_stretch:
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
        self,
        model: QtCore.QAbstractTableModel,
        label_text: str,
        label_icon: str,
        button_text: str,
        button_icon: str,
    ) -> None:
        super().__init__()
        label_text = IconLabel(label_icon, label_text)
        self.addWidget(label_text)

        self.model = model
        self.view = MinimalTableView(self.model)
        self.addWidget(self.view)

        self.button = QtWidgets.QPushButton(button_text)
        self.button.setIcon(utils.get_icon(button_icon))
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


class Communicate(QtCore.QObject):
    """LanguagesWindow' communication bus."""

    on_open_url = QtCore.Signal(str)
    on_change_installed_languages = QtCore.Signal(list)


class LanguagesWindow(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        if not (
            system_info.is_briefcase_package()
            or system_info.is_flatpak_package()
            or True
        ):
            raise RuntimeWarning("Language Manager is available in prebuild NormCap!")

        self.setModal(True)
        self.setWindowTitle("Manage Languages")
        self.setMinimumSize(QtCore.QSize(800, 600))

        self.com = Communicate()
        self.tessdata_path = system_info.config_directory() / "tessdata"
        self.all_languages = constants.LANGUAGES
        self.downloader = Downloader()

        self.installed_layout = LanguageLayout(
            model=LanguageModel(),
            label_icon="SP_DialogApplyButton",
            label_text="Installed:",
            button_text="Delete",
            button_icon="SP_DialogDiscardButton",
        )
        self.installed_layout.button.pressed.connect(self._delete)

        self.available_layout = LanguageLayout(
            model=LanguageModel(),
            label_icon="SP_ArrowDown",
            label_text="Available:",
            button_text="Download",
            button_icon="SP_ArrowDown",
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

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h_layout)
        layout.addWidget(self.close_button)
        layout.addWidget(self.tessdata_label)
        self.setLayout(layout)

        self._update_models()
        self.close_button.setFocus()

    def _update_models(self) -> None:
        installed = self._get_installed_languages()
        self.installed_layout.model.languages = [
            lang for lang in self.all_languages if lang[0] in installed
        ]
        self.available_layout.model.languages = [
            lang for lang in self.all_languages if lang[0] not in installed
        ]
        self.installed_layout.model.layoutChanged.emit()
        self.available_layout.model.layoutChanged.emit()
        self.installed_layout.view.clearSelection()
        self.available_layout.view.clearSelection()
        self.com.on_change_installed_languages.emit(installed)

    def _get_installed_languages(self) -> list[str]:
        languages = []
        for f in self.tessdata_path.glob("*.traineddata"):
            languages.append(f.stem)
        return languages

    def _save_language(self, data: bytes, language: str) -> None:
        with open(self.tessdata_path / f"{language}.traineddata", "wb") as fh:
            fh.write(data)

        self._update_models()
        self._set_in_progress(True)

    def _download(self) -> None:
        indexes = self.available_layout.view.selectedIndexes()
        if indexes:
            self._set_in_progress(False)
            index = indexes[0]
            language = self.available_layout.model.languages[index.row()][0]
            save_language_partial = partial(self._save_language, language=language)
            url = constants.TESSDATA_BASE_URL + language + ".traineddata"
            self.downloader.com.on_download_finished.connect(save_language_partial)
            self.downloader.get(url)
            # TODO: Handle also failed downloads!

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

        self._set_in_progress(False)
        index = indexes[0]
        language = self.installed_layout.model.languages[index.row()][0]
        Path(self.tessdata_path / f"{language}.traineddata").unlink()
        self._update_models()
        self._set_in_progress(True)

    def _set_in_progress(self, value: bool) -> None:
        self.available_layout.view.setEnabled(value)
        self.installed_layout.view.setEnabled(value)
        QtWidgets.QApplication.processEvents()
