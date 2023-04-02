"""Run adjustments while packaging with briefcase during CI/CD."""

import shutil
import urllib
import zipfile

from platforms.utils import BuilderBase, bundle_tesseract_windows_ub_mannheim


class WindowsNuitka(BuilderBase):
    """Create prebuild package for Windows using Nuitka."""

    binary_suffix = "_EXPERIMENTAL"

    def bundle_tesseract(self) -> None:
        """Download tesseract binaries including dependencies into resource path."""
        bundle_tesseract_windows_ub_mannheim(self)

    def download_wix(self) -> None:
        wix_path = self.BUILD_PATH / "wix"
        wix_path.mkdir(exist_ok=True)
        wix_zip = wix_path / "wix-binaries.zip"

        url = (
            "https://github.com/wixtoolset/wix3/releases/download/"
            "wix3112rtm/wix311-binaries.zip"
        )
        urllib.request.urlretrieve(f"{url}", wix_zip)  # noqa: S310

        with zipfile.ZipFile(wix_zip, "r") as zip_ref:
            zip_ref.extractall(wix_path)

        wix_zip.unlink()

    def build_installer(self) -> None:
        wxs = self.BUILD_PATH / "normcap.wxs"
        shutil.copy(wxs, self.BUILD_PATH / "app.dist")

        shutil.copy(
            self.IMG_PATH / "normcap_install_bg.bmp", self.BUILD_PATH / "app.dist"
        )
        shutil.copy(
            self.IMG_PATH / "normcap_install_top.bmp", self.BUILD_PATH / "app.dist"
        )
        shutil.copy(self.IMG_PATH / "normcap.ico", self.BUILD_PATH / "app.dist")

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
        installer_name = (
            f"NormCap-{self.get_version()}-x86_64-Windows{self.binary_suffix}.msi"
        )
        self.run(
            cmd=f"""{(wix_path / "light.exe").resolve()} \
            -nologo \
            -ext WixUtilExtension \
            -ext WixUIExtension \
            -o {(self.BUILD_PATH / installer_name).resolve()} \
            normcap.wixobj \
            normcap-manifest.wixobj
            """,
            cwd=self.BUILD_PATH / "app.dist",
        )

    def run_framework(self) -> None:
        tls_path = (
            self.VENV_PATH / "lib" / "site-packages" / "PySide6" / "plugins" / "tls"
        )
        description = (
            "OCR powered screen-capture tool to capture information "
            "instead of images."
        )
        self.run(
            cmd=f"""python -m nuitka \
                --standalone \
                --assume-yes-for-downloads \
                --windows-company-name=dynobo \
                --windows-product-name=NormCap \
                --windows-file-description="{description}" \
                --windows-product-version={self.get_version()} \
                --windows-icon-from-ico={(self.IMG_PATH / "normcap.ico").resolve()} \
                --windows-disable-console \
                --windows-force-stdout-spec=%PROGRAM%.log \
                --windows-force-stderr-spec=%PROGRAM%.log \
                --enable-plugin=pyside6 \
                --include-data-dir={(self.RESOURCE_PATH).resolve()}=normcap/resources \
                --include-data-dir={tls_path.resolve()}=PySide6/qt-plugins/tls \
                {(self.PROJECT_PATH / "normcap" / "app.py").resolve()}
                """,
            cwd=self.BUILD_PATH,
        )
        normcap_exe = self.BUILD_PATH / "app.dist" / "NormCap.exe"
        normcap_exe.unlink(missing_ok=True)
        (self.BUILD_PATH / "app.dist" / "app.exe").rename(normcap_exe)

    def install_system_deps(self) -> None:
        pass

    def create(self) -> None:
        self.download_tessdata()
        self.bundle_tesseract()
        self.run_framework()
        self.download_wix()
        self.build_installer()
