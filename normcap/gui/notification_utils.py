import logging
import os
import tempfile
import textwrap
from collections.abc import Callable
from pathlib import Path

from PySide6 import QtCore, QtGui

from normcap.detection.models import PlaintextTextTypes, TextDetector, TextType
from normcap.gui import system_info
from normcap.gui.constants import APP_ID
from normcap.gui.localization import _, translate
from normcap.notification.models import NotificationAction

logger = logging.getLogger(__name__)


def _get_shared_temp_dir() -> Path:
    """Get a temporary directory suitable for beeing opened as URI."""
    if system_info.is_flatpak():
        if xdg_runtime_dir := os.getenv("XDG_RUNTIME_DIR"):
            temp_dir = Path(xdg_runtime_dir) / "app" / APP_ID
        else:
            temp_dir = Path.home() / ".cache" / "normcap-temp"
    else:
        temp_dir = Path(tempfile.gettempdir())

    temp_dir.mkdir(exist_ok=True, parents=True)
    return temp_dir


def _open_uris(urls: list[str]) -> None:
    for url in urls:
        logger.debug("Opening URI %s …", url)
        result = QtGui.QDesktopServices.openUrl(
            QtCore.QUrl(url, QtCore.QUrl.ParsingMode.TolerantMode)
        )
        logger.debug("Opened URI with result=%s", result)


def _get_line_ending(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"  # Windows-style line endings

    if "\r" in text:
        return "\r"  # Old Mac-style line endings

    return "\n"  # Unix/Linux-style line endings


def perform_action(text: str, text_type: TextType | None) -> None:
    logger.debug("Notification clicked.")

    urls = []
    if text_type == TextType.URL:
        urls = text.split()
    elif text_type == TextType.MAIL:
        urls = [f"mailto:{text.replace(',', ';').replace(' ', '')}"]
    elif text_type == TextType.PHONE_NUMBER:
        urls = [f"tel:{text.replace(' ', '').replace('-', '').replace('/', '')}"]
    elif text_type == TextType.VCARD:
        temp_file = _get_shared_temp_dir() / "normcap_result.vcf"
        temp_file.write_text(text)
        urls = [temp_file.as_uri()]
    elif text_type == TextType.VEVENT:
        temp_file = _get_shared_temp_dir() / "normcap_result.ics"
        line_sep = _get_line_ending(text)
        temp_file.write_text(f"BEGIN:VCALENDAR{line_sep}{text}{line_sep}END:VCALENDAR")
        urls = [temp_file.as_uri()]
    else:
        temp_file = _get_shared_temp_dir() / "normcap_result.txt"
        temp_file.write_text(text)
        urls = [temp_file.as_uri()]

    _open_uris(urls)


def get_actions(
    text: str, text_type: TextType, action_func: Callable
) -> list[NotificationAction]:
    actions = [
        NotificationAction(
            label=get_action_label(text_type=text_type),
            func=action_func,
            args=[text, text_type],
        )
    ]
    if text_type not in PlaintextTextTypes:
        # Add open in editor action (if first action isn't that action)
        actions.append(
            NotificationAction(
                label=get_action_label(text_type=TextType.NONE),
                func=action_func,
                args=[text, TextType.NONE],
            )
        )
    return actions


def get_title(text: str, text_type: TextType, detector: TextDetector) -> str:
    if not text or len(text.strip()) == 0:
        # L10N: Notification title when nothing got detected
        return _("Nothing captured!")

    if detector == TextDetector.QR:
        count = text.count(os.linesep) + 1 if text_type == TextType.MULTI_LINE else 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 QR code detected", "{count} QR codes detected", count
        ).format(count=count)
    elif detector == TextDetector.BARCODE:
        count = text.count(os.linesep) + 1 if text_type == TextType.MULTI_LINE else 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 barcode detected", "{count} barcodes detected", count
        ).format(count=count)
    elif detector == TextDetector.QR_AND_BARCODE:
        count = text.count(os.linesep) + 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 code detected", "{count} codes detected", count
        ).format(count=count)
    elif text_type == TextType.PARAGRAPH:
        count = text.count(os.linesep * 2) + 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 paragraph captured", "{count} paragraphs captured", count
        ).format(count=count)
    elif text_type == TextType.MAIL:
        count = text.count("@")
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 email captured", "{count} emails captured", count
        ).format(count=count)
    elif text_type == TextType.SINGLE_LINE:
        count = text.count(" ") + 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 word captured", "{count} words captured", count
        ).format(count=count)
    elif text_type == TextType.MULTI_LINE:
        count = text.count(os.linesep) + 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 line captured", "{count} lines captured", count
        ).format(count=count)
    elif text_type == TextType.URL:
        count = text.count(os.linesep) + 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 URL captured", "{count} URLs captured", count
        ).format(count=count)
    else:
        count = len(text)
        # Count linesep only as single char:
        count -= (len(os.linesep) - 1) * text.count(os.linesep)
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 character captured", "{count} characters captured", count
        ).format(count=count)
    return title


def get_text(text: str) -> str:
    if not text or len(text.strip()) == 0:
        # L10N: Notification text when nothing got detected
        text = _("Please try again.")

    text = text.strip().replace(os.linesep, " ")
    shortened = textwrap.shorten(text, width=45, placeholder=" […]").strip()
    if shortened == "[…]":
        # We have one long word which shorten() can not handle
        shortened = text

    return shortened


def get_action_label(text_type: TextType) -> str:
    if text_type == TextType.MAIL:
        # L10N: Button text of notification action in Linux.
        action_name = _("Compose Email")
    if text_type == TextType.PHONE_NUMBER:
        # L10N: Button text of notification action in Linux.
        action_name = _("Call Number")
    elif text_type == TextType.URL:
        # L10N: Button text of notification action in Linux.
        action_name = _("Open in Browser")
    elif text_type == TextType.VCARD:
        # L10N: Button text of notification action in Linux.
        action_name = _("Import to Adressbook")
    elif text_type == TextType.VEVENT:
        # L10N: Button text of notification action in Linux.
        action_name = _("Import to Calendar")
    else:
        # L10N: Button text of notification action in Linux.
        action_name = _("Open in Editor")
    return action_name
