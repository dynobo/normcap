import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from PySide6 import QtWidgets

from normcap.detection.models import TextDetector, TextType
from normcap.gui import notification


@pytest.mark.parametrize(
    ("text", "text_type", "text_detector", "output_title", "output_text"),
    [
        (
            "",
            TextType.SINGLE_LINE,
            TextDetector.OCR_PARSED,
            "Nothing captured",
            "Please try again",
        ),
        (
            f"P1{os.linesep * 2}P2{os.linesep * 2}P3",
            TextType.PARAGRAPH,
            TextDetector.OCR_PARSED,
            "3 paragraphs",
            "P1 P2 P3",
        ),
        (
            "P1",
            TextType.PARAGRAPH,
            TextDetector.OCR_PARSED,
            "1 paragraph ",
            "P1",
        ),
        (
            "a@aa.de, b@bb.de",
            TextType.MAIL,
            TextDetector.OCR_PARSED,
            "2 emails",
            "a@aa.de, b@bb.de",
        ),
        (
            f"{'a' * 15} {'b' * 15} {'c' * 15}",
            TextType.SINGLE_LINE,
            TextDetector.OCR_PARSED,
            "3 words ",
            f"{'a' * 15} {'b' * 15} […]",
        ),
        (
            f"L1{os.linesep}L2{os.linesep}L3{os.linesep}L4",
            TextType.MULTI_LINE,
            TextDetector.OCR_PARSED,
            "4 lines",
            "L1 L2 L3 L4",
        ),
        (
            f"www.aaa.de{os.linesep}www.bbb.de",
            TextType.URL,
            TextDetector.OCR_PARSED,
            "2 URLs",
            "www.aaa.de www.bbb.de",
        ),
        (
            "W1 W2 W3",
            "UnknownTextType",
            TextDetector.OCR_PARSED,
            "",
            "W1 W2 W3",
        ),
        (
            f"W1 W2{os.linesep}W3",
            "RAW",
            TextDetector.OCR_PARSED,
            "8 characters",
            "W1 W2 W3",
        ),
        (
            "www.aaa.de",
            TextType.URL,
            TextDetector.QR,
            "1 QR code",
            "www.aaa.de",
        ),
        (
            f"W1{os.linesep}W2{os.linesep}W3",
            TextType.URL,
            TextDetector.QR_AND_BARCODE,
            "3 codes",
            "W1 W2 W3",
        ),
    ],
)
def test_compose_notification(
    text, text_type, text_detector, output_title, output_text
):
    # GIVEN a Notifier and a certain input
    # WHEN the notification is composed
    title, text = notification._compose_notification(
        text=text, result_type=text_type, detector=text_detector
    )

    # THEN certain title and text should be used
    assert output_title in title
    assert output_text in text


def test_send_via_libnotify(monkeypatch):
    # GIVEN a Notification object (and a mocked Popen)
    notifier = notification.Notifier(None)

    cmd_args = []

    def popen_decorator(func):
        def decorated_popen(cmd: list[str], **kwargs):
            cmd_args.extend(cmd)
            return func(["echo", "test"], **kwargs)

        return decorated_popen

    monkeypatch.setattr(subprocess, "Popen", popen_decorator(subprocess.Popen))

    # WHEN a notification is sent via the libnotify cli tool
    notifier._send_via_libnotify(
        title="Title", message="Message", text="text", text_type=TextType.SINGLE_LINE
    )

    # THEN the command that gets executed via Popen should be in the specific format
    #    and the icon image should exist
    assert cmd_args[0] == "notify-send"
    assert cmd_args[1].startswith("--icon=")
    assert cmd_args[2] == "--app-name=NormCap"
    assert cmd_args[3] == "--action=Open in Editor"
    assert cmd_args[4] == "--transient"
    assert cmd_args[5] == "--wait"
    assert cmd_args[6] == "Title"
    assert cmd_args[7] == "Message"

    icon = cmd_args[1].removeprefix("--icon=")
    assert Path(icon).exists()


@pytest.mark.gui
def test_send_via_qt_tray(qtbot):
    """Only tests if no exception occurs."""
    # GIVEN a Notification object
    #    with a QSystemTrayIcon as parent
    tray = QtWidgets.QSystemTrayIcon()
    notifier = notification.Notifier(tray)

    # WHEN a notification is sent via QT (QSystemTrayIcon)
    notifier._send_via_qt_tray(
        title="Title", message="Message", text=None, text_type=None
    )

    # THEN we expect no exception (it's hard to test, if the notification is shown)


@pytest.mark.gui
def test_send_via_qt_tray_without_qsystemtrayicon_parent_raises(qtbot):
    """Only tests if no exception occurs."""
    # GIVEN a Notification object
    #    without a QSystemTrayIcon as parent
    tray = QtWidgets.QMainWindow()
    notifier = notification.Notifier(tray)

    # WHEN a notification is sent via QT (QSystemTrayIcon)
    with pytest.raises(TypeError, match="QSystemTrayIcon"):
        notifier._send_via_qt_tray(
            title="Title", message="Message", text=None, text_type=None
        )

    # THEN we expect an exception, as the parent has to be a QSystemTrayIcon


@pytest.mark.gui
def test_send_via_qt_tray_handles_message_click(monkeypatch, qtbot):
    """Test if the click-on-notification signal get's reconnect."""

    # GIVEN a Notification object
    #    with a QSystemTrayIcon as parent
    #    and a mocked on message clicked handler
    tray = QtWidgets.QSystemTrayIcon()

    open_ocr_result_calls = []

    def mocked_open_ocr_result(**kwargs):
        open_ocr_result_calls.append(kwargs)

    monkeypatch.setattr(notification, "_open_ocr_result", mocked_open_ocr_result)

    notifier = notification.Notifier(tray)

    # WHEN a notification is send via QT
    #   and it is clicked
    notification_data = {
        "title": "Title",
        "message": "Message",
        "text": "text_1",
        "text_type": "TextType_1",
    }
    notifier._send_via_qt_tray(**notification_data)
    notifier.parent().messageClicked.emit()

    # THEN the mocked click handler function should get called exactly once
    #    and with the expected kwargs
    assert len(open_ocr_result_calls) == 1
    assert open_ocr_result_calls[0]["text"] == notification_data["text"]
    assert open_ocr_result_calls[0]["text_type"] == notification_data["text_type"]


@pytest.mark.gui
def test_send_via_qt_tray_reconnects_signal(monkeypatch, qtbot):
    """Test if the click-on-notification signal get's reconnect."""

    # GIVEN a Notification object
    #    with a QSystemTrayIcon as parent
    #    and a mocked on message clicked handler
    #    and a first notification sent via QT
    tray = QtWidgets.QSystemTrayIcon()

    open_ocr_result_calls = []

    def mocked_open_ocr_result(**kwargs):
        open_ocr_result_calls.append(kwargs)

    monkeypatch.setattr(notification, "_open_ocr_result", mocked_open_ocr_result)

    notifier = notification.Notifier(tray)
    notifier._send_via_qt_tray(
        title="Title",
        message="Message",
        text="text_1",
        text_type="TextType_1",
    )

    # WHEN a subsequent notification is sent via QT
    #   and it is clicked
    notification_data = {
        "title": "Title",
        "message": "Message",
        "text": "text_2",
        "text_type": "TextType_2",
    }
    notifier._send_via_qt_tray(**notification_data)
    notifier.parent().messageClicked.emit()

    # THEN the mocked onclick handler function should be called exactly once
    #   and only contain the kwargs from the second notification.
    #   because the first messageClick handler got cleared
    assert len(open_ocr_result_calls) == 1
    assert open_ocr_result_calls[0]["text"] == notification_data["text"]
    assert open_ocr_result_calls[0]["text_type"] == notification_data["text_type"]


@pytest.mark.parametrize(
    ("platform", "has_libnotify", "expected_method"),
    [
        ("linux", False, "qt"),
        ("linux", True, "libnotify"),
        ("win32", True, "qt"),
        ("win32", False, "qt"),
        ("darwin", True, "qt"),
    ],
)
def test_send_notification(monkeypatch, platform, has_libnotify, expected_method):
    """Test which method is used to send notification under certain conditions."""

    # GIVEN a Notifier (with mocked notification methods)
    notifier = notification.Notifier(None)

    result = []

    def mocked_libnotify(cls, title, message, text, text_type):
        result.append(
            {
                "title": title,
                "message": message,
                "method": "libnotify",
                "text": text,
                "text_type": text_type,
            }
        )

    def mocked_qt_tray(cls, title, message, text, text_type):
        result.append(
            {
                "title": title,
                "message": message,
                "method": "qt",
                "text": text,
                "text_type": text_type,
            }
        )

    monkeypatch.setattr(notification.Notifier, "_send_via_libnotify", mocked_libnotify)
    monkeypatch.setattr(notification.Notifier, "_send_via_qt_tray", mocked_qt_tray)

    text = "text"
    text_type = TextType.SINGLE_LINE
    detector = TextDetector.OCR_PARSED

    # WHEN a notification is send on a certain platform and w/ or w/o libnotify
    monkeypatch.setattr(notification.sys, "platform", platform)
    monkeypatch.setattr(notification.shutil, "which", lambda _: has_libnotify)
    notifier._send_notification(text=text, result_type=text_type, detector=detector)

    # THEN QT should be used to send the notification with a certain content
    # and with the expected method
    assert result[-1]["method"] == expected_method
    assert result[-1]["title"] == "1 word captured"
    assert result[-1]["message"] == "text"
    assert result[-1]["text"] == text
    assert result[-1]["text_type"] == text_type


@pytest.mark.parametrize(
    ("text", "text_type", "expected_urls"),
    [
        ("1@test.tld", TextType.MAIL, ["mailto:1@test.tld"]),
        (
            "1@test.tld, 2@test.tld",
            TextType.MAIL,
            ["mailto:1@test.tld;2@test.tld"],
        ),
        ("http://1.test.ltd", TextType.URL, ["http://1.test.ltd"]),
        (
            "http://1.test.ltd \n http://2.test.ltd",
            TextType.URL,
            ["http://1.test.ltd", "http://2.test.ltd"],
        ),
        (
            "test test\ntest",
            TextType.PARAGRAPH,
            [(Path(tempfile.gettempdir()) / "normcap_temporary_result.txt").as_uri()],
        ),
        (
            "test",
            TextType.SINGLE_LINE,
            [(Path(tempfile.gettempdir()) / "normcap_temporary_result.txt").as_uri()],
        ),
        (
            "test\ntest",
            TextType.MULTI_LINE,
            [(Path(tempfile.gettempdir()) / "normcap_temporary_result.txt").as_uri()],
        ),
        (
            "raw test",
            None,
            [(Path(tempfile.gettempdir()) / "normcap_temporary_result.txt").as_uri()],
        ),
    ],
)
def test_open_ocr_result(monkeypatch, text, text_type, expected_urls):
    # GIVEN a mocked Qt openUrl method
    urls = []

    def mocked_openurl(url):
        return urls.append(url)

    monkeypatch.setattr(notification.QtGui.QDesktopServices, "openUrl", mocked_openurl)

    # WHEN the function is called with certain text and TextType
    notification._open_ocr_result(text=text, text_type=text_type)

    # THEN the expected urls should be in the format so openUrl would result in the
    #   correct action
    #   and in case of a text file was generated, it should contain the detected text.
    assert urls == expected_urls
    if urls[0].toString().startswith("file://"):
        tempfile_text = Path(urls[0].toLocalFile()).read_text()
        assert tempfile_text == text
