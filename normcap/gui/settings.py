import logging
from typing import Any, Iterable, Optional

from PySide6 import QtCore

from normcap.gui.models import Setting

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = (
    Setting(
        key="color",
        flag="c",
        type_=str,
        value="#FF2E88",
        help="Set primary color for UI, e.g. '#FF2E88'",
        choices=None,
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="language",
        flag="l",
        type_=str,
        value="eng",
        help="Set language(s) for text recognition, e.g. '-l eng' or '-l eng deu'",
        choices=None,
        cli_arg=True,
        nargs="+",
    ),
    Setting(
        key="mode",
        flag="m",
        type_=str,
        value="parse",
        help="Set capture mode",
        choices=("raw", "parse"),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="notification",
        flag="n",
        type_=bool,
        value=True,
        help="Disable or enable notification after ocr detection",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="tray",
        flag="t",
        type_=bool,
        value=False,
        help="Disable or enable system tray",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="update",
        flag="u",
        type_=bool,
        value=False,
        help="Disable or enable check for updates",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="version",
        flag="c",
        type_=str,
        value="0.0.0",
        help="NormCap version number",
        choices=None,
        cli_arg=False,
        nargs=None,
    ),
    Setting(
        key="last-update-check",
        flag="d",
        type_=str,
        value="0",
        help="Date of last successful update check in format yyyy-mm-dd",
        choices=None,
        cli_arg=False,
        nargs=None,
    ),
)


class Settings(QtCore.QSettings):
    """Provide interface to persisted user settings."""

    default_settings = DEFAULT_SETTINGS

    def __init__(
        self, *args: Iterable[Any], init_settings: Optional[dict] = None
    ) -> None:
        super().__init__(*args)
        self.setFallbacksEnabled(False)
        self.init_settings: dict = init_settings if init_settings else {}
        self._prepare_and_sync()

    def _prepare_and_sync(self) -> None:
        self._set_missing_to_default()
        self._update_from_init_settings()
        self.sync()

    def _set_missing_to_default(self) -> None:
        for d in self.default_settings:
            key, value = d.key, d.value
            if key not in self.allKeys() or (self.value(key) is None):
                logger.debug("Reset settings to (%s: %s)", key, value)
                self.setValue(key, value)

    def _update_from_init_settings(self) -> None:
        for key, value in self.init_settings.items():
            if self.contains(key):
                if value is not None:
                    self.setValue(key, value)
            elif key in ("reset", "verbosity"):
                continue
            else:
                logger.debug("Skip update of non existing setting (%s: %s)", key, value)

    def reset(self) -> None:
        """Remove all existing settings and values."""
        logger.info("Reset settings to defaults")
        for key in self.allKeys():
            self.remove(key)
        self._prepare_and_sync()
