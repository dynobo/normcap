# Standard
import pathlib
import platform
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# Requirements,
INSTALL_REQUIRES = ["mss", "Pillow", "tesserocr", "pyperclip", "python-Levenshtein"]

# If Platform is window, exchange tesserocr with pre compiled wheel from
# https://github.com/simonflueckiger/tesserocr-windows_build/releases
TESSEROCR_PYPI = "tesserocr"
TESSEROCR_WIN32 = (
    "git+https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/"
    "tesserocr-v2.4.0-tesseract-4.0.0/tesserocr-2.4.0-cp37-cp37m-win32.whl"
)
TESSEROCR_WIN64 = (
    "git+https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/"
    "tesserocr-v2.4.0-tesseract-4.0.0/tesserocr-2.4.0-cp37-cp37m-win_amd64.whl"
)

if platform.system().lower() == "windows":
    if platform.machine().endswith("64"):
        INSTALL_REQUIRES.remove(TESSEROCR_PYPI)
        INSTALL_REQUIRES.append(TESSEROCR_WIN64)
    if platform.machine().endswith("86"):
        INSTALL_REQUIRES.remove(TESSEROCR_PYPI)
        INSTALL_REQUIRES.append(TESSEROCR_WIN32)

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
    install_requires=INSTALL_REQUIRES,
    entry_points={"console_scripts": ["normcap=normcap.normcap:main",]},
)
