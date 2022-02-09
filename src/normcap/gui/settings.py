import logging

from PySide6 import QtCore

from normcap.gui.constants import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


def init_settings(*args, initial: dict, reset=False) -> QtCore.QSettings:
    """Prepare QT settings.

    Apply defaults to missing setting and overwrite with initially
    provided settings (e.g. from CLI args).
    """
    settings = QtCore.QSettings(*args)
    settings.setFallbacksEnabled(False)

    if reset:
        settings = _remove_all_keys(settings)
    settings = _set_missing_to_default(settings, DEFAULT_SETTINGS)
    settings = _update_from_dict(settings, initial)
    settings.sync()

    return settings


def _update_from_dict(settings, update_dict):
    for key, value in update_dict.items():
        if settings.contains(key):
            if value is not None:
                settings.setValue(key, value)
        elif key in ["reset", "verbose", "very_verbose"]:
            continue
        else:
            logger.debug("Skip update of non existing setting (%s: %s)", key, value)
    return settings


def _remove_all_keys(settings):
    logger.info("Remove existing settings")
    for key in settings.allKeys():
        settings.remove(key)
    return settings


def _set_missing_to_default(settings, defaults):
    for d in defaults:
        key, value = d.key, d.value
        if key not in settings.allKeys() or (settings.value(key) is None):
            logger.debug("Setting to default (%s: %s)", key, value)
            settings.setValue(key, value)
    return settings
