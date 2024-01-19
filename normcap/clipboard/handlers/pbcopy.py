import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

install_instructions = ""  # pbcopy is pre-installed on macOS


def copy(text: str) -> None:
    subprocess.run(
        ["pbcopy", "w"],  # noqa: S607
        shell=False,  # noqa: S603
        input=text.encode("utf-8"),
        check=True,
        timeout=30,
        env={"LC_CTYPE": "UTF-8"},
    )


def is_compatible() -> bool:
    if sys.platform != "darwin":
        logger.debug("%s is incompatible on non-macOS systems", __name__)
        return False

    logger.debug("%s is compatible", __name__)
    return True


def is_installed() -> bool:
    logger.debug("%s requires no dependencies", __name__)
    return True
