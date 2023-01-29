<!-- markdownlint-disable MD013 MD026 MD033 -->

# NormCap

**_OCR powered screen-capture tool to capture information instead of images. For Linux,
macOS and Windows._**

[![Build](https://img.shields.io/github/actions/workflow/status/dynobo/normcap/python.yaml?branch=main)](https://github.com/dynobo/normcap/releases)
[![Coverage Status](https://img.shields.io/coverallsCoverage/github/dynobo/normcap?label=Test%20coverage&branch=main)](https://coveralls.io/github/dynobo/normcap)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/dynobo/normcap/codeql-analysis.yml?branch=main&label=CodeQL)](https://github.com/dynobo/normcap/actions/workflows/codeql-analysis.yml)

[![GitHub](https://img.shields.io/github/downloads/dynobo/normcap/total?label=Github%20downloads&color=blue)](https://github.com/dynobo/normcap/releases)
[![PyPi](https://img.shields.io/pypi/dm/normcap?label=PyPi%20downloads&color=blue)](https://pypi.org/project/normcap)
[![Flathub](https://img.shields.io/flathub/downloads/com.github.dynobo.normcap?label=Flathub%20downloads&color=blue)](https://flathub.org/apps/details/com.github.dynobo.normcap)
[![AUR](https://img.shields.io/aur/votes/normcap?label=AUR%20votes&color=blue)](https://aur.archlinux.org/packages/normcap)

**Links:** [Source Code](https://github.com/dynobo/normcap) |
[Documentation](https://dynobo.github.io/normcap/) |
[FAQs](https://dynobo.github.io/normcap/#faqs) |
[Releases](https://github.com/dynobo/normcap/releases) |
[Changelog](https://github.com/dynobo/normcap/blob/main/CHANGELOG.md)

[![Screencast](https://user-images.githubusercontent.com/11071876/189767585-8bc45c18-8392-411d-84dc-cef1cb5dbc47.gif)](https://raw.githubusercontent.com/dynobo/normcap/main/assets/normcap.gif)

## Quickstart

Install a prebuilt release:

- **Windows**:
  [NormCap-0.4.0-x86_64-Windows.msi](https://github.com/dynobo/normcap/releases/download/v0.4.0/NormCap-0.4.0-x86_64-Windows.msi)
- **Linux**:
  [NormCap-0.4.0-x86_64.AppImage](https://github.com/dynobo/normcap/releases/download/v0.4.0/NormCap-0.4.0-x86_64.AppImage)
- **macOS** (x86) ¹:
  [NormCap-0.4.0-x86_64-macOS.dmg](https://github.com/dynobo/normcap/releases/download/v0.4.0/NormCap-0.4.0-x86_64-macOS.dmg)
- **macOS** (M1) ¹·²:
  [NormCap-0.4.0-arm64-macOS.dmg](https://github.com/dynobo/normcap/releases/download/v0.4.0/NormCap-0.4.0-arm64-macOS.dmg)
  \
  <sub>1: On macOS, allow the unsigned application on first start: "System
  Preferences" → "Security & Privacy" → "General" → "Open anyway". You might also need
  to allow NormCap to take screenshots.
  [#135](https://github.com/dynobo/normcap/issues/135)<br> 2: Might be available a bit
  delayed, as it is currently build manually. (Thx,
  [@Takrin](https://github.com/Takrin)!)</sub>

Install from repositories:

- **Arch / Manjaro**: Install the
  [`normcap`](https://aur.archlinux.org/packages/normcap) package from AUR.
- **FlatPak (Linux)**: Install
  [com.github.dynobo.normcap](https://flathub.org/apps/details/com.github.dynobo.normcap)
  from FlatHub.

If you experience issues please look at the
[FAQs](https://dynobo.github.io/normcap/#faqs) or
[open an issue](https://github.com/dynobo/normcap/issues).

## Python package

As an _alternative_ to a prebuilt package you can install the
[NormCap Python package](https://pypi.org/project/normcap/) for **Python >=3.9**:

#### On Linux

```sh
# Install dependencies (Ubuntu/Debian)
sudo apt install build-essential tesseract-ocr tesseract-ocr-eng libtesseract-dev libleptonica-dev wl-clipboard

## Install dependencies (Arch)
sudo pacman -S tesseract tesseract-data-eng wl-clipboard

## Install dependencies (Fedora)
sudo dnf install tesseract wl-clipboard

## Install dependencies (openSUSE)
sudo zypper install python3-devel tesseract-ocr tesseract-ocr-devel wl-clipboard

# Install normcap
pip install normcap

# Run
./normcap
```

#### On macOS

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

- Create an environment variable `TESSDATA_PREFIX` and set it to Tesseract's data
  folder, e.g.:

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
**Poetry>=1.3.2** and **Tesseract** (incl. **language data**).

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

And it depends on external software:

- [tesseract](https://github.com/tesseract-ocr/tesseract) - _OCR engine_
- [wl-clipboard](https://github.com/bugaevc/wl-clipboard) - _Wayland clipboard
  utilities_

Packaging is done with:

- [briefcase](https://pypi.org/project/briefcase/) _- converting Python projects into_
  _standalone apps_

Thanks to the maintainers of those nice tools!

## Similar open source tools

If NormCap doesn't fit your needs, try those alternatives (no particular order):

- [TextSnatcher](https://github.com/RajSolai/TextSnatcher) (Linux)
- [GreenShot](https://getgreenshot.org/) (Linux, macOS)
- [TextShot](https://github.com/ianzhao05/textshot) (Windows)
- [gImageReader](https://github.com/manisandro/gImageReader) (Linux, Windows)
- [Capture2Text](https://sourceforge.net/projects/capture2text) (Windows)
- [Frog](https://github.com/TenderOwl/Frog) (Linux)
- [Textinator](https://github.com/RhetTbull/textinator) (macOS)

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)
