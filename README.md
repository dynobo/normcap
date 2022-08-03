<!-- markdownlint-disable MD013 MD026 MD033 -->

# NormCap

**_OCR powered screen-capture tool to capture information instead of images._**

[![Build passing](https://github.com/dynobo/normcap/workflows/Build/badge.svg)](https://github.com/dynobo/normcap/releases)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/Code%20style-black-%23000000)](https://github.com/psf/black)
[![Coverage Status](https://coveralls.io/repos/github/dynobo/normcap/badge.svg)](https://coveralls.io/github/dynobo/normcap)

**Links:** [Repo](https://github.com/dynobo/normcap) |
[PyPi](https://pypi.org/project/normcap) |
[Releases](https://github.com/dynobo/normcap/releases) |
[Changelog](https://github.com/dynobo/normcap/blob/main/CHANGELOG.md) |
[FAQs](https://dynobo.github.io/normcap/#faqs)

[![Screencast](https://user-images.githubusercontent.com/11071876/123133596-3107d080-d450-11eb-8451-6dcebb7876ad.gif)](https://raw.githubusercontent.com/dynobo/normcap/main/assets/normcap.gif)

## Quickstart

Install a pre-build release:

- **Windows**:
  [NormCap-0.3.7-Windows.msi](https://github.com/dynobo/normcap/releases/download/v0.3.7/NormCap-0.3.7-Windows.msi)
- **Linux**:
  [NormCap-0.3.7-x86_64.AppImage](https://github.com/dynobo/normcap/releases/download/v0.3.7/NormCap-0.3.7-x86_64.AppImage)
- **macOS**:
  [NormCap-0.3.7-MacOS.dmg](https://github.com/dynobo/normcap/releases/download/v0.3.7/NormCap-0.3.7-MacOS.dmg)
  \
  <sub>(On macOS, allow the unsigned application on first start: "System Preferences"
  → "Security & Privacy" → "General" → "Open anyway". You might also need to allow
  NormCap to take screenshots. Background:
  [#135](https://github.com/dynobo/normcap/issues/135))</sub>

Install from system repository:

- **Arch / Manjaro**: Install the
  [`normcap`](https://aur.archlinux.org/packages/normcap) package from AUR.
- **FlatPak (Linux)**: Install
  [com.github.dynobo.normcap](https://flathub.org/apps/details/com.github.dynobo.normcap)
  from FlatHub.

If you experience issues please look at the
[FAQs](https://github.com/dynobo/normcap/blob/main/FAQ.md) or
[open an issue](https://github.com/dynobo/normcap/issues).

## Python package

As an _alternative_ to a pre-build package you can install the
[NormCap Python package](https://pypi.org/project/normcap/) for **Python >=3.9**:

#### On Linux

```sh
# Install dependencies (Ubuntu/Debian)
sudo apt install build-essential tesseract-ocr tesseract-ocr-eng libtesseract-dev libleptonica-dev

## Install dependencies (Arch)
sudo pacman -S tesseract tesseract-data-eng

## Install dependencies (Fedora)
sudo dnf install tesseract

## Install dependencies (openSUSE)
sudo zypper install python3-devel tesseract-ocr tesseract-ocr-devel

# Install normcap
pip install normcap

# Run
./normcap
```

#### On MacOS

```sh
# Install dependencies
brew install tesseract tesseract-lang

# Install normcap
pip install normcap

# Run
./normcap
```

#### On Windows

1\. Install `Tesseract 5` by using the
[installer provided by UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).

2\. Adjust environment variables:

- Create a environment variable `TESSDATA_PREFIX` and set it to Tesseract's data folder,
  e.g.:

  ```cmd
  setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata"
  ```

- Append Tesseract's location to the environment variable `Path`, e.g.:

  ```cmd
  setx Path "%Path%;C:\Program Files\Tesseract-OCR"
  ```

- Make sure to close and reopen your current terminal window to apply the new variables.
  Test it by running:

  ```cmd
  tesseract --list-langs
  ```

3\. Install and run NormCap:

```bash
# Install normcap
pip install normcap

# Run
normcap
```

## Why "NormCap"?

See [XKCD](https://xkcd.com):

[![Comic](https://imgs.xkcd.com/comics/norm_normal_file_format.png)](https://xkcd.com/2116/)

## Development

Prerequisites for setting up a development environment are: **Python >=3.9**,
**Poetry>=1.2.0b2** and **Tesseract** (incl. **language data**).

```sh
# Clone repository
git clone https://github.com/dynobo/normcap.git

# Change into project directory
cd normcap

# Create virtual env and install dependencies
poetry install

# Register pre-commit hook
poetry run pre-commit install

# Run NormCap in virtual env
poetry run python -m normcap
```

## Credits

This project uses the following non-standard libraries:

- [pyside6](https://pypi.org/project/PySide6/) _- bindings for Qt UI Framework_
- [pytesseract](https://pypi.org/project/pytesseract/) _- wrapper for tesseract's API_
- [jeepney](https://pypi.org/project/jeepney/) _- DBUS client_

Packaging is done with:

- [briefcase](https://pypi.org/project/briefcase/) _- converting Python projects into_
  _standalone apps_
- [nuitka](https://pypi.org/project/Nuitka/) _- compiling Python projects into_
  _standalone apps_

And it depends on external software

- [tesseract](https://github.com/tesseract-ocr/tesseract) - _OCR engine_

Thanks to the maintainers of those nice libraries!

## Similar open source tools

If NormCap doesn't fit your needs, try those alternatives (no particular order):

- [TextSnatcher](https://github.com/RajSolai/TextSnatcher)
- [GreenShot](https://getgreenshot.org/)
- [TextShot](https://github.com/ianzhao05/textshot)
- [gImageReader](https://github.com/manisandro/gImageReader)
- [Capture2Text](https://sourceforge.net/projects/capture2text)
- [Frog](https://github.com/TenderOwl/Frog)
- [Textinator](https://github.com/RhetTbull/textinator)

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)
