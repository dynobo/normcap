import shutil
import subprocess
import sys
import uuid

import pytest

from normcap.clipboard import system_info
from normcap.clipboard.handlers import wlclipboard


@pytest.mark.parametrize(
    ("platform", "wayland_display", "xdg_session_type", "gnome_version", "result"),
    [
        ("linux", "Wayland", "", "44", True),
        ("linux", "", "Gnome Wayland", "44", True),
        ("linux", "Wayland", "Gnome Wayland", "44", True),
        ("linux", "Wayland", "Gnome Wayland", "45.1", False),
        ("linux", "", "Gnome Shell", "44", False),
        ("linux", "", "", "44", False),
        ("win32", "Wayland", "Gnome Wayland", "", False),
        ("darwin", "Wayland", "Gnome Wayland", "", False),
    ],
)
def test_wlcopy_is_compatible(
    platform, wayland_display, xdg_session_type, gnome_version, result, monkeypatch
):
    monkeypatch.setenv("WAYLAND_DISPLAY", wayland_display)
    monkeypatch.setenv("XDG_SESSION_TYPE", xdg_session_type)
    monkeypatch.setattr(system_info.sys, "platform", platform)
    monkeypatch.setattr(system_info, "get_gnome_version", lambda *_: gnome_version)

    assert wlclipboard.is_compatible() == result


@pytest.mark.parametrize(
    ("platform", "has_wlcopy", "result"),
    [
        ("linux", True, True),
        ("linux", False, False),
    ],
)
def test_wlcopy_is_installed(platform, has_wlcopy, result, monkeypatch):
    monkeypatch.setattr(system_info.sys, "platform", platform)
    monkeypatch.setattr(
        wlclipboard.shutil, "which", lambda *args: "wl-copy" in args and has_wlcopy
    )

    assert wlclipboard.is_installed() == result


# ONHOLD: Check if wl-copy works on Gnome 45 without the need to click on notification.
# see https://github.com/bugaevc/wl-clipboard/issues/168
@pytest.mark.skipif(True, reason="Buggy in Gnome 45")
@pytest.mark.skipif(not shutil.which("wl-copy"), reason="Needs wl-copy")
@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_wlcopy_copy():
    text = f"this is a unique test {uuid.uuid4()}"

    wlclipboard.copy(text=text)

    with subprocess.Popen(
        ["wl-paste"],  # noqa: S603, S607
        stdout=subprocess.PIPE,
    ) as p:
        stdout = p.communicate()[0]
    clipped = stdout.decode("utf-8").strip()

    assert text == clipped


@pytest.mark.skipif(True, reason="Buggy in Gnome 45")
@pytest.mark.skipif(sys.platform == "linux", reason="Non-Linux specific test")
def test_wlcopy_copy_on_non_linux():
    with pytest.raises((FileNotFoundError, OSError)):
        wlclipboard.copy(text="this is a test")
