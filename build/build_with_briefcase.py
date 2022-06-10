"""Adjustments executed while packaging with briefcase during CI/CD."""

import fileinput
import hashlib
import inspect
import os
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import briefcase  # type: ignore
import toml

platform_str = sys.platform.lower()


EXCLUDE_FROM_PySide6 = [
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
]
# Excluding this breaks application:
# "printsupport",

EXCLUDE_FROM_APP_PACKAGES = [
    "/tests/",
    "docs",
]

EXCLUDE_FROM_LIB = ["qt6qml"]


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


def patch_windows_installer():
    """Customize wix-installer.

    Currently only branding is added.
    """
    print("Preparing installer...")

    wxs_file = Path.cwd() / "windows" / "msi" / "NormCap" / "normcap.wxs"

    # Cache header for inserting later
    with open(wxs_file, encoding="utf-8") as f:
        header_lines = f.readlines()[:3]

    ns = "{http://schemas.microsoft.com/wix/2006/wi}"
    ET.register_namespace("", ns[1:-1])

    tree = ET.parse(wxs_file)
    root = tree.getroot()
    product = root.find(f"{ns}Product")

    # Copy installer images
    left = "normcap_install_bg.bmp"
    top = "normcap_install_top.bmp"
    for image in [left, top]:
        original = Path.cwd() / "src" / "normcap" / "resources" / image
        target = Path.cwd() / "windows" / "msi" / "NormCap" / image
        shutil.copy(original, target)

    # Set installer images
    ET.SubElement(product, "WixVariable", {"Id": "WixUIDialogBmp", "Value": f"{left}"})
    ET.SubElement(product, "WixVariable", {"Id": "WixUIBannerBmp", "Value": f"{top}"})

    # Allow upgrades
    major_upgrade = ET.SubElement(product, "MajorUpgrade")
    major_upgrade.set("DowngradeErrorMessage", "Can't downgrade. Uninstall first.")

    sequence = product.find(f"{ns}InstallExecuteSequence")
    product.remove(sequence)

    upgrade = product.find(f"{ns}Upgrade")
    product.remove(upgrade)

    # Write & fix header
    tree.write(wxs_file, encoding="utf-8", xml_declaration=False)
    with open(wxs_file, "r+", encoding="utf-8") as f:
        lines = f.readlines()
        f.seek(0)
        f.writelines(header_lines + lines)

    print("Installer prepared.")


def download_openssl():
    """Download openssl needed for QNetwork https connections."""
    target_path = Path.cwd() / "src" / "normcap" / "resources" / "openssl"
    target_path.mkdir(exist_ok=True)
    zip_path = Path.cwd() / "openssl.zip"
    urllib.request.urlretrieve(
        "http://wiki.overbyte.eu/arch/openssl-1.1.1m-win64.zip", zip_path
    )
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(target_path)
    print("Openssl extracted")


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


def download_tesseract_windows_build():
    # Link to download artifact might change
    # https://ci.appveyor.com/project/zdenop/tesseract/build/artifacts

    resources_path = Path.cwd() / "src" / "normcap" / "resources"
    tesseract_path = resources_path / "tesseract"

    cmd(
        "curl -L -o tesseract.zip "
        + "https://ci.appveyor.com/api/projects/zdenop/tesseract/artifacts/tesseract.zip"
    )
    zip_file = Path("tesseract.zip")
    with zipfile.ZipFile(zip_file) as artifact_zip:
        members = [
            m
            for m in artifact_zip.namelist()
            if ".test." not in m and ".training." not in m
        ]
        subdir = members[0].split("/")[0]
        artifact_zip.extractall(path=resources_path, members=members)
    print("Tesseract binaries downloaded")

    shutil.rmtree(tesseract_path, ignore_errors=True)

    os.rename(
        resources_path / subdir,
        tesseract_path,
    )
    os.rename(
        tesseract_path / "google.tesseract.tesseract-master.exe",
        tesseract_path / "tesseract.exe",
    )

    print("Tesseract.exe renamed.")


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


def patch_briefcase_appimage_to_prune_deps():
    """Insert code into briefcase appimage code to remove unnecessary libs."""
    def_rm_recursive = inspect.getsource(rm_recursive)

    file_path = Path(briefcase.__file__).parent / "platforms" / "linux" / "appimage.py"
    patch = f"""
import shutil, os
{def_rm_recursive}
app_dir = self.appdir_path(app) / "usr" / "app_packages"
rm_recursive(directory=app_dir, exclude={EXCLUDE_FROM_APP_PACKAGES})
rm_recursive(directory=app_dir / "PySide6", exclude={EXCLUDE_FROM_PySide6})

lib_dir = self.appdir_path(app) / "usr" / "lib"
rm_recursive(directory=lib_dir / "PySide6", exclude={EXCLUDE_FROM_PySide6})
"""
    insert_after = 'self.logger.info(f"[{app.app_name}] Building AppImage...")'
    patch_file(file_path=file_path, insert_after=insert_after, patch=patch)


def patch_info_plist_for_proper_fullscreen():
    """Set attribute to keep dock and menubar hidden in fullscreen.

    See details:
    https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/LaunchServicesKeys.html#//apple_ref/doc/uid/20001431-113616
    """
    file_path = Path("macOS/app/NormCap/NormCap.app/Contents") / "Info.plist"
    patch = """
    <key>LSUIPresentationMode</key>
    <integer>3</integer>
"""
    insert_after = "<string>normcap</string>"
    patch_file(
        file_path=file_path, insert_after=insert_after, patch=patch, mark_patched=False
    )


def patch_briefcase_appimage_to_include_tesseract():
    """Insert code into briefcase appimage code to remove unnecessary libs."""
    file_path = Path(briefcase.__file__).parent / "platforms" / "linux" / "appimage.py"
    insert_after = '"-o", "appimage",'
    patch = """
"--executable",
"/usr/bin/tesseract",
"""
    patch_file(file_path=file_path, insert_after=insert_after, patch=patch)


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


def patch_briefcase_create_to_adjust_dockerfile():
    """Add code to add tesseract ppa to Dockerfile."""
    file_path = Path(briefcase.__file__).parent / "commands" / "create.py"
    insert_after = "self.install_app_support_package(app=app)"
    patch = """
if "linux" in str(bundle_path):
    print()
    print("Patching Dockerfile on Linux")
    import fileinput
    patch = "\\nRUN apt-add-repository ppa:alex-p/tesseract-ocr-devel"
    for line in fileinput.FileInput(bundle_path / "Dockerfile", inplace=1):
        if "RUN apt-add-repository ppa:deadsnakes/ppa" in line:
            line = line.replace(line, line + patch)
        print(line, end="")
"""
    patch_file(file_path=file_path, insert_after=insert_after, patch=patch)


def add_metainfo_to_appimage():
    """Copy metainfo file with info for appimage hub."""
    metainfo = Path.cwd() / "src" / "normcap" / "resources" / "metainfo"
    target_path = (
        Path.cwd()
        / "linux"
        / "appimage"
        / "NormCap"
        / "NormCap.AppDir"
        / "usr"
        / "share"
    )
    shutil.copy(metainfo, target_path / "metainfo")


if __name__ == "__main__":
    if platform_str.lower().startswith("win"):
        app_dir = Path.cwd() / "windows" / "msi" / "NormCap" / "src" / "app_packages"
        download_tesseract_windows_build()
        download_tessdata()
        download_openssl()
        cmd("briefcase create")
        rm_recursive(directory=app_dir, exclude=EXCLUDE_FROM_APP_PACKAGES)
        rm_recursive(directory=app_dir / "PySide6", exclude=EXCLUDE_FROM_PySide6)
        cmd("briefcase build")
        patch_windows_installer()
        cmd("briefcase package")
        if "dev" in sys.argv:
            cmd("mv windows/*.msi windows/NormCap-unstable-Windows.msi")
        else:
            cmd(f"mv windows/*.msi windows/NormCap-{get_version()}-Windows.msi")

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
        cmd("brew install dylibbundler")
        cmd("briefcase create")
        bundle_pytesseract_dylibs()
        rm_recursive(directory=app_dir, exclude=EXCLUDE_FROM_APP_PACKAGES)
        rm_recursive(directory=app_dir / "PySide6", exclude=EXCLUDE_FROM_PySide6)
        cmd("briefcase build")
        # TODO: Re-enable if we have a solution for unfocusing on MacOS
        # patch_info_plist_for_proper_fullscreen()
        cmd("briefcase package macos app --no-sign")
        if "dev" in sys.argv:
            cmd("mv macOS/*.dmg macOS/NormCap-unstable-MacOS.dmg")
        else:
            cmd(f"mv macOS/*.dmg macOS/NormCap-{get_version()}-MacOS.dmg")

    elif platform_str.lower().startswith("linux"):
        if system_requires := get_system_requires("linux"):
            github_actions_uid = 1001
            if os.getuid() == github_actions_uid:  # type: ignore
                cmd("sudo apt update")
                cmd(f"sudo apt install {' '.join(system_requires)}")
        download_tessdata()
        patch_briefcase_appimage_to_prune_deps()
        patch_briefcase_appimage_to_include_tesseract()
        patch_briefcase_create_to_adjust_dockerfile()
        cmd("briefcase create")
        cmd("briefcase build")
        cmd("briefcase package")
        if "dev" in sys.argv:
            cmd("mv linux/*.AppImage linux/NormCap-unstable-x86_64.AppImage")
    else:
        raise ValueError("Unknown operating system.")
