"""Run adjustments while packaging with briefcase during CI/CD."""

import shutil
from pathlib import Path

from platforms.utils import BuilderBase


class MacNuitka(BuilderBase):
    """Create prebuild package for macOS using Nuitka."""

    binary_suffix = "_EXPERIMENTAL"

    def run_framework(self) -> None:
        cache_dir = (self.BUILD_PATH / ".cache").resolve()
        self.run(
            cmd=f"""python -m nuitka \
                    --standalone \
                    --onefile \
                    --assume-yes-for-downloads \
                    --macos-target-arch=x86_64 \
                    --macos-create-app-bundle \
                    --macos-disable-console \
                    --macos-app-icon={(self.IMG_PATH / "normcap.icns").resolve()} \
                    --macos-signed-app-name=eu.dynobo.normcap \
                    --macos-app-name=NormCap \
                    --macos-app-version={self.get_version()} \
                    --enable-plugin=pyside6 \
                    --include-data-dir={(self.RESOURCE_PATH).resolve()}=resources \
                    --include-data-dir={cache_dir}=PySide6/qt-plugins/tls \
                    {(self.PROJECT_PATH / "normcap" / "app.py").resolve()}
                """,
            cwd=self.BUILD_PATH,
        )
        old_app_path = self.BUILD_PATH / "app.app"
        new_app_path = self.BUILD_PATH / "NormCap.app"
        shutil.rmtree(new_app_path, ignore_errors=True)
        Path(old_app_path).rename(new_app_path)
        Path(new_app_path / "Contents" / "macOS" / "app").rename(
            new_app_path / "Contents" / "macOS" / "NormCap",
        )
        shutil.make_archive(
            base_name=str(
                (
                    self.BUILD_PATH
                    / f"NormCap-{self.get_version()}-x86_64-macOS{self.binary_suffix}"
                ).resolve()
            ),
            format="zip",
            root_dir=self.BUILD_PATH,
            base_dir="NormCap.app",
        )

    def bundle_tesseract(self) -> None:
        tesseract_source = "/usr/local/bin/tesseract"
        install_path = "@executable_path/"
        self.run(
            cmd=(
                "dylibbundler "
                f"--fix-file {tesseract_source} "
                f"--dest-dir {self.TESSERACT_PATH.resolve()} "
                f"--install-path {install_path} "
                "--bundle-deps "
                "--overwrite-files"
            ),
            cwd=self.BUILD_PATH,
        )
        shutil.copy(tesseract_source, self.TESSERACT_PATH)

    def bundle_tls(self) -> None:
        cache_path = self.BUILD_PATH / ".cache"
        cache_path.mkdir(exist_ok=True)
        shutil.rmtree(cache_path)
        tls_path = (
            self.VENV_PATH
            / "lib"
            / "python3.10"
            / "site-packages"
            / "PySide6"
            / "Qt"
            / "plugins"
            / "tls"
        )
        shutil.copytree(tls_path, cache_path)
        dylibs = [
            "libqcertonlybackend.dylib",
            "libqopensslbackend.dylib",
            "libqsecuretransportbackend.dylib",
        ]
        for dylib in dylibs:
            self.run(
                cmd=(
                    "install_name_tool -change "
                    "'@rpath/QtNetwork.framework/Versions/A/QtNetwork' "
                    "'@executable_path/QtNetwork' "
                    f"{(cache_path / dylib).resolve()}"
                ),
                cwd=cache_path,
            )
            self.run(
                cmd=(
                    "install_name_tool -change "
                    "'@rpath/QtCore.framework/Versions/A/QtCore' "
                    "'@executable_path/QtCore' "
                    f"{(cache_path / dylib).resolve()}"
                ),
                cwd=cache_path,
            )

    def install_system_deps(self) -> None:
        self.run(cmd="brew install tesseract")
        self.run(cmd="brew install dylibbundler")

    def reinstall_pillow_without_binary(self) -> None:
        output = self.run(cmd="poetry run pip show pillow | grep Version")
        if not output:
            raise RuntimeError("Could not retrieve pillow version!")
        version = output.split(":")[1].strip()
        self.run(cmd="pip uninstall pillow -y", cwd=self.PROJECT_PATH)
        self.run(
            cmd=f"pip install --no-binary=pillow pillow=={version}",
            cwd=self.PROJECT_PATH,
        )

    def create(self) -> None:
        self.download_tessdata()
        self.install_system_deps()
        self.bundle_tesseract()
        self.bundle_tls()
        self.reinstall_pillow_without_binary()
        self.run_framework()
