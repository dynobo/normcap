"""Adjustments executed while packaging with briefcase during CI/CD."""

import os
import shutil
from pathlib import Path

from .utils import BRIEFCASE_EXCLUDES, BuilderBase, rm_recursive


class MacBriefcase(BuilderBase):
    """Create prebuild package for MacOS using Briefcase."""

    def run_framework(self):  # noqa: D102
        app_dir = (
            self.PROJECT_PATH
            / "macOS"
            / "app"
            / "NormCap"
            / "NormCap.app"
            / "Contents"
            / "Resources"
            / "app_packages"
        )
        self.run(cmd="briefcase create", cwd=self.PROJECT_PATH)

        rm_recursive(directory=app_dir, exclude=BRIEFCASE_EXCLUDES["app_packages"])
        rm_recursive(
            directory=app_dir / "PySide6", exclude=BRIEFCASE_EXCLUDES["pyside6"]
        )
        self.run(cmd="briefcase build", cwd=self.PROJECT_PATH)
        # TODO: Re-enable if we have a solution for unfocusing on MacOS
        # patch_info_plist_for_proper_fullscreen()
        self.run(cmd="briefcase package macos app --no-sign", cwd=self.PROJECT_PATH)

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
        print("Bundling tesseract libs...")
        app_pkg_path = (
            self.PROJECT_PATH
            / "macOS/app/NormCap/NormCap.app/Contents/Resources/app_packages"
        )
        tesseract_source = Path("/usr/local/bin/tesseract")
        tesseract_target = app_pkg_path / "tesseract"
        install_path = "@executable_path/"
        self.run(
            cmd="dylibbundler "
            + f"--fix-file {tesseract_source.resolve()} "
            + f"--dest-dir {app_pkg_path.resolve()} "
            + f"--install-path {install_path} "
            + "--bundle-deps "
            + "--overwrite-files",
            cwd=self.BUILD_PATH,
        )
        shutil.copy(tesseract_source, tesseract_target)

    def patch_info_plist_for_proper_fullscreen(self):
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
        self.patch_file(
            file_path=file_path,
            insert_after=insert_after,
            patch=patch,
            mark_patched=False,
        )

    def bundle_tls(self):  # noqa: D102
        print("Bundling tesseract tls...")
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
        self.run(cmd="brew install tesseract")
        self.run(cmd="brew install dylibbundler")

    def rename_package_file(self):  # noqa: D102
        source = list(Path(self.PROJECT_PATH / "macOS").glob("*.dmg"))[0]
        target = (
            self.BUILD_PATH
            / f"NormCap-{self.get_version()}-MacOS{self.binary_prefix}.dmg"
        )
        target.unlink(missing_ok=True)
        shutil.move(source, target)

    def create(self):  # noqa: D102
        self.download_tessdata()
        self.install_system_deps()
        self.bundle_tesseract()
        self.bundle_tls()
        self.run_framework()
        self.rename_package_file()
