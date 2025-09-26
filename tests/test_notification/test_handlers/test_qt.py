import pytest
from PySide6 import QtWidgets

from normcap import notification
from normcap.notification.models import NotificationAction


@pytest.mark.gui
def test_notify(qapp):
    """Only tests if no exception occurs."""
    # GIVEN a QT app with a QSystemTrayIcon as child
    # QtWidgets.QSystemTrayIcon(parent=qapp)
    tray = qapp.findChild(QtWidgets.QSystemTrayIcon)
    if not tray:
        tray = QtWidgets.QSystemTrayIcon(parent=qapp)

    # WHEN a notification is send via QT (QSystemTrayIcon)
    result = notification.handlers.qt.notify(
        title="Title", message="Message", actions=None
    )

    # THEN result status should be ok
    assert result is True


@pytest.mark.gui
def test_notify_without_qsystemtrayicon_raises(monkeypatch, qapp):
    """Only tests if no exception occurs."""
    # GIVEN an qt app without a QSystemTrayIcon
    monkeypatch.setattr(qapp, "findChild", lambda *args: None)

    # WHEN a notification is send
    # THEN a runtime error is raised
    with pytest.raises(RuntimeError, match="QSystemTrayIcon"):
        _ = notification.handlers.qt.notify(
            title="Title",
            message="Message",
            actions=None,
        )


@pytest.mark.gui
def test_notify_runs_action_callback(monkeypatch, qtbot, qapp):
    """Test if the click-on-notification signal gets reconnect."""
    # GIVEN a QT app with a QSystemTrayIcon
    tray = qapp.findChild(QtWidgets.QSystemTrayIcon)
    if not tray:
        tray = QtWidgets.QSystemTrayIcon(parent=qapp)

    # WHEN a notification with an action callback is send
    #   and it is clicked
    callback_result = []

    result = notification.handlers.qt.notify(
        title="Title",
        message="Message",
        actions=[
            # TODO: Also test notification func args
            NotificationAction(
                label="Action", func=lambda args: callback_result.append(1), args=[]
            )
        ],
    )
    tray.messageClicked.emit()

    # THEN the action callback should get called exactly once
    assert result is True
    assert callback_result == [1]


@pytest.mark.gui
def test_notify_reconnects_signal(monkeypatch, qapp, qtbot):
    """Test if the click-on-notification signal get's reconnect."""

    # GIVEN a QT app with a QSystemTrayIcon
    #    and a first notification sent
    tray = qapp.findChild(QtWidgets.QSystemTrayIcon)
    if not tray:
        tray = QtWidgets.QSystemTrayIcon(parent=qapp)

    callback_result = []
    result = notification.handlers.qt.notify(
        title="Title",
        message="Message",
        actions=None,
    )
    assert result is True
    assert callback_result == []

    # WHEN a subsequent notification is send
    #   and it is clicked
    result = notification.handlers.qt.notify(
        title="Title",
        message="Message",
        actions=[
            # TODO: Also test notification func args
            NotificationAction(
                label="Action", func=lambda args: callback_result.append(1), args=[]
            )
        ],
    )
    tray.messageClicked.emit()

    # THEN the action callback of the second notifcation should have been called once
    #   because the action callback of the first notification got cleared
    assert result is True
    assert callback_result == [1]
