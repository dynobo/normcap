"""Adjustments executed while packaging with briefcase during CI/CD."""

import fileinput
import hashlib
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

import toml

BRIEFCASE_EXCLUDES = {
    "pyside6": [
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
        "qmllint",
        "qmltooling",
        "qt3dinput",
        "qt63d",
        "qt6quick",
        "qt6shadertools",
        "qtopengl",
        "qtpositioning",
        "qtprintsupport",
        "qtquick",
        "qtqml",
        "qtshadertools",
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
    "app_packages": [
        "/tests/",
        "docs",
    ],
    "lib": ["qt6"],
}


def rm_recursive(directory, exclude):
    """Remove excluded files from package."""
    for package_path in directory.glob(r"**/*"):
        path_str = str(package_path.absolute()).lower()
        if any(e in path_str for e in exclude):
            if not package_path.exists():
                continue
            if package_path.is_dir():
                shutil.rmtree(package_path)
            if package_path.is_file():
                os.remove(package_path)


def build_wl_clipboard(self, app_packages_path):
    self.subprocess.run(
        "git clone https://github.com/bugaevc/wl-clipboard.git".split(),
        check=True,
    )
    self.subprocess.run("meson build wl-clipboard".split(), check=True)
    self.subprocess.run("ninja -C build".split(), capture_output=True, text=True)


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
    TESSDATA_PATH = RESOURCE_PATH / "tessdata"

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
    def run(cmd: Union[str, list], cwd=None) -> Optional[str]:
        """Executes a shell command and raises in case of error."""
        if not isinstance(cmd, str):
            cmd = " ".join(cmd)

        cmd_str = re.sub(r"\s+", " ", cmd)

        completed_proc = subprocess.run(
            cmd_str, shell=True, cwd=cwd, capture_output=False
        )

        if completed_proc.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=completed_proc.returncode,
                cmd=cmd,
                output=completed_proc.stdout,
                stderr=completed_proc.stderr,
            )

        return (
            completed_proc.stdout.decode(encoding="utf8")
            if completed_proc.stdout
            else None
        )

    def download_tessdata(self):
        """Download trained data for tesseract to include in packages."""
        target_path = self.TESSDATA_PATH
        target_path.mkdir(exist_ok=True, parents=True)
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
        if len(list(target_path.glob("*.traineddata"))) >= len(files):
            return

        for file_name in files:
            url = f"{url_prefix}/{file_name}"
            urllib.request.urlretrieve(f"{url}", target_path / file_name)

    @staticmethod
    def patch_file(
        file_path: Path, insert_after: str, patch: str, mark_patched: bool = True
    ):
        """Insert lines in file, if not already done.

        Indents the patch like the line after which it is inserted.
        """
        patch_hash = hashlib.md5(patch.encode()).hexdigest()  # noqa: S324

        with open(file_path, encoding="utf8") as f:
            if f.read().find(patch_hash) > -1:
                return

        if mark_patched:
            patch = (
                f"# dynobo: {patch_hash} >>>>>>>>>>>>>>"
                + patch
                + f"# dynobo: {patch_hash} <<<<<<<<<<<<<<\n"
            )

        patch_applied = False
        for line in fileinput.FileInput(file_path, inplace=True):
            if insert_after in line:
                pad = len(line) - len(line.lstrip(" "))
                patch = patch.replace("\n", f"\n{pad * ' '}")
                line = line.replace(line, line + pad * " " + patch + "\n")
                patch_applied = True
            print(line, end="")  # noqa

        if not patch_applied:
            raise RuntimeError(
                f"Couldn't apply patch to file {file_path}! "
                + f"Line '{insert_after}' not found!"
            )


# TODO: Make sure it's copied to the correct path!
def bundle_tesseract_windows_ub_mannheim(builder: BuilderBase):
    """Download tesseract binaries including dependencies into resource path."""
    # Link to download artifact might change

    tesseract_path = builder.BUILD_PATH / "tesseract"
    tesseract_path.mkdir(exist_ok=True)

    installer_path = tesseract_path / "tesseract-setup.exe"

    url = (
        "https://digi.bib.uni-mannheim.de/tesseract/"
        + "tesseract-ocr-w64-setup-v5.2.0.20220712.exe"
    )
    urllib.request.urlretrieve(url, installer_path)

    if not installer_path.exists():
        raise FileNotFoundError("Downloading of tesseract binaries might have failed!")

    subprocess.run(
        "7z e tesseract-setup.exe", shell=True, cwd=tesseract_path, check=True
    )

    excluded = [
        "LangDLL.dll",
        "nsDialogs.dll",
        "StartMenu.dll",
        "UserInfo.dll",
        "System.dll",
        "INetC.dll",
    ]

    for each_file in Path(tesseract_path).glob("*.*"):
        if (
            (each_file.suffix not in (".exe", ".dll"))
            or (each_file.name in excluded)
            or (each_file.suffix == ".exe" and each_file.name != "tesseract.exe")
        ):
            continue

        (builder.TESSERACT_PATH / each_file.name).unlink(missing_ok=True)
        each_file.rename(builder.TESSERACT_PATH / each_file.name)

    shutil.rmtree(tesseract_path)


def bundle_tesseract_windows_appveyor(builder: BuilderBase):
    """Download tesseract binaries including dependencies into resource path."""
    # Link to download artifact might change

    zip_path = builder.BUILD_PATH / "tesseract.zip"

    if zip_path.exists():
        return

    # TODO: Check if the official build is up again, then remove this mirror:
    # TODO: Extract UB Mannheims installer instead:
    # https://github.com/UB-Mannheim/tesseract/wiki
    url = "https://normcap.needleinthehay.de/tesseract.zip"

    # The official tesseract artefact for windows is build and available here:
    # https://ci.appveyor.com/project/zdenop/tesseract/build/artifacts
    # url = (
    #     "https://ci.appveyor.com/api/projects/zdenop/tesseract/artifacts/tesseract.zip"
    # )

    urllib.request.urlretrieve(url, zip_path)

    if not zip_path.exists():
        raise FileNotFoundError("Downloading of tesseract.zip might have failed!")

    with zipfile.ZipFile(zip_path) as artifact_zip:
        members = [
            m
            for m in artifact_zip.namelist()
            if ".test." not in m and ".training." not in m
        ]
        subdir = members[0].split("/")[0]
        artifact_zip.extractall(path=builder.RESOURCE_PATH, members=members)  #
    zip_path.unlink()

    for each_file in Path(builder.RESOURCE_PATH / subdir).glob("*.*"):
        (builder.TESSERACT_PATH / each_file.name).unlink(missing_ok=True)
        each_file.rename(builder.TESSERACT_PATH / each_file.name)

    (builder.TESSERACT_PATH / "tesseract.exe").unlink(missing_ok=True)
    (builder.TESSERACT_PATH / "google.tesseract.tesseract-main.exe").rename(
        builder.TESSERACT_PATH / "tesseract.exe"
    )

    shutil.rmtree(builder.RESOURCE_PATH / subdir)
