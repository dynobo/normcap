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

        if platform.system().lower() != "windows":
            print("Not on Windows. Skipping platform specific dependencies.")
            return

        print("Installed Windows specific python packages:")

        # For windows use pre compiled wheel for tesserocr from
        # https://github.com/simonflueckiger/tesserocr-windows_build/releases
        TESSEROCR = {
            "win32": (
                "https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/"
                "tesserocr-v2.4.0-tesseract-4.0.0/tesserocr-2.4.0-cp37-cp37m-win32.whl"
            ),
            "win64": (
                "https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/"
                "tesserocr-v2.4.0-tesseract-4.0.0/tesserocr-2.4.0-cp37-cp37m-win_amd64.whl"
            ),
        }

        # For windows use pre compiled wheel for python-levenshtein from
        # https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-levenshtein
        # (This C++ version of levenshtein is necessary, because it is _fast_)
        LEVENSHTEIN = {
            "win32": (
                "https://download.lfd.uci.edu/pythonlibs/"
                "g5apjq5m/python_Levenshtein-0.12.0-cp37-cp37m-win32.whl"
            ),
            "win64": (
                "https://download.lfd.uci.edu/pythonlibs/"
                "g5apjq5m/python_Levenshtein-0.12.0-cp37-cp37m-win_amd64.whl"
            ),
        }

        win_version = "win32"
        if platform.machine().endswith("64"):
            win_version = "win64"

        print(
            f"Tesserocr: {TESSEROCR[win_version]}...\n"
            f"python-Levenshtein: {TESSEROCR[win_version]}..."
        )

        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                TESSEROCR[win_version],
                LEVENSHTEIN[win_version],
            ]
        )
        print("Done.")


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
        "Development Status :: 3 - Alpha",
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
        "python-Levenshtein; platform_system!='Windows'",
    ],
    entry_points={"console_scripts": ["normcap=normcap.normcap:main"]},
    cmdclass={"install": InstallWinDeps},
)
