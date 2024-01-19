import pytest

from normcap.clipboard import system_info


@pytest.mark.parametrize(
    ("xdg_session_type", "wayland_display", "platform", "expected_result"),
    [
        ("wayland", "wayland", "linux", True),
        ("wayland", "", "linux", True),
        ("", "wayland", "linux", True),
        ("", "", "linux", False),
        ("wayland", "wayland", "win32", False),
        ("wayland", "wayland", "darwin", False),
    ],
)
def test_os_has_wayland_display_manager(
    monkeypatch, xdg_session_type, wayland_display, platform, expected_result
):
    monkeypatch.setenv("XDG_SESSION_TYPE", xdg_session_type)
    monkeypatch.setenv("WAYLAND_DISPLAY", wayland_display)
    monkeypatch.setattr(system_info.sys, "platform", platform)

    assert system_info.os_has_wayland_display_manager() == expected_result


@pytest.mark.parametrize(
    ("platform", "desktop", "expected_result"),
    [
        ("linux", "awesome", True),
        ("linux", "gnome", False),
        ("win32", "awesome", False),
        ("darwin", "awesome", False),
    ],
)
def test_os_has_awesome_wm(monkeypatch, platform, desktop, expected_result):
    with monkeypatch.context() as m:
        m.setenv("XDG_CURRENT_DESKTOP", desktop)
        m.setattr(system_info.sys, "platform", platform)
        assert system_info.os_has_awesome_wm() == expected_result


@pytest.mark.parametrize(
    ("platform", "xdg_desktop", "gnome_desktop", "gnome_shell", "expected_result"),
    [
        ("linux", "gnome", "gnome", "/usr/bin/gnome-shell", "33.3.0"),
        ("linux", "kde", "", "/usr/bin/gnome-shell", ""),
        ("darwin", "", "", "", ""),
        ("darwin", "", "", "/usr/bin/gnome-shell", ""),
        ("win32", "", "", "", ""),
    ],
)
def test_get_gnome_version(
    platform, xdg_desktop, gnome_desktop, gnome_shell, expected_result, monkeypatch
):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", xdg_desktop)
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", gnome_desktop)
    monkeypatch.setattr(system_info.sys, "platform", platform)
    monkeypatch.setattr(
        system_info.shutil,
        "which",
        lambda x: gnome_shell if x == "gnome-shell" else None,
    )
    monkeypatch.setattr(
        system_info.subprocess, "check_output", lambda *_, **__: "GNOME Shell 33.3.0"
    )

    assert system_info.get_gnome_version() == expected_result
