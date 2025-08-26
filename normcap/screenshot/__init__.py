from normcap.screenshot.main import (
    Handler,
    capture,
    capture_with_handler,
    get_available_handlers,
)
from normcap.screenshot.permissions import (
    has_screenshot_permission,
    macos_reset_screenshot_permission,
)

__all__ = [
    "Handler",
    "capture",
    "capture_with_handler",
    "get_available_handlers",
    "has_screenshot_permission",
    "macos_reset_screenshot_permission",
]
