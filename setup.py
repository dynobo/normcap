# Standard
import pathlib
import platform
import subprocess
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install


class InstallWinDeps(install):
    def run(self):
        install.run(self)
        if platform.system() == "Windows":
            self.install_tesserocr_for_windows()

    def install_tesserocr_for_windows(self):
        """Installing Windows specific python packages.

        To avoid the cumbersome installation process of Tesseract on Windows,
        we install a wheel that contains the pre-compiled tesseract lib.
        Thanks to: https://github.com/simonflueckiger/tesserocr-windows_build/releases
        """
        url = (
            "https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/"
            "tesserocr-v2.4.0-tesseract-4.0.0/tesserocr-2.4.0-cp37-cp37m-"
        )
        if platform.machine().endswith("32"):
            url += "win32.whl"
        else:
            url += "win_amd64.whl"

        print(f"Downloading Windows specific 'tesserocr': {url} ...\n")
        subprocess.check_call([sys.executable, "-m", "pip", "install", url])


# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="normcap",
    version="0.0.9",
    description="Intelligent screencapture tool to capture information instead of images.",
    keywords="screenshot ocr capture",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/dynobo/normcap",
    author="dynobo",
    author_email="dynobo@mailbox.org",
    license="GPLv3",
    classifiers=[
        "Development Status :: 3 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Multimedia :: Graphics :: Capture :: Screen Capture",
        "Topic :: Utilities",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    packages=find_packages(exclude=("tests",)),
    include_package_data=False,
    python_requires=">=3.7.0",
    install_requires=[
        "mss",
        "Pillow",
        "pyperclip",
        "tesserocr; platform_system!='Windows'",
    ],
    entry_points={"console_scripts": ["normcap=normcap.normcap:main"]},
    cmdclass={"install": InstallWinDeps},
)
