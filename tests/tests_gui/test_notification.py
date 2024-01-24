import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from PySide6 import QtGui, QtWidgets

from normcap.gui import notification
from normcap.gui.models import Capture, CaptureMode, Rect
from normcap.ocr.structures import Transformer


@pytest.mark.parametrize(
    ("ocr_transform", "ocr_text", "output_title", "output_text"),
    [
        (Transformer.SINGLE_LINE, "", "Nothing captured", "Please try again"),
        (
            Transformer.PARAGRAPH,
            f"P1{os.linesep * 2}P2{os.linesep * 2}P3",
            "3 paragraphs",
            "P1 P2 P3",
        ),
        (Transformer.PARAGRAPH, "P1", "1 paragraph ", "P1"),
        (Transformer.MAIL, "a@aa.de, b@bb.de", "2 emails", "a@aa.de, b@bb.de"),
        (
            Transformer.SINGLE_LINE,
            f"{'a' * 15} {'b' * 15} {'c' * 15}",
            "3 words ",
            f"{'a' * 15} {'b' * 15} [...]",
        ),
        (
            Transformer.MULTI_LINE,
            f"L1{os.linesep}L2{os.linesep}L3{os.linesep}L4",
            "4 lines",
            "L1 L2 L3 L4",
        ),
        (
            Transformer.URL,
            f"www.aaa.de{os.linesep}www.bbb.de",
            "2 URLs",
            "www.aaa.de www.bbb.de",
        ),
        ("UnknownTransformer", "W1 W2 W3", "", "W1 W2 W3"),
        ("RAW", f"W1 W2{os.linesep}W3", "8 characters", "W1 W2 W3"),
    ],
)
def test_compose_notification(ocr_transform, ocr_text, output_title, output_text):
    # GIVEN a Notifier
    #   and an OCR capture with a certain results
    notifier = notification.Notifier(None)
    capture = Capture(
        ocr_text=ocr_text,
        ocr_transformer=ocr_transform,
        mode=CaptureMode.PARSE if ocr_transform != "RAW" else CaptureMode.RAW,
        image=QtGui.QImage(),
        screen=None,
        scale_factor=1,
        rect=Rect(0, 0, 10, 10),
    )

    # WHEN the notification is composed
    title, text = notifier._compose_notification(capture)

    # THEN certain title and text should be used
    assert output_title in title
    assert output_text in text


def test_send_via_libnotify(monkeypatch):
    # GIVEN a Notification object (and a mocked Popen)
    notifier = notification.Notifier(None)

    cmd_args = []

    def _mocked_popen(cmd: str, start_new_session: bool):
        cmd_args.extend(cmd)

    monkeypatch.setattr(subprocess, "Popen", _mocked_popen)

    # WHEN a notification is sent via the libnotify cli tool
    notifier._send_via_libnotify("Title", "Message")

    # THEN the command that gets executed via Popen should be in the specific format
    #    and the icon image should exist
    assert cmd_args[0] == "notify-send"
    assert cmd_args[1].startswith("--icon=")
    assert cmd_args[2] == "--app-name=NormCap"
    assert cmd_args[3] == "Title"
    assert cmd_args[4] == "Message"

    icon = cmd_args[1].removeprefix("--icon=")
    assert Path(icon).exists()


@pytest.mark.gui()
def test_send_via_qt_tray(qtbot):
    """Only tests if no exception occurs."""
    # GIVEN a Notification object
    #    with a QSystemTrayIcon as parent
    tray = QtWidgets.QSystemTrayIcon()
    notifier = notification.Notifier(tray)

    # WHEN a notification is sent via QT (QSystemTrayIcon)
    notifier._send_via_qt_tray(
        title="Title", message="Message", ocr_text=None, ocr_transformer=None
    )

    # THEN we expect no exception (it's hard to test, if the notification is shown)


@pytest.mark.gui()
def test_send_via_qt_tray_without_qsystemtrayicon_parent_raises(qtbot):
    """Only tests if no exception occurs."""
    # GIVEN a Notification object
    #    without a QSystemTrayIcon as parent
    tray = QtWidgets.QMainWindow()
    notifier = notification.Notifier(tray)

    # WHEN a notification is sent via QT (QSystemTrayIcon)
    with pytest.raises(TypeError, match="QSystemTrayIcon"):
        notifier._send_via_qt_tray(
            title="Title", message="Message", ocr_text=None, ocr_transformer=None
        )

    # THEN we expect an exception, as the parent has to be a QSystemTrayIcon


@pytest.mark.gui()
def test_send_via_qt_tray_handles_message_click(monkeypatch, qtbot):
    """Test if the click-on-notification signal get's reconnect."""

    # GIVEN a Notification object
    #    with a QSystemTrayIcon as parent
    #    and a mocked on message clicked handler
    tray = QtWidgets.QSystemTrayIcon()

    open_ocr_result_calls = []

    def mocked_open_ocr_result(cls, **kwargs):
        open_ocr_result_calls.append(kwargs)

    monkeypatch.setattr(
        notification.Notifier, "_open_ocr_result", mocked_open_ocr_result
    )

    notifier = notification.Notifier(tray)

    # WHEN a notification is send via QT
    #   and it is clicked
    notification_data = {
        "title": "Title",
        "message": "Message",
        "ocr_text": "text_1",
        "ocr_transformer": "transformer_1",
    }
    notifier._send_via_qt_tray(**notification_data)
    notifier.parent().messageClicked.emit()

    # THEN the mocked click handler function should get called exactly once
    #    and with the expected kwargs
    assert len(open_ocr_result_calls) == 1
    assert open_ocr_result_calls[0]["text"] == notification_data["ocr_text"]
    assert (
        open_ocr_result_calls[0]["applied_transformer"]
        == notification_data["ocr_transformer"]
    )


@pytest.mark.gui()
def test_send_via_qt_tray_reconnects_signal(monkeypatch, qtbot):
    """Test if the click-on-notification signal get's reconnect."""

    # GIVEN a Notification object
    #    with a QSystemTrayIcon as parent
    #    and a mocked on message clicked handler
    #    and a first notification sent via QT
    tray = QtWidgets.QSystemTrayIcon()

    open_ocr_result_calls = []

    def mocked_open_ocr_result(cls, **kwargs):
        open_ocr_result_calls.append(kwargs)

    monkeypatch.setattr(
        notification.Notifier, "_open_ocr_result", mocked_open_ocr_result
    )

    notifier = notification.Notifier(tray)
    notifier._send_via_qt_tray(
        title="Title",
        message="Message",
        ocr_text="text_1",
        ocr_transformer="transformer_1",
    )

    # WHEN a subsequent notification is sent via QT
    #   and it is clicked
    notification_data = {
        "title": "Title",
        "message": "Message",
        "ocr_text": "text_2",
        "ocr_transformer": "transformer_2",
    }
    notifier._send_via_qt_tray(**notification_data)
    notifier.parent().messageClicked.emit()

    # THEN the mocked onclick handler function should be called exactly once
    #   and only contain the kwargs from the second notification.
    #   because the first messageClick handler got cleared
    assert len(open_ocr_result_calls) == 1
    assert open_ocr_result_calls[0]["text"] == notification_data["ocr_text"]
    assert (
        open_ocr_result_calls[0]["applied_transformer"]
        == notification_data["ocr_transformer"]
    )


def test_send_notification(monkeypatch):
    """Test which method is used to send notification under certain conditions."""

    # GIVEN a Notifier (with mocked notification methods)
    notifier = notification.Notifier(None)

    result = []

    def mocked_libnotify(cls, title, message):
        result.append({"title": title, "message": message, "method": "libnotify"})

    def mocked_qt_tray(cls, title, message, ocr_text, ocr_transformer):
        result.append(
            {
                "title": title,
                "message": message,
                "method": "qt_tray",
                "ocr_text": ocr_text,
                "ocr_transformer": ocr_transformer,
            }
        )

    monkeypatch.setattr(notification.Notifier, "_send_via_libnotify", mocked_libnotify)
    monkeypatch.setattr(notification.Notifier, "_send_via_qt_tray", mocked_qt_tray)

    capture = Capture(
        ocr_text="text",
        ocr_transformer=Transformer.SINGLE_LINE,
        mode=CaptureMode.PARSE,
        image=QtGui.QImage(),
        screen=None,
        scale_factor=1,
        rect=Rect(0, 0, 10, 10),
    )

    # WHEN a notification signal is emitted on a linux system _without_ libnotify
    monkeypatch.setattr(notification.sys, "platform", "linux")
    monkeypatch.setattr(notification.shutil, "which", lambda _: False)

    notifier._send_notification(capture)

    # THEN QT should be used to send the notification with a certain content
    assert result[-1]["method"] == "qt_tray"
    assert result[-1]["title"] == "1 word captured"
    assert result[-1]["message"] == "text"
    assert result[-1]["ocr_text"] == capture.ocr_text
    assert result[-1]["ocr_transformer"] == capture.ocr_transformer

    # WHEN a notification signal is emitted on a system _with_ libnotify
    monkeypatch.setattr(notification.sys, "platform", "linux")
    monkeypatch.setattr(notification.shutil, "which", lambda _: True)

    notifier._send_notification(capture)

    # THEN libnotify should be used to send the notification with a certain content
    assert result[-1]["title"] == "1 word captured"
    assert result[-1]["message"] == "text"
    assert result[-1]["method"] == "libnotify"

    # WHEN a notification signal is emitted on a different system than linux
    #    and even if a binary libnotify is available
    monkeypatch.setattr(notification.sys, "platform", "win32")
    monkeypatch.setattr(notification.shutil, "which", lambda _: True)

    notifier._send_notification(capture)

    # THEN QT should be used to send the notification with a certain content
    assert result[-1]["title"] == "1 word captured"
    assert result[-1]["message"] == "text"
    assert result[-1]["method"] == "qt_tray"


@pytest.mark.parametrize(
    ("ocr_text", "applied_transformer", "expected_urls"),
    [
        ("1@test.tld", Transformer.MAIL, ["mailto:1@test.tld"]),
        ("1@test.tld, 2@test.tld", Transformer.MAIL, ["mailto:1@test.tld;2@test.tld"]),
        ("http://1.test.ltd", Transformer.URL, ["http://1.test.ltd"]),
        (
            "http://1.test.ltd \n http://2.test.ltd",
            Transformer.URL,
            ["http://1.test.ltd", "http://2.test.ltd"],
        ),
        (
            "test test\ntest",
            Transformer.PARAGRAPH,
            [(Path(tempfile.gettempdir()) / "normcap_temporary_result.txt").as_uri()],
        ),
        (
            "test",
            Transformer.SINGLE_LINE,
            [(Path(tempfile.gettempdir()) / "normcap_temporary_result.txt").as_uri()],
        ),
        (
            "test\ntest",
            Transformer.MULTI_LINE,
            [(Path(tempfile.gettempdir()) / "normcap_temporary_result.txt").as_uri()],
        ),
        (
            "raw test",
            None,
            [(Path(tempfile.gettempdir()) / "normcap_temporary_result.txt").as_uri()],
        ),
    ],
)
def test_open_ocr_result(monkeypatch, ocr_text, applied_transformer, expected_urls):
    # GIVEN a mocked Qt openUrl method
    urls = []

    def mocked_openurl(url):
        return urls.append(url)

    monkeypatch.setattr(notification.QtGui.QDesktopServices, "openUrl", mocked_openurl)

    # WHEN the function is called with certain text and transformer
    notification.Notifier._open_ocr_result(
        text=ocr_text, applied_transformer=applied_transformer
    )

    # THEN the expected urls should be in the format so openUrl would result in the
    #   correct action
    #   and in case of a text file was generated, it should contain the detected text.
    assert urls == expected_urls
    if urls[0].toString().startswith("file://"):
        tempfile_text = Path(urls[0].toLocalFile()).read_text()
        assert tempfile_text == ocr_text
