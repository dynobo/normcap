"""Adjustments executed while packaging with briefcase during CI/CD."""

import inspect
import os
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import List

import briefcase  # type: ignore

platform_str = sys.platform.lower()


EXCLUDE_FROM_PYSIDE2 = [
    "3danimation",
    "3dcore",
    "3dextras",
    "3drender",
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
    "qt3d",
    "qt53d",
    "qt5quick",
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
]
# Excluding this breaks application:
# "printsupport",

EXCLUDE_FROM_APP_PACKAGES = [
    "/tests/",
    "docs",
]


def cmd(cmd_str: str):
    """Wraps subprocess.run()."""
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


def prepare_windows_installer():
    """Customize wix-installer.

    Currently only branding is added.
    """
    print("Preparing installer...")
    left = "normcap_install_bg.bmp"
    top = "normcap_install_top.bmp"

    for image in [left, top]:
        original = Path.cwd() / "src" / "normcap" / "resources" / image
        target = Path.cwd() / "windows" / "msi" / "NormCap" / image
        shutil.copy(original, target)

    with open(
        Path.cwd() / "windows" / "msi" / "NormCap" / "normcap.wxs", "r"
    ) as wxs_file:
        content = wxs_file.readlines()

    insert_idx = None
    for idx, line in enumerate(content):
        if "normcap.ico" in line:
            insert_idx = idx + 1
            break

    if insert_idx is not None:
        content.insert(
            insert_idx, f'        <WixVariable Id="WixUIBannerBmp" Value="{top}" />\n'
        )
        content.insert(
            insert_idx, f'        <WixVariable Id="WixUIDialogBmp" Value="{left}" />\n'
        )
        with open(
            Path.cwd() / "windows" / "msi" / "NormCap" / "normcap.wxs", "w"
        ) as wxs_file:
            wxs_file.writelines(content)
    else:
        raise ValueError("Couldn't patch wxs file!")
    print("Installer prepared.")


def download_openssl():
    """Download openssl needed for QNetwork https connections."""
    target_path = Path.cwd() / "src" / "normcap" / "resources" / "openssl"
    target_path.mkdir()
    zip_path = Path.cwd() / "openssl.zip"
    urllib.request.urlretrieve(
        "http://wiki.overbyte.eu/arch/openssl-1.1.1g-win64.zip", zip_path
    )
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(target_path)
    print("Openssl extracted")


def download_tessdata():
    """Download trained data for tesseract.

    Necessary to include it in the packages.
    """
    print("Downloading language data...")

    target_path = Path.cwd() / "src" / "normcap" / "resources" / "tessdata"
    url_prefix = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/4.1.0"
    files = [
        "ara.traineddata",
        "chi_sim.traineddata",
        "deu.traineddata",
        "rus.traineddata",
        "spa.traineddata",
        "eng.traineddata",
    ]
    for file_name in files:
        urllib.request.urlretrieve(f"{url_prefix}/{file_name}", target_path / file_name)
        print(
            f"Downloaded {url_prefix}/{file_name} to {(target_path / file_name).absolute()}"
        )

    print("Download done.")


def bundle_tesserocr_dylibs():
    """Include two dylibs needed by tesserocr into app package."""
    app_pkg_path = "macOS/app/NormCap/NormCap.app/Contents/Resources/app_packages"

    # Copy libs to package dir

    libtess = "/usr/local/opt/tesseract/lib/libtesseract.4.dylib"
    liblept = "/usr/local/opt/leptonica/lib/liblept.5.dylib"
    libpng = "/usr/local/opt/libpng/lib/libpng16.16.dylib"
    libjpeg = "/usr/local/opt/jpeg/lib/libjpeg.9.dylib"
    libgif = "/usr/local/opt/giflib/lib/libgif.dylib"
    libtiff = "/usr/local/opt/libtiff/lib/libtiff.5.dylib"
    libopenjpeg = "/usr/local/opt/openjpeg/lib/libopenjp2.7.dylib"
    libwebp = "/usr/local/opt/webp/lib/libwebp.7.dylib"
    libwebpmux = "/usr/local/opt/webp/lib/libwebpmux.3.dylib"

    for lib_path in [
        libtess,
        liblept,
        libpng,
        libjpeg,
        libgif,
        libtiff,
        libopenjpeg,
        libwebp,
        libwebpmux,
    ]:
        lib_filename = lib_path.rsplit("/", maxsplit=1)[-1]
        new_lib_path = f"{app_pkg_path}/{lib_filename}"
        shutil.copy(lib_path, new_lib_path)
        os.chmod(new_lib_path, stat.S_IRWXU)

    # Relink libs
    tesserocr = f"{app_pkg_path}/tesserocr.cpython-39-darwin.so"
    libwebp7 = "/usr/local/Cellar/webp/1.2.1/lib/libwebp.7.dylib"
    changeset = [
        (libtiff, [libjpeg]),
        (libwebpmux, [libwebp7]),
        (liblept, [libpng, libjpeg, libgif, libtiff, libopenjpeg, libwebp, libwebpmux]),
        (libtess, [liblept]),
        (tesserocr, [libtess, liblept]),
    ]

    for lib_path, link_paths in changeset:
        lib_filename = lib_path.rsplit("/", maxsplit=1)[-1]
        new_lib_path = f"{app_pkg_path}/{lib_filename}"

        for link_path in link_paths:
            link_filename = link_path.rsplit("/", maxsplit=1)[-1]
            cmd(
                f"install_name_tool -change {link_path} "
                + f"@executable_path/../Resources/app_packages/{link_filename} "
                + f"{new_lib_path}"
            )


def patch_file(file_path: Path, insert_above: str, lines: List[str]):
    """Insert lines above given string of a file."""

    with open(file_path, "r") as f:
        file_content = f.readlines()

    lines = (
        ["", "# dynobo: patch start >>>>>>>>>>>>>>>>>>>>>>>>>"]
        + lines
        + ["# dynobo: patch end <<<<<<<<<<<<<<<<<<<<<<<<<<<", ""]
    )

    found_idx = None
    for idx, line in enumerate(file_content):
        if "# dynobo:" in line:
            print("Patch was already applied!")
            return
        if insert_above in line:
            found_idx = idx
            break

    if not found_idx:
        raise ValueError("Line to manipulate not found!")

    pad = file_content[found_idx].index(insert_above[0]) * " "
    for row in reversed(lines):
        file_content.insert(found_idx, f"{pad}{row}\n")

    with open(file_path, "w") as f:
        print(f"Patching {file_path.absolute()}...")
        f.writelines(file_content)


def rm_recursive(directory, exclude):
    """Remove excluded files from package."""
    for path in directory.glob(r"**/*"):
        path_str = str(path.absolute()).lower()
        if any(e in path_str for e in exclude):
            if not path.exists():
                continue
            print(f"Removing: {str(path.absolute())}")
            if path.is_dir():
                shutil.rmtree(path)
            if path.is_file():
                os.remove(path)


def patch_briefcase_appimage():
    """Insert code into briefcase source code to remove unnecessary libs."""

    # Convert function to string
    def_rm_recursive = inspect.getsource(rm_recursive).splitlines()

    # fmt: off
    lines_to_insert = ['import shutil, os'] + def_rm_recursive + [
        'app_dir = self.appdir_path(app) / "usr" / "app_packages"',
        f'rm_recursive(directory=app_dir, exclude={EXCLUDE_FROM_APP_PACKAGES})',
        f'rm_recursive(directory=app_dir / "PySide2", exclude={EXCLUDE_FROM_PYSIDE2})'
    ]
    # fmt: on

    insert_above = "so_folders = set()"
    file_path = Path(briefcase.__file__).parent / "platforms" / "linux" / "appimage.py"
    patch_file(file_path=file_path, insert_above=insert_above, lines=lines_to_insert)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "download-tessdata":
        download_tessdata()
        sys.exit(0)

    if platform_str.lower().startswith("win"):
        app_dir = Path.cwd() / "windows" / "msi" / "NormCap" / "src" / "app_packages"
        download_tessdata()
        download_openssl()
        cmd("briefcase create")
        rm_recursive(directory=app_dir, exclude=EXCLUDE_FROM_APP_PACKAGES)
        rm_recursive(directory=app_dir / "PySide2", exclude=EXCLUDE_FROM_PYSIDE2)
        cmd("briefcase build")
        prepare_windows_installer()
        cmd("briefcase package")
        cmd("mv windows/*.msi windows/NormCap-Windows.msi")

    elif platform_str.lower().startswith("darwin"):
        app_dir = (
            Path.cwd()
            / "macOS"
            / "app"
            / "NormCap"
            / "NormCap.app"
            / "Contents"
            / "Resources"
            / "app_packages"
        )
        download_tessdata()
        cmd("brew install tesseract")
        cmd("briefcase create")
        bundle_tesserocr_dylibs()
        rm_recursive(directory=app_dir, exclude=EXCLUDE_FROM_APP_PACKAGES)
        rm_recursive(directory=app_dir / "PySide2", exclude=EXCLUDE_FROM_PYSIDE2)
        cmd("briefcase build")
        cmd("briefcase package macos app --no-sign")
        cmd("mv macOS/*.dmg macOS/NormCap-MacOS.dmg")

    elif platform_str.lower().startswith("linux"):
        print(f"Current User ID: {os.getuid()}")  # type: ignore
        github_actions_uid = 1001
        if os.getuid() == github_actions_uid:  # type: ignore
            cmd("sudo apt update")
            cmd("sudo apt install libleptonica-dev libtesseract-dev")
        else:
            print(
                "Dependencies installed? Otherwise, execute:\n"
                "sudo apt install libleptonica-dev libtesseract-dev"
            )
        download_tessdata()
        patch_briefcase_appimage()
        cmd("briefcase create")
        cmd("briefcase build")
        cmd("briefcase package")
        cmd("mv linux/*.AppImage linux/NormCap-Linux.AppImage")

    else:
        raise ValueError("Unknown Operating System.")
