"""Logger used accross all modules."""

import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)-7s - %(name)s.%(module)-14s - L:%(lineno)-3d - %(message)s",
    datefmt="%H:%M:%S",
    level="WARNING",
)
logger = logging.getLogger(__name__.split(".", maxsplit=1)[0])


def format_section(section: str, title: str) -> str:
    """Wrap a string inside section delimiters."""
    title_start = f" <{title}> "
    title_end = f" </{title}> "
    return f"\n{title_start:-^60s}\n{section.strip()}\n{title_end:-^60s}"
