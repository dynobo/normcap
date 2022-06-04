"""Adjustments executed while packaging with briefcase during CI/CD."""

import os
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import toml

platform_str = sys.platform.lower()


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
    if platform_str.lower().startswith("win"):
        raise NotImplementedError

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
            "nuitka3 "
            + "--onefile "  # Use for building distribution packages
            # + "--standalone "  # Use for debugging build process
            + "--assume-yes-for-downloads "
            + "--linux-onefile-icon=src/normcap/resources/normcap.svg "
            + "--enable-plugin=pyside6 "
            + "--include-package=normcap.resources "
            + "--include-package-data=normcap.resources "
            + "src/normcap/app.py"
        )
        version = "unstable" if "dev" in sys.argv else get_version()
        cmd(f"mv app.bin NormCap-{version}-x86_64.AppImage")
    else:
        raise ValueError("Unknown operating system.")
