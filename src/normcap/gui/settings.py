from PySide2 import QtCore

from normcap import system_info
from normcap.data import DEFAULT_SETTINGS
from normcap.logger import logger


def init_settings(*args, initial: dict, reset=False) -> QtCore.QSettings:
    """Prepare QT settings.

    Apply defaults to missing setting and overwrite with initially
    provided settings (e.g. from CLI args)."""

    settings = QtCore.QSettings(*args)
    settings.setFallbacksEnabled(False)

    if reset:
        settings = _remove_all_keys(settings)
    settings = _set_missing_to_default(settings, DEFAULT_SETTINGS)
    settings = _update_from_dict(settings, initial)
    settings.sync()
    _remove_deprecated()

    return settings


def _update_from_dict(settings, update_dict):
    for key, value in update_dict.items():
        if settings.contains(key):
            if value is not None:
                settings.setValue(key, value)
        else:
            logger.debug(f"Skip update of non existing setting ({key}:{value})")
    return settings


def _remove_all_keys(settings):
    logger.info("Removing existing settings")
    for key in settings.allKeys():
        settings.remove(key)
    return settings


def _set_missing_to_default(settings, defaults):
    for d in defaults:
        key, value = d.key, d.value
        if key not in settings.allKeys() or (settings.value(key) is None):
            logger.debug(f"Setting to default ({key}: {value})")
            settings.setValue(key, value)
    return settings


def _remove_deprecated():
    # TODO: Remove in some month
    config_file = system_info.config_directory() / "config.yaml"
    if config_file.is_file():
        logger.debug("Removing deprecated config file.")
        config_file.unlink()
