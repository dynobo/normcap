import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

install_instructions = ""  # pbcopy is pre-installed on macOS


def copy(text: str) -> None:
    subprocess.run(  # noqa: S603
        ["pbcopy", "w"],  # noqa: S607
        shell=False,
        input=text.encode("utf-8"),
        check=True,
        timeout=30,
        env={"LC_CTYPE": "UTF-8"},
    )


def is_compatible() -> bool:
    return sys.platform == "darwin"


def is_installed() -> bool:
    return True
