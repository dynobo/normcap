"""Load translations dictionary for usage in GUI."""

import gettext
from pathlib import Path

translate = gettext.translation(
    domain="messages",
    localedir=Path(__file__).parent.parent / "resources" / "locales",
    fallback=True,
)
_ = translate.gettext
