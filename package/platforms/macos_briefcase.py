"""Adjustments executed while packaging with briefcase during CI/CD."""

import shutil
from pathlib import Path

from platforms.utils import BRIEFCASE_EXCLUDES, BuilderBase, rm_recursive


class MacBriefcase(BuilderBase):
    """Create prebuild package for macOS using Briefcase."""

    binary_suffix = ""

    def run_framework(self):
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
        self.bundle_tesseract()

        self.run(cmd="briefcase build", cwd=self.PROJECT_PATH)
        # TODO: Re-enable if we have a solution for unfocusing on macOS
        # patch_info_plist_for_proper_fullscreen()
        self.run(cmd="briefcase package macos app --no-sign", cwd=self.PROJECT_PATH)

    def bundle_tesseract(self):
        bin_path = (
            self.PROJECT_PATH / "macOS/app/NormCap/NormCap.app/Contents/Resources/bin"
        )
        bin_path.mkdir(exist_ok=True)
        tesseract_source = Path("/usr/local/bin/tesseract")
        tesseract_target = bin_path / "tesseract"
        install_path = "@executable_path/"
        self.run(
            cmd="dylibbundler "
            + f"--fix-file {tesseract_source.resolve()} "
            + f"--dest-dir {bin_path.resolve()} "
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

    def install_system_deps(self):
        self.run(cmd="brew install tesseract")
        self.run(cmd="brew install dylibbundler")

    def rename_package_file(self):
        source = list(Path(self.PROJECT_PATH / "macOS").glob("*.dmg"))[0]
        target = (
            self.BUILD_PATH
            / f"NormCap-{self.get_version()}-x86_64-macOS{self.binary_suffix}.dmg"
        )
        target.unlink(missing_ok=True)
        shutil.move(source, target)

    def create(self):
        self.download_tessdata()
        self.install_system_deps()
        self.run_framework()
        self.rename_package_file()
