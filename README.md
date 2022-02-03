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
[FAQs](https://github.com/dynobo/normcap/blob/main/FAQ.md)

**Content:** [Quickstart](#Quickstart) | [Python package](#Python-package) |
[Usage](#Usage) | [Contribute](#Contribute) | [Credits](#Credits)

[![Screencast](https://user-images.githubusercontent.com/11071876/123133596-3107d080-d450-11eb-8451-6dcebb7876ad.gif)](https://raw.githubusercontent.com/dynobo/normcap/main/assets/normcap.gif)

## Features

- On-screen recognition of selected text
- Multi platform support for Linux, Windows, MacOS
- Multi monitor support, incl. HDPI displays
- "[Magically](#magics)" parsing the text (optional, on by default)
- Show notifications (optional)
- Stay in system tray (optional)
- Check for updates (optional, off by default)

## Quickstart

**❱❱
[Download & run a pre-build package for Linux, MacOS or Windows](https://github.com/dynobo/normcap/releases)
❰❰**

If you experience issues please look at the
[FAQs](https://github.com/dynobo/normcap/blob/main/FAQ.md) or
[open an issue](https://github.com/dynobo/normcap/issues).

(On **MacOS**, allow the unsigned application on first start: "System Preferences" →
"Security & Privacy" → "General" → "Open anyway". You might also need to allow NormCap
to take screenshots.)

## Python package

As an _alternative_ to a pre-build package you can install the
[NormCap Python package](https://pypi.org/project/normcap/):

### On Linux

```sh
# Install dependencies (Ubuntu/Debian)
sudo apt install tesseract-ocr tesseract-ocr-eng \
                 libtesseract-dev libleptonica-dev \
                 python3-dev

## Install dependencies (Arch)
sudo pacman -S tesseract tesseract-data-eng leptonica

## Install dependencies (Fedora)
sudo dnf install tesseract tesseract-devel \
                 libleptonica-devel python3-devel

# Install normcap
pip install normcap

# Run
./normcap
```

### On MacOS

```sh
# Install dependencies
brew install tesseract tesseract-lang

# Install normcap
pip install normcap

# Run
./normcap
```

### On Windows

1\. Install "Tesseract **4.1**", e.g. by using the
[installer provided by UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).

2\. Set the environment variable `TESSDATA_PREFIX` to Tesseract's data folder, e.g.:

```cmd
setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata"
```

3\. Install [tesserocr](https://pypi.org/project/tesserocr/) using the
[Windows specific wheel](https://github.com/simonflueckiger/tesserocr-windows_build) and
NormCap afterwards:

```bash
# Install tesserocr package
pip install https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/tesserocr-v2.4.0-tesseract-4.0.0/tesserocr-2.4.0-cp37-cp37m-win_amd64.whl

# Install normcap
pip install normcap

# Run
normcap
```

## Usage

### General

- Select a region on screen with your mouse to perform text recognition

- Press `<esc>` key to abort a capture and quit the application.

### Magics

"Magics" are like add-ons providing automated functionality to intelligently detect and
format the captured input.

First, every "magic" calculates a "**score**" to determine the likelihood of being
responsible for this type of text. Second, the "magic" which achieved the highest
"score" takes the necessary actions to **"transform"** the input text according to its
type.

Currently implemented Magics:

| Magic           | Score                                                | Transform                                                                            |
| --------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Single line** | Only single line is detected                         | Trim unnecessary whitespace                                                          |
| **Multi line**  | Multi lines, but single Paragraph                    | Separated by line breaks and trim each lined                                         |
| **Paragraph**   | Multiple blocks of lines or multiple paragraphs      | Join every paragraph into a single line, separate different paragraphs by empty line |
| **E-Mail**      | Number of chars in email addresses vs. overall chars | Transform to a comma-separated list of email addresses                               |
| **URL**         | Number of chars in URLs vs. overall chars            | Transform to line-break separated URLs                                               |

## Why "NormCap"?

See [XKCD](https://xkcd.com):

[![Comic](https://imgs.xkcd.com/comics/norm_normal_file_format.png)](https://xkcd.com/2116/)

## Contribute

### Setup Environment

Prerequisites are **Python >=3.7.1**, **Poetry**, **Tesseract** (incl. **language
data**).

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

- [pyside2](https://pypi.org/project/PySide2/) _- bindings for Qt UI Framework_
- [tesserocr](https://pypi.org/project/tesserocr/) _- wrapper for tesseract's API_
- [jeepney](https://pypi.org/project/jeepney/) _- DBUS client_

Packaging is done with:

- [briefcase](https://pypi.org/project/briefcase/) _- converting Python projects into_
  _standalone apps_

And it depends on external software

- [tesseract](https://github.com/tesseract-ocr/tesseract) - _OCR engine_

Thanks to the maintainers of those nice libraries!

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)
