import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable

import pytest

from normcap.detection.models import TextDetector, TextType
from normcap.gui import notification
from normcap.notification.handlers import notify_send, qt


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

    # THEN we expect no exception (it's hard to test, if the notification is shown)

    # THEN we expect an exception, as the parent has to be a QSystemTrayIcon


@pytest.mark.parametrize(
    ("platform", "has_notify_send", "expected_method"),
    [
        ("linux", False, "qt"),
        ("linux", True, "notify_send"),
        ("win32", True, "qt"),
        ("win32", False, "qt"),
        ("darwin", True, "qt"),
    ],
)
def test_send_notification(monkeypatch, platform, has_notify_send, expected_method):
    """Test which method is used to send notification under certain conditions."""

    # GIVEN a Notifier (with mocked notification methods)
    result = []

    def mocked_notify_send(title, message, action_label, action_callback):
        result.append(
            {
                "title": title,
                "message": message,
                "method": "notify_send",
                "action_label": action_label,
                "action_callback": action_callback,
            }
        )

    def mocked_qt(title, message, action_label, action_callback):
        result.append(
            {
                "title": title,
                "message": message,
                "method": "qt",
                "action_label": action_label,
                "action_callback": action_callback,
            }
        )

    monkeypatch.setattr(notify_send, "notify", mocked_notify_send)
    monkeypatch.setattr(qt, "notify", mocked_qt)

    text = "text"
    text_type = TextType.SINGLE_LINE
    detector = TextDetector.OCR_PARSED

    # WHEN a notification is send on a certain platform and w/ or w/o libnotify
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(shutil, "which", lambda _: has_notify_send)

    notification.send_notification(text=text, text_type=text_type, detector=detector)

    # THEN QT should be used to send the notification with a certain content
    # and with the expected method
    assert result[-1]["method"] == expected_method
    assert result[-1]["title"] == "1 word captured"
    assert result[-1]["message"] == "text"
    assert result[-1]["action_label"]
    assert isinstance(result[-1]["action_callback"], Callable)


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
