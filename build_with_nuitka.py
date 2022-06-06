"""Adjustments executed while packaging with briefcase during CI/CD."""

import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Union

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


def cmd(cmd_str: Union[str, list], cwd=None):
    """Run command in subprocess.run()."""
    if not isinstance(cmd_str, str):
        cmd_str = " ".join(cmd_str)

    completed_proc = subprocess.run(  # pylint: disable=subprocess-run-check
        cmd_str, shell=True, cwd=cwd
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


def download_wix_toolset():
    wix_path = Path.cwd() / "wix"
    wix_path.mkdir(exist_ok=True)
    wix_zip = wix_path / "wix-binaries.zip"
    if wix_zip.exists():
        return "Skip downloading wix toolkit. Already there."

    print("Downloading wix toolkit...")
    url = "https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311-binaries.zip"
    urllib.request.urlretrieve(f"{url}", wix_zip)

    print(f"Downloaded {url} to {wix_zip.absolute()}")
    with zipfile.ZipFile(wix_zip, "r") as zip_ref:
        zip_ref.extractall(wix_path)


def prepare_windows_installer():
    print("Copying wxs configuration file to app.dist folder...")
    wxs = Path.cwd() / "assets" / "normcap.wxs"
    shutil.copy(wxs, Path.cwd() / "app.dist")

    print("Copying images to app.dist folder...")
    resource_path = Path.cwd() / "src" / "normcap" / "resources"
    shutil.copy(resource_path / "normcap_install_bg.bmp", Path.cwd() / "app.dist")
    shutil.copy(resource_path / "normcap_install_top.bmp", Path.cwd() / "app.dist")
    shutil.copy(resource_path / "normcap.ico", Path.cwd() / "app.dist")

    print("Compiling application manifest...")
    wix_path = Path().cwd() / "wix"
    cmd(
        [
            str((wix_path / "heat.exe").resolve()),
            "dir",
            "app.dist",
            "-nologo",  # Don't display startup text
            "-gg",  # Generate GUIDs
            "-sfrag",  # Suppress fragment generation for directories
            "-sreg",  # Suppress registry harvesting
            "-srd",  # Suppress harvesting the root directory
            "-scom",  # Suppress harvesting COM components
            "-dr",
            "normcap_ROOTDIR",  # Root directory reference name
            "-cg",
            "normcap_COMPONENTS",  # Root component group name
            "-var",
            "var.SourceDir",  # variable to use as the source dir
            "-out",
            "app.dist/normcap-manifest.wxs",
        ]
    )
    print("Compiling installer...")
    cmd(
        [
            str((wix_path / "candle.exe").resolve()),
            "-nologo",  # Don't display startup text
            "-ext",
            "WixUtilExtension",
            "-ext",
            "WixUIExtension",
            "-dSourceDir=.",
            f"normcap.wxs",
            f"normcap-manifest.wxs",
        ],
        cwd="app.dist"
    )
    print("Linking installer...")
    cmd(
        [
            str((wix_path / "light.exe").resolve()),
            "-nologo",  # Don't display startup text
            "-ext",
            "WixUtilExtension",
            "-ext",
            "WixUIExtension",
            "-o",
            "normcap.msi",
            "normcap.wixobj",
            "normcap-manifest.wixobj",
        ],
        cwd="app.dist"
    )


if __name__ == "__main__":
    download_tessdata()
    platform_str = sys.platform.lower()
    version = "unstable" if "dev" in sys.argv else get_version()

    if platform_str.lower().startswith("win"):
        # TODO: Rename app.exe to NormCap.exe
        # TODO: Adjust run path in normcap wxs
        # TODO: Adjust version number dynamically in wxs
        # TODO: File handling cleaner
        # bundle_tesseract_for_windows()
        # download_wix_toolset()
        # cmd(
        #     "python -m nuitka "
        #     + "--standalone "
        #     + "--assume-yes-for-downloads "
        #     + "--windows-company-name=dynobo "
        #     + "--windows-product-name=NormCap "
        #     + '--windows-file-description="OCR powered screen-capture tool to capture information instead of images." '
        #     + f"--windows-product-version={get_version()} "
        #     + "--windows-icon-from-ico=src/normcap/resources/normcap.ico "
        #     + "--windows-disable-console "
        #     + "--enable-plugin=pyside6 "
        #     + "--include-package=normcap.resources "
        #     + "--include-package-data=normcap.resources "
        #     + "--include-data-files=src/normcap/resources/tesseract/*.dll=normcap/resources/tesseract/ "
        #     + "src/normcap/app.py"
        # )
        prepare_windows_installer()

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
