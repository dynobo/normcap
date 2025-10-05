import logging

from PySide6 import QtCore

from normcap import __version__
from normcap.gui.models import Setting
from normcap.gui.system_info import config_directory, is_portable_windows_package

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
        key="parse-text",
        flag="",
        type_=_parse_str_to_bool,
        value=True,
        help_=(
            "Try to determine the text's type (e.g. line, paragraph, URL, email) and "
            "format the output accordingly."
        ),
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="detect-codes",
        flag="",
        type_=_parse_str_to_bool,
        value=True,
        help_="Detect barcodes and QR codes.",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="detect-text",
        flag="",
        type_=_parse_str_to_bool,
        value=True,
        help_="Detect text using ocr.",
        choices=(True, False),
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
        key="current-version",
        flag="_c",
        type_=str,
        value="0.0.0",
        help_="NormCap version number",
        choices=None,
        cli_arg=False,
        nargs=None,
    ),
    Setting(
        key="has-screenshot-permission",
        flag="_h",
        type_=_parse_str_to_bool,
        value=False,
        help_="Screenshot permission has been confirmed",
        choices=(True, False),
        cli_arg=False,
        nargs=None,
    ),
    Setting(
        key="show-introduction",
        flag="",
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


class Communicate(QtCore.QObject):
    """Settings's communication bus."""

    on_value_changed = QtCore.Signal(str, object)


class Settings(QtCore.QSettings):
    """Provide interface to persisted user settings."""

    default_settings = DEFAULT_SETTINGS

    def __init__(
        self,
        organization: str = "normcap",
        application: str = "settings",
        parent: QtCore.QObject | None = None,
        init_settings: dict | None = None,
    ) -> None:
        if is_portable_windows_package():
            ini_file = (config_directory() / f"{application}.ini").resolve()
            super().__init__(str(ini_file), QtCore.QSettings.IniFormat)
        else:
            super().__init__(organization, application=application, parent=parent)

        self.init_settings: dict = init_settings or {}
        self.setFallbacksEnabled(False)
        self.com = Communicate()
        self._prepare_and_sync()

    def _prepare_and_sync(self) -> None:
        self._migrate_deprecated()
        self._on_version_change()
        self._set_missing_to_default()
        self._update_from_init_settings()
        self.sync()

    def _migrate_deprecated(self) -> None:
        # Remove deprected settings from v0.6.0
        # ONHOLD: Delete in 2026/7
        if self.value("version", None):
            self.remove("version")

        # Migrations to v0.6.0
        # ONHOLD: Delete in 2026/7
        if self.value("mode", None):
            mode = self.value("mode")
            parse_text = mode == "parse"
            self.setValue("parse-text", parse_text)
            self.remove("mode")
            logger.debug(
                "Migrated setting 'mode=%s' to 'parse-text=%s'.", mode, parse_text
            )

    def _set_missing_to_default(self) -> None:
        for d in self.default_settings:
            key, value = d.key, d.value
            if key not in self.allKeys() or (self.value(key) is None):
                logger.debug("Reset settings to (%s: %s)", key, value)
                self.setValue(key, value)

    def _update_from_init_settings(self) -> None:
        non_persisted_settings = {
            "reset",
            "verbosity",
            "log-file",
            "version",
            "cli-mode",
            "background-mode",
            "screenshot-handler",
            "clipboard-handler",
            "notification-handler",
            "dbus-activation",
        }
        for key, value in self.init_settings.items():
            # TODO: Migrate setting keys to underscore instead minus
            setting_key = key.replace("_", "-")
            if self.contains(setting_key):
                if value is not None:
                    self.setValue(setting_key, value)
            elif setting_key in non_persisted_settings:
                continue
            else:
                logger.debug(
                    "Skip update of unknown setting (%s: %s)", setting_key, value
                )

    def _on_version_change(self) -> None:
        if self.value("current-version", "") != __version__:
            logger.info("First run of new NormCap version")
            # Assume we've lost screenshot permissions.
            # (which will trigger an additional probing screenshot)
            self.setValue("has-screenshot-permission", False)

            # Update version setting
            self.setValue("current-version", __version__)

    def setValue(self, key: str, value: object) -> None:  # noqa: N802 # all lowercase
        old_value = self.value(key)
        super().setValue(key, value)
        if old_value != value:
            logger.debug(
                "Setting '%s' changed from '%s' to '%s'", key, old_value, value
            )
            self.com.on_value_changed.emit(key, value)

    def reset(self) -> None:
        """Remove all existing settings and values."""
        logger.info("Reset settings to defaults")
        for key in self.allKeys():
            self.remove(key)
        self._prepare_and_sync()
