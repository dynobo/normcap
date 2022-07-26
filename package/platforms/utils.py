"""Adjustments executed while packaging with briefcase during CI/CD."""

import fileinput
import hashlib
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

import toml

BRIEFCASE_EXCLUDES = dict(
    pyside6=[
        "3danimation",
        "3dcore",
        "3dextras",
        "3drender",
        "assistant",
        "audio",
        "bluetooth",
        "canbus",
        "charts",
        "datavisualization",
        "designer",
        "examples",
        "gamepad",
        "geoservices",
        "help",
        "icudtl",
        "labs",
        "libexec",
        "linguist",
        "location",
        "lupdate",
        "mediaservice",
        "multimedia",
        "nfc",
        "openglfunct",
        "pdf",
        "purchasing",
        "qt63d",
        "qt6quick",
        "qt6shadertools",
        "qtopengl",
        "qtquick",
        "rcc",
        "remoteobjects",
        "scene",
        "sensor",
        "serialport",
        "sql",
        "test",
        "texttospeech",
        "uic",
        "uitools",
        "virtualkeyboard",
        "webchannel",
        "webengine",
        "websockets",
        "webview",
    ],
    app_packages=[
        "/tests/",
        "docs",
    ],
    lib=["qt6"],
)


def rm_recursive(directory, exclude):
    """Remove excluded files from package."""
    for package_path in directory.glob(r"**/*"):
        path_str = str(package_path.absolute()).lower()
        if any(e in path_str for e in exclude):
            if not package_path.exists():
                continue
            print(f"Removing: {package_path.absolute()}")
            if package_path.is_dir():
                shutil.rmtree(package_path)
            if package_path.is_file():
                os.remove(package_path)


class BuilderBase(ABC):
    """Creates a prebuild package."""

    PROJECT_PATH = Path(__file__).absolute().parent.parent.parent
    BUILD_PATH = (PROJECT_PATH / "package").resolve()
    IMG_PATH = BUILD_PATH / "imgs"
    RESOURCE_PATH = PROJECT_PATH / "src" / "normcap" / "resources"
    TESSERACT_PATH = RESOURCE_PATH / "tesseract"
    PYPROJECT_PATH = PROJECT_PATH / "pyproject.toml"
    VENV_PATH = Path(os.environ["VIRTUAL_ENV"])
    binary_suffix = "_legacy"

    @abstractmethod
    def run_framework(self):
        """Run nuitka compiler and rename resulting package."""

    @abstractmethod
    def bundle_tesseract(self):
        """Include tesseract binary and its dependencies."""

    @abstractmethod
    def install_system_deps(self):
        """Install system dependencies required for building."""

    @abstractmethod
    def create(self):
        """Run all steps to build prebuild packages."""

    def get_system_requires(self) -> list[str]:
        """Get versions string from pyproject.toml."""
        with open(self.PYPROJECT_PATH, encoding="utf8") as toml_file:
            pyproject_toml = toml.load(toml_file)
        return pyproject_toml["tool"]["briefcase"]["app"]["normcap"][sys.platform][
            "system_requires"
        ]

    def get_version(self) -> str:
        """Get versions string from pyproject.toml."""
        if "--dev" in sys.argv:
            return "0.0.1"

        with open(self.PYPROJECT_PATH, encoding="utf8") as toml_file:
            pyproject_toml = toml.load(toml_file)
        return pyproject_toml["tool"]["poetry"]["version"]

    @staticmethod
    def run(cmd: Union[str, list], cwd=None):
        """Executes a shell command and raises in case of error."""
        if not isinstance(cmd, str):
            cmd = " ".join(cmd)

        cmd_str = re.sub(r"\s+", " ", cmd)
        print(f">>> {cmd_str}")

        completed_proc = subprocess.run(  # pylint: disable=subprocess-run-check
            cmd, shell=True, cwd=cwd, capture_output=True
        )
        if completed_proc.returncode != 0:
            print(completed_proc.stdout.decode("utf-8"))
            print(completed_proc.stderr.decode("utf-8"))
            raise subprocess.CalledProcessError(
                returncode=completed_proc.returncode,
                cmd=cmd,
                output=completed_proc.stdout,
                stderr=completed_proc.stderr,
            )

        return completed_proc.stdout

    def download_tessdata(self):
        """Download trained data for tesseract to include in packages."""
        print("Downloading tessdata...")
        tessdata_path = self.RESOURCE_PATH / "tessdata"
        url_prefix = (
            "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0"
        )
        files = [
            "ara.traineddata",
            "chi_sim.traineddata",
            "deu.traineddata",
            "rus.traineddata",
            "spa.traineddata",
            "eng.traineddata",
        ]

        if len(list(tessdata_path.glob("*.traineddata"))) >= len(files):
            print("Language data already present. Skipping download.")
            return

        print("Downloading language data...")
        for file_name in files:
            url = f"{url_prefix}/{file_name}"
            urllib.request.urlretrieve(f"{url}", tessdata_path / file_name)
            print(f"Downloaded {url} to {(tessdata_path / file_name).absolute()}")

        print("Download done.")

    @staticmethod
    def patch_file(
        file_path: Path, insert_after: str, patch: str, mark_patched: bool = True
    ):
        """Insert lines in file, if not already done.

        Indents the patch like the line after which it is inserted.
        """
        patch_applied = False
        patch_hash = hashlib.md5(patch.encode()).hexdigest()

        with open(file_path, "r", encoding="utf8") as f:
            if f.read().find(patch_hash) > -1:
                print("Skipping patch. Already applied.")
                return

        print(f"Patching file {file_path.resolve()}")
        if mark_patched:
            patch = (
                f"# dynobo: {patch_hash} >>>>>>>>>>>>>>"
                + patch
                + f"# dynobo: {patch_hash} <<<<<<<<<<<<<<\n"
            )
        for line in fileinput.FileInput(file_path, inplace=True):
            if insert_after in line:
                pad = len(line) - len(line.lstrip(" "))
                patch = patch.replace("\n", f"\n{pad * ' '}")
                line = line.replace(line, line + pad * " " + patch + "\n")
                patch_applied = True
            print(line, end="")

        if not patch_applied:
            raise RuntimeError(
                f"Couldn't apply patch to file {file_path}! "
                + f"Line '{insert_after}' not found!"
            )
