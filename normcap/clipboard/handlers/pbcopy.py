import logging
import shutil
import subprocess
import sys

from .base import ClipboardHandlerBase

logger = logging.getLogger(__name__)


class PbCopyHandler(ClipboardHandlerBase):
    @staticmethod
    def _copy(text: str) -> None:
        subprocess.run(
            ["pbcopy", "w"],  # noqa: S607
            shell=False,  # noqa: S603
            input=text.encode("utf-8"),
            check=True,
            timeout=30,
            env={"LC_CTYPE": "UTF-8"},
        )

    def _is_compatible(self) -> bool:
        if sys.platform != "darwin":
            logger.debug("%s is incompatible on non-macOS systems", self.name)
            return False

        if not (pbcopy_bin := shutil.which("pbcopy")):
            logger.debug("%s is incompatible: pbcopy seems missing", self.name)
            return False

        logger.debug("%s is compatible (%s)", self.name, pbcopy_bin)
        return True
