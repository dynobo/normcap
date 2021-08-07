import pprint

from PySide2 import QtCore

from normcap.logger import format_section, logger
from normcap.utils import get_config_directory

DEFAULTS = {
    "color": "#FF2E88",
    "language": ("eng",),
    "mode": "parse",
    "notification": True,
    "tray": False,
    "update": False,
}


def log_settings(settings: QtCore.QSettings):
    """Print formated settings."""
    settings_dict = {
        k: settings.value(k)
        if settings.value(k) not in ["true", "false"]
        else settings.value(k) == "true"
        for k in settings.allKeys()
    }
    string = pprint.pformat(settings_dict, indent=3)
    string = format_section(string, title="Settings")
    logger.debug(f"Current settings:{string}")


def init_settings(args: dict) -> QtCore.QSettings:
    """Load settings, apply defaults if necessary and overwrite from cli args."""
    settings = QtCore.QSettings("normcap", "settings")
    settings.setFallbacksEnabled(False)
    if not settings.allKeys() or args.get("reset", False):
        logger.debug("Adjust settings to default values")
        for key in settings.allKeys():
            settings.remove(key)

    # Overwrite current with settings passed through cli arguments
    for key, value in args.items():
        if value and key in settings.allKeys():
            settings.setValue(key, value)

    # Overwrite missing settings with defaults
    for key, value in DEFAULTS.items():
        if key not in settings.allKeys() or (settings.value(key) is None):
            settings.setValue(key, value)

    log_settings(settings)

    # Remove deprecated config file
    # TODO: Remove in some month
    config_file = get_config_directory() / "normcap" / "config.yaml"
    if config_file.is_file():
        logger.debug("Removing deprecated config file.")
        config_file.unlink()

    return settings
