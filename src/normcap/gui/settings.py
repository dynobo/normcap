import logging

from PySide6 import QtCore

from normcap.gui.constants import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class Settings(QtCore.QSettings):
    """Customized settings."""

    def __init__(self, *args, initial: dict, reset=False):
        super().__init__(*args)
        self.setFallbacksEnabled(False)

        # Do nicer?
        if reset:
            self.reset()

        self._set_missing_to_default(DEFAULT_SETTINGS)
        self._update_from_dict(initial)

        self.sync()

    def reset(self):
        """Remove all existing settings and values."""
        logger.info("Remove existing settings")
        for key in self.allKeys():
            self.remove(key)

    def _set_missing_to_default(self, defaults):
        for d in defaults:
            key, value = d.key, d.value
            if key not in self.allKeys() or (self.value(key) is None):
                logger.debug("Reset settings to (%s: %s)", key, value)
                self.setValue(key, value)

    def _update_from_dict(self, settings_dict):
        for key, value in settings_dict.items():
            if self.contains(key):
                if value is not None:
                    self.setValue(key, value)
            elif key in ["reset", "verbose", "very_verbose"]:
                continue
            else:
                logger.debug("Skip update of non existing setting (%s: %s)", key, value)
