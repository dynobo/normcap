import logging
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.detection.models import TextDetector, TextType
from normcap.gui import system_info
from normcap.gui.localization import _, translate

logger = logging.getLogger(__name__)


def _compose_title(text: str, result_type: TextType, detector: TextDetector) -> str:
    if not text:
        return ""

    if detector == TextDetector.QR:
        count = text.count(os.linesep) + 1 if result_type == TextType.MULTI_LINE else 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 QR code detected", "{count} QR codes detected", count
        ).format(count=count)
    elif detector == TextDetector.BARCODE:
        count = text.count(os.linesep) + 1 if result_type == TextType.MULTI_LINE else 1
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
    elif result_type == TextType.PARAGRAPH:
        count = text.count(os.linesep * 2) + 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 paragraph captured", "{count} paragraphs captured", count
        ).format(count=count)
    elif result_type == TextType.MAIL:
        count = text.count("@")
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 email captured", "{count} emails captured", count
        ).format(count=count)
    elif result_type == TextType.SINGLE_LINE:
        count = text.count(" ") + 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 word captured", "{count} words captured", count
        ).format(count=count)
    elif result_type == TextType.MULTI_LINE:
        count = text.count(os.linesep) + 1
        # L10N: Notification title.
        # Do NOT translate the variables in curly brackets "{some_variable}"!
        title = translate.ngettext(
            "1 line captured", "{count} lines captured", count
        ).format(count=count)
    elif result_type == TextType.URL:
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


def _compose_text(text: str) -> str:
    if not text:
        return ""

    text = text.strip().replace(os.linesep, " ")
    shortened = textwrap.shorten(text, width=45, placeholder=" […]").strip()
    if shortened == "[…]":
        # We have one long word which shorten() can not handle
        shortened = text

    return shortened


def _compose_notification(
    text: str, result_type: TextType, detector: TextDetector
) -> tuple[str, str]:
    """Extract message text out of captures object and include icon."""
    # Compose message text
    if text and text.strip():
        title = _compose_title(text=text, result_type=result_type, detector=detector)
        text = _compose_text(text=text)
    else:
        # L10N: Notification title
        title = _("Nothing captured!")
        # L10N: Notification text
        text = _("Please try again.")

    return title, text


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


def _open_ocr_result(text: str, text_type: TextType) -> None:
    logger.debug("Notification clicked.")

    urls = []
    if text_type == TextType.URL:
        urls = text.split()
    elif text_type == TextType.MAIL:
        urls = [f"mailto:{text.replace(',', ';').replace(' ', '')}"]
    elif text_type == TextType.PHONE_NUMBER:
        urls = [f"tel:{text.replace(' ', '').replace('-', '').replace('/', '')}"]
    elif text_type == TextType.VCARD:
        temp_file = Path(tempfile.gettempdir()) / "normcap_temporary_result.vcf"
        temp_file.write_text(text)
        urls = [temp_file.as_uri()]
    elif text_type == TextType.VEVENT:
        temp_file = Path(tempfile.gettempdir()) / "normcap_temporary_result.ics"
        line_sep = _get_line_ending(text)
        temp_file.write_text(f"BEGIN:VCALENDAR{line_sep}{text}{line_sep}END:VCALENDAR")
        urls = [temp_file.as_uri()]
    else:
        temp_file = Path(tempfile.gettempdir()) / "normcap_temporary_result.txt"
        temp_file.write_text(text)
        urls = [temp_file.as_uri()]

    _open_uris(urls)


class Communicate(QtCore.QObject):
    """Notifier's communication bus."""

    send_notification = QtCore.Signal(str, str, str)
    on_notification_sent = QtCore.Signal()


class Notifier(QtCore.QObject):
    """Send notifications."""

    def __init__(self, parent: Optional[QtCore.QObject]) -> None:
        super().__init__(parent=parent)
        self.com = Communicate(parent=self)
        self.com.send_notification.connect(self._send_notification)

    @QtCore.Slot(str, str, str)
    def _send_notification(
        self, text: str, result_type: TextType, detector: TextDetector
    ) -> None:
        """Show tray icon then send notification."""
        title, message = _compose_notification(
            text=text, result_type=result_type, detector=detector
        )
        if sys.platform == "linux" and shutil.which("notify-send"):
            self._send_via_libnotify(
                title=title,
                message=message,
                text=text,
                text_type=result_type,
            )
        else:
            self._send_via_qt_tray(
                title=title,
                message=message,
                text=text,
                text_type=result_type,
            )
        self.com.on_notification_sent.emit()

    def _send_via_libnotify(
        self,
        title: str,
        message: str,
        text: str,
        text_type: TextType,
    ) -> None:
        """Send via notify-send.

        Seems to work more reliable on Linux + Gnome, but requires libnotify.
        Running in detached mode to avoid freezing KDE bar in some distributions.

        A drawback is, that it's difficult to receive clicks on the notification
        like it's done with the Qt method. `notify-send` _is_ able to support this,
        but it would require leaving the subprocess running and monitoring its output,
        which doesn't feel very solid.

        ONHOLD: Switch from notify-send to org.freedesktop.Notifications.
        A cleaner way would be to use DBUS org.freedesktop.Notifications instead of
        notify-send, but this seems to be quite difficult to implement with QtDbus,
        where the types seem not to be correctly casted to DBUS-Types. A future PySide
        version might improve the situation.
        """
        logger.debug("Send notification via notify-send")
        icon_path = system_info.get_resources_path() / "icons" / "notification.png"

        # Escape chars interpreted by notify-send
        message = message.replace("\\", "\\\\")
        message = message.replace("-", "\\-")

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

        cmds = [
            "notify-send",
            f"--icon={icon_path.resolve()}",
            "--app-name=NormCap",
            f"--action={action_name}",
            "--transient",
            "--wait",
            f"{title}",
            f"{message}",
        ]

        # Left detached on purpose.
        proc = subprocess.Popen(  # noqa: S603
            cmds,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = proc.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        if stdout.decode(encoding="utf-8").strip() == "0":
            _open_ocr_result(text=text, text_type=text_type)

        if error := stderr.decode(encoding="utf-8"):
            logger.warning("notify-send returned with error: %s", error)

    def _send_via_qt_tray(
        self,
        title: str,
        message: str,
        text: str,
        text_type: TextType,
    ) -> None:
        """Send via QSystemTrayIcon.

        Used for:
            - Windows
            - macOS
            - Linux (Fallback in case no notify-send)

        On Linux, this method has draw backs (probably Qt Bugs):
            - The custom icon is ignored. Instead the default icon
              `QtWidgets.QSystemTrayIcon.MessageIcon.Information` is shown.
            - Notifications clicks are not received. It _does_ work, if
              `QtWidgets.QSystemTrayIcon.MessageIcon.Critical` is used as icon.
        """
        logger.debug("Send notification via QT")

        parent = self.parent()

        if not isinstance(parent, QtWidgets.QSystemTrayIcon):
            raise TypeError("Parent is expected to be of type QSystemTrayIcon.")

        # Because clicks on different notifications can not be distinguished in Qt,
        # only the last notification is associated with an action/signal. All previous
        # get removed.
        if parent.isSignalConnected(
            QtCore.QMetaMethod.fromSignal(parent.messageClicked)
        ):
            parent.messageClicked.disconnect()

        # It only makes sense to act on notification clicks, if we have a result.
        if text and len(text.strip()) >= 1:
            parent.messageClicked.connect(
                lambda: _open_ocr_result(text=text, text_type=text_type)
            )

        parent.show()
        parent.showMessage(title, message, QtGui.QIcon(":notification"))
