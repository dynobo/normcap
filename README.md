<!-- markdownlint-disable MD013 MD026 MD033 -->

# normcap

***Intelligent OCR powered screen-capture tool to capture information instead of images.***

<p align="center"><br>
<a href="https://github.com/dynobo/normcap/releases"><img alt="Build passing" src="https://github.com/dynobo/normcap/workflows/Release/badge.svg"></a>
<a href="https://www.gnu.org/licenses/gpl-3.0"><img alt="License: GPLv3" src="https://img.shields.io/badge/License-GPLv3-blue.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/Code%20style-black-%23000000"></a>
<a href='https://coveralls.io/github/dynobo/normcap'><img src='https://coveralls.io/repos/github/dynobo/normcap/badge.svg' alt='Coverage Status' /></a>
</p>

<p align="center">
<strong>Links:</strong> <a href="https://github.com/dynobo/normcap/releases">Releases</a> |
<a href="https://github.com/dynobo/normcap/blob/master/CHANGELOG.md">Changelog</a> |
<a href="https://github.com/dynobo/normcap/labels/backlog">Roadmap</a> |
<a href="https://github.com/dynobo/normcap/">Repo</a>
</p>

<p align="center">
<strong>Content:</strong> <a href="#Introduction">Introduction</a> |
<a href="#Installation">Installation</a> |
<a href="#Usage">Usage</a> |
<a href="#Contribute">Contribute</a> |
<a href="#Contribute">Credits</a>
<br><br></p>

## Introduction

**Basic usage:**

1. Launch `normcap`
2. Select region on screen
3. Retrieve recognized text in clipboard

## Installation

### On Linux

1\. Install dependencies:

```sh
## on Ubuntu/Debian:
sudo apt-get install tesseract-ocr xclip

# on Arch:
sudo pacman -S tesseract tesseract-data-eng xclip

# on Fedora
sudo dnf install tesseract xclip
```

2\. Run `pip install normcap` (***OR*** download and extract binary package from the [latest release](
https://github.com/dynobo/normcap/releases))

3\. Execute `./normcap`

### On Windows

**Recommended method:**

1\. Download and extract binary package from the [latest release](https://github.com/dynobo/normcap/releases) (no installation is required)

2\. Execute `normcap.exe`

**Alternative method:**

1\. Install "Tesseract", e.g. by using the [installer provided by UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

2\. Install [tesserocr](https://pypi.org/project/tesserocr/), e.g. by using the [Windows specific wheel](https://github.com/simonflueckiger/tesserocr-windows_build):

```bash
pip install https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/tesserocr-v2.4.0-tesseract-4.0.0/tesserocr-2.4.0-cp37-cp37m-win_amd64.whl
```

3\. Run `pip install normcap`

4\. Execute `normcap`

### On Mac

***Attention! On Mac, some issues occur. [Help needed](https://github.com/dynobo/normcap/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)***

1\. Install dependencies:

```sh
brew install tesseract tesseract-lang
```

2\.  Download and extract binary package from the [latest release](
https://github.com/dynobo/normcap/releases)

3\. Execute `normcap.app`

## Usage

### Basics

1. Run the `normcap` executable (A red border will appear around your screen)
2. Select a region with text using your mouse (Or press `<esc>` to quit program)
3. (Optional) Before letting go the mouse button, press `<space>`-key to switch through different modes of operation, as indicated by a symbol:
   - **☰ (raw):** Copy detected text line by line, without further modification
   - **☶ (parse):** Try to auto-detect type of text using [magics](#Magics) and format the text accordingly, then copy
4. Paste the text from clipboard (e.g. `<ctrl> + v`)

### Hints

The [Windows release](https://github.com/dynobo/normcap/releases) of normcap supports English and German out of the box. Please [file an issue](https://github.com/dynobo/normcap/issues), if other languages should be included permanently, or download additional language files from [the tesseract repo](https://github.com/tesseract-ocr/tessdata_best) yourself and place them in the `/normcap/tessdata/` folder.

normcap is intended to be executed on demand via keybinding or desktop shortcut. Therefore it doesn't occupy resources by running in the background, but it's startup is a bit slower.

By default normcap is "stateless": it copies recognized text to the systems clipboard, but doesn't save images or text on the disk. However, you can use the `--path` switch to store the images in any folder.

### Command line options

normcap has no settings, just a set of command line arguments:

```plain
[holger@cioran normcap]$ poetry run python normcap/normcap.py --help
usage: normcap [-h] [-v] [-m MODE] [-l LANG] [-c COLOR] [-p PATH]

Intelligent OCR-powered screen-capture tool to capture information instead of images.

optional arguments:
  -h, --help               show this help message and exit
  -v, --verbose            print debug information to console (default: False)
  -m MODE, --mode MODE     startup mode [raw,parse] (default: parse)
  -l LANG, --lang LANG     set language for ocr tool (default: eng)
  -c COLOR, --color COLOR  set primary color for UI (default: #FF0000)
  -p PATH, --path PATH     set a path for storing images (default: None)
```

### Magics

"Magics" are like addons providing automated functionality to intelligently detect and format the captured input.

First, every "magic" calculates a **"score"** to determine the likelihood of the magic being responsible for this type of text. Second, the "magic" which achieved the highest "score" take the necessary actions to **"parse"** the input text according to its type

#### Single Line Magic

- **Score:** If single line is detected
- **Parse:** Trim unnecessary whitespace

TODO: Screencast Single Line Magic

#### E-Mail Magic

- **Score:** Number of chars in email addresses vs. overall chars
- **Parse:** Transform to comma separated list

TODO: Screencast E-Mail Magic

#### URL Magic

- **Score:** Number of chars in URLs vs. overall chars
- **Parse:** Transform to line-break separated URLs

TODO: Screencast URL Magic

### Why "normcap"?

See [XKCD](https://xkcd.com):

<a href="https://xkcd.com/2116/"><img src="https://imgs.xkcd.com/comics/norm_normal_file_format.png" width="250px;"></a>

## Contribute

### Setup Environment

Prerequisites are **Python**, **Tesseract** (incl. **language data**) and on Linux also **XClip**.

```sh
# Clone repository
git clone https://github.com/dynobo/normcap.git

# Change into project directory
cd normcap

# Install pipenv (if not already installed)
pip install pipenv

# Install project development incl. dependencies
pipenv install --dev

# Register pre-commit hook
pipenv run pre-commit install -t pre-commit

# Run normcap in pipenv environment
pipenv run python -m normcap
```

### Design Principles

- **Multi-Platform**<br>Should work on on Linux, Mac & Windows.
- **Don't run as service**<br>As normcap is (hopefully) not used too often, it shouldn't consume resources in the background, even if it leads to a slower start-up time.
- **No network connection**<br>Everything should run locally without any network communication.
- **Avoid text in UI**<br>This just avoids translations ;-) And I think it is feasible in such an simple application.
- **Avoid configuration file or settings UI**<br>Focus on simplicity and core functionality.
- **Dependencies**<br>The less dependencies, the better. Of course I have to compromise, but I'm always open to suggestions on how to further reduce dependencies.
- **Chain of Responsibility as main design pattern**<br>[See description on refactoring.guru](https://refactoring.guru/design-patterns/chain-of-responsibility)
- **Multi-Monitors**<br>Supports setups with two or more display.

## Credits

This projected uses the following non-standard libraries:

- [mss](https://pypi.org/project/mss/) *- taking screenshots*
- [pillow](https://pypi.org/project/Pillow/) *- manipulating images*
- [tesserocr](https://pypi.org/project/tesserocr/) *- wrapper for tesseract's API*
- [pyperclip](https://pypi.org/project/pyperclip/) *- accessing clipboard*
- [pyinstaller](https://pypi.org/project/PyInstaller/) *- packaging for platforms*

And it depends on external software

- [tesseract](https://github.com/tesseract-ocr/tesseract) - *OCR engine*

Thanks to the maintainers of those nice libraries!

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)
