"""Normcap base window.

Inherited for the main window, instantiated for the child windows (which get created
in multi display setups).
"""

import logging
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import system_info, tray, utils
from normcap.gui.menu_button import MenuButton
from normcap.gui.models import CaptureMode, DesktopEnvironment, Rect

logger = logging.getLogger(__name__)


class Window(QtWidgets.QMainWindow):
    """Used for child windows and as base class for MainWindow."""

    settings_menu: Optional[QtWidgets.QToolButton] = None

    def __init__(
        self, screen_idx: int, color: str, parent: QtWidgets.QSystemTrayIcon
    ) -> None:
        """Initialize window."""
        super().__init__()
        logger.debug("Create window for screen %s", screen_idx)

        self.screen_idx: int = screen_idx
        self.color: QtGui.QColor = QtGui.QColor(color)
        self.tray: tray.SystemTray = parent
        self.is_positioned: bool = False

        self.setWindowTitle("NormCap")
        self.setWindowIcon(utils.get_icon("normcap"))
        self.setAnimated(False)
        self.setEnabled(True)

        self.selection_start: QtCore.QPoint = QtCore.QPoint()
        self.selection_end: QtCore.QPoint = QtCore.QPoint()
        self.is_selecting: bool = False
        self.scale_factor = self._get_scale_factor()

        self._add_image_layer()
        self._add_ui_layer()

    def _get_scale_factor(self) -> float:
        """Calculate scale factor from image and screen dimenensions."""
        screen = self.tray.screens[self.screen_idx]
        if not screen.screenshot:
            raise ValueError("Screenshot image is missing!")
        return screen.screenshot.width() / screen.width

    def _add_image_layer(self) -> None:
        """Add widget showing screenshot."""
        self.image_layer = QtWidgets.QLabel()
        self.image_layer.setScaledContents(True)
        self.setCentralWidget(self.image_layer)

    def _add_ui_layer(self) -> None:
        """Add widget for showing selection rectangle and settings button."""
        self.ui_layer = UiLayerLabel(self)
        self.ui_layer.setGeometry(self.image_layer.geometry())
        self.ui_layer.raise_()

    def _draw_background_image(self) -> None:
        """Draw screenshot as background image."""
        screen = self.tray.screens[self.screen_idx]
        pixmap = QtGui.QPixmap()
        pixmap.convertFromImage(screen.screenshot)
        self.image_layer.setPixmap(pixmap)

    def _position_windows_on_wayland(self) -> None:
        """Move window to respective monitor on Wayland.

        In Wayland, the compositor has the responsiblity for positioning windows, the
        client itself can't do this. However, there are DE dependent workarounds.
        """
        self.setFocus()
        screen_rect = self.tray.screens[self.screen_idx].rect
        logger.debug("Move window %s to position  %s", self.screen_idx, screen_rect)
        if system_info.desktop_environment() == DesktopEnvironment.GNOME:
            utils.move_active_window_to_position_on_gnome(screen_rect)
        elif system_info.desktop_environment() == DesktopEnvironment.KDE:
            utils.move_active_window_to_position_on_kde(screen_rect)
        self.is_positioned = True

    # TODO: Shouldn't be in window, but in tray
    def create_settings_menu(self, tray: QtWidgets.QSystemTrayIcon) -> None:
        """Add settings menu to current window."""
        # TODO: Remove! Used for LanguageManager Debug
        # system_info.is_prebuild_package = lambda: True
        self.settings_menu = MenuButton(
            parent=self,
            settings=tray.settings,
            has_language_manager=system_info.is_prebuild_package(),
        )
        # TODO: Is this signal chaining relly necessary?
        self.settings_menu.com.on_open_url.connect(tray.com.on_open_url_and_hide)
        self.settings_menu.com.on_manage_languages.connect(tray.com.on_manage_languages)
        self.settings_menu.com.on_close_in_settings.connect(
            lambda: self.tray.com.on_close_or_exit.emit("clicked close in menu")
        )
        self.settings_menu.move(self.width() - self.settings_menu.width() - 26, 26)
        self.settings_menu.show()

    def set_fullscreen(self) -> None:
        """Set window to full screen using platform specific methods."""
        logger.debug("Set window for screen %s to fullscreen", self.screen_idx)

        self.setWindowFlags(
            QtGui.Qt.FramelessWindowHint
            | QtGui.Qt.CustomizeWindowHint
            | QtGui.Qt.WindowStaysOnTopHint
        )
        self.setFocusPolicy(QtGui.Qt.StrongFocus)

        # Moving window to corresponding monitor
        self.setGeometry(*self.tray.screens[self.screen_idx].rect.geometry)

        # On unity, setting min/max window size breaks fullscreen.
        if system_info.desktop_environment() != DesktopEnvironment.UNITY:
            self.setMinimumSize(self.geometry().size())
            self.setMaximumSize(self.geometry().size())

        self.showFullScreen()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa: N802
        """Handle ESC key pressed."""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.is_selecting:
                self.is_selecting = False
                self.update()
            else:
                self.tray.com.on_close_or_exit.emit("esc button pressed")
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Handle left mouse button clicked."""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.selection_start = self.selection_end = event.position().toPoint()
            self.is_selecting = True
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Update selection on mouse move."""
        self.selection_end = event.position().toPoint()
        self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Start OCR workflow on left mouse button release."""
        if (event.button() == QtCore.Qt.MouseButton.LeftButton) and self.is_selecting:
            self.selection_end = event.position().toPoint()

            rect = QtCore.QRect(self.selection_start, self.selection_end).normalized()
            self.tray.com.on_region_selected.emit(
                (Rect(*rect.getCoords()).scaled(self.scale_factor), self.screen_idx)
            )

            self.selection_start = self.selection_end = QtCore.QPoint()
            self.is_selecting = False
            self.update()
        super().mouseReleaseEvent(event)

    def changeEvent(self, event: QtCore.QEvent) -> None:  # noqa: N802
        """Update position on Wayland."""
        if (
            event.type() == QtCore.QEvent.Type.ActivationChange
            and system_info.display_manager_is_wayland()
            and self.isActiveWindow()
            and not self.is_positioned
        ):
            self._position_windows_on_wayland()
            self.tray.com.on_window_positioned.emit()
        super().changeEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: N802
        """Adjust child widget on resize."""
        self.ui_layer.resize(self.size())
        # TODO: Should be in menu_button (with signal to parent)
        if self.settings_menu:
            self.settings_menu.move(self.width() - self.settings_menu.width() - 26, 26)
        super().resizeEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:  # noqa: N802
        """Update background image on show/reshow."""
        self._draw_background_image()
        super().showEvent(event)


class UiLayerLabel(QtWidgets.QLabel):
    """Widget to draw border, selection rectangle and potentially debug infos."""

    def __init__(self, parent: Window) -> None:
        super().__init__(parent)
        self.color: QtGui.QColor = self.parent().color
        self.draw_debug_infos: bool = False

        self.setObjectName("ui_layer")
        self.setStyleSheet(f"#ui_layer {{border: 3px solid {self.color.name()};}}")
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setScaledContents(True)

    def _draw_debug_infos(self, painter: QtGui.QPainter, rect: QtCore.QRect) -> None:
        """Draw debug information on screen."""
        selection = Rect(*rect.normalized().getCoords())
        scale_factor = self.parent().scale_factor
        selection_scaled = selection.scaled(scale_factor)

        screen = self.parent().tray.screens[self.parent().screen_idx]
        x = y = 25
        painter.setPen(QtGui.QPen(self.color))
        painter.drawText(x, y * 1, f"QScreen: {screen.geometry}")
        painter.drawText(x, y * 2, f"Image: {screen.screenshot.size().toTuple()}")
        painter.drawText(x, y * 3, f"Pos QScreen: {selection.geometry}")
        painter.drawText(x, y * 4, f"Pos Image: {selection_scaled.geometry}")
        painter.drawText(x, y * 5, f"Scale factor: {scale_factor}")
        painter.drawText(x, y * 6, f"DPR: {screen.device_pixel_ratio}")

    def paintEvent(self, event: QtCore.QEvent) -> None:  # noqa: N802
        """Draw screenshot and selection rectangle on window."""
        super().paintEvent(event)

        if not (self.parent().is_selecting or self.draw_debug_infos):
            return

        painter = QtGui.QPainter(self)
        rect = QtCore.QRect(self.parent().selection_start, self.parent().selection_end)
        rect = rect.normalized()

        if self.draw_debug_infos:
            self._draw_debug_infos(painter, rect)

        if not self.parent().is_selecting:
            return

        painter.setPen(QtGui.QPen(self.color, 2, QtGui.Qt.DashLine))
        painter.drawRect(rect)

        mode = self.parent().tray.settings.value("mode")
        if CaptureMode[mode.upper()] is CaptureMode.PARSE:
            mode_indicator = utils.get_icon("normcap-parse")
        else:
            mode_indicator = utils.get_icon("normcap-raw")
        mode_indicator.paint(painter, rect.right() - 24, rect.top() - 30, 24, 24)

        painter.end()
