"""Normcap base window.

Inherited for the main window, instantiated for the child windows (which get created
in multi display setups).
"""

import logging
import sys
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import system_info
from normcap.gui.models import CaptureMode, Selection
from normcap.gui.settings_menu import SettingsMenu
from normcap.gui.utils import get_icon, move_active_window_to_position

logger = logging.getLogger(__name__)


class Window(QtWidgets.QMainWindow):
    """Used for child windows and as base class for MainWindow."""

    settings_menu: Optional[QtWidgets.QToolButton] = None
    ui_layer_css: str = ""

    def __init__(self, screen_idx: int, color: str, parent=None):
        """Initialize window."""
        super().__init__()
        self.screen_idx: int = screen_idx
        self.color: QtGui.QColor = QtGui.QColor(color)
        self.tray: QtWidgets.QMainWindow = parent or self
        self.ui_layer_css = f"#ui_layer {{border: 3px solid {self.color.name()};}}"
        self.is_positioned: bool = False

        # Window properties
        self.setObjectName(f"window-{self.screen_idx}")
        self.setWindowTitle("NormCap")
        self.setWindowIcon(get_icon("normcap.png"))
        self.setAnimated(False)
        self.setEnabled(True)

        # Prepare selection rectangle
        self.selection: Selection = Selection()
        self.is_selecting: bool = False
        self.mode_indicator: QtGui.QIcon = QtGui.QIcon()
        self.pen_width: int = 2

        # Setup widgets and show
        logger.debug("Create window for screen %s", self.screen_idx)
        self._add_image_layer()
        self._add_ui_layer()

    def _add_image_layer(self):
        """Add widget showing screenshot."""
        self.image_layer = QtWidgets.QLabel()
        self.image_layer.setObjectName("central_widget")
        self.image_layer.setScaledContents(True)
        self.setCentralWidget(self.image_layer)

    def _add_ui_layer(self):
        """Add widget for showing selection rectangle and settings button."""
        self.ui_layer = QtWidgets.QLabel(self)
        self.ui_layer.setObjectName("ui_layer")
        self.ui_layer.setStyleSheet(self.ui_layer_css)
        self.ui_layer.setCursor(QtCore.Qt.CrossCursor)
        self.ui_layer.setScaledContents(True)
        self.ui_layer.setGeometry(self.image_layer.geometry())
        self.ui_layer.paintEvent = self._ui_layer_paintEvent
        self.ui_layer.raise_()

    def draw_background_image(self):
        """Draw screenshot as background image."""
        screen = self.tray.screens[self.screen_idx]
        pixmap = QtGui.QPixmap()
        pixmap.convertFromImage(screen.screenshot)
        self.image_layer.setPixmap(pixmap)

    def add_settings_menu(self, tray):
        """Add settings menu to current window."""
        self.settings_menu = SettingsMenu(self, tray.settings)
        self.settings_menu.com.on_open_url.connect(tray.com.on_open_url_and_hide)
        self.settings_menu.com.on_close_in_settings.connect(
            lambda: self.tray.com.on_close_or_exit.emit("clicked close in menu")
        )
        self.settings_menu.move(self.width() - self.settings_menu.width() - 26, 26)
        self.settings_menu.show()

    ##################
    # Events
    ##################

    def _ui_layer_paintEvent(self, _):
        """Draw screenshot and selection rectangle on window."""
        painter = QtGui.QPainter(self.ui_layer)

        if logger.getEffectiveLevel() == logging.DEBUG:
            # Draw debug information on screen
            screen = self.tray.screens[self.screen_idx]
            x = y = 25
            painter.setPen(QtGui.QPen(self.color))
            painter.drawText(x, y * 1, f"QScreen: {screen.geometry}")
            painter.drawText(x, y * 2, f"Image: {screen.screenshot.size().toTuple()}")
            painter.drawText(x, y * 3, f"Pos QScreen: {self.selection.rect}")
            painter.drawText(x, y * 4, f"Pos Image: {self.selection.scaled_rect}")
            painter.drawText(x, y * 5, f"Scale factor: {self.selection.scale_factor}")
            painter.drawText(x, y * 6, f"DPR: {screen.device_pixel_ratio}")

        if not self.is_selecting:
            return

        # Draw selection rectangle
        rect = self.selection.rect
        painter.setPen(QtGui.QPen(self.color, self.pen_width, QtCore.Qt.DashLine))
        painter.drawRect(*rect.geometry)

        # Draw Mode indicator
        if CaptureMode[self.tray.settings.value("mode").upper()] is CaptureMode.PARSE:
            mode_indicator = get_icon("parse.svg")
        else:
            mode_indicator = get_icon("raw.svg")
        mode_indicator.paint(painter, rect.right - 24, rect.top - 30, 24, 24)

        painter.end()

    def keyPressEvent(self, event):
        """Handle ESC key pressed."""
        if event.key() == QtCore.Qt.Key_Escape:
            if self.is_selecting:
                # Abort selection process, allowing to reselect
                self.is_selecting = False
                self.update()
            else:
                self.tray.com.on_close_or_exit.emit("esc button pressed")

    def mousePressEvent(self, event):
        """Handle left mouse button clicked."""
        if event.button() == QtCore.Qt.LeftButton:
            screen = self.tray.screens[self.screen_idx]
            self.selection.scale_factor = screen.screenshot.width() / screen.width
            self.selection.start_y = self.selection.end_y = event.position().y()
            self.selection.start_x = self.selection.end_x = event.position().x()
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        """Update selection on mouse move."""
        self.selection.end_y = event.position().y()
        self.selection.end_x = event.position().x()
        self.update()

    def mouseReleaseEvent(self, event):
        """Start OCR workflow on left mouse button release."""
        if (event.button() == QtCore.Qt.LeftButton) and self.is_selecting:
            self.selection.end_y = event.position().y()
            self.selection.end_x = event.position().x()
            self.tray.com.on_set_cursor_wait.emit()
            self.tray.com.on_region_selected.emit(
                (self.selection.scaled_rect, self.screen_idx)
            )
            self.selection = Selection()
            self.is_selecting = False
            self.update()

    def changeEvent(self, event) -> None:
        """Update position on Wayland."""
        if (
            event.type() == QtCore.QEvent.Type.ActivationChange
            and system_info.display_manager_is_wayland()
            and self.isActiveWindow()
            and not self.is_positioned
        ):
            self._position_windows_on_wayland()
            self.tray.com.on_window_positioned.emit()

        return super().changeEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Adjust child widget on resize."""
        self.ui_layer.resize(self.size())
        if self.settings_menu:
            # Reposition settings menu
            self.settings_menu.move(self.width() - self.settings_menu.width() - 26, 26)

        return super().resizeEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Update background image on show/reshow."""
        self.draw_background_image()
        return super().showEvent(event)

    ##################
    # Adjust UI
    ##################

    def set_fullscreen(self):
        """Set window to full screen using platform specific methods."""
        logger.debug("Set window for screen %s to fullscreen", self.screen_idx)

        if sys.platform == "linux":
            self._set_fullscreen_linux()
        elif sys.platform == "darwin":
            self._set_fullscreen_macos()
        elif sys.platform == "win32":
            self._set_fullscreen_windows()
        else:
            raise NotImplementedError(f"Platform {sys.platform} not supported")

    def _set_fullscreen_linux(self):
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        screen_geometry = self.tray.screens[self.screen_idx].geometry
        self.move(screen_geometry.left, screen_geometry.top)
        self.setMinimumSize(QtCore.QSize(screen_geometry.width, screen_geometry.height))
        self.setMaximumSize(QtCore.QSize(screen_geometry.width, screen_geometry.height))
        self.showFullScreen()

    def _set_fullscreen_macos(self):
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.NoDropShadowWindowHint
        )
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        screen_geometry = self.tray.screens[self.screen_idx].geometry
        self.setGeometry(
            screen_geometry.left,
            screen_geometry.top,
            screen_geometry.width,
            screen_geometry.height,
        )
        self.showFullScreen()

    def _set_fullscreen_windows(self):
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        screen_geometry = self.tray.screens[self.screen_idx].geometry
        self.move(screen_geometry.left, screen_geometry.top)
        self.showFullScreen()

    def _position_windows_on_wayland(self):
        self.setFocus()
        screen_geometry = self.tray.screens[self.screen_idx].geometry
        logger.debug("Move window %s to position  %s", self.screen_idx, screen_geometry)
        move_active_window_to_position(screen_geometry)
        self.is_positioned = True
