#!/usr/bin/env python

import argparse
from pathlib import Path

from babel.messages.frontend import CommandLineInterface


def _get_version() -> str:
    """Get versions string from pyproject.toml."""
    import toml

    with (Path(__file__).parent / "pyproject.toml").open(encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)
    return pyproject_toml["tool"]["poetry"]["version"]


def compile_locales() -> None:
    CommandLineInterface().run(
        ["pybabel", "compile", "--directory", "normcap/resources/locales"]
    )


def extract_strings() -> None:
    CommandLineInterface().run(
        [
            "pybabel",
            "extract",
            "--copyright-holder=dynobo",
            "--project=NormCap",
            f"--version={_get_version()}",
            "--msgid-bugs-address=dynobo@mailbox.org",
            "--add-comments=L10N:",
            "--strip-comment-tag",
            "--input-dirs=./normcap",
            "--output-file=./normcap/resources/locales/messages.pot",
        ]
    )


def update_locales() -> None:
    CommandLineInterface().run(
        [
            "pybabel",
            "update",
            "--input-file=./normcap/resources/locales/messages.pot",
            "--output-dir=./normcap/resources/locales",
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="l10n",
        description=("Compile NormCap localizations to .mo-files."),
    )
    parser.add_argument(
        "--update-all",
        action="store_true",
        default=False,
        help="Also extract strings (.pot) and update locales (.po).",
    )
    args = parser.parse_args()

    if args.update_all:
        extract_strings()
        update_locales()

    compile_locales()
