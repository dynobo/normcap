import subprocess

import pytest
from PySide6 import QtCore, QtGui

from normcap.screengrab import grim, utils
from normcap.screengrab.grim import capture


@pytest.mark.gui()
@pytest.mark.skipif(
    utils.has_grim_support(), reason="Non-grim compatible platform test"
)
def test_capture_with_grim_not_supported_raises():
    # GIVEN a linux system w/o grim support (e.g. Windows or incompatible Compositor)
    assert not utils.has_grim_support()

    # WHEN screenshot is taking using grim
    # THEN an exception should be raised
    with pytest.raises((subprocess.CalledProcessError, OSError)):
        _ = capture()


@pytest.mark.gui()
@pytest.mark.skipif(
    not utils.has_grim_support(), reason="Grim compatible platform test"
)
def test_capture_on_wayland(qapp):
    # GIVEN a linux system with grim support (Linux with compatible Wayland Compositor)
    assert utils.has_grim_support()
    assert utils.has_wayland_display_manager()

    # WHEN screenshot is taking using QT
    images = capture()

    # THEN there should be at least one image
    #   and the size should not be (0, 0)
    assert images
    assert all(isinstance(i, QtGui.QImage) for i in images)
    assert all(i.size().toTuple() != (0, 0) for i in images)


@pytest.mark.gui()
@pytest.mark.skipif(
    utils.has_grim_support(), reason="Non-grim compatible platform test"
)
def test_capture_with_grim_mocked(monkeypatch, caplog, qapp):
    # GIVEN grim support is mocked to return a test image
    called_kwargs = {}
    test_image_size = (640, 480)

    def mocked_which(*args):
        return "/some/path"

    def mocked_run(args, **kwargs):
        called_kwargs["args"] = args
        called_kwargs["kwargs"] = kwargs
        image_path = args[-1]
        screenshot = QtGui.QImage(
            QtCore.QSize(*test_image_size), QtGui.QImage.Format.Format_RGB32
        )
        screenshot.save(image_path)
        return subprocess.CompletedProcess(args="", returncode=0, stdout="", stderr="")

    monkeypatch.setattr(utils.shutil, "which", mocked_which)
    monkeypatch.setattr(utils.subprocess, "run", mocked_run)
    monkeypatch.setattr(grim.subprocess, "run", mocked_run)

    assert utils.has_grim_support()

    # WHEN screenshot is taking using grim
    images = capture()

    # THEN there should be at least one image (depends on number of displays)
    #   and the size should not be (0, 0) (depends on display settings)
    assert images
    assert all(isinstance(i, QtGui.QImage) for i in images)
    assert all(i.size().toTuple() != (0, 0) for i in images)
