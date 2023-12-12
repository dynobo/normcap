"""Window for managing downloaded language files."""

import logging
from pathlib import Path
from typing import Optional, Union

from PySide6 import QtCore, QtWidgets

from normcap.gui import constants
from normcap.gui.downloader import Downloader
from normcap.gui.loading_indicator import LoadingIndicator
from normcap.gui.localization import _

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    """LanguagesWindow' communication bus."""

    on_open_url = QtCore.Signal(str)
    on_languages_changed = QtCore.Signal(list)


class LanguageManager(QtWidgets.QDialog):
    def __init__(
        self, tessdata_path: Path, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent=parent)

        self.setModal(True)
        # L10N: Title of Language Manager
        self.setWindowTitle(_("Manage Languages"))
        self.setMinimumSize(800, 600)

        self.tessdata_path = tessdata_path

        self.com = Communicate(parent=self)
        self.downloader = Downloader(parent=self)
        self.downloader.com.on_download_failed.connect(self._on_download_error)
        self.downloader.com.on_download_finished.connect(self._on_download_finished)

        self.installed_layout = LanguageLayout(
            label_icon="SP_DialogApplyButton",
            # L10N: Language Manager section
            label_text=_("Installed:"),
            button_icon="SP_DialogDiscardButton",
            # L10N: Language Manager button
            button_text=_("Delete"),
        )
        self.installed_layout.button.pressed.connect(self._on_delete_btn_clicked)

        self.available_layout = LanguageLayout(
            label_icon="SP_ArrowDown",
            # L10N: Language Manager section
            label_text=_("Available:"),
            button_icon="SP_ArrowDown",
            # L10N: Language Manager button
            button_text=_("Download"),
        )
        self.available_layout.button.pressed.connect(self._on_download_btn_clicked)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addLayout(self.installed_layout)
        h_layout.addLayout(self.available_layout)

        # L10N: Language Manager button
        close_button = QtWidgets.QPushButton(_("Close"))
        close_button.pressed.connect(self.close)

        self.tessdata_label = QtWidgets.QLabel(
            f"<a href='file:///{self.tessdata_path.resolve()}'>"
            # L10N: Language Manager link to directory on file system
            + _("Close and view tessdata folder in file manager...")
            + "</a>"
        )
        self.tessdata_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.tessdata_label.linkActivated.connect(self.com.on_open_url)
        self.com.on_open_url.connect(self.close)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h_layout)
        layout.addWidget(close_button)
        layout.addWidget(self.tessdata_label)

        self.setLayout(layout)

        self.loading_indicator = LoadingIndicator(parent=self, size=256)

        self._update_models()
        close_button.setFocus()

    @QtCore.Slot(str, str)
    def _on_download_error(self, reason: str, url: str) -> None:
        self._set_in_progress(False)
        QtWidgets.QMessageBox.critical(
            parent=self,
            # L10N: Language Manager error message box title
            title=_("Error"),
            # L10N: Language Manager error message box text
            text=("<b>" + _("Language download failed!") + f"</b><br><br>{reason}"),
        )

    @QtCore.Slot(bytes, str)
    def _on_download_finished(self, data: bytes, url: str) -> None:
        """Save language to tessdata folder."""
        file_name = url.split("/")[-1]
        with Path(self.tessdata_path / file_name).open(mode="wb") as fh:
            fh.write(data)
        self._update_models()
        self._set_in_progress(False)

    @QtCore.Slot()
    def _on_download_btn_clicked(self) -> None:
        if indexes := self.available_layout.view.selectedIndexes():
            self._set_in_progress(True)
            index = indexes[0]
            language = self.available_layout.model.languages[index.row()][0]
            self.downloader.get(constants.TESSDATA_BASE_URL + language + ".traineddata")

    @QtCore.Slot()
    def _on_delete_btn_clicked(self) -> None:
        indexes = self.installed_layout.view.selectedIndexes()
        if not indexes:
            return

        if len(self.installed_layout.model.languages) <= 1:
            QtWidgets.QMessageBox.information(
                parent=self,
                # L10N: Language Manager information message box title
                title=_("Information"),
                # L10N: Language Manager information message box text
                text=_(
                    "It is not possible to delete all languages. "
                    "NormCap needs at least one to function correctly."
                ),
            )
            return

        index = indexes[0]
        language = self.installed_layout.model.languages[index.row()][0]
        Path(self.tessdata_path / f"{language}.traineddata").unlink()
        self._update_models()

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
        self.com.on_languages_changed.emit(installed)

    def _get_installed_languages(self) -> list[str]:
        languages = [f.stem for f in self.tessdata_path.glob("*.traineddata")]
        return sorted(languages)

    def _set_in_progress(self, value: bool) -> None:
        self.available_layout.view.setEnabled(not value)
        self.available_layout.button.setEnabled(not value)
        self.installed_layout.view.setEnabled(not value)
        self.installed_layout.button.setEnabled(not value)
        self.tessdata_label.setEnabled(not value)
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
        self.model = LanguageModel(parent=self)

        self.addWidget(IconLabel(icon=label_icon, text=label_text))

        self.view = MinimalTableView(model=self.model)
        self.addWidget(self.view)

        pixmap = getattr(
            QtWidgets.QStyle.StandardPixmap,
            button_icon,
            QtWidgets.QStyle.StandardPixmap.SP_DialogHelpButton,
        )

        button_qicon = QtWidgets.QApplication.style().standardIcon(pixmap)
        self.button = QtWidgets.QPushButton(button_qicon, button_text)
        self.addWidget(self.button)


class LanguageModel(QtCore.QAbstractTableModel):
    def __init__(
        self, parent: Optional[QtCore.QObject] = None, languages: Optional[list] = None
    ) -> None:
        super().__init__(parent=parent)
        self.languages: list = languages or []

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
