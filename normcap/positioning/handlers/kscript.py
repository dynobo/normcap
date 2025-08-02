import functools
import logging
import re
import subprocess
import tempfile
import traceback

from jeepney.io.blocking import Proxy, open_dbus_connection
from jeepney.wrappers import Message, MessageGenerator, new_method_call
from PySide6 import QtWidgets

from normcap.gui import system_info
from normcap.gui.models import DesktopEnvironment, Screen

logger = logging.getLogger(__name__)

install_instructions = ""


@functools.cache
def _is_compatible_plasma_version() -> bool:
    compatible = True
    try:
        completed = subprocess.run(
            ["plasmashell", "--version"],  # noqa: S607  # start process partial path
            check=True,
            capture_output=True,
            text=True,
        )
        out = completed.stdout.strip()
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
        if not m:
            logger.warning("Could not parse KDE plasma version from: '%s'", out)
            return compatible

        major, minor, _patch = map(int, m.groups())

        # Incompatible since 5.71.0 (2020)
        max_supported_major = 5
        max_supported_minor = 70
        if major > max_supported_major or (
            major == max_supported_major and minor > max_supported_minor
        ):
            compatible = False
    except Exception:
        logger.warning("Could not retrieved KDE plasma version.", exc_info=True)
    return compatible


class DBusKwinScripting(MessageGenerator):
    interface = "org.kde.kwin.Scripting"

    def __init__(
        self,
        object_path: str = "/Scripting",
        bus_name: str = "org.kde.KWin",
    ) -> None:
        super().__init__(object_path=object_path, bus_name=bus_name)

    def load_script(self, script_file: str) -> Message:
        return new_method_call(self, "loadScript", "s", (script_file,))

    def start(self) -> Message:
        return new_method_call(self, "start")


class DBusKWin(MessageGenerator):
    interface = "org.kde.KWin"

    def __init__(
        self,
        object_path: str = "/org/kde/KWin",
        bus_name: str = "org.kde.KWin",
    ) -> None:
        super().__init__(object_path=object_path, bus_name=bus_name)

    def introspect(self) -> Message:
        return new_method_call(self, "Introspect")


def is_compatible() -> bool:
    """Check if the system theoretically could to use this method.

    Returns:
        System could be capable of using this method
    """
    return (
        system_info.desktop_environment() == DesktopEnvironment.KDE
        and _is_compatible_plasma_version()
    )


def is_installed() -> bool:
    """Check if the dependencies (binaries) for this method are available.

    Returns:
        System has all necessary dependencies
    """
    # TODO: Test Kwin inspection on KDE
    try:
        with open_dbus_connection() as router:
            proxy = Proxy(DBusKWin(), router)
            introspection = proxy.introspect()[0]
    except Exception as exc:
        logger.debug("Couldn't inspect Kwin: %s", exc)
        introspection = []

    return "Scripting" in introspection


def move(window: QtWidgets.QMainWindow, screen: Screen) -> None:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on KDE.

    Args:
        window: Qt Window to be re-positioned.
        screen: Geometry of the target screen.
    """
    title_id = window.windowTitle()
    position = screen

    logger.debug(
        "Moving window '%s' to %s via org.kde.kwin.Scripting", title_id, position
    )

    js_code = f"""
    const clients = workspace.clientList();
    for (var i = 0; i < clients.length; i++) {{
        if (clients[i].caption() == "{title_id}" ) {{
            clients[i].geometry = {{
                "x": {position.left},
                "y": {position.top},
                "width": {position.width},
                "height": {position.height}
            }};
        }}
    }}
    """
    with tempfile.NamedTemporaryFile(delete=True, suffix=".js") as script_file:
        script_file.write(js_code.encode())

        try:
            with open_dbus_connection() as router:
                proxy = Proxy(DBusKwinScripting(), router)
                response = proxy.load_script(script_file=script_file.name)
                if response[0] != 0:
                    raise RuntimeError(  # noqa: TRY301
                        "org.kde.kwin.Scripting.loadScript response: %s", response
                    )
                response = proxy.start()

        except Exception as exc:
            logger.warning("Failed to move window via org.kde.kwin.Scripting!")
            logger.debug(
                "".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__)
                ).strip()
            )
