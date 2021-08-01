from PySide2 import QtCore

from normcap.logger import logger

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
    settings_dict = {k: settings.value(k) for k in settings.allKeys()}
    string = [
        f"\t{k}: {v if v not in ['true', 'false'] else v=='true'}"
        for k, v in settings_dict.items()
    ]
    logger.debug("Current settings:\n" + "\n".join(string))


def init_settings(args: dict) -> QtCore.QSettings:
    """Load settings, apply defaults if necessary and overwrite from cli args."""
    settings = QtCore.QSettings("normcap", "settings")
    if "reset" in args and args["reset"]:
        # Reset settings to defaults
        for key, value in DEFAULTS.items():
            settings.setValue(key, value)

        # Delete all leftover settings
        for key in settings.allKeys():
            if key not in DEFAULTS:
                settings.remove(key)

    # Overwrite current with settings passed through cli arguments
    for key, value in args.items():
        if value and key in settings.allKeys():
            settings.setValue(key, value)

    log_settings(settings)

    return settings
