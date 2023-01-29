"""Normcap base window.

Inherited for the main window, instantiated for the child windows (which get created
in multi display setups).
"""

import logging
import os
import tempfile

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


def _move_active_window_to_position_on_gnome(screen_rect: Rect) -> None:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on Gnome Shell.
    """
    if not HAS_QTDBUS:
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
    if not HAS_QTDBUS:
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

    os.unlink(script_file.name)


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
    ) -> None:
        """Initialize window."""
        super().__init__()
        logger.debug("Create window for screen %s", screen.index)

        self.settings = settings
        self.screen_ = screen

        self.com = Communicate()
        self.color: QtGui.QColor = QtGui.QColor(str(settings.value("color")))
        self.is_positioned: bool = False

        self.setWindowTitle("NormCap")
        self.setWindowIcon(QtGui.QIcon(":normcap"))
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
        if not self.screen_.screenshot:
            raise ValueError("Screenshot image is missing!")
        return self.screen_.screenshot.width() / self.screen_.width

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
        pixmap = QtGui.QPixmap()
        pixmap.convertFromImage(self.screen_.screenshot)
        self.image_layer.setPixmap(pixmap)

    def _position_windows_on_wayland(self) -> None:
        """Move window to respective monitor on Wayland.

        In Wayland, the compositor has the responsiblity for positioning windows, the
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
            QtGui.Qt.FramelessWindowHint
            | QtGui.Qt.CustomizeWindowHint
            | QtGui.Qt.WindowStaysOnTopHint
        )
        self.setFocusPolicy(QtGui.Qt.StrongFocus)

        # Moving window to corresponding monitor
        self.setGeometry(*self.screen_.rect.geometry)

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
                self.com.on_esc_key_pressed.emit()
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
            self.com.on_region_selected.emit(
                (Rect(*rect.getCoords()).scaled(self.scale_factor), self.screen_.index)
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
            self.com.on_window_positioned.emit()
        super().changeEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: N802
        """Adjust child widget on resize."""
        self.ui_layer.resize(self.size())
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

        x = y = 25
        painter.setPen(QtGui.QPen(self.color))
        painter.drawText(x, y * 1, f"QScreen: {self.screen_.geometry}")
        painter.drawText(x, y * 2, f"Image: {self.screen_.screenshot.size().toTuple()}")
        painter.drawText(x, y * 3, f"Pos QScreen: {selection.geometry}")
        painter.drawText(x, y * 4, f"Pos Image: {selection_scaled.geometry}")
        painter.drawText(x, y * 5, f"Scale factor: {scale_factor}")
        painter.drawText(x, y * 6, f"DPR: {self.screen_.device_pixel_ratio}")

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

        mode = self.parent().settings.value("mode")
        if CaptureMode[mode.upper()] is CaptureMode.PARSE:
            mode_indicator = QtGui.QIcon(":parse")
        else:
            mode_indicator = QtGui.QIcon(":raw")
        mode_indicator.paint(painter, rect.right() - 24, rect.top() - 30, 24, 24)

        painter.end()
