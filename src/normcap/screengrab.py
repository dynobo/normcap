"""Some utility functions."""

import sys
import tempfile
from pathlib import Path

from jeepney.io.blocking import open_dbus_connection  # type: ignore
from jeepney.wrappers import (  # type: ignore
    DBusErrorResponse,
    MessageGenerator,
    new_method_call,
)
from PySide2 import QtCore, QtGui, QtWidgets

from normcap import system_info, utils
from normcap.logger import logger
from normcap.models import Capture, DisplayManager, ScreenInfo


class ScreenGrabber:
    """Responsible for performing screenshots on various platforms."""

    capture: Capture

    def __call__(self, capture: Capture) -> Capture:
        """Grab screenshot of supplied region."""
        self.capture = capture

        if not isinstance(capture.screen, ScreenInfo):
            raise ValueError("Capture object doesn't contain screen information")

        logger.debug("Grab screen: %s", self.capture.screen)
        if sys.platform == "linux":
            if system_info.display_manager() == DisplayManager.WAYLAND:
                self.grab_with_dbus()
            else:
                self.grab_with_qt_by_screen()
                self.crop_to_selection()
        elif sys.platform == "darwin":
            self.grab_with_qt_by_position()
            self.crop_to_selection()
        elif sys.platform == "win32":
            self.grab_with_qt_by_screen()
            self.crop_to_selection()
        else:
            raise RuntimeError(f"Platform {sys.platform} not supported!")

        capture.image.setDevicePixelRatio(1)
        return capture

    def grab_with_qt_by_position(self):
        """Capture screenshot with QT method and Screen object.

        Works well on MacOS, fails on multi monitor on X11.
        """
        logger.debug("Use capture method: QT by position")
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
        logger.debug("Use capture method: QT by screen")
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
            logger.debug("Region selected is very small: %s", box)
            box.setRect(0, 0, 1, 1)

        logger.debug("Screen scale factor: %s", self.capture.scale_factor)
        logger.debug(
            "Image devicePixelRatio: %s", self.capture.image.devicePixelRatio()
        )
        logger.debug("Image crop box rect: %s", box.getRect())

        self.capture.image = self.capture.image.copy(box)
        utils.save_image_in_tempfolder(self.capture.image, postfix="_cropped")

    def grab_with_dbus(self):
        """Capture rect of screen on gnome systems using wayland."""
        logger.debug("Use capture method: DBUS")

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
