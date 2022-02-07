"""Normcap base window.

Inherited for the main window, instantiated for the child windows (which get created
in multi display setups).
"""

import logging
import sys
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import system_info
from normcap.gui.models import CaptureMode, Rect
from normcap.gui.utils import get_icon, move_active_window_to_position_on_gnome

logger = logging.getLogger(__name__)


class BaseWindow(QtWidgets.QMainWindow):
    """Used for child windows and as base class for MainWindow."""

    # Helper window to extend the red border
    macos_border: Optional[QtWidgets.QMainWindow] = None

    def __init__(self, screen_idx: int, color: str, parent=None):
        """Initialize window."""
        super().__init__()
        self.screen_idx: int = screen_idx
        self.primary_color: QtGui.QColor = QtGui.QColor(color)
        self.main_window: QtWidgets.QMainWindow = parent or self

        # Window properties
        self.setObjectName(f"window-{self.screen_idx}")
        self.setWindowTitle("NormCap")
        self.setWindowIcon(get_icon("normcap.png"))
        self.setAnimated(False)
        self.setEnabled(True)

        # Prepare selection rectangle
        self.selection: Rect = Rect()
        self.is_positioned: bool = False
        self.pen_width: int = 2
        self.is_selecting: bool = False
        self.mode_indicator: str = "?"
        self.mode_indicator_font = QtGui.QFont()
        self.mode_indicator_font.setPixelSize(24)

        # Setup widgets and show
        logger.debug("Create window for screen %s", self.screen_idx)
        self._add_central_widget()
        self.set_fullscreen()

    def _add_central_widget(self):
        self.frame = QtWidgets.QFrame()
        self.frame.setObjectName("central_widget")
        self.frame.setEnabled(True)
        self.frame.setAutoFillBackground(True)
        self.frame.setStyleSheet(
            f"QFrame {{border: 3px solid {self.primary_color.name()};}}"
        )
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame.setLineWidth(0)
        self.frame.setCursor(QtCore.Qt.CrossCursor)
        self.setCentralWidget(self.frame)

    ##################
    # Utility
    ##################
    def _get_mode_indicator_char(self):
        if self.main_window.capture.mode is CaptureMode.RAW:
            return "☰"
        if self.main_window.capture.mode is CaptureMode.PARSE:
            return "★"
        return ""

    ##################
    # Events
    ##################

    def paintEvent(self, _):
        """Draw screenshot and selection rectangle on window."""
        painter = QtGui.QPainter(self)

        window_size = self.centralWidget().size()
        screen = self.main_window.screens[self.screen_idx]
        image = screen.get_scaled_screenshot(window_size)

        painter.drawImage(0, 0, image)

        if not self.is_selecting:
            return

        # Draw selection rectangle
        painter.setPen(
            QtGui.QPen(self.primary_color, self.pen_width, QtCore.Qt.DashLine)
        )
        painter.drawRect(*self.selection.geometry)

        # Draw Mode indicator
        painter.setFont(self.mode_indicator_font)
        painter.drawText(
            max(self.selection.right, self.selection.left) - 18,
            min(self.selection.bottom, self.selection.top) - 8,
            self.mode_indicator,
        )
        painter.end()

    def keyPressEvent(self, event):
        """Handle ESC key pressed."""
        if event.key() == QtCore.Qt.Key_Escape:
            if self.is_selecting:
                # Abort selection process, allowing to reselect
                self.is_selecting = False
                self.update()
            else:
                # Quit application
                self.main_window.com.on_quit_or_hide.emit("esc button pressed")

    def mousePressEvent(self, event):
        """Handle left mouse button clicked."""
        if event.button() == QtCore.Qt.LeftButton:
            self.is_selecting = True
            self.mode_indicator = self._get_mode_indicator_char()
            self.selection.top = self.selection.bottom = event.position().y()
            self.selection.left = self.selection.right = event.position().x()
            self.update()

    def mouseMoveEvent(self, event):
        """Update selection on mouse move."""
        self.selection.bottom = event.position().y()
        self.selection.right = event.position().x()
        self.update()

    def mouseReleaseEvent(self, event):
        """Start OCR workflow on left mouse button release."""
        if (event.button() == QtCore.Qt.LeftButton) and self.is_selecting:
            self.selection.bottom = event.position().y()
            self.selection.right = event.position().x()

            self.is_selecting = False
            self.main_window.com.on_set_cursor_wait.emit()
            self.main_window.com.on_minimize_windows.emit()

            factor = self.main_window.screens[self.screen_idx].screen_window_ratio
            self.selection.scale(factor)
            self.selection.normalize()

            self.main_window.com.on_region_selected.emit(
                (self.selection, self.screen_idx)
            )

            self.selection = Rect()
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
            self.main_window.com.on_window_positioned.emit()
        return super().changeEvent(event)

    def hideEvent(self, _) -> None:
        """Make sure MacOS border window is hidden."""
        if self.macos_border:
            self.macos_border.hide()

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
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.BypassWindowManagerHint
        )

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setWindowState(QtCore.Qt.WindowActive)

        screen_geometry = self.main_window.screens[self.screen_idx].geometry
        self.move(screen_geometry.left, screen_geometry.top)
        self.setMinimumSize(QtCore.QSize(screen_geometry.width, screen_geometry.height))
        self.showFullScreen()

    def _set_fullscreen_macos(self):
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            # | QtCore.Qt.WindowStaysOnTopHint
            # | QtCore.Qt.NoDropShadowWindowHint
        )
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        screen_geometry = self.main_window.screens[self.screen_idx].geometry
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
        screen_geometry = self.main_window.screens[self.screen_idx].geometry
        self.move(screen_geometry.left, screen_geometry.top)
        self.showFullScreen()

    def _position_windows_on_wayland(self):
        self.setFocus()
        screen_geometry = self.main_window.screens[self.screen_idx].geometry
        logger.debug("Move window %s to position  %s", self.screen_idx, screen_geometry)
        move_active_window_to_position_on_gnome(screen_geometry)
        self.is_positioned = True
