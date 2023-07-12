import os
import subprocess
from pathlib import Path

import pytest
from PySide6 import QtGui, QtWidgets

from normcap.gui import notification
from normcap.gui.models import Capture, CaptureMode, Rect


@pytest.mark.parametrize(
    ("ocr_applied_magic", "ocr_text", "output_title", "output_text"),
    [
        ("SingleLineMagic", "", "Nothing captured", "Please try again"),
        (
            "ParagraphMagic",
            f"P1{os.linesep*2}P2{os.linesep*2}P3",
            "3 paragraphs",
            "P1 P2 P3",
        ),
        ("ParagraphMagic", "P1", "1 paragraph ", "P1"),
        ("EmailMagic", "a@aa.de, b@bb.de", "2 emails", "a@aa.de, b@bb.de"),
        (
            "SingleLineMagic",
            f"{'a'*15} {'b'*15} {'c'*15}",
            "3 words ",
            f"{'a'*15} {'b'*15} [...]",
        ),
        (
            "MultiLineMagic",
            f"L1{os.linesep}L2{os.linesep}L3{os.linesep}L4",
            "4 lines",
            "L1 L2 L3 L4",
        ),
        (
            "UrlMagic",
            f"www.aaa.de{os.linesep}www.bbb.de",
            "2 URLs",
            "www.aaa.de www.bbb.de",
        ),
        ("UnknownMagic", "W1 W2 W3", "", "W1 W2 W3"),
        ("RAW", f"W1 W2{os.linesep}W3", "8 chars", "W1 W2 W3"),
    ],
)
def test_compose_notification(ocr_applied_magic, ocr_text, output_title, output_text):
    # GIVEN a Notifier
    #   and an OCR capture with a certain results
    notifier = notification.Notifier(None)
    capture = Capture(
        ocr_text=ocr_text,
        ocr_applied_magic=ocr_applied_magic,
        mode=CaptureMode.PARSE if ocr_applied_magic != "RAW" else CaptureMode.RAW,
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
    notifier._send_via_qt_tray("Title", "Message")

    # THEN we expect no exception (it's hard to test, if the notification is shown)


def test_send_notification(monkeypatch):
    """Test which method is used to send notification under certain conditions."""

    # GIVEN a Notifier (with mocked notification methods)
    notifier = notification.Notifier(None)

    result = []

    def mocked_libnotify(cls, title, message):
        result.append({"title": title, "message": message, "method": "libnotify"})

    def mocked_qt_tray(cls, title, message):
        result.append({"title": title, "message": message, "method": "qt_tray"})

    monkeypatch.setattr(notification.Notifier, "_send_via_libnotify", mocked_libnotify)
    monkeypatch.setattr(notification.Notifier, "_send_via_qt_tray", mocked_qt_tray)

    capture = Capture(
        ocr_text="text",
        ocr_applied_magic="SingleLineMagic",
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
