"""Normcap window.

Supposed to show a screenshot of the current desktop in full screen, on which the
user can draw a selection rectangle.

One instance (single-display) or multiple instances (multi-display) might be created.

On Linux's Wayland DE, where the compositor and not the application is supposed to
control the window's position, some platform specific workarounds are implemented to
nevertheless display potentially multiple windows in fullscreen on multiple displays.
"""


import logging
import sys
import tempfile
from pathlib import Path
from typing import Callable, NamedTuple, cast

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import system_info
from normcap.gui.models import CaptureMode, DesktopEnvironment, Rect, Screen
from normcap.gui.settings import Settings

try:
    from PySide6 import QtDBus

    HAS_QTDBUS = True
except ImportError:
    HAS_QTDBUS = False


logger = logging.getLogger(__name__)


class DebugInfo(NamedTuple):
    screen: Screen | None = None
    scale_factor: float = 1


def _move_active_window_to_position_on_gnome(screen_rect: Rect) -> None:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on Gnome Shell.
    """
    if not HAS_QTDBUS or sys.platform != "linux":
        raise TypeError("QtDBus should only be called on Linux systems!")

    js_code = f"""
    const GLib = imports.gi.GLib;
    global.get_window_actors().forEach(function (w) {{
        var mw = w.meta_window;
        if (mw.has_focus()) {{
            mw.move_resize_frame(
                0,
                {screen_rect.left},
                {screen_rect.top},
                {screen_rect.width},
                {screen_rect.height}
            );
        }}
    }});
    """
    item = "org.gnome.Shell"
    interface = "org.gnome.Shell"
    path = "/org/gnome/Shell"

    bus = QtDBus.QDBusConnection.sessionBus()
    if not bus.isConnected():
        logger.error("Not connected to dbus!")

    shell_interface = QtDBus.QDBusInterface(item, path, interface, bus)
    if shell_interface.isValid():
        x = shell_interface.call("Eval", js_code)
        if x.errorName():
            logger.error("Failed move Window!")
            logger.error(x.errorMessage())
    else:
        logger.warning("Invalid dbus interface on Gnome")


def _move_active_window_to_position_on_kde(screen_rect: Rect) -> None:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on KDE.
    """
    if not HAS_QTDBUS or sys.platform != "linux":
        raise TypeError("QtDBus should only be called on Linux systems!")

    js_code = f"""
    client = workspace.activeClient;
    client.geometry = {{
        "x": {screen_rect.left},
        "y": {screen_rect.top},
        "width": {screen_rect.width},
        "height": {screen_rect.height}
    }};
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".js") as script_file:
        script_file.write(js_code.encode())

    bus = QtDBus.QDBusConnection.sessionBus()
    if not bus.isConnected():
        logger.error("Not connected to dbus!")

    item = "org.kde.KWin"
    interface = "org.kde.kwin.Scripting"
    path = "/Scripting"
    shell_interface = QtDBus.QDBusInterface(item, path, interface, bus)

    # FIXME: shell_interface is not valid on latest KDE in Fedora 36.
    if shell_interface.isValid():
        x = shell_interface.call("loadScript", script_file.name)
        y = shell_interface.call("start")
        if x.errorName() or y.errorName():
            logger.error("Failed move Window!")
            logger.error(x.errorMessage(), y.errorMessage())
    else:
        logger.warning("Invalid dbus interface on KDE")

    Path(script_file.name).unlink()


class Communicate(QtCore.QObject):
    """Window's communication bus."""

    on_esc_key_pressed = QtCore.Signal()
    on_region_selected = QtCore.Signal(Rect)
    on_window_positioned = QtCore.Signal()


class Window(QtWidgets.QMainWindow):
    """Provide fullscreen UI for interacting with NormCap."""

    def __init__(
        self,
        screen: Screen,
        settings: Settings,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initialize window."""
        super().__init__(parent=parent)
        logger.debug("Create window for screen %s", screen.index)

        self.settings = settings
        self.screen_ = screen

        self.com = Communicate(parent=self)
        self.color: QtGui.QColor = QtGui.QColor(str(settings.value("color")))
        self.is_positioned: bool = False

        self.setWindowTitle("NormCap")
        self.setWindowIcon(QtGui.QIcon(":normcap"))
        self.setAnimated(False)
        self.setEnabled(True)

        self.selection_rect: QtCore.QRect = QtCore.QRect()

        self._add_image_container()
        self._add_ui_container()

    def _get_scale_factor(self) -> float:
        """Calculate scale factor from image and screen dimensions."""
        if not self.screen_.screenshot:
            raise ValueError("Screenshot image is missing!")
        return self.screen_.screenshot.width() / self.screen_.width

    def _add_image_container(self) -> None:
        """Add widget showing screenshot."""
        self.image_container = QtWidgets.QLabel()
        self.image_container.setScaledContents(True)
        self.setCentralWidget(self.image_container)

    def _add_ui_container(self) -> None:
        """Add widget for showing selection rectangle and settings button."""
        self.ui_container = UiContainerLabel(
            parent=self, color=self.color, capture_mode_func=self.get_capture_mode
        )

        if logger.getEffectiveLevel() is logging.DEBUG:
            self.ui_container.debug_info = DebugInfo(
                scale_factor=self._get_scale_factor(), screen=self.screen_
            )

        self.ui_container.color = self.color
        self.ui_container.setGeometry(self.image_container.geometry())
        self.ui_container.raise_()

    def _draw_background_image(self) -> None:
        """Draw screenshot as background image."""
        if not self.screen_.screenshot:
            raise ValueError("Screenshot image is missing!")

        pixmap = QtGui.QPixmap()
        pixmap.convertFromImage(self.screen_.screenshot)
        self.image_container.setPixmap(pixmap)

    def _position_windows_on_wayland(self) -> None:
        """Move window to respective monitor on Wayland.

        In Wayland, the compositor has the responsibility for positioning windows, the
        client itself can't do this. However, there are DE dependent workarounds.
        """
        self.setFocus()
        logger.debug("Move window %s to %s", self.screen_.index, self.screen_.rect)
        if system_info.desktop_environment() == DesktopEnvironment.GNOME:
            _move_active_window_to_position_on_gnome(self.screen_.rect)
        elif system_info.desktop_environment() == DesktopEnvironment.KDE:
            _move_active_window_to_position_on_kde(self.screen_.rect)
        self.is_positioned = True

    def set_fullscreen(self) -> None:
        """Set window to full screen using platform specific methods."""
        logger.debug("Set window of screen %s to fullscreen", self.screen_.index)

        self.setWindowFlags(
            QtGui.Qt.WindowType.FramelessWindowHint
            | QtGui.Qt.WindowType.CustomizeWindowHint
            | QtGui.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        # Moving window to corresponding monitor
        self.setGeometry(*self.screen_.rect.geometry)

        # On unity, setting min/max window size breaks fullscreen.
        if system_info.desktop_environment() != DesktopEnvironment.UNITY:
            self.setMinimumSize(self.geometry().size())
            self.setMaximumSize(self.geometry().size())

        self.showFullScreen()

    def clear_selection(self) -> None:
        self.selection_rect = QtCore.QRect()
        self.ui_container.rect = self.selection_rect
        self.update()

    def get_capture_mode(self) -> CaptureMode:
        """Read current capture mode from application settings."""
        mode_setting = str(self.settings.value("mode"))
        try:
            mode = CaptureMode[mode_setting.upper()]
        except ValueError:
            logger.warning(f"Unknown capture mode: {mode_setting}. Fallback to PARSE.")
            mode = CaptureMode.PARSE
        return mode

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa: N802
        """Handle ESC key pressed.

        Cancels the selection progress (if ongoing), otherwise emit signal.
        """
        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.selection_rect:
                self.clear_selection()
            else:
                self.com.on_esc_key_pressed.emit()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Handle left mouse button clicked.

        Creates a new selection rectangle with both points set to pointer position.
        Note that the points "topLeft" and "bottomRight" are more like start and end
        points and not necessarily relate to the geometrical position.

        The selection rectangle will be normalized just before emitting the signal in
        the mouseReleaseEvent.
        """
        super().mousePressEvent(event)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.selection_rect = QtCore.QRect()
            self.selection_rect.setTopLeft(event.position().toPoint())
            self.selection_rect.setBottomRight(event.position().toPoint())
            self.ui_container.rect = self.selection_rect
            self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Update position of bottom right point of selection rectangle."""
        super().mouseMoveEvent(event)
        if self.selection_rect:
            self.selection_rect.setBottomRight(event.position().toPoint())
            self.ui_container.rect = self.selection_rect
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Start OCR workflow on left mouse button release."""
        super().mouseReleaseEvent(event)
        if (
            event.button() != QtCore.Qt.MouseButton.LeftButton
            or not self.selection_rect
        ):
            return

        self.selection_rect.setBottomRight(event.position().toPoint())

        selection_coords = cast(tuple, self.selection_rect.normalized().getCoords())
        scaled_selection_rect = Rect(*selection_coords).scaled(self._get_scale_factor())

        self.clear_selection()

        # Emit as last action, cause self might get destroyed by the slots
        self.com.on_region_selected.emit((scaled_selection_rect, self.screen_.index))

    def changeEvent(self, event: QtCore.QEvent) -> None:  # noqa: N802
        """Update position on Wayland.

        This is a workaround to move windows to different displays in multi monitor
        setups on Wayland. Necessary, because under Wayland the application is not
        supposed to control the position of its windows.
        """
        super().changeEvent(event)
        if (
            event.type() == QtCore.QEvent.Type.ActivationChange
            and system_info.display_manager_is_wayland()
            and self.isActiveWindow()
            and not self.is_positioned
        ):
            self._position_windows_on_wayland()
            self.com.on_window_positioned.emit()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: N802
        """Adjust child widget on resize."""
        super().resizeEvent(event)
        self.ui_container.resize(self.size())

    def showEvent(self, event: QtGui.QShowEvent) -> None:  # noqa: N802
        """Update background image on show/reshow."""
        super().showEvent(event)
        self._draw_background_image()


class UiContainerLabel(QtWidgets.QLabel):
    """Widget to draw border, selection rectangle and potentially debug infos."""

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        color: QtGui.QColor,
        capture_mode_func: Callable,
    ) -> None:
        super().__init__(parent)

        self.color: QtGui.QColor = color

        self.debug_info: DebugInfo | None = None

        self.rect: QtCore.QRect = QtCore.QRect()
        self.rect_pen = QtGui.QPen(self.color, 2, QtCore.Qt.PenStyle.DashLine)
        self.get_capture_mode = capture_mode_func

        self.setObjectName("ui_container")
        self.setStyleSheet(f"#ui_container {{border: 3px solid {self.color.name()};}}")
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setScaledContents(True)

    def _draw_debug_infos(self, painter: QtGui.QPainter, rect: QtCore.QRect) -> None:
        """Draw debug information to top left."""
        if not self.debug_info or not self.debug_info.screen:
            return

        normalized_coords = cast(tuple, rect.normalized().getCoords())
        selection = Rect(*normalized_coords)
        selection_scaled = selection.scaled(self.debug_info.scale_factor)

        x = y = 25
        screen_size = (self.debug_info.screen.width, self.debug_info.screen.height)
        if self.debug_info.screen.screenshot:
            screenshot_size = self.debug_info.screen.screenshot.size().toTuple()
        else:
            screenshot_size = (-1, -1)

        painter.setPen(QtGui.QPen(self.color))
        painter.drawText(x, y * 1, "QScreen:")
        painter.drawText(x, y * 2, f"     Size: {screen_size}")
        painter.drawText(x, y * 3, f"     Selected region: {selection.geometry}")
        painter.drawText(x, y * 4, "Image:")
        painter.drawText(x, y * 5, f"     Size: {screenshot_size}")
        painter.drawText(x, y * 6, f"     Selected region: {selection_scaled.geometry}")
        painter.drawText(x, y * 7, "Scaling:")
        painter.drawText(x, y * 8, f"     Factor: {self.debug_info.scale_factor:.2f}")
        dpr = self.debug_info.screen.device_pixel_ratio
        painter.drawText(x, y * 9, f"     Device pixel ratio: {dpr:.2f}")

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: N802
        """Draw selection rectangle and mode indicator icon."""
        super().paintEvent(event)

        if not (self.rect or self.debug_info):
            return

        painter = QtGui.QPainter(self)
        self.rect = self.rect.normalized()

        if self.debug_info:
            self._draw_debug_infos(painter, self.rect)

        if not self.rect:
            return

        painter.setPen(self.rect_pen)
        painter.drawRect(self.rect)

        if self.get_capture_mode() is CaptureMode.PARSE:
            mode_icon = QtGui.QIcon(":parse")
        else:
            mode_icon = QtGui.QIcon(":raw")
        mode_icon.paint(painter, self.rect.right() - 24, self.rect.top() - 30, 24, 24)

        painter.end()
