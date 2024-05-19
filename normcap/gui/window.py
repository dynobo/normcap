"""Normcap window.

Supposed to show a screenshot of the current desktop in full screen, on which the
user can draw a selection rectangle.

One instance (single-display) or multiple instances (multi-display) might be created.

On Linux's Wayland DE, where the compositor and not the application is supposed to
control the window's position, some platform specific workarounds are implemented to
nevertheless display potentially multiple windows in fullscreen on multiple displays.
"""

import logging
from dataclasses import dataclass
from typing import Callable, Optional, cast

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import dbus, system_info
from normcap.gui.models import CaptureMode, DesktopEnvironment, Rect, Screen
from normcap.gui.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class DebugInfo:
    screen: Optional[Screen] = None
    window: Optional[QtWidgets.QMainWindow] = None
    scale_factor: float = 1


class Communicate(QtCore.QObject):
    """Window's communication bus."""

    on_esc_key_pressed = QtCore.Signal()
    on_region_selected = QtCore.Signal(Rect)


class Window(QtWidgets.QMainWindow):
    """Provide fullscreen UI for interacting with NormCap."""

    def __init__(
        self,
        screen: Screen,
        settings: Settings,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Initialize window."""
        super().__init__(parent=parent)
        logger.debug("Create window for screen %s", screen.index)

        self.settings = settings
        self.screen_ = screen

        self.com = Communicate(parent=self)
        self.color: QtGui.QColor = QtGui.QColor(str(settings.value("color")))

        self.setWindowTitle(f"NormCap [{screen.index}]")
        self.setWindowIcon(QtGui.QIcon(":normcap"))
        self.setWindowFlags(
            QtGui.Qt.WindowType.FramelessWindowHint
            | QtGui.Qt.WindowType.CustomizeWindowHint
            | QtGui.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setAnimated(False)
        self.setEnabled(True)

        self.selection_rect: QtCore.QRect = QtCore.QRect()

        self._add_image_container()
        self._add_ui_container()

    def _get_scale_factor(self) -> float:
        """Calculate scale factor from image and screen dimensions."""
        if not self.screen_.screenshot:
            raise ValueError("Screenshot image is missing!")
        return self.screen_.screenshot.width() / self.width()

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
                scale_factor=self._get_scale_factor(), screen=self.screen_, window=self
            )

        self.ui_container.color = self.color
        self.ui_container.setGeometry(self.image_container.geometry())
        self.ui_container.raise_()

    def _draw_background_image(self) -> None:
        """Draw screenshot as background image."""
        pixmap = QtGui.QPixmap()
        pixmap.convertFromImage(self.screen_.screenshot)
        self.image_container.setPixmap(pixmap)

    def _move_to_screen_on_wayland(self) -> None:
        """Move window to respective monitor on Wayland.

        In Wayland, the compositor has the responsibility for positioning windows, the
        client itself can't do this. However, there are DE dependent workarounds.
        """

        def move_to_screen(win: Window) -> None:
            if system_info.desktop_environment() == DesktopEnvironment.GNOME:
                result = dbus.move_windows_via_window_calls_extension(
                    title_id=win.windowTitle(), position=win.screen_
                )
                if not result:
                    dbus.move_window_via_gnome_shell_eval(
                        title_id=win.windowTitle(), position=win.screen_
                    )
            elif system_info.desktop_environment() == DesktopEnvironment.KDE:
                dbus.move_window_via_kde_kwin_scripting(
                    title_id=win.windowTitle(), position=win.screen_
                )
            else:
                logger.warning(
                    "No window move method for %s", system_info.desktop_environment()
                )

        # Delay move to ensure window is active & registered in window manager.
        QtCore.QTimer.singleShot(20, lambda: move_to_screen(win=self))

    def set_fullscreen(self) -> None:
        """Set window to full screen using platform specific methods."""
        # TODO: Test in Multi Display setups with different scaling
        # TODO: Test in Multi Display setups with different position
        # TODO: Position in Multi Display probably problematic!
        logger.debug("Set window of screen %s to fullscreen", self.screen_.index)

        if not self.screen_.screenshot:
            raise ValueError("Screenshot is missing on screen %s", self.screen_)

        # Using scaled window dims to fit sizing with dpr in case scaling is enabled
        # See: https://github.com/dynobo/normcap/issues/397
        if (
            system_info.display_manager_is_wayland()
            and self.screen_.size == self.screen_.screenshot.size().toTuple()
            and self.screen_.device_pixel_ratio != 1
        ):
            # TODO: Check if still necessary on latest supported Ubuntu.
            # If not, remove Screen.scale() and this condition.
            self.setGeometry(*self.screen_.scale().geometry)
        else:
            self.setGeometry(*self.screen_.geometry)

        if system_info.desktop_environment() != DesktopEnvironment.UNITY:
            # On some DEs, setting a fixed window size can enforce the correct size.
            # However, on Unity, it breaks the full screen view.
            self.setMinimumSize(self.geometry().size())
            self.setMaximumSize(self.geometry().size())

        if system_info.display_manager_is_wayland():
            # For unknown reason .showFullScreen() on Ubuntu 24.04 does not show the
            # window. Showing the Window in normal state upfront seems to help.
            # (It seems like .setWindowState(WindowFullScreen) should not be set before
            # .setVisible(True) on that system. Might be a QT bug.)
            self.show()

        self.showFullScreen()
        self.setFocus()

        # On Wayland, setting geometry doesn't move the window to the right screen, as
        # only the compositor is allowed to do this. In case of multi-display setups, we
        # need to use hacks to position the window:
        if system_info.display_manager_is_wayland():
            self._move_to_screen_on_wayland()

    def clear_selection(self) -> None:
        self.selection_rect = QtCore.QRect()
        self.ui_container.rect = self.selection_rect
        self.update()

    def get_capture_mode(self) -> CaptureMode:
        """Read current capture mode from application settings."""
        mode_setting = str(self.settings.value("mode"))
        try:
            mode = CaptureMode[mode_setting.upper()]
        except KeyError:
            logger.warning("Unknown capture mode: %s. Fallback to PARSE.", mode_setting)
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
        scaled_selection_rect = Rect(*selection_coords).scale(self._get_scale_factor())

        self.clear_selection()

        # Emit as last action, cause self might get destroyed by the slots
        self.com.on_region_selected.emit((scaled_selection_rect, self.screen_.index))

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: N802
        """Adjust child widget on resize."""
        super().resizeEvent(event)
        self.ui_container.resize(self.size())
        if self.ui_container.debug_info:
            self.ui_container.debug_info.scale_factor = self._get_scale_factor()

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

        self.debug_info: Optional[DebugInfo] = None

        self.rect: QtCore.QRect = QtCore.QRect()
        self.rect_pen = QtGui.QPen(self.color, 2, QtCore.Qt.PenStyle.DashLine)
        self.get_capture_mode = capture_mode_func

        self.setObjectName("ui_container")
        self.setStyleSheet(f"#ui_container {{border: 3px solid {self.color.name()};}}")
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setScaledContents(True)

    def _draw_debug_infos(self, painter: QtGui.QPainter, rect: QtCore.QRect) -> None:
        """Draw debug information to top left."""
        if (
            not self.debug_info
            or not self.debug_info.screen
            or not self.debug_info.screen.screenshot
            or not self.debug_info.window
        ):
            return

        selection = Rect(*cast(tuple, rect.normalized().getCoords()))
        selection_scaled = selection.scale(self.debug_info.scale_factor)

        lines = (
            "[ Screen ]",
            f"Size: {self.debug_info.screen.size}",
            f"Position: {self.debug_info.screen.coords}",
            f"Device pixel ratio: {self.debug_info.screen.device_pixel_ratio}",
            "",
            "[ Window ]",
            f"Size: {self.debug_info.window.size().toTuple()}",
            f"Position: {cast(tuple, self.debug_info.window.geometry().getCoords())}",
            f"Device pixel ratio: {self.debug_info.window.devicePixelRatio()}",
            f"Selected region: {selection.coords}",
            "",
            "[ Screenshot ]",
            f"Size: {self.debug_info.screen.screenshot.size().toTuple()}",
            f"Selected region (scaled): {selection_scaled.coords}",
            "",
            "[ Scaling detected ]",
            f"Factor: {self.debug_info.scale_factor:.2f}",
        )

        painter.setPen(QtGui.QColor(0, 0, 0, 0))
        painter.setBrush(QtGui.QColor(0, 0, 0, 175))
        painter.drawRect(3, 3, 300, 20 * len(lines) + 5)
        painter.setBrush(QtGui.QColor(0, 0, 0, 0))

        painter.setPen(self.color)
        painter.setFont(QtGui.QFont(QtGui.QFont().family(), 10, 600))
        for idx, line in enumerate(lines):
            painter.drawText(10, 20 * (idx + 1), line)

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
