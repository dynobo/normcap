"""Adjustments executed while packaging with briefcase during CI/CD."""

import os
import shutil

from .utils import BuilderBase


class MacNuitka(BuilderBase):
    """Create prebuild package for MacOS using Nuitka."""

    def run_framework(self):  # noqa: D102
        print(f"{'='*40}\nRun framework\n{'='*40}")
        self.run(
            cmd=f"""python -m nuitka \
                    --standalone \
                    --assume-yes-for-downloads \
                    --macos-target-arch=x86_64 \
                    --macos-create-app-bundle \
                    --macos-disable-console \
                    --macos-app-icon={(self.IMG_PATH / "normcap.icns").resolve()} \
                    --macos-signed-app-name=eu.dynobo.normcap \
                    --macos-app-name=NormCap \
                    --macos-app-version={self.get_version()} \
                    --enable-plugin=pyside6 \
                    --include-data-dir={(self.RESOURCE_PATH).resolve()}=resources\
                    --include-data-dir={(self.BUILD_PATH / ".cache").resolve()}=PySide6/qt-plugins/tls \
                    {(self.PROJECT_PATH / "src"/ "normcap" / "app.py").resolve()}
                """,
            cwd=self.BUILD_PATH,
        )
        old_app_path = self.BUILD_PATH / "app.app"
        new_app_path = self.BUILD_PATH / "NormCap.app"
        shutil.rmtree(new_app_path)
        os.rename(old_app_path, new_app_path)
        os.rename(
            new_app_path / "Contents" / "MacOS" / "app",
            new_app_path / "Contents" / "MacOS" / "NormCap",
        )
        shutil.make_archive(
            base_name=self.BUILD_PATH / f"NormCap-{self.get_version()}-MacOS",
            format="zip",
            root_dir=self.BUILD_PATH,
            base_dir="NormCap.app",
        )

    def bundle_tesseract(self):  # noqa: D102
        print(f"{'='*40}\nBundle tesseract\n{'='*40}")
        tesseract_source = "/usr/local/bin/tesseract"
        install_path = "@executable_path/"
        self.run(
            cmd="dylibbundler "
            + f"--fix-file {tesseract_source} "
            + f"--dest-dir {self.TESSERACT_PATH.resolve()} "
            + f"--install-path {install_path} "
            + "--bundle-deps "
            + "--overwrite-files",
            cwd=self.BUILD_PATH,
        )
        shutil.copy(tesseract_source, self.TESSERACT_PATH)

    def bundle_tls(self):  # noqa: D102
        print(f"{'='*40}\nBundle TLS\n{'='*40}")
        cache_path = self.BUILD_PATH / ".cache"
        cache_path.mkdir(exist_ok=True)
        shutil.rmtree(cache_path)
        TLS_PATH = (
            self.VENV_PATH
            / "lib"
            / "python3.10"
            / "site-packages"
            / "PySide6"
            / "Qt"
            / "plugins"
            / "tls"
        )
        shutil.copytree(TLS_PATH, cache_path)
        dylibs = [
            "libqcertonlybackend.dylib",
            "libqopensslbackend.dylib",
            "libqsecuretransportbackend.dylib",
        ]
        for dylib in dylibs:
            self.run(
                cmd="install_name_tool -change "
                + "'@rpath/QtNetwork.framework/Versions/A/QtNetwork' '@executable_path/QtNetwork' "
                + f"{(cache_path / dylib).resolve()}",
                cwd=cache_path,
            )
            self.run(
                cmd="install_name_tool -change "
                + "'@rpath/QtCore.framework/Versions/A/QtCore' '@executable_path/QtCore' "
                + f"{(cache_path / dylib).resolve()}",
                cwd=cache_path,
            )

    def install_system_deps(self):  # noqa: D102
        print(f"{'='*40}\nInstall system deps\n{'='*40}")
        self.run(cmd="brew install tesseract")
        self.run(cmd="brew install dylibbundler")

    def create(self):  # noqa: D102
        self.download_tessdata()
        self.install_system_deps()
        self.bundle_tesseract()
        self.bundle_tls()
        self.run_framework()
