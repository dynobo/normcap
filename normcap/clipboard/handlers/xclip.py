import logging
import shutil
import subprocess
import sys
from pathlib import Path

from .base import ClipboardHandlerBase

logger = logging.getLogger(__name__)


class XclipCopyHandler(ClipboardHandlerBase):
    @staticmethod
    def _copy(text: str) -> None:
        """Use xclip package to copy text to system clipboard."""
        subprocess.run(
            args=["xclip", "-selection", "clipboard", "-in"],
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
        if sys.platform != "linux":
            logger.debug("%s is not compatible on non-Linux systems", self.name)
            return False

        if not (xclip_bin := shutil.which("xclip")):
            logger.debug("%s is not compatible: xclip was not found", self.name)
            logger.warning(
                "Please install the system package 'xclip' to ensure that text can be"
                "copied to the clipboard correctly"
            )
            return False

        logger.debug("%s is compatible (%s)", self.name, xclip_bin)
        return True
