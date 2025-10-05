import logging
import os
import sys
from pathlib import Path

from PySide6 import QtGui

logger = logging.getLogger(__name__)

# TODO: Reconsider having different system_info.py per feature.


def get_resources_path() -> Path:
    return Path(__file__).resolve().parents[1] / "resources"


def has_wayland_display_manager() -> bool:
    if sys.platform != "linux" and "bsd" not in sys.platform:
        return False

    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    has_wayland_display_env = bool(os.environ.get("WAYLAND_DISPLAY", ""))
    return "wayland" in xdg_session_type or has_wayland_display_env


def is_flatpak() -> bool:
    if sys.platform != "linux" and "bsd" not in sys.platform:
        return False
    return os.getenv("FLATPAK_ID") is not None


def is_dbus_service_running() -> bool:
    # TODO: Improve dbus service check.
    # E.g. try to call the following async (to still be able to process the request)
    # dbus-send --session --print-reply --dest=com.github.dynobo.normcap_dev \
    #    /com/github/dynobo/normcap_dev org.freedesktop.DBus.Introspectable.Introspect
    app = QtGui.QGuiApplication.instance()
    if not app:
        return False

    service = getattr(app, "dbus_service", None)
    return getattr(service, "_registered", False)
