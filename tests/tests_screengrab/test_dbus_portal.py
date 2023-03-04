import time

import pytest

from normcap.screengrab import ScreenshotRequestError, ScreenshotResponseError

# ONHOLD: Remove skip_on_gh's once gh-runners support portal.Screenshot w/o dialog
#       which is probably with Ubuntu 22.10+


@pytest.mark.gui()
@pytest.mark.skip_on_gh()
def test_synchronized_capture(qtbot, dbus_portal):
    result = dbus_portal._synchronized_capture(interactive=False)
    assert result


def test_synchronized_capture_triggers_timeout(monkeypatch, qtbot, dbus_portal):
    timeout = 1

    monkeypatch.setattr(dbus_portal, "TIMEOUT_SECONDS", timeout)
    monkeypatch.setattr(
        dbus_portal.OrgFreedesktopPortalScreenshot,
        "grab_full_desktop",
        lambda _: time.sleep(timeout + 0.1),
    )

    with pytest.raises(TimeoutError):
        _ = dbus_portal._synchronized_capture(interactive=False)


def test_synchronized_capture_triggers_request_error(monkeypatch, qtbot, dbus_portal):
    def _mocked_interface_call(*args):
        return dbus_portal.QtDBus.QDBusMessage()

    monkeypatch.setattr(
        dbus_portal.QtDBus.QDBusInterface, "call", _mocked_interface_call
    )
    with pytest.raises(ScreenshotRequestError):
        _ = dbus_portal._synchronized_capture(interactive=False)


@pytest.mark.gui()
@pytest.mark.skip_on_gh()
def test_synchronized_capture_triggers_response_error(monkeypatch, qtbot, dbus_portal):
    def _decorate_got_signal(method):
        def decorated_msg(cls, msg):
            args = msg.arguments()
            args[0] = 1  # set error code
            msg.setArguments(args)
            return method(cls, msg)

        return decorated_msg

    monkeypatch.setattr(
        dbus_portal.OrgFreedesktopPortalScreenshot,
        "got_signal",
        _decorate_got_signal(dbus_portal.OrgFreedesktopPortalScreenshot.got_signal),
    )
    with pytest.raises(ScreenshotResponseError):
        _ = dbus_portal._synchronized_capture(interactive=False)
