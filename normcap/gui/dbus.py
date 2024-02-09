import json
import logging
import os
import tempfile
import traceback

from jeepney.io.blocking import Proxy, open_dbus_connection
from jeepney.wrappers import Message, MessageGenerator, new_method_call

from normcap.gui.models import Rect

logger = logging.getLogger(__name__)


class DBusShell(MessageGenerator):
    interface = "org.gnome.Shell"

    def __init__(
        self, object_path: str = "/org/gnome/Shell", bus_name: str = "org.gnome.Shell"
    ) -> None:
        super().__init__(object_path=object_path, bus_name=bus_name)

    def eval_(self, script: str) -> Message:
        return new_method_call(self, "Eval", "s", (script,))


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

    def move_resize(  # noqa: PLR0913
        self, win_id: int, x: int, y: int, width: int, height: int
    ) -> Message:
        return new_method_call(
            self, "MoveResize", "uiiuu", (win_id, x, y, width, height)
        )


def move_window_via_gnome_shell_eval(title_id: str, position: Rect) -> bool:
    """Move currently active window to a certain position.

    This is a workaround for not being able to reposition windows on wayland.
    It only works on Gnome Shell.

    Args:
        title_id: Window title (has to be unique)
        position: Target geometry

    Returns:
        If call was successful
    """
    logger.debug(
        "Moving window '%s' to %s via org.gnome.Shell.Eval", title_id, position
    )
    js_code = f"""
    const GLib = imports.gi.GLib;
    global.get_window_actors().forEach(function (w) {{
        var mw = w.meta_window;
        if (mw.get_title() == "{title_id}") {{
            mw.move_resize_frame(
                0,
                {position.left},
                {position.top},
                {position.width},
                {position.height}
            );
        }}
    }});
    """
    try:
        with open_dbus_connection() as router:
            proxy = Proxy(DBusShell(), router)
            response = proxy.eval_(script=js_code)
        if not response[0]:
            raise RuntimeError("DBus response was not OK!")  # noqa: TRY301
    except Exception as exc:
        logger.warning("Failed to move window via org.gnome.Shell.Eval!")
        logger.debug("".join(traceback.format_exception(exc)).strip())
        return False
    else:
        return True


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
            logger.debug("".join(traceback.format_exception(exc)).strip())
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
    except Exception as exc:
        logger.warning("Failed to move window via org.gnome.Shell.extensions.windows!")
        logger.debug("".join(traceback.format_exception(exc)).strip())
        logger.warning(
            "If you experience issues with NormCap's in a multi monitor setting, "
            "try installing the Gnome Shell Extension 'Window Calls' "
            "from https://extensions.gnome.org/extension/4724/window-calls/"
        )
        return False
    else:
        return True
