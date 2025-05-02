from typing import Callable, Optional

install_instructions = ""


def is_compatible() -> bool:
    return False


def is_installed() -> bool:
    return True


def notify(
    title: str,
    message: str,
    action_label: Optional[str] = None,
    action_callback: Optional[Callable] = None,
) -> bool:
    return False
