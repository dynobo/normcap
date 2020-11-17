# Standard
import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="normcap",
    version="0.1.8",
    description="OCR-powered screen-capture tool to capture information instead of images",
    keywords="screenshot ocr capture clipboard",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/dynobo/normcap",
    author="dynobo",
    author_email="dynobo@mailbox.org",
    license="GPLv3",
    classifiers=[
        "Development Status :: 4 - Beta",
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
    include_package_data=True,
    package_data={"ressources": ["*"]},
    python_requires=">=3.7.0",
    install_requires=[
        "mss>=6.1.0",
        "Pillow>=8.0.1",
        "pyperclip>=1.8.1",
        "tesserocr>=2.4.0",
        "pyscreenshot>=2.2",
        "notify-py>=0.3.0",
        "importlib-resources>=3.3.0",
    ],
    entry_points={"console_scripts": ["normcap=normcap.__main__:run"]},
)
