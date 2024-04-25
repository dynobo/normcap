"""Run adjustments while packaging with briefcase during CI/CD."""

import shutil
from pathlib import Path

import briefcase

from platforms.utils import BuilderBase


class LinuxBriefcase(BuilderBase):
    """Create prebuilt package for Linux using Briefcase."""

    binary_suffix = ""
    binary_extension = "AppImage"
    binary_platform = "x86_64"

    def _add_metainfo_to_appimage(self) -> None:
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

    def _patch_briefcase_appimage_to_include_deps(self) -> None:
        """Insert code into briefcase appimage code to add additional deps.

        Currently adds:
        - tesseract
        - libxcb-cursor
        - wl-copy
        - xclip
        - xsel
        """
        file_path = (
            Path(briefcase.__file__).parent / "platforms" / "linux" / "appimage.py"
        )
        insert_after = '"appimage",'
        patch = """
        "--executable=/usr/bin/tesseract",
        "--executable=/usr/bin/xclip",
        "--executable=/usr/bin/xsel",
        "--executable=/usr/local/bin/wl-copy",
        "--library=/usr/lib64/libxcb-cursor.so.0",
        """
        self.patch_file(file_path=file_path, insert_after=insert_after, patch=patch)

    def _patch_briefcase_appimage_to_run_cmd(self) -> None:
        """Execute _before_ linuxdeploy."""
        file_path = (
            Path(briefcase.__file__).parent / "platforms" / "linux" / "appimage.py"
        )
        insert_after = "# Build the AppImage."
        patch = """
        self.tools[app].app_context.run(
            ["env"],
            env=env,
            check=True,
            cwd=self.bundle_path(app),
        )
        """
        self.patch_file(file_path=file_path, insert_after=insert_after, patch=patch)

    def run_framework(self) -> None:
        self.run(
            cmd="briefcase create linux appimage --no-input", cwd=self.PROJECT_PATH
        )
        self.run(cmd="briefcase build linux appimage", cwd=self.PROJECT_PATH)
        self._add_metainfo_to_appimage()
        self.run(cmd="briefcase package linux appimage", cwd=self.PROJECT_PATH)

    def bundle_tesseract(self) -> None: ...

    def install_system_deps(self) -> None: ...

    def pre_framework(self) -> None:
        self._patch_briefcase_appimage_to_run_cmd()
        self._patch_briefcase_appimage_to_include_deps()
