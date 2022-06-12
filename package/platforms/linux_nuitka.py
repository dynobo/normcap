"""Adjustments executed while packaging with briefcase during CI/CD."""

import os
import shutil

from .utils import BuilderBase


class LinuxNuitka(BuilderBase):
    """Create prebuild package for Linux using Nuitka."""

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

    def install_system_deps(self):  # noqa: D102
        if system_requires := self.get_system_requires():
            github_actions_uid = 1001
            if os.getuid() == github_actions_uid:  # type: ignore
                self.run(cmd="sudo apt update")
                self.run(cmd=f"sudo apt install {' '.join(system_requires)}")

    def run_framework(self):  # noqa: D102
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
        self.run(
            cmd=f"""python -m nuitka \
                    --onefile \
                    --assume-yes-for-downloads \
                    --linux-onefile-icon={(self.IMG_PATH / "normcap.svg").resolve()} \
                    --enable-plugin=pyside6 \
                    --include-data-dir={(self.RESOURCE_PATH).resolve()}=normcap/resources \
                    --include-data-dir={(TLS_PATH).resolve()}=PySide6/qt-plugins/tls \
                    --include-data-files={(self.BUILD_PATH / "metainfo").resolve()}=usr/share/ \
                    --include-data-files={(self.BUILD_PATH / ".cache").resolve()}/*.*=./ \
                    -o NormCap-{self.get_version()}-x86_64{self.binary_prefix}.AppImage \
                    {(self.PROJECT_PATH / "src"/ "normcap" / "app.py").resolve()}
            """,
            cwd=self.BUILD_PATH,
        )

    def create(self):  # noqa: D102
        self.download_tessdata()
        self.install_system_deps()
        self.bundle_tesseract()
        self.run_framework()