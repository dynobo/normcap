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

[![Screencast](https://user-images.githubusercontent.com/11071876/97786948-39ed1e80-1baf-11eb-852c-bce87abc6890.gif)](https://raw.githubusercontent.com/dynobo/normcap/main/assets/normcap.gif)

## Quickstart

**❱❱
[Download & run a pre-build package for Linux, MacOS or Windows](https://github.com/dynobo/normcap/releases)
❰❰**

Hints:

- If you experience issues or have questions please look at the
  [FAQs](https://github.com/dynobo/normcap/blob/main/FAQ.md) or
  [open an issue](https://github.com/dynobo/normcap/issues).
- On **Linux**, make the AppImage executable before running it:
  ```
  chmod +x NormCap-Linux.AppImage
  ./NormCap-Linux.AppImage
  ```
- On **MacOS**, you have to allow the unsigned application on first start: "System
  Preferences" → "Security & Privacy" → Tab "General" → "Open anyway". \
  Depending on
  your OS, you might also need to allow NormCap to take screenshots.

## Python package

As an _alternative_ to a pre-build package you can install the
[NormCap Python package](https://pypi.org/project/normcap/):

### On Linux

```sh
# Install dependencies (Ubuntu/Debian)
sudo apt install tesseract-ocr tesseract-ocr-eng \
                 libtesseract-dev libleptonica-dev

## Install dependencies (Arch)
sudo pacman -S tesseract tesseract-data-eng leptonica

## Install dependencies (Fedora)
sudo dnf install tesseract tesseract-devel leptonica-devel

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

- Press `<esc>` key to abort a capture and quit the application.

- Press `<space>` key while selecting a region with the mouse (left mouse button has to
  be hold down) to switch between the two capture modes:

  - **★ (parse):** Try to auto-detect the type of text using [magics](#Magics) and
    format the text accordingly, then copy
  - **☰ (raw):** Copy detected text line by line, without further modification

### Command line options

NormCap has no settings, just a set of command line arguments:

```plain
(normcap)dynobo@cioran:~$ normcap --help
usage: normcap [-h] [-l LANGUAGE] [-c COLOR] [-n] [-t] [-v] [-V]

OCR-powered screen-capture tool to capture information instead of images.

optional arguments:
  -h, --help                  show this help message and exit
  -l LANGUAGE, --language LANGUAGE
                              set language(s) for text recognition, e.g.
                              eng+deu (default: eng)
  -c COLOR, --color COLOR     set primary color for UI (default: #FF2E88)
  -n, --no-notifications      disable notifications shown after ocr detection
                              (default: False)
  -t, --tray                  keep running in system tray - experimental
                              (default: False)
  -v, --verbose               print debug information to console (default:
                              False)
  -V, --very-verbose          print more debug information to console
                              (default: False)
```

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
