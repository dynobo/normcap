import logging
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from PySide6 import QtGui

from normcap import ocr
from normcap.gui import tray
from normcap.gui.settings import Settings


def test_save_image_in_tempfolder():
    logger = logging.getLogger(__name__).root
    logger.setLevel("DEBUG")

    image = QtGui.QImage(20, 20, QtGui.QImage.Format.Format_RGB32)

    test_id = f"_unittest_{datetime.now():%H-%M-%S.%f}"
    tray._save_image_in_tempfolder(image, postfix=test_id)

    png_files = (Path(tempfile.gettempdir()) / "normcap").glob(f"*{test_id}.png")
    assert len(list(png_files)) == 1


@pytest.mark.parametrize(
    ("active", "available", "sanatized"),
    [
        ("eng", ["eng"], ["eng"]),
        (["eng"], ["deu"], ["deu"]),
        (["eng"], ["afr", "eng"], ["eng"]),
        (["eng"], ["afr", "deu"], ["afr"]),
        (["deu", "eng"], ["afr", "deu"], ["deu"]),
        (["afr", "deu", "eng"], ["afr", "ben", "deu"], ["afr", "deu"]),
    ],
)
def test_sanatize_active_language(monkeypatch, active, available, sanatized):
    monkeypatch.setattr(ocr.tesseract, "get_languages", lambda **kwargs: available)
    try:
        settings = Settings("TEST_normcap", "settings")
        settings.setValue("language", active)
        tray.SystemTray._sanatize_active_language(settings)
        assert settings.value("language") == sanatized
    finally:
        for k in settings.allKeys():
            settings.remove(k)
