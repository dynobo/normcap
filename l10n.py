#!/usr/bin/env python

import argparse
import contextlib
import io
import re
from pathlib import Path

from babel.messages.frontend import CommandLineInterface


def _get_version() -> str:
    """Get versions string from pyproject.toml."""
    import toml

    with (Path(__file__).parent / "pyproject.toml").open(encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)
    return pyproject_toml["tool"]["poetry"]["version"]


def _update_coverage(lines: list[str]) -> None:
    # Parse stats
    locales_stats = [line for line in lines if line.endswith(".po")]

    locales_rows = []
    for stat in locales_stats:
        if m := re.search(
            r"""(\d+\ of\ \d+).*            # message counts
                \((\d+\%)\).*               # message percentage
                locales\/(.*)\/LC_MESSAGES  # locale name""",
            stat,
            re.VERBOSE,
        ):
            locales_rows.append(
                f"| [{m[3]}](./{m[3]}/LC_MESSAGES/messages.po) "
                f"| {m[2]} "
                f"| {m[1]} |"
            )
    locales_rows.sort()

    # Generate markdown table
    coverage_table = (
        "| Locale | Progress | Translated |\n| :----- | -------: | ---------: |\n"
        + "\n".join(locales_rows)
        + "\n"
    )

    # Render stats to markdown file
    md_file = Path(__file__).parent / "normcap" / "resources" / "locales" / "README.md"
    md_text = md_file.read_text("utf-8")
    md_text = re.sub(
        r"(.*## Status\n).*?(##.*)",
        rf"\1\n{coverage_table}\n\2",
        md_text,
        flags=re.DOTALL,
    )
    md_file.write_text(md_text, "utf-8")


def compile_locales() -> None:
    CommandLineInterface().run(
        [
            "pybabel",
            "compile",
            "--use-fuzzy",
            "--directory",
            "normcap/resources/locales",
            "--statistics",
        ]
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
            "--width=79",
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
            "--width=79",
            "--ignore-obsolete",
            "--omit-header",
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

    try:
        # Run commands while capturing output to generate stats.
        f = io.StringIO()
        with contextlib.redirect_stderr(f), contextlib.redirect_stdout(f):
            if args.update_all:
                extract_strings()
                update_locales()
            compile_locales()
        output = f.getvalue()
        print(output)  # noqa: T201
        _update_coverage(lines=output.splitlines())
    except Exception:
        # In case of error, run again without output capturing
        if args.update_all:
            extract_strings()
            update_locales()
        compile_locales()
