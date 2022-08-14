"""Adjustments executed while packaging with briefcase during CI/CD."""

import inspect
import os
import shutil
from pathlib import Path

import briefcase  # type: ignore
from platforms.utils import BRIEFCASE_EXCLUDES, BuilderBase, rm_recursive


class LinuxBriefcase(BuilderBase):
    """Create prebuild package for Linux using Briefcase."""

    binary_suffix = ""

    def patch_briefcase_appimage_to_prune_deps(self):
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

    def patch_briefcase_appimage_to_include_tesseract(self):
        """Insert code into briefcase appimage code to remove unnecessary libs."""
        file_path = (
            Path(briefcase.__file__).parent / "platforms" / "linux" / "appimage.py"
        )
        insert_after = '"appimage",'
        patch = """
"--executable",
"/usr/bin/tesseract",
"""
        self.patch_file(file_path=file_path, insert_after=insert_after, patch=patch)

    def patch_briefcase_create_to_adjust_dockerfile(self):
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

    def bundle_tesseract(self):  # noqa: D102
        target_path = self.RESOURCE_PATH / "tesseract"
        target_path.mkdir(exist_ok=True)
        lib_cache_path = self.BUILD_PATH / ".cache"
        lib_cache_path.mkdir(exist_ok=True)
        try:
            shutil.copy("/usr/bin/tesseract", target_path)
        except shutil.SameFileError:
            print("'tesseract' already copied.")
        self.run(
            r"ldd /usr/bin/tesseract | grep '=> /' | awk '{print $3}' | "
            "xargs -I '{}' cp -v '{}' " + f"{(lib_cache_path).resolve()}/"
        )
        print(f"Copying tesseract dependencies to {target_path.resolve()}...")
        for pattern in ("liblept*", "libtesseract*"):
            dependency = list(lib_cache_path.glob(pattern))[0]
            print(f"{dependency.resolve()}")
            shutil.copy(dependency, target_path)

    def install_system_deps(self):  # noqa: D102
        if system_requires := self.get_system_requires():
            github_actions_uid = 1001
            if os.getuid() == github_actions_uid:  # type: ignore
                self.run(cmd="sudo apt update")
                self.run(cmd=f"sudo apt install {' '.join(system_requires)}")

    def build_wl_clipboard(self):  # noqa: D102
        temp_path = Path().cwd() / ".temp"
        shutil.rmtree(temp_path, ignore_errors=True)
        temp_path.mkdir(exist_ok=True)
        self.run(
            cmd="git clone https://github.com/bugaevc/wl-clipboard.git", cwd=temp_path
        )
        wl_path = temp_path / "wl-clipboard"
        self.run(cmd="meson build", cwd=wl_path)
        self.run(cmd="ninja", cwd=wl_path / "build")

        target_path = self.RESOURCE_PATH / "wl-copy"
        target_path.mkdir(exist_ok=True)
        shutil.copy(wl_path / "build" / "src" / "wl-copy", target_path / "wl-copy")
        shutil.rmtree(wl_path, ignore_errors=True)

    def run_framework(self):  # noqa: D102
        self.run(cmd="briefcase create --no-input", cwd=self.PROJECT_PATH)
        self.run(cmd="briefcase build", cwd=self.PROJECT_PATH)
        self.add_metainfo_to_appimage()
        self.run(cmd="briefcase package", cwd=self.PROJECT_PATH)

    def rename_package_file(self):  # noqa: D102
        source = list(Path(self.PROJECT_PATH / "linux").glob("*.AppImage"))[0]
        target = (
            self.BUILD_PATH
            / f"NormCap-{self.get_version()}-x86_64{self.binary_suffix}.AppImage"
        )
        target.unlink(missing_ok=True)
        shutil.move(source, target)

    def add_metainfo_to_appimage(self):
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

    def create(self):  # noqa: D102
        self.download_tessdata()
        self.install_system_deps()
        self.build_wl_clipboard()
        # self.bundle_tesseract()

        self.patch_briefcase_appimage_to_prune_deps()
        self.patch_briefcase_appimage_to_include_tesseract()
        self.patch_briefcase_create_to_adjust_dockerfile()

        self.run_framework()
        self.rename_package_file()
