import logging
import sys
from typing import Callable

from normcap.clipboard import linux, macos, windows

logger = logging.getLogger(__name__)


def get_copy_func() -> Callable:
    if sys.platform == "win32":
        return windows.get_copy_func()
    if sys.platform == "linux":
        return linux.get_copy_func()
    if sys.platform == "darwin":
        return macos.get_copy_func()

    raise RuntimeError(f"Unknown platform {sys.platform}")
