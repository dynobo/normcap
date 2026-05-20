"""KDE Plasma 6 window positioning via KWin D-Bus scripting.

This replaces kscript.py which stopped working in Plasma 5.71 due to API changes.
Plasma 6 uses workspace.windowList() and window.frameGeometry instead of
workspace.clientList() / client.geometry.
"""

import functools
import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path

from jeepney.io.blocking import Proxy, open_dbus_connection
from jeepney.wrappers import Message, MessageGenerator, new_method_call
from PySide6 import QtWidgets

from normcap.system import info
from normcap.system.models import DesktopEnvironment, Screen

logger = logging.getLogger(__name__)

install_instructions = ""

_MIN_PLASMA_MAJOR = 6


@functools.cache
def _get_plasma_major_version() -> int | None:
    try:
        completed = subprocess.run(
            ["plasmashell", "--version"],  # noqa: S607
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        m = re.search(r"(\d+)\.", completed.stdout.strip())
        return int(m.group(1)) if m else None
    except Exception:
        logger.debug("Could not retrieve KDE Plasma version", exc_info=True)
        return None


class DBusKwinScripting6(MessageGenerator):
    interface = "org.kde.kwin.Scripting"

    def __init__(
        self,
        object_path: str = "/Scripting",
        bus_name: str = "org.kde.KWin",
    ) -> None:
        super().__init__(object_path=object_path, bus_name=bus_name)

    def load_script(self, script_file: str, plugin_name: str) -> Message:
        # Plasma 6 loadScript requires both filename and plugin name
        return new_method_call(self, "loadScript", "ss", (script_file, plugin_name))

    def unload_script(self, plugin_name: str) -> Message:
        return new_method_call(self, "unloadScript", "s", (plugin_name,))

    def start(self) -> Message:
        return new_method_call(self, "start")


class DBusKWinIntrospectable(MessageGenerator):
    interface = "org.freedesktop.DBus.Introspectable"

    def __init__(self) -> None:
        super().__init__(object_path="/Scripting", bus_name="org.kde.KWin")

    def introspect(self) -> Message:
        return new_method_call(self, "Introspect")


def is_compatible() -> bool:
    if info.desktop_environment() != DesktopEnvironment.KDE:
        return False
    major = _get_plasma_major_version()
    return major is not None and major >= _MIN_PLASMA_MAJOR


def is_installed() -> bool:
    try:
        with open_dbus_connection() as router:
            proxy = Proxy(DBusKWinIntrospectable(), router)
            introspection = proxy.introspect()[0]
    except Exception as exc:
        logger.debug("Couldn't inspect KWin: %s", exc)
        return False
    else:
        return "org.kde.kwin.Scripting" in introspection


def move(window: QtWidgets.QMainWindow, screen: Screen) -> None:
    """Move NormCap overlay window to the correct screen on KDE Plasma 6.

    Uses KWin D-Bus scripting with the updated Plasma 6 JavaScript API
    (workspace.windowList / window.frameGeometry).

    Args:
        window: Qt Window to be re-positioned.
        screen: Geometry of the target screen.
    """
    title_id = window.windowTitle()

    logger.debug(
        "Moving window '%s' to %s via KWin Plasma 6 scripting", title_id, screen
    )

    # Plasma 6 JS API changes across minor versions:
    # - workspace.windowList() (function) OR workspace.windows (property)
    # - window.caption may be a property or a method depending on version
    # - window.frameGeometry = Qt.rect(x, y, w, h) is stable since Plasma 6.0
    #
    # json.dumps() produces a properly escaped JS string literal (handles quotes,
    # backslashes, newlines, and all other special characters in window titles).
    safe_title = json.dumps(title_id)
    js_code = f"""
    var clients = (typeof workspace.windowList === 'function')
        ? workspace.windowList()
        : workspace.windows;
    for (var i = 0; i < clients.length; i++) {{
        var cap = (typeof clients[i].caption === 'function')
            ? clients[i].caption()
            : clients[i].caption;
        if (cap === {safe_title}) {{
            clients[i].frameGeometry = Qt.rect(
                {screen.left}, {screen.top}, {screen.width}, {screen.height}
            );
        }}
    }}
    """

    # Use delete=False so KWin can still read the file after loadScript() returns.
    # Manual cleanup in finally to ensure no leftover temp files on any code path.
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(js_code)
            tmp_path = tmp.name

        with open_dbus_connection() as router:
            proxy = Proxy(DBusKwinScripting6(), router)
            # Unload any leftover script from a previous run before loading fresh.
            try:
                proxy.unload_script(plugin_name="normcap_positioning")
            except Exception as exc:
                logger.debug(
                    "kwin6: unload_script failed (expected on first run): %s", exc
                )
            response = proxy.load_script(
                script_file=tmp_path, plugin_name="normcap_positioning"
            )
            if response[0] < 0:
                raise RuntimeError(  # noqa: TRY301
                    f"KWin loadScript returned error code: {response[0]}"
                )
            proxy.start()

    except Exception:
        logger.warning("Failed to move window via KWin Plasma 6 scripting!")
        logger.debug("KWin Plasma 6 scripting exception details:", exc_info=True)
    finally:
        if tmp_path is not None:
            Path(tmp_path).unlink(missing_ok=True)
