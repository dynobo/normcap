import logging
import os
import tempfile
import textwrap
from collections.abc import Callable
from pathlib import Path

from PySide6 import QtCore, QtGui

from normcap import app_id
from normcap.detection.models import (
    DetectionResult,
    PlaintextTextTypes,
    TextDetector,
    TextType,
)
from normcap.gui.localization import _, translate
from normcap.notification.models import NotificationAction
from normcap.system import info

logger = logging.getLogger(__name__)


def _get_shared_temp_dir() -> Path:
    """Get a temporary directory suitable for beeing opened as URI."""
    if info.is_flatpak():
        if xdg_runtime_dir := os.getenv("XDG_RUNTIME_DIR"):
            temp_dir = Path(xdg_runtime_dir) / "app" / app_id
        else:
            temp_dir = Path.home() / ".cache" / "normcap-temp"
    else:
        temp_dir = Path(tempfile.gettempdir())

    temp_dir.mkdir(exist_ok=True, parents=True)
    return temp_dir


def _open_uris(urls: list[str]) -> None:
    logger.info("urls %s", urls)
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


def perform_action(texts_and_types: list) -> None:
    logger.debug("Notification clicked.")

    texts = [t[0] for t in texts_and_types]
    unique_text_types = list({t[1] for t in texts_and_types})
    line_sep = _get_line_ending(text="".join(texts))
    logger.info("unique %s", unique_text_types)

    urls = []
    match unique_text_types:
        case [TextType.URL]:
            urls = texts
        case [TextType.MAIL]:
            urls = [f"mailto:{t.replace(',', ';').replace(' ', '')}" for t in texts]
        case [TextType.PHONE_NUMBER]:
            urls = [
                f"tel:{t.replace(' ', '').replace('-', '').replace('/', '')}"
                for t in texts
            ]
        case [TextType.VCARD]:
            text = line_sep.join(texts)
            temp_file = _get_shared_temp_dir() / "normcap_result.vcf"
            temp_file.write_text(text)
            urls = [temp_file.as_uri()]
        case [TextType.VEVENT]:
            text = line_sep.join(texts)
            text = f"BEGIN:VCALENDAR{line_sep}{text}{line_sep}END:VCALENDAR"
            temp_file = _get_shared_temp_dir() / "normcap_result.ics"
            temp_file.write_text(text)
            urls = [temp_file.as_uri()]
        case _:
            temp_file = _get_shared_temp_dir() / "normcap_result.txt"
            temp_file.write_text(line_sep.join(texts))
            urls = [temp_file.as_uri()]

    _open_uris(urls)


def get_actions(
    detection_results: list[DetectionResult], action_func: Callable
) -> list[NotificationAction]:
    text_types = [r.text_type for r in detection_results]

    actions = [
        NotificationAction(
            label=get_action_label(text_types=text_types),
            func=action_func,
            args=[(d.text, d.text_type) for d in detection_results],
        )
    ]
    if not set(text_types).issubset(set(PlaintextTextTypes)):
        actions.append(
            NotificationAction(
                label=get_action_label(text_types=[TextType.NONE]),
                func=action_func,
                args=[(d.text, TextType.NONE) for d in detection_results],
            )
        )
    return actions


def _get_code_postfix(detection_results: list[DetectionResult]) -> str:
    if not detection_results:
        # L10N: Notification title when nothing got detected
        return _("Nothing captured!")

    detectors = [r.detector for r in detection_results]
    unique_detectors = list(set(detectors))

    count = len(detection_results)

    match unique_detectors:
        case [TextDetector.QR]:
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            postfix = translate.ngettext(
                "in 1 QR code", "in {count} QR codes", count
            ).format(count=count)
        case [TextDetector.BARCODE]:
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            postfix = translate.ngettext(
                "in 1 barcode", "in {count} barcodes", count
            ).format(count=count)
        case [TextDetector.BARCODE, TextDetector.QR]:
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            postfix = translate.ngettext("in 1 code", "in {count} codes", count).format(
                count=count
            )
        case _:
            postfix = ""

    return postfix


def _get_elements_description(detection_results: list[DetectionResult]) -> str:
    unqiue_text_types = list({r.text_type for r in detection_results})
    count = len(detection_results)

    match unqiue_text_types:
        case [TextType.MAIL]:
            count = sum(d.text.count("@") for d in detection_results)
            # l10n: notification title.
            # do not translate the variables in curly brackets "{some_variable}"!
            title = translate.ngettext(
                "1 email captured", "{count} emails captured", count
            ).format(count=count)
        case [TextType.URL]:
            count = len(detection_results)
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            title = translate.ngettext(
                "1 URL captured", "{count} URLs captured", count
            ).format(count=count)
        case [TextType.PHONE_NUMBER]:
            count = len(detection_results)
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            title = translate.ngettext(
                "1 phone number captured", "{count} phone numbers captured", count
            ).format(count=count)
        case [TextType.VEVENT]:
            count = len(detection_results)
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            title = translate.ngettext(
                "1 calendar event captured", "{count} calender events captured", count
            ).format(count=count)
        case [TextType.VCARD]:
            count = len(detection_results)
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            title = translate.ngettext(
                "1 contact captured", "{count} contact captured", count
            ).format(count=count)
        case [TextType.PARAGRAPH]:
            count = sum(d.text.count(os.linesep * 2) for d in detection_results) + 1
            title = translate.ngettext(
                "1 paragraph captured", "{count} paragraphs captured", count
            ).format(count=count)
        case [TextType.MULTI_LINE]:
            count = sum(d.text.count(os.linesep) + 1 for d in detection_results)
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            title = translate.ngettext(
                "1 line captured", "{count} lines captured", count
            ).format(count=count)
        case _:
            count = sum(d.text.count(" ") + 1 for d in detection_results)
            # L10N: Notification title.
            # Do NOT translate the variables in curly brackets "{some_variable}"!
            title = translate.ngettext(
                "1 word captured", "{count} words captured", count
            ).format(count=count)

    return title


def get_title(detection_results: list[DetectionResult]) -> str:
    if not detection_results:
        # L10N: Notification title when nothing got detected
        return _("Nothing captured!")

    description = _get_elements_description(detection_results=detection_results)
    postfix = _get_code_postfix(detection_results=detection_results)
    return f"{description} {postfix}"


def get_text(detection_results: list[DetectionResult]) -> str:
    if not detection_results:
        # L10N: Notification text when nothing got detected
        return _("Please try again.")

    text = " ".join(d.text.strip().replace(os.linesep, " ") for d in detection_results)

    shortened = textwrap.shorten(text, width=45, placeholder=" […]").strip()
    if shortened == "[…]":
        # We have one long word which shorten() can not handle
        shortened = text

    return shortened


def get_action_label(text_types: list[TextType]) -> str:
    unique_text_types = list(set(text_types))
    match unique_text_types:
        case [TextType.MAIL]:
            # L10N: Button text of notification action in Linux.
            action_name = _("Compose Email")
        case [TextType.PHONE_NUMBER]:
            # L10N: Button text of notification action in Linux.
            action_name = _("Call Number")
        case [TextType.URL]:
            # L10N: Button text of notification action in Linux.
            action_name = _("Open in Browser")
        case [TextType.VCARD]:
            # L10N: Button text of notification action in Linux.
            action_name = _("Import to Adressbook")
        case [TextType.VEVENT]:
            # L10N: Button text of notification action in Linux.
            action_name = _("Import to Calendar")
        case _:
            # L10N: Button text of notification action in Linux.
            action_name = _("Open in Editor")
    return action_name
