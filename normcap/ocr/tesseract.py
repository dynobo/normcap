import csv
import logging
import os
import re
import subprocess
import tempfile
from os import PathLike
from pathlib import Path
from typing import Optional

from PySide6 import QtCore
from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)


def _run_command(cmd_args: list[str], stdin: Optional[bytes] = None) -> str:
    try:
        output = subprocess.run(cmd_args, capture_output=True, input=stdin)
        output_str = output.stdout.decode("utf-8")
        logger.debug("Tesseract command output:\n%s", output_str.strip())
        if output.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=output.returncode, cmd=output.args, stderr=output.stderr
            )
    except FileNotFoundError as e:
        raise FileNotFoundError("Could not find Tesseract binary") from e
    return output_str


def get_languages(
    tesseract_cmd: PathLike, tessdata_path: Optional[PathLike]
) -> list[str]:
    cmd_args = [str(tesseract_cmd), "--list-langs"]
    if tessdata_path:
        cmd_args.extend(["--tessdata-dir", str(tessdata_path)])

    output = _run_command(cmd_args=cmd_args)

    languages = re.findall(r"^([a-zA-Z_]+)\r{0,1}$", output, flags=re.M)

    if not languages:
        raise ValueError(
            "Could not load any languages for tesseract. "
            "On Windows, make sure that TESSDATA_PREFIX environment variable is set. "
            "On Linux/macOS see if 'tesseract --list-langs' work is the command line."
        )
    return languages


def _run_tesseract(cmd: PathLike, image: QImage, args: list[str]) -> list[list[str]]:
    with tempfile.NamedTemporaryFile(
        prefix="normcap_", suffix=".png", delete=False
    ) as input_image_fh:
        image.save(input_image_fh.name)
        input_image_path = input_image_fh.name
    output_tsv_path = f"{input_image_path}.tsv"

    try:
        cmd_args = [
            str(cmd),
            input_image_path,
            input_image_path,  # will be suffixed with .tsv
            "-c",
            "tessedit_create_tsv=1",
            *args,
        ]
        _ = _run_command(cmd_args=cmd_args)
        with Path(output_tsv_path).open() as fh:
            tsv_file = csv.reader(fh, delimiter="\t")
            lines = list(tsv_file)
    finally:
        Path(input_image_path).unlink(missing_ok=True)
        Path(output_tsv_path).unlink(missing_ok=True)

    return lines


def _run_tesseract_piped(
    cmd: PathLike, image: QImage, args: list[str]
) -> list[list[str]]:
    """Pipe image through stdin and read the result through stdout.

    TODO: Seems a bit slower. Needs further testing.
    """
    cmd_args = [
        str(cmd),
        "stdin",
        "stdout",
        "-c",
        "tessedit_create_tsv=1",
        *args,
    ]

    buffer = QtCore.QBuffer()
    try:
        qt_openmode = QtCore.QIODevice.OpenModeFlag
    except AttributeError:
        qt_openmode = QtCore.QIODevice.OpenMode
    buffer.open(qt_openmode.ReadWrite)
    image.save(buffer, "png")  # type: ignore

    output = _run_command(cmd_args=cmd_args, stdin=buffer.data())
    lines = output.strip().split(os.linesep)
    tsv_file = csv.reader(lines, delimiter="\t")
    lines = list(tsv_file)  # type: ignore
    return lines  # type:ignore


def _tsv_to_list_of_dict(tsv_lines: list[list[str]]) -> list[dict]:
    fields = tsv_lines.pop(0)
    words: list[dict] = [{} for _ in range(len(tsv_lines))]
    for idx, line in enumerate(tsv_lines):
        for field, value in zip(fields, line):
            if field == "text":
                words[idx][field] = value
            elif field == "conf":
                words[idx][field] = float(value)
            else:
                words[idx][field] = int(value)

    # Filter empty words
    words = [w for w in words if "text" in w]
    return [w for w in words if w["text"].strip()]


def perform_ocr(cmd: PathLike, image: QImage, args: list[str]) -> list[dict]:
    lines = _run_tesseract(cmd=cmd, image=image, args=args)
    word_data_new = _tsv_to_list_of_dict(lines)
    return word_data_new
