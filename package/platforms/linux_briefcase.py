"""Adjustments executed while packaging with briefcase during CI/CD."""

import inspect
import os
import shutil
from pathlib import Path

import briefcase

from platforms.utils import (
    BRIEFCASE_EXCLUDES,
    BuilderBase,
    build_wl_clipboard,
    rm_recursive,
)


class LinuxBriefcase(BuilderBase):
    """Create prebuild package for Linux using Briefcase."""

    binary_suffix = ""

    def patch_briefcase_appimage_to_prune_deps(self) -> None:
        """Insert code into briefcase appimage code to remove unnecessary libs."""
        def_rm_recursive = inspect.getsource(rm_recursive)

        file_path = (
            Path(briefcase.__file__).parent / "platforms" / "linux" / "appimage.py"
        )
        patch = f"""
import shutil, os
{def_rm_recursive}
app_dir = self.appdir_path(app) / "usr" / "app_packages"
rm_recursive(directory=app_dir, exclude={BRIEFCASE_EXCLUDES["app_packages"]})
rm_recursive(directory=app_dir / "PySide6", exclude={BRIEFCASE_EXCLUDES["pyside6"]})

lib_dir = self.appdir_path(app) / "usr" / "lib"
rm_recursive(directory=lib_dir / "PySide6", exclude={BRIEFCASE_EXCLUDES["pyside6"]})
"""
        insert_after = 'self.logger.info("Building AppImage...", prefix=app.app_name)'
        self.patch_file(file_path=file_path, insert_after=insert_after, patch=patch)

    def patch_briefcase_appimage_to_build_wl_clipboard(self) -> None:
        """Patch briefcase appimage code to build wl clipboard inside docker."""
        def_build_wl_clipboard = inspect.getsource(build_wl_clipboard)

        file_path = Path(briefcase.__file__).parent / "commands" / "create.py"
        patch = f"""
{def_build_wl_clipboard}
build_wl_clipboard(self, app_packages_path)
"""
        insert_after = "        # Install dependencies"
        self.patch_file(file_path=file_path, insert_after=insert_after, patch=patch)

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
f"{self.appdir_path(app).parent.parent.parent / 'build' / 'src' / 'wl-copy'}",
"""
        self.patch_file(file_path=file_path, insert_after=insert_after, patch=patch)

    def patch_briefcase_create_to_adjust_dockerfile(self) -> None:
        """Add code to add tesseract ppa to Dockerfile."""
        file_path = Path(briefcase.__file__).parent / "commands" / "create.py"
        insert_after = "self.install_app_support_package(app=app)"
        patch = """
if "linux" in str(bundle_path):
    print()
    print("Patching Dockerfile on Linux")
    import fileinput
    patch = "\\nRUN apt-add-repository ppa:alex-p/tesseract-ocr-devel"
    for line in fileinput.FileInput(bundle_path / "Dockerfile", inplace=1):
        if "RUN apt-add-repository ppa:deadsnakes/ppa" in line:
            line = line.replace(line, line + patch)
        print(line, end="")
"""
        self.patch_file(file_path=file_path, insert_after=insert_after, patch=patch)

    def install_system_deps(self) -> None:
        if system_requires := self.get_system_requires():
            github_actions_uid = 1001
            if os.getuid() == github_actions_uid:  # type: ignore
                self.run(cmd="sudo apt update")
                self.run(cmd=f"sudo apt install {' '.join(system_requires)}")

    def run_framework(self) -> None:
        self.run(cmd="briefcase create --no-input", cwd=self.PROJECT_PATH)
        self.run(cmd="briefcase build", cwd=self.PROJECT_PATH)
        self.add_metainfo_to_appimage()
        self.run(cmd="briefcase package", cwd=self.PROJECT_PATH)

    def rename_package_file(self) -> None:
        source = list(Path(self.PROJECT_PATH / "linux").glob("*.AppImage"))[0]
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
            / "linux"
            / "appimage"
            / "NormCap"
            / "NormCap.AppDir"
            / "usr"
            / "share"
        )
        shutil.copy(metainfo, target_path / "metainfo")

    def bundle_tesseract(self) -> None:
        ...

    def create(self) -> None:
        self.download_tessdata()
        self.install_system_deps()

        self.patch_briefcase_appimage_to_build_wl_clipboard()
        self.patch_briefcase_appimage_to_prune_deps()
        self.patch_briefcase_appimage_to_include_tesseract_and_wlcopy()
        self.patch_briefcase_create_to_adjust_dockerfile()

        self.run_framework()
        self.rename_package_file()
