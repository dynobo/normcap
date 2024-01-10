import logging
import shutil
import subprocess
from pathlib import Path

from .base import ClipboardHandlerBase

logger = logging.getLogger(__name__)


class WlCopyHandler(ClipboardHandlerBase):
    install_instructions = (
        "Please install the package 'wl-clipboard' with your system's package manager."
    )

    @staticmethod
    def _copy(text: str) -> None:
        """Use wl-clipboard package to copy text to system clipboard."""
        subprocess.run(
            args=["wl-copy"],
            shell=False,
            input=text,
            encoding="utf-8",
            check=True,
            # It seems like wl-copy works more reliable when output is piped to
            # somewhere. This is e.g. the case when NormCap got started via a shortcut
            # on KDE (#422).
            stdout=Path("/dev/null").open("w"),  # noqa: SIM115
            timeout=5,
        )

    def is_compatible(self) -> bool:
        if not self._os_has_wayland_display_manager():
            logger.debug(
                "%s is not compatible on non-Linux systems and on Linux w/o Wayland",
                self.name,
            )
            return False

        if self._os_has_awesome_wm():
            logger.debug("%s is not compatible with Awesome WM", self.name)
            return False

        gnome_version = self._get_gnome_version()
        if gnome_version.startswith("45."):
            logger.debug("%s is not compatible with Gnome %s", self.name, gnome_version)
            return False

        logger.debug("%s is compatible", self.name)
        return True

    def is_installed(self) -> bool:
        if not (wl_copy_bin := shutil.which("wl-copy")):
            logger.debug("%s is not installed: wl-copy was not found", self.name)
            return False

        logger.debug("%s dependencies are installed (%s)", self.name, wl_copy_bin)
        return True
