from normcap.models import Setting, Urls

DEFAULT_SETTINGS = (
    Setting(
        key="color",
        flag="c",
        type_=str,
        value="#FF2E88",
        help="set primary color for UI, e.g. '#FF2E88'",
    ),
    Setting(
        key="language",
        flag="l",
        type_=lambda s: list(s.split("+")),
        value=("eng",),
        help="set language(s) for text recognition, e.g. 'eng' or 'eng+deu'",
    ),
    Setting(
        key="mode",
        flag="m",
        type_=str,
        value="parse",
        help="set capture mode to 'raw' or 'parse'",
    ),
    Setting(
        key="notification",
        flag="n",
        type_=bool,
        value=True,
        help="disable or enable notification after ocr detection with '0' or '1' ",
    ),
    Setting(
        key="tray",
        flag="t",
        type_=bool,
        value=False,
        help="disable or enable system tray with '0' or '1'",
    ),
    Setting(
        key="update",
        flag="u",
        type_=bool,
        value=False,
        help="disable or enable check for updates with '0' or '1'",
    ),
)

URLS = Urls(
    releases="https://github.com/dynobo/normcap/releases",
    changelog="https://github.com/dynobo/normcap/blob/main/CHANGELOG.md",
    pypi="https://pypi.org/pypi/normcap",
    github="https://github.com/dynobo/normcap",
    issues="https://github.com/dynobo/normcap/issues",
    faqs="https://github.com/dynobo/normcap/blob/main/FAQ.md",
    xcb_error="https://github.com/dynobo/normcap/blob/main/FAQ.md"
    + "#linux-could-not-load-the-qt-platform-plugin-xcb",
)

FILE_ISSUE_TEXT = (
    "Please create a new issue with the output above on "
    f"{URLS.issues} . I'll see what I can do about it."
)

DESCRIPTION = (
    "OCR-powered screen-capture tool to capture information instead of images."
)

MESSAGE_LANGUAGES = (
    "You are not using the prebuild package version of NormCap. "
    "Please refer to the documentation of Tesseract for your "
    "Operating System on how to install additional languages."
)
