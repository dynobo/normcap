import logging
from typing import Optional

from PySide6 import QtCore

from normcap.gui.models import Setting

logger = logging.getLogger(__name__)


def _parse_str_to_bool(string: str) -> bool:
    if string.lower() in {"true", "1"}:
        return True
    if string.lower() in {"false", "0"}:
        return False
    raise ValueError("Expected bool, got '{string}'")


# Default values for settings stored in the application's QSettings.
# Also exposed as cli-args.
DEFAULT_SETTINGS = (
    Setting(
        key="color",
        flag="c",
        type_=str,
        value="#FF2E88",
        help_="Set primary color for UI, e.g. '#FF2E88'",
        choices=None,
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="language",
        flag="l",
        type_=str,
        value="eng",
        help_="Set language(s) for text recognition, e.g. '-l eng' or '-l eng deu'",
        choices=None,
        cli_arg=True,
        nargs="+",
    ),
    Setting(
        key="mode",
        flag="m",
        type_=str,
        value="parse",
        help_="Set capture mode",
        choices=("raw", "parse"),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="notification",
        flag="n",
        type_=_parse_str_to_bool,
        value=True,
        help_="Disable or enable notification after ocr detection",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="tray",
        flag="t",
        type_=_parse_str_to_bool,
        value=False,
        help_="Disable or enable system tray",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="update",
        flag="u",
        type_=_parse_str_to_bool,
        value=False,
        help_="Disable or enable check for updates",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="version",
        flag="_v",
        type_=str,
        value="0.0.0",
        help_="NormCap version number",
        choices=None,
        cli_arg=False,
        nargs=None,
    ),
    Setting(
        key="show-introduction",
        flag="i",
        type_=_parse_str_to_bool,
        value=True,
        help_="Show introductional screen on start",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="last-update-check",
        flag="_l",
        type_=str,
        value="0",
        help_="Date of last successful update check in format yyyy-mm-dd",
        choices=None,
        cli_arg=False,
        nargs=None,
    ),
    Setting(
        key="has-screenshot-permission",
        flag="_p",
        type_=_parse_str_to_bool,
        value=False,
        help_="Used to cache screenshot permission state to avoid testing to often",
        choices=None,
        cli_arg=False,
        nargs=None,
    ),
)


class Settings(QtCore.QSettings):
    """Provide interface to persisted user settings."""

    default_settings = DEFAULT_SETTINGS

    def __init__(
        self,
        organization: str = "normcap",
        application: str = "settings",
        parent: Optional[QtCore.QObject] = None,
        init_settings: Optional[dict] = None,
    ) -> None:
        super().__init__(organization, application=application, parent=parent)
        self.setFallbacksEnabled(False)
        self.init_settings: dict = init_settings or {}
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
            elif key in {"reset", "verbosity"}:
                continue
            else:
                logger.debug("Skip update of non existing setting (%s: %s)", key, value)

    def reset(self) -> None:
        """Remove all existing settings and values."""
        logger.info("Reset settings to defaults")
        for key in self.allKeys():
            self.remove(key)
        self._prepare_and_sync()
