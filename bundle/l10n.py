#!/usr/bin/env python

import argparse
import contextlib
import io
import re
import subprocess
from pathlib import Path

import toml
from babel.messages.frontend import CommandLineInterface

LOCALES_PATH = Path(__file__).parent.parent / "normcap" / "resources" / "locales"


def _get_version() -> str:
    """Get normcap versions string."""
    try:
        from normcap import __version__

        version = __version__
    except Exception:
        print("Could not import __version__. Fallback to pyproject.toml.")  # noqa: T201
        with (Path(__file__).parent.parent / "pyproject.toml").open(
            encoding="utf8"
        ) as toml_file:
            pyproject_toml = toml.load(toml_file)
        version = pyproject_toml["tool"]["briefcase"]["version"]

    return version


def _update_coverage(lines: list[str]) -> None:
    # Parse stats
    locales_stats = [line for line in lines if line.endswith(".po")]

    locales_rows = sorted(
        f"| [{m[3]}](./{m[3]}/LC_MESSAGES/messages.po) | {m[2]} | {m[1]} |"
        for stat in locales_stats
        if (
            m := re.search(
                r"""(\d+\ of\ \d+).*        # message counts
                \((\d+\%)\).*               # message percentage
                locales\/(.*)\/LC_MESSAGES  # locale name""",
                stat,
                re.VERBOSE,
            )
        )
    )
    locales_rows.sort()

    # Generate markdown table
    coverage_table = (
        "<!-- Generated automatically! -->\n\n"
        "| Locale | Progress | Translated |\n| :----- | -------: | ---------: |\n"
        + "\n".join(locales_rows)
        + "\n"
    )

    # Render stats to markdown file
    md_file = LOCALES_PATH / "README.md"
    md_text = md_file.read_text("utf-8")
    md_text = re.sub(
        r"(.*## Status\n).*?(##.*)",
        rf"\1\n{coverage_table}\n\2",
        md_text,
        flags=re.DOTALL,
    )
    md_file.write_text(md_text, "utf-8")

    subprocess.run(
        f"mdformat {md_file.resolve()}",
        shell=True,  # noqa: S602
        check=True,
        capture_output=True,
        encoding="utf-8",
    )


def compile_locales() -> None:
    CommandLineInterface().run(
        [
            "pybabel",
            "compile",
            "--use-fuzzy",
            "--directory",
            f"{LOCALES_PATH.resolve()}",
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
            f"--input-dir={Path('__file__').parent.parent.resolve()}",
            f"--output-file={(LOCALES_PATH / 'messages.pot').resolve()}",
        ]
    )


def update_locales() -> None:
    CommandLineInterface().run(
        [
            "pybabel",
            "update",
            f"--input-file={(LOCALES_PATH / 'messages.pot').resolve()}",
            f"--output-dir={LOCALES_PATH.resolve()}",
            "--width=79",
            "--ignore-obsolete",
        ]
    )


def create_new(locales: list[str]) -> None:
    for locale in locales:
        CommandLineInterface().run(
            [
                "pybabel",
                "init",
                f"--input-file={(LOCALES_PATH / 'messages.pot').resolve()}",
                f"--output-dir={LOCALES_PATH.resolve()}",
                f"--locale={locale}",
            ]
        )


def main(args: argparse.Namespace) -> None:
    if args.update_all:
        extract_strings()
        update_locales()
    if args.create_new:
        create_new(locales=args.create_new)
    compile_locales()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="l10n",
        description=("Compile NormCap localizations to .mo-files."),
    )
    parser.add_argument(
        "--create-new",
        action="store",
        type=str,
        default=False,
        help="Create locales (.po) for one or more new locales (e.g. de_DE).",
        nargs="+",
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
            main(args)
        output = f.getvalue()
        print(output, flush=True)  # noqa: T201
        _update_coverage(lines=output.splitlines())
    except Exception:
        # In case of error, run again without output capturing
        main(args)
