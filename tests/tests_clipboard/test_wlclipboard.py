import shutil
import subprocess
import sys
import uuid

import pytest

from normcap.clipboard.handlers import base, wlclipboard


@pytest.mark.parametrize(
    ("platform", "wayland_display", "xdg_session_type", "has_wlcopy", "result"),
    [
        ("linux", "Wayland", "", True, True),
        ("linux", "", "Gnome Wayland", True, True),
        ("linux", "Wayland", "Gnome Wayland", True, True),
        ("linux", "", "Gnome Shell", True, False),
        ("linux", "", "", True, False),
        ("linux", "Wayland", "Gnome Wayland", False, False),
        ("win32", "Wayland", "Gnome Wayland", True, False),
        ("darwin", "Wayland", "Gnome Wayland", True, False),
    ],
)
def test_wlcopy_is_compatible(
    platform, wayland_display, xdg_session_type, has_wlcopy, result, monkeypatch
):
    monkeypatch.setenv("WAYLAND_DISPLAY", wayland_display)
    monkeypatch.setenv("XDG_SESSION_TYPE", xdg_session_type)

    monkeypatch.setattr(base.sys, "platform", platform)
    monkeypatch.setattr(
        wlclipboard.shutil, "which", lambda *args: "wl-copy" in args and has_wlcopy
    )

    assert wlclipboard.WlCopyHandler().is_compatible == result


# ONHOLD: Check if wl-copy works on Gnome 45 without the need to click on notification.
# see https://github.com/bugaevc/wl-clipboard/issues/168
@pytest.mark.skipif(True, reason="Buggy in Gnome 45")
@pytest.mark.skipif(not shutil.which("wl-copy"), reason="Needs wl-copy")
@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_wlcopy_copy():
    text = f"this is a unique test {uuid.uuid4()}"

    result = wlclipboard.WlCopyHandler().copy(text=text)

    with subprocess.Popen(
        ["wl-paste"],  # noqa: S603, S607
        stdout=subprocess.PIPE,
    ) as p:
        stdout = p.communicate()[0]
    clipped = stdout.decode("utf-8").strip()

    assert result is True
    assert text == clipped


@pytest.mark.skipif(True, reason="Buggy in Gnome 45")
@pytest.mark.skipif(sys.platform == "linux", reason="Non-Linux specific test")
def test_wlcopy_copy_on_non_linux():
    result = wlclipboard.WlCopyHandler().copy(text="this is a test")
    assert result is False
