import json
import logging
import os

from jeepney.io.blocking import Proxy, open_dbus_connection
from jeepney.wrappers import Message, MessageGenerator, new_method_call
from PySide6 import QtWidgets

from normcap.platform import system_info
from normcap.platform.models import DesktopEnvironment, Screen

logger = logging.getLogger(__name__)

install_instructions = """\
If you experience issues with the position of NormCaps windows, \
e.g. in a multi monitor setting, \
try installing the Gnome Shell Extension 'Window Calls'from \
https://extensions.gnome.org/extension/4724/window-calls/
"""


class DBusWindowCalls(MessageGenerator):
    interface = "org.gnome.Shell.Extensions.Windows"

    def __init__(
        self,
        object_path: str = "/org/gnome/Shell/Extensions/Windows",
        bus_name: str = "org.gnome.Shell",
    ) -> None:
        super().__init__(object_path=object_path, bus_name=bus_name)

    def list_(self) -> Message:
        return new_method_call(self, "List")

    def activate(self, win_id: int) -> Message:
        return new_method_call(self, "Activate", "u", (win_id,))

    def move_resize(
        self, win_id: int, x: int, y: int, width: int, height: int
    ) -> Message:
        return new_method_call(
            self, "MoveResize", "uiiuu", (win_id, x, y, width, height)
        )


class DBusShell(MessageGenerator):
    interface = "org.gnome.Shell.Extensions"

    def __init__(
        self,
        object_path: str = "/org/gnome/Shell",
        bus_name: str = "org.gnome.Shell",
    ) -> None:
        super().__init__(object_path=object_path, bus_name=bus_name)

    def list_extensions(self) -> Message:
        return new_method_call(self, "ListExtensions")


def is_compatible() -> bool:
    """Check if the system theoretically could to use this method.

    Returns:
        System could be capable of using this method
    """
    return system_info.desktop_environment() == DesktopEnvironment.GNOME


def is_installed() -> bool:
    """Check if the dependencies (binaries) for this method are available.

    Returns:
        System has all necessary dependencies
    """
    try:
        with open_dbus_connection() as router:
            proxy = Proxy(DBusShell(), router)
            extensions = proxy.list_extensions()[0]
    except Exception as exc:
        logger.debug("Couldn't retrieve Gnome Shell extensions list: %s", exc)
        extensions = []

    return "window-calls@domandoman.xyz" in extensions


def move(window: QtWidgets.QMainWindow, screen: Screen) -> None:
    """Position window on screen.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on Gnome and requires the Gnome Shell Extension 'Window Calls'
    https://github.com/ickyicky/window-calls

    Args:
        window: Qt Window to be re-positioned.
        screen: Geometry of the target screen.
    """
    title_id = window.windowTitle()
    position = screen

    logger.debug(
        "Moving window '%s' to %s via org.gnome.Shell.extensions.windows",
        title_id,
        position,
    )
    try:
        with open_dbus_connection() as router:
            proxy = Proxy(DBusWindowCalls(), router)

            response = proxy.list_()[0]

            all_windows = json.loads(response)
            all_normcap_windows = [w for w in all_windows if w["pid"] == os.getpid()]

            window_id = next(
                w["id"] for w in all_normcap_windows if w["title"] == title_id
            )

            response = proxy.move_resize(
                window_id,
                position.left,
                position.top,
                position.width,
                position.height,
            )

            response = proxy.activate(window_id)

    except Exception as exc:
        logger.warning(exc)
        logger.warning("Failed to move window via org.gnome.Shell.extensions.windows! ")
