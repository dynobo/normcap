"""Some utility functions."""

import tempfile
from pathlib import Path

from jeepney.io.blocking import open_dbus_connection  # type: ignore
from jeepney.wrappers import (  # type: ignore
    DBusErrorResponse,
    MessageGenerator,
    new_method_call,
)
from PySide2 import QtCore, QtGui, QtWidgets

from normcap import utils
from normcap.logger import logger
from normcap.models import Capture, DisplayManager, Platform, ScreenInfo, SystemInfo


class ScreenGrabber:
    """Responsible for performing screenshots on various platforms."""

    capture: Capture

    def __call__(self, capture: Capture, system_info: SystemInfo) -> Capture:
        """Grab screenshot of supplied region."""
        self.capture = capture

        if not isinstance(capture.screen, ScreenInfo):
            raise ValueError("Capture object doesn't contain screen information")

        logger.debug(f"Capturing screen {self.capture.screen}")
        if (
            system_info.platform == Platform.LINUX
            and system_info.display_manager == DisplayManager.WAYLAND
        ):
            logger.debug("Using DBUS for screenshot")
            self.grab_with_dbus()
        elif system_info.platform == Platform.MACOS:
            logger.debug("Using QT for screenshot by position")
            self.grab_with_qt_by_position()
            self.crop_to_selection()
        else:
            logger.debug("Using QT for screenshot by screen")
            self.grab_with_qt_by_screen()
            self.crop_to_selection()

        capture.image.setDevicePixelRatio(1)
        return capture

    def grab_with_qt_by_position(self):
        """Capture screenshot with QT method and Screen object.

        Works well on MacOS, fails on multi monitor on X11.
        """
        screen = QtWidgets.QApplication.screens()[self.capture.screen.index]
        screenshot = screen.grabWindow(
            0,
            screen.geometry().x(),
            screen.geometry().y(),
            screen.size().width(),
            screen.size().height(),
        )
        self.capture.image = screenshot.toImage()
        utils.save_image_in_tempfolder(self.capture.image, postfix="_raw_qt")

    def grab_with_qt_by_screen(self):
        """Capture screenshot with QT method and Screen object.

        Works well on X11, fails on multi monitor MacOS.
        """
        screenshot = QtGui.QScreen.grabWindow(
            QtWidgets.QApplication.screens()[self.capture.screen.index], 0
        )
        self.capture.image = screenshot.toImage()
        utils.save_image_in_tempfolder(self.capture.image, postfix="_raw_qt")

    def crop_to_selection(self):
        """Crop screenshot to selected region.

        With QT's grabWindow() the whole screen is capture. It needs to be cropped to
        the selected rectangle. Different dpi have to be considered.
        """
        self.capture.scale_factor = round(
            self.capture.image.width() / self.capture.screen.width, 4
        )

        # Transform capture rect
        # Substract margins and adjust according to scaling
        rect = self.capture.rect
        screen = self.capture.screen.geometry
        scale = self.capture.scale_factor
        box = QtCore.QRect(
            round((rect.left - screen.left) * scale),  # x
            round((rect.top - screen.top) * scale),  # y
            round((rect.right - rect.left) * scale),  # width
            round((rect.bottom - rect.top) * scale),  # height
        )

        if box.width() <= 10 or box.height() <= 10:
            logger.debug(f"Region selected is very small: {box}")
            box.setRect(0, 0, 1, 1)

        logger.debug(f"Screen scale factor: {self.capture.scale_factor}")
        logger.debug(f"Image devicePixelRatio: {self.capture.image.devicePixelRatio()}")
        logger.debug(f"Image crop box rect: {box.getRect()}")

        self.capture.image = self.capture.image.copy(box)
        utils.save_image_in_tempfolder(self.capture.image, postfix="_cropped")

    def grab_with_dbus(self):
        """Capture rect of screen on gnome systems using wayland."""

        class DbusScreenshot(MessageGenerator):
            """Capture screenshot through dbus."""

            interface = "org.gnome.Shell.Screenshot"

            def __init__(self):
                """Init jeepney message generator."""
                super().__init__(
                    object_path="/org/gnome/Shell/Screenshot",
                    bus_name="org.gnome.Shell.Screenshot",
                )

            def grab_rect(self, x, y, width, height, filename):
                """Grab specific section to file with flash disabled."""
                return new_method_call(
                    self,
                    "ScreenshotArea",
                    "iiiibs",
                    (x, y, width, height, False, filename),
                )

        rect = self.capture.rect
        _, temp_name = tempfile.mkstemp(prefix="normcap")
        try:
            connection = open_dbus_connection(bus="SESSION")
            msg = DbusScreenshot().grab_rect(*rect.geometry, temp_name)
            _ = connection.send_and_get_reply(msg)
            self.capture.image = QtGui.QImage(temp_name)
            utils.save_image_in_tempfolder(self.capture.image, postfix="_raw_dbus")
        except DBusErrorResponse as e:
            if "invalid params" in [d.lower() for d in e.data]:
                logger.info("ScreenShot with DBUS failed with 'invalid params'")
            else:
                logger.exception("ScreenShot with DBUS through exception")
        finally:
            Path(temp_name).unlink()


grab_screen = ScreenGrabber()
