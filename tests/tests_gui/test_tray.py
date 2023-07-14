import pytest

from normcap import ocr
from normcap.gui import tray
from normcap.gui.settings import Settings


def test_debug_language_manager_is_deactivated(qapp):
    assert not tray.SystemTray._testing_language_manager


@pytest.mark.parametrize(
    ("active", "available", "sanitized"),
    [
        ("eng", ["eng"], ["eng"]),
        (["eng"], ["deu"], ["deu"]),
        (["eng"], ["afr", "eng"], ["eng"]),
        (["eng"], ["afr", "deu"], ["afr"]),
        (["deu", "eng"], ["afr", "deu"], ["deu"]),
        (["afr", "deu", "eng"], ["afr", "ben", "deu"], ["afr", "deu"]),
    ],
)
def test_sanitize_active_language(qapp, monkeypatch, active, available, sanitized):
    monkeypatch.setattr(ocr.tesseract, "get_languages", lambda **kwargs: available)
    settings = Settings(organization="normcap_TEST")
    try:
        settings.setValue("language", active)
        tray_cls = tray.SystemTray
        tray_cls.settings = settings
        tray_cls._sanitize_language_setting(tray_cls, installed_languages=available)
        assert settings.value("language") == sanitized
    finally:
        for k in settings.allKeys():
            settings.remove(k)
