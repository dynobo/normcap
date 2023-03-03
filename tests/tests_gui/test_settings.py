import logging

from normcap.gui.settings import Settings


def test_reset_settings():
    default = "parse"
    non_default = "raw"
    try:
        settings = Settings("normcap", "tests")
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
                "normcap",
                "tests",
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
        settings = Settings("normcap", "tests")
        assert settings.value("mode") == default_mode

        settings.setValue("mode", non_default_mode)
        assert settings.value("mode") == non_default_mode

        assert settings.value("language") == default_language
        settings.remove("language")
        assert not settings.value("language", False)

        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            settings = Settings("normcap", "tests")

        assert settings.value("mode") == non_default_mode
        assert settings.value("language") == default_language
        assert "Reset settings to" in caplog.records[0].msg
        assert caplog.records[0].args == ("language", default_language)
    finally:
        settings.clear()
