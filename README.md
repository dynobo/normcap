<!-- markdownlint-disable MD013 MD026 MD033 -->

# NormCap

**_OCR powered screen-capture tool to capture information instead of images. For Linux,
macOS and Windows._**

[![Test](https://img.shields.io/github/actions/workflow/status/dynobo/normcap/cicd.yaml?label=CI/CD&branch=main)](https://github.com/dynobo/normcap/actions/workflows/cicd.yaml)
[![Coverage Status](https://img.shields.io/coverallsCoverage/github/dynobo/normcap?label=Coverage&branch=main)](https://coveralls.io/github/dynobo/normcap)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/dynobo/normcap/cicd.yaml?label=CodeQL&branch=main)](https://github.com/dynobo/normcap/security/code-scanning/tools/CodeQL/status/)

[![GitHub](https://img.shields.io/github/downloads/dynobo/normcap/total?label=Github%20downloads&color=blue)](https://hanadigital.github.io/grev/?user=dynobo&repo=normcap)
[![PyPi](https://img.shields.io/pypi/dm/normcap?label=PyPi%20downloads&color=blue)](https://pypi.org/project/normcap)
[![Flathub](https://img.shields.io/flathub/downloads/com.github.dynobo.normcap?label=Flathub%20downloads&color=blue)](https://flathub.org/apps/details/com.github.dynobo.normcap)
[![AUR](https://img.shields.io/aur/votes/normcap?label=AUR%20votes&color=blue)](https://aur.archlinux.org/packages/normcap)

<a href="https://www.buymeacoffee.com/dynobo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;" ></a>

**Links:** [Source Code](https://github.com/dynobo/normcap) |
[Documentation](https://dynobo.github.io/normcap/) |
[FAQs](https://dynobo.github.io/normcap/#faqs) |
[Releases](https://github.com/dynobo/normcap/releases) |
[Changelog](https://github.com/dynobo/normcap/blob/main/CHANGELOG)

[![Screencast](https://user-images.githubusercontent.com/11071876/189767585-8bc45c18-8392-411d-84dc-cef1cb5dbc47.gif)](https://raw.githubusercontent.com/dynobo/normcap/main/assets/normcap.gif)

## Quickstart

Choose **_one_** of the options for a prebuilt release. If you encounter an issue please
take a look at the [FAQs](https://dynobo.github.io/normcap/#faqs) or
[report](https://github.com/dynobo/normcap/issues) it.

#### Windows

- [NormCap-0.5.8-x86_64-Windows.msi](https://github.com/dynobo/normcap/releases/download/v0.5.8/NormCap-0.5.8-x86_64-Windows.msi)
  (Installer)

#### Linux

- [NormCap-0.5.8-x86_64.AppImage](https://github.com/dynobo/normcap/releases/download/v0.5.8/NormCap-0.5.8-x86_64.AppImage)
  (Binary)
- [`normcap` @ AUR](https://aur.archlinux.org/packages/normcap) (Arch/Manjaro)
- [com.github.dynobo.normcap @ FlatHub](https://flathub.org/apps/details/com.github.dynobo.normcap)
  (FlatPak)

#### macOS

Note: You have to allow the unsigned application on first start: "System Preferences" →
"Security & Privacy" → "General" → "Open anyway". You also have to allow NormCap to take
screenshots. ([#135](https://github.com/dynobo/normcap/issues/135))

- [NormCap-0.5.8-x86_64-macOS.dmg](https://github.com/dynobo/normcap/releases/download/v0.5.8/NormCap-0.5.8-x86_64-macOS.dmg)
  (Installer for x86/64)
- [NormCap-0.5.8-arm64-macOS.dmg](https://github.com/dynobo/normcap/releases/download/v0.5.8/NormCap-0.5.8-arm64-macOS.dmg)
  (Installer for M1)

## Install Python package

As an _alternative_ to a prebuilt package from above you can install the
[NormCap Python package](https://pypi.org/project/normcap/) for **Python >=3.9**, but it
is a bit more complicated:

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

2\. Identify the path to Tesseract base folder. It should contain a `/tessdata` subfolder
and the `tesseract.exe` binary. Depending on if you installed Tesseract system-wide or
in userspace, the base folder should be:

```
C:\Program Files\Tesseract-OCR
```

or

```
C:\Users\<USERNAME>\AppData\Local\Programs\Tesseract-OCR
```

3\. Adjust environment variables:

- Create an environment variable `TESSDATA_PREFIX` and set it to _your_ Tesseract base
  folder, e.g.: "System Properties" → Tab "Advanced" → "Environment Variables..." →
  "New..." → Variable: `TESSDATA_PREFIX`, Value: `"C:\Program Files\Tesseract-OCR"`

- Append Tesseract's base folder to the environment variable `PATH`, e.g.: "System
  Properties" → Tab "Advanced" → "Environment Variables..." → Section "User variables"
  → Select `PATH` → "Edit..." → Add a new entry `"C:\Program Files\Tesseract-OCR"`

- To test your setup, open a new `cmd`-terminal and run:

    ```cmd
    tesseract --list-langs
    ```

4\. Install and run NormCap:

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

Prerequisites for setting up a development environment are:
[**Python >=3.9**](https://www.python.org/downloads/),
[**hatch**](https://hatch.pypa.io/latest/install/) and
[**Tesseract >=5.0**](https://tesseract-ocr.github.io/tessdoc/#5xx) (incl. **language
data**).

```sh
# Clone repository
git clone https://github.com/dynobo/normcap.git

# Change into project directory
cd normcap

# Create virtual env and install dependencies
hatch env create

# Register pre-commit hook
hatch run pre-commit install

# Run NormCap in virtual env
hatch run python -m normcap
```

## Credits

This project uses the following non-standard libraries:

- [pyside6](https://pypi.org/project/PySide6/) _- bindings for Qt UI Framework_

And it depends on external software:

- [tesseract](https://github.com/tesseract-ocr/tesseract) - _OCR engine_
- [wl-clipboard](https://github.com/bugaevc/wl-clipboard) - _Wayland clipboard
  utilities_
- [xclip](https://github.com/astrand/xclip) - _CLI to the X11 clipboard_

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
- [Text-Grab](https://github.com/TheJoeFin/Text-Grab) (Windows)
- [dpScreenOCR](https://danpla.github.io/dpscreenocr/) (Linux, Windows)
- [PowerToys Text Extractor](https://learn.microsoft.com/en-us/windows/powertoys/text-extractor)
  (Windows)

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)

## Contributors

<a href="https://github.com/dynobo/normcap/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=dynobo/normcap" />
</a>

<small>Made with [contrib.rocks](https://contrib.rocks)</small>
