"""Normcap base window.

Inherited for the main window, instantiated for the child windows (which get created
in multi display setups).
"""

from copy import deepcopy

from PySide2 import QtCore, QtGui, QtWidgets

from normcap.logger import logger
from normcap.models import CaptureMode, DisplayManager, Platform, Rect, SystemInfo
from normcap.utils import get_icon, move_active_window_to_position_on_gnome


class BaseWindow(QtWidgets.QMainWindow):
    """Main (parent) window."""

    # Helper window to extend the red border
    macos_border_window: QtWidgets.QMainWindow

    def __init__(
        self, system_info: SystemInfo, screen_idx: int, color: str, parent=None
    ):
        super().__init__()
        self.system_info: SystemInfo = system_info
        self.screen_idx: int = screen_idx
        self.primary_color: str = color
        self.main_window: QtWidgets.QMainWindow = parent if parent else self

        # Window properties
        self.setObjectName(f"window-{self.screen_idx}")
        self.setWindowTitle("NormCap")
        self.setWindowIcon(get_icon("normcap.png"))
        self.setAnimated(False)
        self.setEnabled(True)

        # Prepare selection rectangle
        self.qt_primary_color: QtGui.QColor = QtGui.QColor(self.primary_color)
        self.selection_rect: Rect = Rect()
        self.is_positioned: bool = False
        self.pen_width: int = 2
        self.is_selecting: bool = False
        self.mode_indicator: str = "?"
        self.mode_indicator_font = QtGui.QFont()
        self.mode_indicator_font.setPixelSize(24)

        # Setup widgets and show
        logger.debug(f"Creating window for screen {self.screen_idx}")
        self._add_central_widget()
        self.set_fullscreen()

    def _add_central_widget(self):
        self.frame = QtWidgets.QFrame()
        self.frame.setObjectName("central_widget")
        self.frame.setEnabled(True)
        self.frame.setAutoFillBackground(True)
        self.frame.setStyleSheet(f"QFrame {{border: 3px solid {self.primary_color};}}")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame.setLineWidth(0)
        self.frame.setCursor(QtCore.Qt.CrossCursor)
        self.setCentralWidget(self.frame)

    ##################
    # Utility
    ##################
    def _to_global_rect(self, rect: Rect) -> Rect:
        """Transform coordinates on display to global coordinates for multi screen"""

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
    def _sanatize_rect(rect: Rect) -> Rect:
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
        if not self.is_selecting:
            return

        painter = QtGui.QPainter(self)

        # Draw selection rectangle
        painter.setPen(
            QtGui.QPen(self.qt_primary_color, self.pen_width, QtCore.Qt.DashLine)
        )
        painter.drawRect(*self.selection_rect.geometry)

        # Draw Mode indicator
        painter.setFont(self.mode_indicator_font)
        painter.drawText(
            max(self.selection_rect.right, self.selection_rect.left) - 18,
            min(self.selection_rect.bottom, self.selection_rect.top) - 8,
            self.mode_indicator,
        )
        painter.end()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            if self.is_selecting:
                # Abort selection process, allowing to reselect
                self.is_selecting = False
                self.update()
            else:
                # Quit application
                self.main_window.com.on_quit_or_hide.emit("esc button pressed")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_selecting = True
            self.mode_indicator = self._get_mode_indicator_char()
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
            self.main_window.com.on_set_cursor_wait.emit()
            self.main_window.com.on_minimize_windows.emit()

            capture_rect = deepcopy(self.selection_rect)
            capture_rect = self._to_global_rect(capture_rect)
            capture_rect = self._sanatize_rect(capture_rect)
            self.main_window.com.on_region_selected.emit(
                (capture_rect, self.screen_idx)
            )

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
            self.main_window.com.on_window_positioned.emit()
        return super().changeEvent(event)

    def hideEvent(self, _) -> None:
        if self.macos_border_window:
            self.macos_border_window.hide()

    ##################
    # Adjust UI
    ##################

    def _create_macos_border_window(self):
        """Create 'fake' window to draw red border around whole screen on MacOS.

        The only way I found to draw a window on top of Mac's menu bar and dock is the
        window flag QtCore.Qt.ToolTip.
        The drawback of that flag is that the windows doesn't accept any keypress events
        and can not change the mouse curser. Therefore, a "normal" window (self) is created
        as before, and a second window (macos_border_window) is drawn above it with the Tooltip
        flag.
        """
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(f"QFrame {{border: 3px solid {self.primary_color};}}")
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Plain)
        frame.setLineWidth(0)

        self.macos_border_window = QtWidgets.QMainWindow()
        self.macos_border_window.setCentralWidget(frame)
        self.macos_border_window.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.BypassWindowManagerHint
            | QtCore.Qt.NoDropShadowWindowHint
            | QtCore.Qt.ToolTip
        )

        self.macos_border_window.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.macos_border_window.setStyleSheet(
            "QFrame { background-color:rgba(0,0,0,0); }"
        )

        screen_geometry = self.system_info.screens[self.screen_idx].geometry
        self.macos_border_window.setGeometry(
            screen_geometry.left,
            screen_geometry.top,
            screen_geometry.width,
            screen_geometry.height,
        )
        self.macos_border_window.show()

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
            raise NotImplementedError(
                f"Platform {self.system_info.platform} not supported"
            )

    def _set_fullscreen_linux(self):
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.BypassWindowManagerHint
            | QtCore.Qt.WindowStaysOnTopHint
        )

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color:transparent")
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setWindowState(QtCore.Qt.WindowActive)

        screen_geometry = self.system_info.screens[self.screen_idx].geometry
        self.move(screen_geometry.left, screen_geometry.top)
        self.setMinimumSize(QtCore.QSize(screen_geometry.width, screen_geometry.height))
        self.show()

    def _set_fullscreen_macos(self):
        self._create_macos_border_window()

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.NoDropShadowWindowHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        # Full transparent bg makes window click trough. Therefore:
        self.setStyleSheet("QFrame { background-color:rgba(88,88,88,0.09); }")
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        screen_geometry = self.system_info.screens[self.screen_idx].geometry
        self.setGeometry(
            screen_geometry.left,
            screen_geometry.top,
            screen_geometry.width,
            screen_geometry.height,
        )

    def _set_fullscreen_windows(self):
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
        self.setFocus()
        screen_geometry = self.system_info.screens[self.screen_idx].geometry
        logger.debug(f"Moving window to screen {self.screen_idx} to {screen_geometry}")
        move_active_window_to_position_on_gnome(screen_geometry)
        self.is_positioned = True
