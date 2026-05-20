import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from normcap.positioning.handlers import kwin6
from normcap.system import info
from normcap.system.models import DesktopEnvironment, Screen


def test_is_compatible_false_on_non_kde(monkeypatch):
    monkeypatch.setattr(info, "desktop_environment", lambda: DesktopEnvironment.GNOME)
    assert not kwin6.is_compatible()


def test_is_compatible_false_on_plasma5(monkeypatch):
    monkeypatch.setattr(info, "desktop_environment", lambda: DesktopEnvironment.KDE)
    monkeypatch.setattr(kwin6, "_get_plasma_major_version", lambda: 5)
    assert not kwin6.is_compatible()


def test_is_compatible_true_on_plasma6(monkeypatch):
    monkeypatch.setattr(info, "desktop_environment", lambda: DesktopEnvironment.KDE)
    monkeypatch.setattr(kwin6, "_get_plasma_major_version", lambda: 6)
    assert kwin6.is_compatible()


def test_is_compatible_false_when_version_unknown(monkeypatch):
    monkeypatch.setattr(info, "desktop_environment", lambda: DesktopEnvironment.KDE)
    monkeypatch.setattr(kwin6, "_get_plasma_major_version", lambda: None)
    assert not kwin6.is_compatible()


@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only D-Bus test")
def test_is_installed_returns_bool(monkeypatch):
    # is_installed() must return a bool without raising.
    # Skip actual D-Bus check — just verify it doesn't crash.
    result = kwin6.is_installed()
    assert isinstance(result, bool)


def _make_mock_router_class():
    class MockRouter:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return MockRouter


def test_move_writes_valid_js_and_calls_dbus(monkeypatch):
    """move() must write a temp JS file and invoke the KWin D-Bus scripting API."""
    written_js: list[str] = []
    load_script_args: list[tuple] = []

    class MockProxy:
        def __init__(self, gen, router):
            pass

        def unload_script(self, plugin_name):
            pass

        def load_script(self, script_file, plugin_name):
            written_js.append(Path(script_file).read_text())
            load_script_args.append((script_file, plugin_name))
            return (1,)

        def start(self):
            pass

    monkeypatch.setattr(kwin6, "open_dbus_connection", _make_mock_router_class())
    monkeypatch.setattr(kwin6, "Proxy", MockProxy)

    window = mock.MagicMock()
    window.windowTitle.return_value = "NormCap"
    screen = Screen(
        left=0, top=0, right=1919, bottom=1079, device_pixel_ratio=1.0, index=0
    )

    kwin6.move(window=window, screen=screen)

    assert written_js, "No JS was written to the temp file"
    assert "NormCap" in written_js[0]
    assert "frameGeometry" in written_js[0]


@pytest.mark.parametrize(
    "title",
    [
        'title with "double quotes"',
        "title with 'single quotes'",
        "title\nwith\nnewline",
        "title\\with\\backslash",
        "title\twith\ttab",
        "title with <script>alert(1)</script>",
    ],
)
def test_move_escapes_special_chars_in_title(monkeypatch, title):
    """Window titles with special characters must not break the generated JS literal."""
    written_js: list[str] = []

    class MockProxy:
        def __init__(self, gen, router):
            pass

        def unload_script(self, plugin_name):
            pass

        def load_script(self, script_file, plugin_name):
            written_js.append(Path(script_file).read_text())
            return (1,)

        def start(self):
            pass

    monkeypatch.setattr(kwin6, "open_dbus_connection", _make_mock_router_class())
    monkeypatch.setattr(kwin6, "Proxy", MockProxy)

    window = mock.MagicMock()
    window.windowTitle.return_value = title
    screen = Screen(left=0, top=0, right=99, bottom=99, device_pixel_ratio=1.0, index=0)

    kwin6.move(window=window, screen=screen)

    assert written_js, "No JS was written"
    js = written_js[0]

    # The title must appear as a properly JSON-encoded string literal.
    # json.dumps handles all special characters: quotes, backslashes, newlines, etc.
    expected_literal = json.dumps(title)
    assert expected_literal in js, (
        f"Expected JSON-encoded title {expected_literal!r} not found in JS:\n{js}"
    )


def test_move_does_not_raise_when_load_script_fails(monkeypatch):
    """move() must log a warning but not raise when KWin rejects the script.

    loadScript() returns a negative int on error (e.g. invalid path or
    KWin internal error). move() should log and return, not propagate.
    """

    class MockProxy:
        def __init__(self, gen, router):
            pass

        def unload_script(self, plugin_name):
            pass

        def load_script(self, script_file, plugin_name):
            return (-1,)  # negative = error

        def start(self):
            pass

    monkeypatch.setattr(kwin6, "open_dbus_connection", _make_mock_router_class())
    monkeypatch.setattr(kwin6, "Proxy", MockProxy)

    window = mock.MagicMock()
    window.windowTitle.return_value = "NormCap"
    screen = Screen(
        left=0, top=0, right=1919, bottom=1079, device_pixel_ratio=1.0, index=0
    )

    # Must not raise — move() catches exceptions and logs a warning
    kwin6.move(window=window, screen=screen)
