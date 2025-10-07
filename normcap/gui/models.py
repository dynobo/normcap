"""Various Data Models."""

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, NamedTuple

logger = logging.getLogger(__name__)

# Type aliases
Seconds = float
Days = int


class Setting(NamedTuple):
    key: str
    flag: str
    type_: type | Callable
    value: Any
    choices: Iterable | None
    help_: str
    cli_arg: bool
    nargs: int | str | None


@dataclass
class Urls:
    """URLs used on various places."""

    releases: str
    changelog: str
    pypi: str
    github: str
    issues: str
    website: str
    faqs: str
    buymeacoffee: str

    @property
    def releases_atom(self) -> str:
        """URL to github releases rss feed."""
        return f"{self.releases}.atom"

    @property
    def pypi_json(self) -> str:
        """URL to github releases rss feed."""
        return f"{self.pypi}/json"
