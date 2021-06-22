"""Normcap base window.

Instantiated for child windows (multi display), inherited for the main window.

To launch designer:
    .venv/lib/python3.9/site-packages/PySide2/designer

To generate a new python class from ui-file:
    uic -g python base_window.ui > ../window_base_ui.py

"""
from copy import deepcopy

from PySide2 import QtCore, QtGui, QtWidgets

from normcap.logger import logger
from normcap.models import CaptureMode, DisplayManager, Platform, Rect, SystemInfo
from normcap.utils import move_active_window_to_position_on_gnome
from normcap.window_base_ui import Ui_BaseWindow


class WindowBase(QtWidgets.QMainWindow):
    """Main (parent) window."""

    def __init__(
        self, system_info: SystemInfo, screen_idx: int, color: str, parent=None
    ):
        super().__init__()
        self.system_info: SystemInfo = system_info
        self.screen_idx: int = screen_idx
        self.primary_color: str = color
        self.main_window: QtWidgets.QMainWindow = parent if parent else self

        self.qt_primary_color: QtGui.QColor = QtGui.QColor(self.primary_color)
        self.selection_rect: Rect = Rect()
        self.is_positioned: bool = False
        self.pen_width: int = 2
        self.is_selecting: bool = False

        logger.debug(f"Creating window for screen {self.screen_idx}")
        self.ui = Ui_BaseWindow()
        self.ui.setupUi(self)
        self.set_border_color()
        self.set_fullscreen()

    ##################
    # Utility
    ##################

    def to_global_rect(self, rect: Rect) -> Rect:
        """Transform coordinates on display to global coordinates.

        Necessary in multi display settings.
        """
        # Reposition if necessary (multi monitor)
        screen = self.system_info.screens[self.screen_idx]
        offset_x = screen.geometry.left
        offset_y = screen.geometry.top
        if offset_x != 0:
            rect.left += offset_x
            rect.right += offset_x
        if offset_y != 0:
            rect.top += offset_y
            rect.bottom += offset_y

        # Shrink to remove selection border
        rect.left += self.pen_width
        rect.top += self.pen_width
        rect.right -= self.pen_width
        rect.bottom -= self.pen_width
        return rect

    @staticmethod
    def sanatize_rect(rect: Rect) -> Rect:
        """Make sure that first coordinates are top/left and second bottom/right.

        Also for unknown reason, the selections drawn from bottom/right to
        top/left are larger than in the opposite direction and can include some
        pixels of the dashes border. This is removed here, too.
        """

        margin_correction = 4
        if rect.top > rect.bottom:
            bottom = rect.top - margin_correction
            top = rect.bottom + margin_correction
            rect.top = top
            rect.bottom = bottom
        if rect.left > rect.right:
            left = rect.right + margin_correction
            right = rect.left - margin_correction
            rect.right = right
            rect.left = left

        return rect

    def get_mode_indicator_char(self):
        """Map mode to char rendered on screen as indicator."""
        if self.main_window.capture.mode is CaptureMode.RAW:
            return "☰"
        if self.main_window.capture.mode is CaptureMode.PARSE:
            return "★"
        return ""

    ##################
    # Events
    ##################

    def paintEvent(self, _):
        if not self.is_selecting:
            return

        painter = QtGui.QPainter(self)
        # Draw selection rectangle
        painter.setPen(
            QtGui.QPen(self.qt_primary_color, self.pen_width, QtCore.Qt.DashLine)
        )
        painter.drawRect(*self.selection_rect.geometry)

        # Draw Mode indicator
        font = painter.font()
        font.setPixelSize(24)
        painter.setFont(font)
        painter.drawText(
            max(self.selection_rect.right, self.selection_rect.left) - 18,
            min(self.selection_rect.bottom, self.selection_rect.top) - 8,
            self.get_mode_indicator_char(),
        )
        painter.end()

    def keyPressEvent(self, event):
        """Handle keyboard events."""
        if event.key() == QtCore.Qt.Key_Escape:
            if self.is_selecting:
                # Abort selection process, allowing to reselect
                self.is_selecting = False
                self.update()
            else:
                # Quit application
                self.main_window.com.onQuitOrHide.emit()
        elif event.key() == QtCore.Qt.Key_Space:
            mode = self.main_window.capture.mode
            if mode < max(CaptureMode):
                mode = CaptureMode(mode.value + 1)
            else:
                mode = CaptureMode(0)
            self.main_window.capture.mode = mode
            self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_selecting = True
            self.selection_rect.top = event.pos().y()
            self.selection_rect.left = event.pos().x()
            self.selection_rect.bottom = event.pos().y()
            self.selection_rect.right = event.pos().x()
            self.update()

    def mouseMoveEvent(self, event):
        self.selection_rect.bottom = event.pos().y()
        self.selection_rect.right = event.pos().x()
        self.update()

    def mouseReleaseEvent(self, event):
        if (event.button() == QtCore.Qt.LeftButton) and self.is_selecting:
            self.selection_rect.bottom = event.pos().y()
            self.selection_rect.right = event.pos().x()

            self.is_selecting = False
            self.main_window.com.onSetCursorWait.emit()
            self.main_window.com.onMinimizeWindows.emit()

            capture_rect = deepcopy(self.selection_rect)
            capture_rect = self.to_global_rect(capture_rect)
            capture_rect = self.sanatize_rect(capture_rect)
            self.main_window.com.onRegionSelected.emit((capture_rect, self.screen_idx))

            self.selection_rect = Rect()
            self.update()

    def changeEvent(self, event) -> None:
        if (
            event.type() == QtCore.QEvent.Type.ActivationChange
            and self.system_info.display_manager == DisplayManager.WAYLAND
            and self.isActiveWindow()
            and not self.is_positioned
        ):
            logger.debug(f"Positioning window on screen {self.screen_idx}")
            self._position_windows_on_wayland()
            self.main_window.com.onWindowPositioned.emit()

        return super().changeEvent(event)

    ##################
    # Adjust UI
    ##################

    def set_border_color(self):
        """Set style to set color of border around display."""
        css = self.ui.frame.styleSheet()
        self.ui.frame.setStyleSheet(
            f"{css} QFrame {{border-color: {self.primary_color};}}"
        )

    def set_fullscreen(self):
        """Set window to full screen using platform specific methods."""
        logger.debug(f"Setting window for screen {self.screen_idx} to fullscreen")

        if self.system_info.platform == Platform.LINUX:
            self._set_fullscreen_linux()
        elif self.system_info.platform == Platform.MACOS:
            self._set_fullscreen_macos()
        elif self.system_info.platform == Platform.WINDOWS:
            self._set_fullscreen_windows()
        else:
            raise NotImplementedError(f"Platform {self.config.platform} not supported")

    def _set_fullscreen_linux(self):
        """Set fullscreen on Linux platforms."""
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setStyleSheet("background-color:transparent")
        screen_geometry = self.system_info.screens[self.screen_idx].geometry
        self.move(screen_geometry.left, screen_geometry.top)
        self.showFullScreen()

    def _set_fullscreen_macos(self):
        """Set fullscreen on MacOS platforms."""
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.NoDropShadowWindowHint
            # | QtCore.Qt.ToolTip
            #    ^^ Sets window in front of dock, but doesn't receive keyPressEvents
            #       and doesn't set the crosshair cursor.
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setStyleSheet("background-color:transparent")
        screen_geometry = self.system_info.screens[self.screen_idx].geometry
        self.setGeometry(
            screen_geometry.left,
            screen_geometry.top,
            screen_geometry.width,
            screen_geometry.height,
        )

    def _set_fullscreen_windows(self):
        """Set fullscreen on Windows platforms."""
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        # Full transparent bg makes window click trough. Therefore:
        self.setStyleSheet("background-color:rgba(0,0,0,0.01)")
        screen_geometry = self.system_info.screens[self.screen_idx].geometry
        self.move(screen_geometry.left, screen_geometry.top)
        self.showFullScreen()

    def _position_windows_on_wayland(self):
        """Set fullscreen on Linux platforms."""
        self.setFocus()
        screen_geometry = self.system_info.screens[self.screen_idx].geometry
        logger.debug(f"Moving window to screen {self.screen_idx} to {screen_geometry}")
        move_active_window_to_position_on_gnome(screen_geometry)
        self.is_positioned = True
