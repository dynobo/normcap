import logging
from contextlib import nullcontext as does_not_raise

import pytest

from normcap.gui.settings import Settings, _parse_str_to_bool


def test_reset_settings():
    default = True
    non_default = False
    try:
        settings = Settings(organization="normcap_TEST")
        settings.setValue("parse-text", non_default)
        assert bool(settings.value("parse-text", type=bool)) == non_default

        settings.reset()
        assert bool(settings.value("parse-text", type=bool)) == default
    finally:
        settings.clear()


def test_update_from_init_settings(caplog):
    initial_parse_text = False
    try:
        with caplog.at_level(logging.DEBUG):
            settings = Settings(
                organization="normcap_TEST",
                init_settings={"parse-text": initial_parse_text, "non_existing": True},
            )
        assert bool(settings.value("parse-text", type=bool)) == initial_parse_text
        assert settings.value("non_existing", False) is False
        assert caplog.records[0].msg
    finally:
        settings.clear()


def test_set_missing_to_default(caplog):
    default_parse_text = True
    non_default_parse_text = False
    default_language = "eng"

    try:
        settings = Settings(organization="normcap_TEST")
        assert bool(settings.value("parse-text", type=bool)) == default_parse_text

        settings.setValue("parse-text", non_default_parse_text)
        assert bool(settings.value("parse-text", type=bool)) == non_default_parse_text

        assert settings.value("language") == default_language
        settings.remove("language")
        assert not settings.value("language", False)

        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            settings = Settings(organization="normcap_TEST")

        assert bool(settings.value("parse-text", type=bool)) == non_default_parse_text
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
