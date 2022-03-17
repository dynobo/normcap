"""Global constants."""

from normcap.gui.models import Setting, Urls

DEFAULT_SETTINGS = (
    Setting(
        key="color",
        flag="c",
        type_=str,
        value="#FF2E88",
        help="set primary color for UI, e.g. '#FF2E88'",
        choices=None,
    ),
    Setting(
        key="language",
        flag="l",
        type_=lambda s: list(s.split("+")),
        value=("eng",),
        help="set language(s) for text recognition, e.g. 'eng' or 'eng+deu'",
        choices=None,
    ),
    Setting(
        key="mode",
        flag="m",
        type_=str,
        value="parse",
        help="set capture mode",
        choices=("raw", "parse"),
    ),
    Setting(
        key="notification",
        flag="n",
        type_=bool,
        value=True,
        help="disable or enable notification after ocr detection",
        choices=(True, False),
    ),
    Setting(
        key="tray",
        flag="t",
        type_=bool,
        value=False,
        help="disable or enable system tray",
        choices=(True, False),
    ),
    Setting(
        key="update",
        flag="u",
        type_=bool,
        value=False,
        help="disable or enable check for updates",
        choices=(True, False),
    ),
)

URLS = Urls(
    releases="https://github.com/dynobo/normcap/releases",
    changelog="https://github.com/dynobo/normcap/blob/main/CHANGELOG.md",
    pypi="https://pypi.org/pypi/normcap",
    github="https://github.com/dynobo/normcap",
    issues="https://github.com/dynobo/normcap/issues",
    faqs="https://dynobo.github.io/normcap/#faqs",
    website="https://dynobo.github.io/normcap",
    xcb_error="https://github.com/dynobo/normcap/blob/main/FAQ.md"
    + "#linux-could-not-load-the-qt-platform-plugin-xcb",
)

DESCRIPTION = (
    "OCR-powered screen-capture tool to capture information instead of images."
)

MESSAGE_LANGUAGES = (
    "You are not using the prebuild package version of NormCap. "
    "Please refer to the documentation of Tesseract for your "
    "operating system on how to install additional languages."
)
