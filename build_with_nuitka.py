"""Adjustments executed while packaging with briefcase during CI/CD."""

import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import toml


def get_version() -> str:
    """Get versions string from pyproject.toml."""
    with open("pyproject.toml", encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)
    return pyproject_toml["tool"]["poetry"]["version"]


def get_system_requires(platform) -> list[str]:
    """Get versions string from pyproject.toml."""
    with open("pyproject.toml", encoding="utf8") as toml_file:
        pyproject_toml = toml.load(toml_file)
    return pyproject_toml["tool"]["briefcase"]["app"]["normcap"][platform][
        "system_requires"
    ]


def cmd(cmd_str: str):
    """Run command in subprocess.run()."""
    completed_proc = subprocess.run(  # pylint: disable=subprocess-run-check
        cmd_str, shell=True
    )
    if completed_proc.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=completed_proc.returncode,
            cmd=cmd_str,
            output=completed_proc.stdout,
            stderr=completed_proc.stderr,
        )


def download_tessdata():
    """Download trained data for tesseract.

    Necessary to include it in the packages.
    """
    target_path = Path.cwd() / "src" / "normcap" / "resources" / "tessdata"
    url_prefix = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0"
    files = [
        "ara.traineddata",
        "chi_sim.traineddata",
        "deu.traineddata",
        "rus.traineddata",
        "spa.traineddata",
        "eng.traineddata",
    ]

    if len(list(target_path.glob("*.traineddata"))) >= len(files):
        print("Language data already present. Skipping download.")
        return

    print("Downloading language data...")
    for file_name in files:
        urllib.request.urlretrieve(f"{url_prefix}/{file_name}", target_path / file_name)
        print(
            f"Downloaded {url_prefix}/{file_name} to {(target_path / file_name).absolute()}"
        )

    print("Download done.")


def bundle_tesseract_for_windows():
    # Link to download artifact might change
    # https://ci.appveyor.com/project/zdenop/tesseract/build/artifacts

    resources_path = Path.cwd() / "src" / "normcap" / "resources"
    tesseract_path = resources_path / "tesseract"

    if (tesseract_path / "tesseract.exe").exists():
        print("Tesseract binary already present. Skipping download.")
        return

    cmd(
        "curl -L -o tesseract.zip "
        + "https://ci.appveyor.com/api/projects/zdenop/tesseract/artifacts/tesseract.zip"
    )
    with zipfile.ZipFile(Path("tesseract.zip")) as artifact_zip:
        members = [
            m
            for m in artifact_zip.namelist()
            if ".test." not in m and ".training." not in m
        ]
        subdir = members[0].split("/")[0]
        artifact_zip.extractall(path=resources_path, members=members)
    print("Tesseract binaries downloaded")

    for each_file in Path(resources_path / subdir).glob("*.*"):
        each_file.rename(tesseract_path / each_file.name)
    (tesseract_path / "google.tesseract.tesseract-master.exe").rename(
        tesseract_path / "tesseract.exe"
    )
    shutil.rmtree(resources_path / subdir)
    print("Binaries moved. Tesseract.exe renamed.")


def bundle_pytesseract_dylibs():
    print("Bundling tesseract libs...")
    app_pkg_path = "macOS/app/NormCap/NormCap.app/Contents/Resources/app_packages"
    tesseract_source = "/usr/local/bin/tesseract"
    tesseract_target = f"{app_pkg_path}/tesseract"
    install_path = "@executable_path/"
    cmd(
        "dylibbundler "
        + f"--fix-file {tesseract_source} "
        + f"--dest-dir {app_pkg_path} "
        + f"--install-path {install_path} "
        + "--bundle-deps "
        + "--overwrite-files"
    )
    shutil.copy(tesseract_source, tesseract_target)


def bundle_tesseract_for_linux():
    target_path = Path.cwd() / "src" / "normcap" / "resources" / "tesseract"
    target_path.mkdir(exist_ok=True)
    cmd(
        "ldd /bin/bash | grep \"=> /\" | awk '{print $3}' | xargs -I '{}' cp -v '{}' "
        + str(target_path.resolve())
    )
    try:
        shutil.copy("/usr/bin/tesseract", target_path)
    except shutil.SameFileError:
        print("'tesseract' already copied.")


if __name__ == "__main__":
    download_tessdata()
    platform_str = sys.platform.lower()
    version = "unstable" if "dev" in sys.argv else get_version()

    if platform_str.lower().startswith("win"):
        bundle_tesseract_for_windows()
        cmd(
            "python -m nuitka "
            + "--standalone "
            + "--assume-yes-for-downloads "
            + "--windows-company-name=dynobo "
            + "--windows-product-name=NormCap "
            + '--windows-file-description="OCR powered screen-capture tool to capture information instead of images." '
            + f"--windows-product-version={get_version()} "
            + "--windows-icon-from-ico=src/normcap/resources/normcap.ico "
            + "--windows-disable-console "
            + "--enable-plugin=pyside6 "
            + "--include-package=normcap.resources "
            + "--include-package-data=normcap.resources "
            + "--include-data-files=src/normcap/resources/tesseract/*.dll=normcap/resources/tesseract/ "
            + "src/normcap/app.py"
        )

    elif platform_str.lower().startswith("darwin"):
        raise NotImplementedError

    elif platform_str.lower().startswith("linux"):
        if system_requires := get_system_requires("linux"):
            github_actions_uid = 1001
            if os.getuid() == github_actions_uid:  # type: ignore
                cmd("sudo apt update")
                cmd(f"sudo apt install {' '.join(system_requires)}")
        bundle_tesseract_for_linux()
        cmd(
            "python -m "
            + "--onefile "
            + "--assume-yes-for-downloads "
            + "--linux-onefile-icon=src/normcap/resources/normcap.svg "
            + "--enable-plugin=pyside6 "
            + "--include-package=normcap.resources "
            + "--include-package-data=normcap.resources "
            + f"-o NormCap-{version}-x86_64.AppImage "
            + "src/normcap/app.py"
        )
    else:
        raise ValueError("Unknown operating system.")
