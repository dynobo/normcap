<!-- markdownlint-disable MD013 MD026 MD033 -->

# normcap

***OCR powered screen-capture tool to capture information instead of images.***

<p align="center"><br>
<a href="https://github.com/dynobo/normcap/releases"><img alt="Build passing" src="https://github.com/dynobo/normcap/workflows/Build/badge.svg"></a>
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

![&nbsp;](https://github.com/dynobo/normcap/blob/master/ressource/normcap.gif)
[normcap screencast](https://github.com/dynobo/normcap/blob/master/ressource/normcap.gif)

## Installation

### On Linux

1\. Install dependencies:

```sh
## on Ubuntu/Debian:
sudo apt-get install tesseract-ocr xclip python3-tk python3-pil.imagetk

# on Arch:
sudo pacman -S tesseract tesseract-data-eng xclip tk python-pillow  

# on Fedora
sudo dnf install tesseract xclip python3-tkinter
```

2\. Install normcap:

```sh
pip install normcap
```

(***OR*** download and extract binary package from the [latest release](
https://github.com/dynobo/normcap/releases))

3\. Execute `./normcap`

### On Windows *(recommended method)*

1\. Download and extract binary package from the [latest release](https://github.com/dynobo/normcap/releases) (no installation required)

2\. Execute `normcap.exe`

### On Windows *(alternative method)*

1\. Install "Tesseract", e.g. by using the [installer provided by UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

2\. Set the environment variable `TESSDATA_PREFIX` to Tesseract's data folder, e.g.:

```cmd
setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata"
```

3\. Install [tesserocr](https://pypi.org/project/tesserocr/), e.g. by using the [Windows specific wheel](https://github.com/simonflueckiger/tesserocr-windows_build):

```bash
pip install https://github.com/simonflueckiger/tesserocr-windows_build/releases/download/tesserocr-v2.4.0-tesseract-4.0.0/tesserocr-2.4.0-cp37-cp37m-win_amd64.whl
```

4\. Run

```sh
pip install normcap
```

5\. Execute `normcap`

### On Mac

***Attention! On Mac not everything works. [Help needed!](https://github.com/dynobo/normcap/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)***

1\. Install dependencies:

```sh
brew install tesseract tesseract-lang
```

2\. Install normcap:

```sh
pip install normcap
```

(***OR*** download and extract binary package from the [latest release](
https://github.com/dynobo/normcap/releases))

3\. Execute `normcap.app`

## Usage

### General

- After launching `normcap` press `<esc>` to abort and quit.

- Before letting go the mouse button, press `<space>`-key to switch mode, as indicated by a symbol:
   - **☰ (raw):** Copy detected text line by line, without further modification
   - **☶ (parse):** Try to auto-detect type of text using [magics](#Magics) and format the text accordingly, then copy

- To download additional languages for Mac and Linux, check the official repository of your distribution for `tesseract`-languages. Packages names might vary.

- The [Windows release](https://github.com/dynobo/normcap/releases) of normcap supports English and German out of the box. If you need additional languages, download the appropriate files from [the tesseract repo](https://github.com/tesseract-ocr/tessdata_best) and place them into the `/normcap/tessdata/` folder.

- normcap is intended to be executed on demand via keybinding or desktop shortcut. Therefore it doesn't occupy resources by running in the background, but it's startup is a bit slower.

- By default normcap is "stateless": it copies recognized text to the systems clipboard, but doesn't save images or text on the disk. However, you can use the `--path` switch to store the images in any folder.

### Command line options

normcap has no settings, just a set of command line arguments:

```plain
(normcap)dynobo@cioran:~$ normcap --help
usage: normcap [-h] [-v] [-m MODE] [-l LANG] [-c COLOR] [-p PATH]

OCR-powered screen-capture tool to capture information instead of images.

optional arguments:
  -h, --help               show this help message and exit
  -v, --verbose            print debug information to console (default: False)
  -m MODE, --mode MODE     startup mode [raw,parse] (default: parse)
  -l LANG, --lang LANG     languages for ocr, e.g. eng+deu (default: eng)
  -c COLOR, --color COLOR  set primary color for UI (default: #FF0000)
  -p PATH, --path PATH     set a path for storing images (default: None)
```

### Magics

"Magics" are like addons providing automated functionality to intelligently detect and format the captured input.

First, every "magic" calculates a **"score"** to determine the likelihood of the magic being responsible for this type of text. Second, the "magic" which achieved the highest "score" take the necessary actions to **"transform"** the input text according to its type.

Currently implemented Magics:

| Magic                | Score                                                | Transform                                                                          |
| -------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Single&nbsp;line** | Only single line is detected                         | Trim unnecessary whitespace                                                        |
| **Multi&nbsp;line**  | Multi lines, but single Paragraph                    | Separated by line break and trim each lined                                        |
| **Paragraph**        | Multiple blocks of lines or multiple paragraphs      | Join every paragraph into single line, separate different paragraphs by empty line |
| **E-Mail**           | Number of chars in email addresses vs. overall chars | Transform to comma separated list of email addresses                               |
| **URL**              | Number of chars in URLs vs. overall chars            | Transform to line-break separated URLs                                             |

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
