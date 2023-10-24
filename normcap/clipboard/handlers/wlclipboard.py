import logging
import shutil
import subprocess
from pathlib import Path

from .base import ClipboardHandlerBase

logger = logging.getLogger(__name__)


class WlCopyHandler(ClipboardHandlerBase):
    def _copy(self, text: str) -> None:
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
            timeout=30,
        )

    def _is_compatible(self) -> bool:
        if not self._os_has_wayland_display_manager():
            logger.debug(
                "%s is not compatible on non-Linux systems and on Linux w/o Wayland",
                self.name,
            )
            return False

        if not (wl_copy_bin := shutil.which("wl-copy")):
            logger.debug("%s is not compatible: wl-copy was not found", self.name)
            logger.warning(
                "Your Linux runs with Wayland. Please install the system "
                "package 'wl-clipboard' to ensure that text can be copied to "
                "the clipboard correctly"
            )
            return False

        logger.debug("%s is compatible (%s)", self.name, wl_copy_bin)
        return True
