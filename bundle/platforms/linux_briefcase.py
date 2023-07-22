"""Run adjustments while packaging with briefcase during CI/CD."""

import os
import shutil
from pathlib import Path

import briefcase

from platforms.utils import BuilderBase


class LinuxBriefcase(BuilderBase):
    """Create prebuilt package for Linux using Briefcase."""

    binary_suffix = ""

    def patch_briefcase_appimage_to_include_tesseract_and_wlcopy(self) -> None:
        """Insert code into briefcase appimage code to remove unnecessary libs."""
        file_path = (
            Path(briefcase.__file__).parent / "platforms" / "linux" / "appimage.py"
        )
        insert_after = '"appimage",'
        patch = """
"--executable",
"/usr/bin/tesseract",
"--executable",
"/usr/bin/wl-copy",
"""
        self.patch_file(file_path=file_path, insert_after=insert_after, patch=patch)

    def install_system_deps(self) -> None:
        if system_requires := self.get_system_requires():
            github_actions_uid = 1001
            if os.getuid() == github_actions_uid:  # type: ignore
                self.run(cmd="sudo apt update")
                self.run(cmd=f"sudo apt install {' '.join(system_requires)}")

    def run_framework(self) -> None:
        self.run(
            cmd="briefcase create linux appimage --no-input", cwd=self.PROJECT_PATH
        )
        self.run(cmd="briefcase build linux appimage", cwd=self.PROJECT_PATH)
        self.add_metainfo_to_appimage()
        self.run(cmd="briefcase package linux appimage", cwd=self.PROJECT_PATH)

    def rename_package_file(self) -> None:
        source = next(Path(self.PROJECT_PATH / "dist").glob("*.AppImage"))
        target = (
            self.BUILD_PATH
            / f"NormCap-{self.get_version()}-x86_64{self.binary_suffix}.AppImage"
        )
        target.unlink(missing_ok=True)
        shutil.move(source, target)

    def add_metainfo_to_appimage(self) -> None:
        """Copy metainfo file with info for appimage hub."""
        metainfo = self.BUILD_PATH / "metainfo"
        target_path = (
            self.PROJECT_PATH
            / "build"
            / "normcap"
            / "linux"
            / "appimage"
            / "NormCap.AppDir"
            / "usr"
            / "share"
        )
        shutil.copy(metainfo, target_path / "metainfo")

    def bundle_tesseract(self) -> None:
        ...

    def create(self) -> None:
        self.download_tessdata()

        self.patch_briefcase_appimage_to_include_tesseract_and_wlcopy()

        self.run_framework()
        self.rename_package_file()
