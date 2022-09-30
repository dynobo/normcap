import pytest

from normcap import clipboard


# pylint: disable=protected-access
@pytest.mark.parametrize(
    "wayland_display,xdg_session_type,result",
    [
        ("Wayland", "", True),
        ("", "Gnome Wayland", True),
        ("Wayland", "Gnome Wayland", True),
        ("X11", "Gnome Wayland", True),
        ("X11", "Gnome Shell", False),
    ],
)
def test_is_wayland_display_manager(
    wayland_display, xdg_session_type, result, monkeypatch
):
    def mocked_environ_get(var, _):
        if var == "WAYLAND_DISPLAY":
            return wayland_display
        elif var == "XDG_SESSION_TYPE":
            return xdg_session_type

    monkeypatch.setattr(clipboard.linux.os.environ, "get", mocked_environ_get)
    assert clipboard.linux._is_wayland_display_manager() == result
