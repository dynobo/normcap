"""Load translations dictionary for usage in GUI."""

import gettext
from pathlib import Path

translate = gettext.translation(
    domain="messages",
    localedir=Path(__file__).resolve().parents[1] / "resources" / "locales",
    fallback=True,
)
_ = translate.gettext
