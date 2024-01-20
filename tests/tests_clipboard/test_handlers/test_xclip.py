import shutil
import subprocess
import sys
import uuid

import pytest

from normcap.clipboard import system_info
from normcap.clipboard.handlers import xclip


@pytest.mark.parametrize(
    ("platform", "wayland_display", "xdg_session_type", "has_xclip", "result"),
    [
        ("linux", "Wayland", "", True, True),
        ("linux", "", "Gnome Wayland", True, True),
        ("linux", "Wayland", "Gnome Wayland", True, True),
        ("linux", "", "Gnome Shell", True, True),
        ("linux", "", "", True, True),
        ("linux", "Wayland", "Gnome Wayland", False, True),
        ("win32", "Wayland", "Gnome Shell", False, False),
        ("win32", "Wayland", "Gnome Wayland", True, False),
        ("darwin", "Wayland", "Gnome Wayland", True, False),
    ],
)
def test_xclip_is_compatible(
    platform, wayland_display, xdg_session_type, has_xclip, result, monkeypatch
):
    monkeypatch.setenv("WAYLAND_DISPLAY", wayland_display)
    monkeypatch.setenv("XDG_SESSION_TYPE", xdg_session_type)

    monkeypatch.setattr(system_info.sys, "platform", platform)
    monkeypatch.setattr(
        xclip.shutil, "which", lambda *args: "xclip" in args and has_xclip
    )

    assert xclip.is_compatible() == result


@pytest.mark.skipif(not shutil.which("xclip"), reason="Needs xclip")
@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_xclip_copy():
    text = f"this is a unique test {uuid.uuid4()}"

    xclip.copy(text=text)

    with subprocess.Popen(
        ["xclip", "-selection", "clipboard", "-out"],  # noqa: S603, S607
        stdout=subprocess.PIPE,
    ) as p:
        stdout = p.communicate()[0]
    clipped = stdout.decode("utf-8").strip()

    assert text == clipped


@pytest.mark.skipif(sys.platform == "linux", reason="Non-Linux specific test")
def test_xclip_copy_on_non_linux():
    with pytest.raises((FileNotFoundError, OSError)):
        xclip.copy(text="this is a test")
