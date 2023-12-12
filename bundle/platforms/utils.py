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
from textwrap import dedent
from typing import Optional, Union

import toml
from retry import retry


class BuilderBase(ABC):
    """Create a prebuilt package."""

    PROJECT_PATH = Path(__file__).absolute().parent.parent.parent
    BUILD_PATH = (PROJECT_PATH / "bundle").resolve()
    IMG_PATH = BUILD_PATH / "imgs"
    RESOURCE_PATH = PROJECT_PATH / "normcap" / "resources"
    TESSERACT_PATH = RESOURCE_PATH / "tesseract"
    PYPROJECT_PATH = PROJECT_PATH / "pyproject.toml"
    VENV_PATH = Path(os.environ["VIRTUAL_ENV"])
    TESSDATA_PATH = RESOURCE_PATH / "tessdata"
    binary_suffix = "_legacy"
    binary_extension: Optional[str] = None
    binary_platform: Optional[str] = None

    @abstractmethod
    def install_system_deps(self) -> None:
        """Install system dependencies required for building."""

    @abstractmethod
    def bundle_tesseract(self) -> None:
        """Include tesseract binary and its dependencies."""

    @abstractmethod
    def pre_framework(self) -> None:
        """Steps to execute before running the bundling framework."""

    @abstractmethod
    def run_framework(self) -> None:
        """Run compiler and rename resulting package."""

    def rename_package_file(self) -> None:
        """Rename final binary package/installer file."""
        if not self.binary_platform or not self.binary_extension:
            raise AttributeError("bundle_platform and bundle_extension must be set.")

        source = next(
            Path(self.PROJECT_PATH / "dist").glob(f"*.{self.binary_extension}")
        )
        target = self.BUILD_PATH / (
            f"NormCap-{self.get_version()}-{self.binary_platform}{self.binary_suffix}"
            f".{self.binary_extension}"
        )
        target.unlink(missing_ok=True)
        shutil.move(source, target)

    def compile_locales(self) -> None:
        """Create .mo files for all locales."""
        print("Compiling locales...")  # noqa: T201
        self.run(
            cmd="python bundle/l10n.py",
            cwd=self.PROJECT_PATH,
        )

    def clean(self) -> None:
        build_dir = self.PROJECT_PATH / "build"
        if build_dir.exists():
            print(f"Removing old build directory {build_dir.resolve()}")  # noqa: T201
            shutil.rmtree(build_dir, ignore_errors=True)

    def create(self) -> None:
        """Run all steps to build prebuilt packages."""
        self.clean()
        self.download_tessdata()
        self.install_system_deps()
        self.compile_locales()
        self.pre_framework()
        self.run_framework()
        self.rename_package_file()

    def get_version(self) -> str:
        """Get versions string from pyproject.toml."""
        if "--dev" in sys.argv:
            return "0.0.1"

        with Path(self.PYPROJECT_PATH).open(encoding="utf8") as toml_file:
            pyproject_toml = toml.load(toml_file)
        return pyproject_toml["tool"]["briefcase"]["version"]

    @staticmethod
    def run(cmd: Union[str, list], cwd: Optional[Path] = None) -> Optional[str]:
        """Execute a shell command and raises in case of error."""
        if not isinstance(cmd, str):
            cmd = " ".join(cmd)

        cmd_str = re.sub(r"\s+", " ", cmd)

        completed_proc = subprocess.run(
            cmd_str,
            shell=True,  # noqa: S602
            cwd=cwd,
            capture_output=False,
            check=False,
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

    @retry(tries=5, delay=1, backoff=2)
    def download_tessdata(self) -> None:
        """Download trained data for tesseract to include in packages."""
        target_path = self.TESSDATA_PATH
        target_path.mkdir(exist_ok=True, parents=True)
        url_prefix = (
            "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0"
        )
        files = ["eng.traineddata"]
        if len(list(target_path.glob("*.traineddata"))) >= len(files):
            return

        for file_name in files:
            url = f"{url_prefix}/{file_name}"
            urllib.request.urlretrieve(f"{url}", target_path / file_name)  # noqa: S310

    @staticmethod
    def patch_file(
        file_path: Path, insert_after: str, patch: str, comment_prefix: str = "# "
    ) -> None:
        """Insert lines in file, if not already done.

        Indents the patch like the line after which it is inserted.
        """
        patch = dedent(patch.strip("\n"))

        patch_hash = hashlib.md5(patch.encode()).hexdigest()  # noqa: S324

        with Path(file_path).open(encoding="utf8") as f:
            if f.read().find(patch_hash) > -1:
                return

        if comment_prefix:
            patch = (
                f"{comment_prefix} dynobo: {patch_hash} >>>>>>>>>>>>>>\n"
                + patch
                + f"{comment_prefix} dynobo: {patch_hash} <<<<<<<<<<<<<<\n"
            )

        patch_applied = False
        for line in fileinput.FileInput(file_path, inplace=True):
            if insert_after in line:
                pad = len(line) - len(line.lstrip(" "))
                patch = patch.replace("\n", f"\n{pad * ' '}")
                line = line + pad * " " + patch + "\n"  # noqa: PLW2901
                patch_applied = True
            print(line, end="")  # noqa: T201

        if not patch_applied:
            raise RuntimeError(
                f"Couldn't apply patch to file {file_path}! "
                f"Line '{insert_after}' not found!"
            )

    @staticmethod
    def remove_lines_from_file(
        file_path: Path, delete_from: str, delete_to: str
    ) -> None:
        """Delete range of lines (from included, to excluded."""
        from_idx = 0
        to_idx = 0

        with Path(file_path).open() as fh:
            lines = fh.readlines()

        # Find lines
        for idx, line in enumerate(lines):
            if (not from_idx) and (delete_from in line):
                from_idx = idx
            if (not to_idx) and (delete_to in line):
                to_idx = idx

        if not from_idx or not to_idx:
            raise RuntimeError(
                "Could't remove lines. References not found in file. "
                f"(from_idx={from_idx}, to_idx={to_idx})"
            )

        lines = lines[:from_idx] + lines[to_idx:]

        with Path(file_path).open("w") as f:
            f.writelines(lines)


@retry(tries=5, delay=1, backoff=2)
def bundle_tesseract_windows_ub_mannheim(builder: BuilderBase) -> None:
    """Download tesseract binaries including dependencies into resource path."""
    tesseract_path = builder.BUILD_PATH / "tesseract"
    tesseract_path.mkdir(exist_ok=True)
    builder.TESSERACT_PATH.mkdir(exist_ok=True)

    installer_path = tesseract_path / "tesseract-setup.exe"
    url = (
        "https://digi.bib.uni-mannheim.de/tesseract/"
        "tesseract-ocr-w64-setup-v5.3.0.20221214.exe"
    )
    urllib.request.urlretrieve(url, installer_path)  # noqa: S310

    if not installer_path.exists():
        raise FileNotFoundError("Downloading of tesseract binaries might have failed!")

    subprocess.run(
        "7z e tesseract-setup.exe",  # noqa: S607
        shell=True,  # noqa: S602
        cwd=tesseract_path,
        check=True,
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
            (each_file.suffix not in {".exe", ".dll"})
            or (each_file.name in excluded)
            or (each_file.suffix == ".exe" and each_file.name != "tesseract.exe")
        ):
            continue

        (builder.TESSERACT_PATH / each_file.name).unlink(missing_ok=True)
        each_file.rename(builder.TESSERACT_PATH / each_file.name)

    shutil.rmtree(tesseract_path)


@retry(tries=5, delay=1, backoff=2)
def bundle_tesseract_windows_appveyor(builder: BuilderBase) -> None:
    """Download tesseract binaries including dependencies into resource path."""
    zip_path = builder.BUILD_PATH / "tesseract.zip"

    if zip_path.exists():
        return

    url = (
        "https://ci.appveyor.com/api/projects/zdenop/tesseract/artifacts/tesseract.zip"
    )

    urllib.request.urlretrieve(url, zip_path)  # noqa: S310

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
