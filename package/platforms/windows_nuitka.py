"""Adjustments executed while packaging with briefcase during CI/CD."""

import shutil
import urllib
import zipfile
from pathlib import Path

from .utils import BuilderBase


class WindowsNuitka(BuilderBase):
    """Create prebuild package for Windows using Nuitka."""

    def bundle_tesseract(self):  # noqa: D102
        # Link to download artifact might change

        # https://ci.appveyor.com/project/zdenop/tesseract/build/artifacts

        if (self.TESSERACT_PATH / "tesseract.exe").exists():
            print("Tesseract.exe already present. Skipping download.")
            return

        url = "https://ci.appveyor.com/api/projects/zdenop/tesseract/artifacts/tesseract.zip"
        urllib.request.urlretrieve(f"{url}", self.BUILD_PATH / "tesseract.zip")
        with zipfile.ZipFile(self.BUILD_PATH / "tesseract.zip") as artifact_zip:
            members = [
                m
                for m in artifact_zip.namelist()
                if ".test." not in m and ".training." not in m
            ]
            subdir = members[0].split("/")[0]
            artifact_zip.extractall(path=self.RESOURCE_PATH, members=members)
        print("Tesseract binaries downloaded.")

        for each_file in Path(self.RESOURCE_PATH / subdir).glob("*.*"):
            each_file.rename(self.TESSERACT_PATH / each_file.name)
        (self.TESSERACT_PATH / "google.tesseract.tesseract-master.exe").rename(
            self.TESSERACT_PATH / "tesseract.exe"
        )
        shutil.rmtree(self.RESOURCE_PATH / subdir)
        print("Binaries moved. Tesseract.exe renamed.")

    def download_wix(self):  # noqa: D102
        wix_path = self.BUILD_PATH / "wix"
        wix_path.mkdir(exist_ok=True)
        wix_zip = wix_path / "wix-binaries.zip"
        if wix_zip.exists():
            print("Skip downloading wix toolkit. Already there.")
            return

        print("Downloading wix toolkit...")
        url = "https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311-binaries.zip"
        urllib.request.urlretrieve(f"{url}", wix_zip)

        print(f"Downloaded {url} to {wix_zip.absolute()}")
        with zipfile.ZipFile(wix_zip, "r") as zip_ref:
            zip_ref.extractall(wix_path)

    def build_installer(self):  # noqa: D102
        print("Copying wxs configuration file to app.dist folder...")
        wxs = self.BUILD_PATH / "normcap.wxs"
        shutil.copy(wxs, self.BUILD_PATH / "app.dist")

        print("Copying images to app.dist folder...")
        shutil.copy(
            self.IMG_PATH / "normcap_install_bg.bmp", self.BUILD_PATH / "app.dist"
        )
        shutil.copy(
            self.IMG_PATH / "normcap_install_top.bmp", self.BUILD_PATH / "app.dist"
        )
        shutil.copy(self.IMG_PATH / "normcap.ico", self.BUILD_PATH / "app.dist")

        print("Compiling application manifest...")
        wix_path = self.BUILD_PATH / "wix"
        self.run(
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
                -out {(self.BUILD_PATH / "app.dist" / "normcap-manifest.wxs").resolve()}
            """,
            cwd=self.BUILD_PATH,
        )
        print("Compiling installer...")
        self.run(
            cmd=f"""{(wix_path / "candle.exe").resolve()} \
                -nologo \
                -ext WixUtilExtension \
                -ext WixUIExtension \
                -dSourceDir=. \
                normcap.wxs \
                normcap-manifest.wxs
            """,
            cwd=self.BUILD_PATH / "app.dist",
        )
        print("Linking installer...")
        self.run(
            cmd=f"""{(wix_path / "light.exe").resolve()} \
                -nologo \
                -ext WixUtilExtension \
                -ext WixUIExtension \
                -o {(self.BUILD_PATH / f"NormCap-{self.get_version()}-Windows.msi").resolve()} \
                normcap.wixobj \
                normcap-manifest.wixobj
            """,
            cwd=self.BUILD_PATH / "app.dist",
        )

    def run_framework(self):  # noqa: D102
        TLS_PATH = (
            self.VENV_PATH / "lib" / "site-packages" / "PySide6" / "plugins" / "tls"
        )

        self.run(
            cmd=f"""python -m nuitka \
                    --standalone \
                    --assume-yes-for-downloads \
                    --windows-company-name=dynobo \
                    --windows-product-name=NormCap \
                    --windows-file-description="OCR powered screen-capture tool to capture information instead of images." \
                    --windows-product-version={self.get_version()} \
                    --windows-icon-from-ico={(self.IMG_PATH / "normcap.ico").resolve()} \
                    --windows-disable-console \
                    --windows-force-stdout-spec=%PROGRAM%.log \
                    --windows-force-stderr-spec=%PROGRAM%.log \
                    --enable-plugin=pyside6 \
                    --include-data-dir={(self.RESOURCE_PATH).resolve()}=normcap/resources \
                    --include-data-dir={(TLS_PATH).resolve()}=PySide6/qt-plugins/tls \
                    {(self.PROJECT_PATH / "src"/ "normcap" / "app.py").resolve()}
                """,
            cwd=self.BUILD_PATH,
        )
        normcap_exe = self.BUILD_PATH / "app.dist" / "NormCap.exe"
        normcap_exe.unlink(missing_ok=True)
        (self.BUILD_PATH / "app.dist" / "app.exe").rename(normcap_exe)

    def install_system_deps(self):  # noqa: D102
        pass

    def create(self):  # noqa: D102
        self.download_tessdata()
        self.bundle_tesseract()
        self.run_framework()
        self.download_wix()
        self.build_installer()
