import logging
from contextlib import nullcontext as does_not_raise

import pytest

from normcap.gui.settings import Settings, _parse_str_to_bool


def test_reset_settings():
    default = "parse"
    non_default = "raw"
    try:
        settings = Settings(organization="normcap_TEST")
        settings.setValue("mode", non_default)
        assert settings.value("mode") == non_default

        settings.reset()
        assert settings.value("mode") == default
    finally:
        settings.clear()


def test_update_from_init_settings(caplog):
    init_setting = "raw"
    try:
        with caplog.at_level(logging.DEBUG):
            settings = Settings(
                organization="normcap_TEST",
                init_settings={"mode": init_setting, "non_existing": True},
            )
        assert settings.value("mode") == init_setting
        assert settings.value("non_existing", False) is False
        assert caplog.records[0].msg
    finally:
        settings.clear()


def test_set_missing_to_default(caplog):
    default_mode = "parse"
    non_default_mode = "raw"
    default_language = "eng"

    try:
        settings = Settings(organization="normcap_TEST")
        assert settings.value("mode") == default_mode

        settings.setValue("mode", non_default_mode)
        assert settings.value("mode") == non_default_mode

        assert settings.value("language") == default_language
        settings.remove("language")
        assert not settings.value("language", False)

        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            settings = Settings(organization="normcap_TEST")

        assert settings.value("mode") == non_default_mode
        assert settings.value("language") == default_language
        assert "Reset settings to" in caplog.records[0].msg
        assert caplog.records[0].args == ("language", default_language)
    finally:
        settings.clear()


@pytest.mark.parametrize(
    ("value", "expected_value", "expected_exc"),
    [
        ("True", True, does_not_raise()),
        ("true", True, does_not_raise()),
        ("1", True, does_not_raise()),
        ("False", False, does_not_raise()),
        ("false", False, does_not_raise()),
        ("0", False, does_not_raise()),
        ("foo", None, pytest.raises(ValueError, match="Expected bool")),
        ("-1", None, pytest.raises(ValueError, match="Expected bool")),
    ],
)
def test_parse_to_bool(value, expected_value, expected_exc):
    result = None
    with expected_exc:
        result = _parse_str_to_bool(value)
    assert result == expected_value
