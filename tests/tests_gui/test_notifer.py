import os
import subprocess
from pathlib import Path

import pytest
from PySide6 import QtGui, QtWidgets

from normcap.gui import notifier
from normcap.gui.models import Capture, CaptureMode, Rect


@pytest.mark.parametrize(
    "ocr_applied_magic,ocr_text,output_title,output_text",
    (
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
    ),
)
def test_compose_notification(
    qtbot, ocr_applied_magic, ocr_text, output_title, output_text
):
    capture = Capture(
        ocr_text=ocr_text,
        ocr_applied_magic=ocr_applied_magic,
        mode=CaptureMode.PARSE if ocr_applied_magic != "RAW" else CaptureMode.RAW,
        image=QtGui.QImage(),
        screen=None,
        scale_factor=1,
        rect=Rect(0, 0, 10, 10),
    )
    notifi = notifier.Notifier(None)
    title, text = notifi._compose_notification(capture)
    assert output_title in title
    assert output_text in text


def test_send_via_libnotify(monkeypatch):
    def mocked_popen(cmd: str, start_new_session: bool):
        assert cmd[0] == "notify-send"
        assert cmd[1].startswith("--icon=")
        assert cmd[2] == "--app-name=NormCap"
        assert cmd[3] == "Titel"
        assert cmd[4] == "Message"

        icon = cmd[1].removeprefix("--icon=")
        assert Path(icon).exists()

    monkeypatch.setattr(subprocess, "Popen", mocked_popen)
    notifi = notifier.Notifier(None)
    notifi.send_via_libnotify("Titel", "Message")


def test_send_via_qt_tray(qtbot):
    """Only tests if no exception occurs."""
    tray = QtWidgets.QSystemTrayIcon()
    notifi = notifier.Notifier(tray)
    notifi.send_via_qt_tray("Titel", "Message")


def test_send_notification(monkeypatch):
    capture = Capture(
        ocr_text="text",
        ocr_applied_magic="SingleLineMagic",
        mode=CaptureMode.PARSE,
        image=QtGui.QImage(),
        screen=None,
        scale_factor=1,
        rect=Rect(0, 0, 10, 10),
    )

    result = []

    def mocked_libnotify(cls, title, message):
        result.append({"title": title, "message": message, "method": "libnotify"})

    def mocked_qt_tray(cls, title, message):
        result.append({"title": title, "message": message, "method": "qt_tray"})

    monkeypatch.setattr(notifier.Notifier, "send_via_libnotify", mocked_libnotify)
    monkeypatch.setattr(notifier.Notifier, "send_via_qt_tray", mocked_qt_tray)

    # On linux systems w/o libnotify
    monkeypatch.setattr(notifier.sys, "platform", "linux")
    monkeypatch.setattr(notifier.shutil, "which", lambda _: False)

    notifi = notifier.Notifier(None)
    notifi.send_notification(capture)
    assert result[-1]["title"] == "1 word captured"
    assert result[-1]["message"] == "text"
    assert result[-1]["method"] == "qt_tray"

    # On linux systems with libnotify
    monkeypatch.setattr(notifier.sys, "platform", "linux")
    monkeypatch.setattr(notifier.shutil, "which", lambda _: True)

    notifi = notifier.Notifier(None)
    notifi.send_notification(capture)
    assert result[-1]["title"] == "1 word captured"
    assert result[-1]["message"] == "text"
    assert result[-1]["method"] == "libnotify"

    # On other systems
    monkeypatch.setattr(notifier.sys, "platform", "win32")
    monkeypatch.setattr(notifier.shutil, "which", lambda _: True)

    notifi = notifier.Notifier(None)
    notifi.send_notification(capture)
    assert result[-1]["title"] == "1 word captured"
    assert result[-1]["message"] == "text"
    assert result[-1]["method"] == "qt_tray"
