import subprocess

import pytest
from PySide6 import QtCore, QtGui

from normcap.screengrab import system_info
from normcap.screengrab.handlers import grim


@pytest.mark.gui()
@pytest.mark.skipif(
    not grim.is_compatible() or not grim.is_installed(),
    reason="Grim compatible platform test",
)
def test_capture_on_wayland(qapp):
    # GIVEN a linux system with grim support (Linux with compatible Wayland Compositor)
    assert system_info.has_wayland_display_manager()

    # WHEN screenshot is taking using QT
    images = grim.capture()

    # THEN there should be at least one image
    #   and the size should not be (0, 0)
    assert images
    assert all(isinstance(i, QtGui.QImage) for i in images)
    assert all(i.size().toTuple() != (0, 0) for i in images)


@pytest.mark.gui()
@pytest.mark.skipif(
    grim.is_compatible() and grim.is_installed(),
    reason="Non-grim compatible platform test",
)
def test_capture_with_grim_not_supported_raises():
    # GIVEN a linux system w/o grim support (e.g. Windows or incompatible Compositor)
    # WHEN screenshot is taking using grim
    # THEN an exception should be raised
    with pytest.raises((subprocess.CalledProcessError, OSError)):
        _ = grim.capture()


@pytest.mark.gui()
@pytest.mark.skipif(
    grim.is_compatible() and grim.is_installed(),
    reason="Non-grim compatible platform test",
)
def test_capture_with_grim_mocked(monkeypatch, caplog, qapp):
    # GIVEN grim support is mocked to return a test image
    called_kwargs = {}
    test_image_size = (640, 480)

    def mocked_run(args, **kwargs):
        called_kwargs["args"] = args
        called_kwargs["kwargs"] = kwargs
        image_path = args[-1]
        screenshot = QtGui.QImage(
            QtCore.QSize(*test_image_size), QtGui.QImage.Format.Format_RGB32
        )
        screenshot.save(image_path)
        return subprocess.CompletedProcess(args="", returncode=0, stdout="", stderr="")

    monkeypatch.setattr(grim.sys, "platform", "linux")
    monkeypatch.setattr(grim.shutil, "which", lambda *_: "/some/path")
    monkeypatch.setattr(grim.subprocess, "run", mocked_run)
    monkeypatch.setattr(system_info, "has_wlroots_compositor", lambda: True)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland")

    assert grim.is_compatible()
    assert grim.is_installed()

    # WHEN screenshot is taking using grim
    images = grim.capture()

    # THEN there should be at least one image (depends on number of displays)
    #   and the size should not be (0, 0) (depends on display settings)
    assert images
    assert all(isinstance(i, QtGui.QImage) for i in images)
    assert all(i.size().toTuple() != (0, 0) for i in images)


def test_grim_is_installed(monkeypatch):
    # GIVEN a system with workable grim (or a mocked one)
    if not grim.shutil.which("grim"):
        monkeypatch.setattr(grim.shutil, "which", lambda _: "/usr/bin/grim")

    # WHEN the function is called
    # THEN the grim support should indicated
    assert grim.is_installed()


def test_grim_is_installed_no_grim_binary(monkeypatch):
    # GIVEN a system without grim binary (or mocked away)
    if grim.shutil.which("grim"):
        monkeypatch.setattr(grim.shutil, "which", lambda _: None)

    # WHEN the function is called
    # THEN the no grim support should indicated
    assert not grim.is_installed()
