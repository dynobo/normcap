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

PROJECT_PATH = Path("__file__").parent.parent
BUILD_PATH = PROJECT_PATH / "build"
IMG_PATH = BUILD_PATH / "imgs"
RESOURCE_PATH = PROJECT_PATH / "src" / "normcap" / "resources"
TESSERACT_PATH = RESOURCE_PATH / "tesseract"


def get_version() -> str:
    """Get versions string from pyproject.toml."""
    if "dev" in sys.argv:
        return "unstable"

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


def run(cmd: Union[str, list], cwd=None):
    """Run command in subprocess.run()."""
    if not isinstance(cmd, str):
        cmd = " ".join(cmd)

    completed_proc = subprocess.run(  # pylint: disable=subprocess-run-check
        cmd, shell=True, cwd=cwd
    )
    if completed_proc.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=completed_proc.returncode,
            cmd=cmd,
            output=completed_proc.stdout,
            stderr=completed_proc.stderr,
        )


def download_tessdata():
    """Download trained data for tesseract to include in packages."""
    tessdata_path = RESOURCE_PATH / "tessdata"
    url_prefix = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0"
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


def windows_bundle_tesseract():
    # Link to download artifact might change

    # https://ci.appveyor.com/project/zdenop/tesseract/build/artifacts

    if (TESSERACT_PATH / "tesseract.exe").exists():
        print("Tesseract.exe already present. Skipping download.")
        return

    url = (
        "https://ci.appveyor.com/api/projects/zdenop/tesseract/artifacts/tesseract.zip"
    )
    urllib.request.urlretrieve(f"{url}", BUILD_PATH / "tesseract.zip")
    with zipfile.ZipFile(BUILD_PATH / "tesseract.zip") as artifact_zip:
        members = [
            m
            for m in artifact_zip.namelist()
            if ".test." not in m and ".training." not in m
        ]
        subdir = members[0].split("/")[0]
        artifact_zip.extractall(path=RESOURCE_PATH, members=members)
    print("Tesseract binaries downloaded.")

    for each_file in Path(RESOURCE_PATH / subdir).glob("*.*"):
        each_file.rename(TESSERACT_PATH / each_file.name)
    (TESSERACT_PATH / "google.tesseract.tesseract-master.exe").rename(
        TESSERACT_PATH / "tesseract.exe"
    )
    shutil.rmtree(RESOURCE_PATH / subdir)
    print("Binaries moved. Tesseract.exe renamed.")


def bundle_pytesseract_dylibs():
    print("Bundling tesseract libs...")
    app_pkg_path = "macOS/app/NormCap/NormCap.app/Contents/Resources/app_packages"
    tesseract_source = "/usr/local/bin/tesseract"
    tesseract_target = f"{app_pkg_path}/tesseract"
    install_path = "@executable_path/"
    run(
        cmd=f"""dylibbundler \
            --fix-file {tesseract_source} \
            --dest-dir {app_pkg_path} \
            --install-path {install_path} \
            --bundle-deps \
            --overwrite-files
        """
    )
    shutil.copy(tesseract_source, tesseract_target)


def linux_bundle_tesseract():
    target_path = RESOURCE_PATH / "tesseract"
    target_path.mkdir(exist_ok=True)
    run(
        "ldd /bin/bash | grep \"=> /\" | awk '{print $3}' | xargs -I '{}' cp -v '{}' "
        + str(target_path.resolve())
    )
    try:
        shutil.copy("/usr/bin/tesseract", target_path)
    except shutil.SameFileError:
        print("'tesseract' already copied.")


def windows_download_wix():
    wix_path = BUILD_PATH / "wix"
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


def windows_build_installer():
    print("Copying wxs configuration file to app.dist folder...")
    wxs = BUILD_PATH / "normcap.wxs"
    shutil.copy(wxs, BUILD_PATH / "app.dist")

    print("Copying images to app.dist folder...")
    shutil.copy(IMG_PATH / "normcap_install_bg.bmp", BUILD_PATH / "app.dist")
    shutil.copy(IMG_PATH / "normcap_install_top.bmp", BUILD_PATH / "app.dist")
    shutil.copy(IMG_PATH / "normcap.ico", BUILD_PATH / "app.dist")

    print("Compiling application manifest...")
    wix_path = BUILD_PATH / "wix"
    run(
        cmd=f"""{(wix_path / "heat.exe").resolve()} \
            dir \
            app.dist \
            -nologo \
            -gg \
            -sfrag \
            -sreg \
            -srd \
            -scom \
            -dr normcap_ROOTDIR \
            -cg normcap_COMPONENTS \
            -var var.SourceDir \
            -out {(BUILD_PATH / "app.dist" / "normcap-manifest.wxs").resolve()}
        """,
        cwd=BUILD_PATH,
    )
    print("Compiling installer...")
    run(
        cmd=f"""{(wix_path / "candle.exe").resolve()} \
            -nologo \
            -ext WixUtilExtension \
            -ext WixUIExtension \
            -dSourceDir=. \
            normcap.wxs \
            normcap-manifest.wxs
        """,
        cwd=BUILD_PATH / "app.dist",
    )
    print("Linking installer...")
    run(
        cmd=f"""{(wix_path / "light.exe").resolve()} \
            -nologo \
            -ext WixUtilExtension \
            -ext WixUIExtension \
            -o {(BUILD_PATH / f"NormCap-{get_version()}-Windows.msi").resolve()} \
            normcap.wixobj \
            normcap-manifest.wixobj
        """,
        cwd=BUILD_PATH / "app.dist",
    )


def linux_system_deps():
    if system_requires := get_system_requires("linux"):
        github_actions_uid = 1001
        if os.getuid() == github_actions_uid:  # type: ignore
            run(cmd="sudo apt update")
            run(cmd=f"sudo apt install {' '.join(system_requires)}")


def linux_nuitka():
    run(
        cmd=f"""python -m nuitka \
                --onefile \
                --assume-yes-for-downloads \
                --linux-onefile-icon={(IMG_PATH / "normcap.svg").resolve()} \
                --enable-plugin=pyside6 \
                --include-package=normcap.resources \
                --include-package-data=normcap.resources \
                -o NormCap-{get_version()}-x86_64.AppImage \
                {(PROJECT_PATH / "src"/ "normcap" / "app.py").resolve()}
        """,
        cwd=BUILD_PATH,
    )


def windows_nuitka():
    VENV_PATH = Path(os.environ["VIRTUAL_ENV"])
    TLS_PATH = VENV_PATH / "lib" / "site-packages" / "PySide6" / "plugins" / "tls"
    run(
        cmd=f"""python -m nuitka \
                --standalone \
                --assume-yes-for-downloads \
                --windows-company-name=dynobo \
                --windows-product-name=NormCap \
                --windows-file-description="OCR powered screen-capture tool to capture information instead of images." \
                --windows-product-version={get_version()} \
                --windows-icon-from-ico={(IMG_PATH / "normcap.ico").resolve()} \
                --windows-disable-console \
                --windows-force-stdout-spec=%PROGRAM%.log \
                --windows-force-stderr-spec=%PROGRAM%.log \
                --enable-plugin=pyside6 \
                --include-package=normcap.resources \
                --include-package-data=normcap.resources \
                --include-data-files={(TESSERACT_PATH).resolve()}/*.dll=normcap/resources/tesseract/ \
                --include-data-files={(TLS_PATH).resolve()}/*.*=PySide6/qt-plugins/tls/ \
                {(PROJECT_PATH / "src"/ "normcap" / "app.py").resolve()}
            """,
        cwd=BUILD_PATH,
    )
    normcap_exe = BUILD_PATH / "app.dist" / "NormCap.exe"
    normcap_exe.unlink(missing_ok=True)
    (BUILD_PATH / "app.dist" / "app.exe").rename(normcap_exe)


if __name__ == "__main__":
    download_tessdata()
    platform_str = sys.platform.lower()

    if platform_str.lower().startswith("win"):
        windows_bundle_tesseract()
        windows_nuitka()
        windows_download_wix()
        windows_build_installer()

    elif platform_str.lower().startswith("darwin"):
        raise NotImplementedError

    elif platform_str.lower().startswith("linux"):
        # TODO: bring build/metadata into appimage
        linux_system_deps()
        linux_bundle_tesseract()
        linux_nuitka()
    else:
        raise ValueError("Unknown operating system.")
