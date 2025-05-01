import json
import logging
import os
import tempfile
import traceback

from jeepney.io.blocking import Proxy, open_dbus_connection
from jeepney.wrappers import Message, MessageGenerator, new_method_call

from normcap.gui.models import Rect

logger = logging.getLogger(__name__)


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

    def get_title(self, win_id: int) -> Message:
        return new_method_call(self, "GetTitle", "u", (win_id,))

    def activate(self, win_id: int) -> Message:
        return new_method_call(self, "Activate", "u", (win_id,))

    def move_resize(
        self, win_id: int, x: int, y: int, width: int, height: int
    ) -> Message:
        return new_method_call(
            self, "MoveResize", "uiiuu", (win_id, x, y, width, height)
        )


def move_window_via_kde_kwin_scripting(title_id: str, position: Rect) -> bool:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on KDE.

    Args:
        title_id: Window title (has to be unique)
        position: Target geometry

    Returns:
        If call was successful
    """
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
            return False
        else:
            return True


def move_windows_via_window_calls_extension(title_id: str, position: Rect) -> bool:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on Gnome and requires the Gnome Shell Extension 'Window Calls'
    https://github.com/ickyicky/window-calls

    Args:
        title_id: Window title (has to be unique)
        position: Target geometry

    Returns:
        If call was successful
    """
    logger.debug(
        "Moving window '%s' to %s via org.gnome.Shell.extensions.windows",
        title_id,
        position,
    )
    try:
        with open_dbus_connection() as router:
            proxy = Proxy(DBusWindowCalls(), router)

            response = proxy.list_()
            all_windows = json.loads(response[0])
            normcap_windows = [w for w in all_windows if w["pid"] == os.getpid()]

            window_id = None
            for window in normcap_windows:
                # TODO: No need to check title, it's already in list!
                response = proxy.get_title(window["id"])
                window_title = response[0]
                if window_title == title_id:
                    window_id = window["id"]
                    break

            if not window_id:
                raise RuntimeError(  # noqa: TRY301
                    f"Could not retrieve window title: {response}"
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
        logger.warning(
            "Failed to move window via org.gnome.Shell.extensions.windows! "
            "If you experience issues with NormCap's position, e.g. in a multi monitor "
            "setting, try installing the Gnome Shell Extension 'Window Calls' "
            "from https://extensions.gnome.org/extension/4724/window-calls/"
        )
        # FIXME: Test availability via dbus call instead:
        # dbus-send --session --dest=org.gnome.Shell --type=method_call \
        # --print-reply /org/gnome/Shell/Extensions/Windowss \
        # org.freedesktop.DBus.Introspectable.Introspect
        return False
    else:
        return True
