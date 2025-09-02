import logging
import shutil
import subprocess
import sys
from collections.abc import Callable

from normcap.gui import system_info

logger = logging.getLogger(__name__)

install_instructions = (
    "The 'notify-send' utility and its dependency 'libnotify' are required.\n"
    "You can install them using your system's package manager. For example:\n"
    "- On Debian/Ubuntu: sudo apt install libnotify-bin\n"
    "- On Fedora: sudo dnf install libnotify\n"
    "- On Arch Linux: sudo pacman -S libnotify\n"
)


def is_compatible() -> bool:
    return sys.platform == "linux" or "bsd" in sys.platform


def is_installed() -> bool:
    if not (notify_send_bin := shutil.which("notify-send")):
        return False

    logger.debug("%s dependencies are installed (%s)", __name__, notify_send_bin)
    return True


def notify(
    title: str,
    message: str,
    action_label: str | None,
    action_callback: Callable | None,
) -> bool:
    """Send via notify-send.

    Seems to work more reliable on Linux + Gnome, but requires libnotify.
    Running in detached mode to avoid freezing KDE bar in some distributions.

    A drawback is, that it's difficult to receive clicks on the notification
    like it's done with the Qt method. `notify-send` _is_ able to support this,
    but it would require leaving the subprocess running and monitoring its output,
    which doesn't feel very solid.
    """
    logger.debug("Send notification via notify-send")
    icon_path = system_info.get_resources_path() / "icons" / "notification.png"

    # Escape chars interpreted by notify-send
    message = message.replace("\\", "\\\\")
    message = message.replace("-", "\\-")

    cmds = [
        "notify-send",
        f"--icon={icon_path.resolve()}",
        "--app-name=NormCap",
        "--transient",
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
        _stdout, stderr = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        _stdout, stderr = proc.communicate()

    if error := stderr.decode(encoding="utf-8"):
        logger.warning("notify-send returned with error: %s", error)
        return False

    return True
