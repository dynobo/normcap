<!-- markdownlint-disable MD013 MD026 MD033 -->

# NormCap

***Intelligent OCR powered screen-capture tool to capture information instead of images.***

<p align="center"><br>
<a href="https://saythanks.io/to/dynobo"><img alt="Say thanks!" src="https://img.shields.io/badge/Say-thanks-%23ff69b4"></a>
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
2. Select region of interest on screen
3. Retrieve recognized text in clipboard

**Example use cases:**

- Extract URLs, tables, etc. that have been sent to you in screenshot.
- Copy non-selectable error messages from alert windows.
- Capture subtitles from video stills.
- Extract text from menu entries or hover messages.

## Installation

### On Linux

NormCap on Linux requires **Tesseract** (incl. **language data**) and **XClip**.

1\. Install requirements:

```sh
## on Debian/Ubuntu/Mint
sudo apt-get install tesseract-ocr tesseract-ocr-eng xclip

## on Arch:
sudo pacman -S tesseract tesseract-data-eng xclip

## on Fedora:
sudo dnf install tesseract xclip
```

2\.  Download and extract a [released binary package](https://github.com/dynobo/normcap/releases), then:

```sh
# make binary executable
cd normcap
chmod +x ./normcap

# Run
./normcap
```

### On Windows

NormCap on Windows requires **Tesseract** (incl. **language data**):

1. Download the latest **32bit** version from [Tesseract Installer by University Library Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and execute it.
2. Append the path of `tesseract.exe` to the `PATH` [environment variable](https://duckduckgo.com/?q=edit+environment+variable+windows+10).
3. Create a new environment variable called `TESSDATA_PREFIX` and set it to `YOUR_TESSERACT_DIR\tessdata`

To test successful installation, reboot windows and execute `tesseract.exe` in command prompt. If everything worked well, you should see an output describing its command line options.

After the requirements are installed, continue with **NormCap**:

1. Download and extract binary package from the [release page](https://github.com/dynobo/normcap/releases).
2. Run `normcap.exe` to start the program (no installation needed).

### On Mac

*On Mac, some issues occur. [Help needed](https://github.com/dynobo/normcap/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22).*

1\. Install requirements:

```sh
brew install tesseract tesseract-lang
```

2\.  Download and extract [released binary package](https://github.com/dynobo/normcap/releases), then execute `normcap.app`

## Usage

### Basics

1. Run the `normcap` executable. A red border will appear around your screen.
2. Select a region with text using your mouse. Or press `<esc>` to quit program.
3. (Optional) Before letting go the mouse button, press `<space>`-key to switch through different modes of operation, as indicated by a symbol:
   - **☰ (raw):** Copy detected text line by line, without further modification.
   - **⚙ (parse):** Try to auto-detect type of text using [magics](#Magics) and format the text accordingly, then copy.
   - **★ (trigger):** "Parse" the text *and* trigger an action corresponding to the detected [magic](#Magics).
4. Paste the text from clipboard (e.g. `<ctrl> + p`).

### Hints

NormCap is intended to be executed via a custom keybinding or desktop shortcut, so it doesn't run as daemon and won't use memory while not in use. On the downside, this makes NormCap a little bit slower

By default NormCap is "stateless": it copies recognized text to the systems clipboard, but doesn't save images or text on the disk.

### Command line options

NormCap doesn't have a configuration file, instead it's behavior can be customized using command line arguments:

```plain
[holger@cioran normcap]$ poetry run python normcap/normcap.py --help
usage: normcap [-h] [-v] [-m MODE] [-l LANG] [-c COLOR] [-p PATH]

Intelligent OCR-powered screen-capture tool to capture information instead of
images.

optional arguments:
  -h, --help               show this help message and exit
  -v, --verbose            print debug information to console (default: False)
  -m MODE, --mode MODE     startup mode [raw,parse,trigger] (default: trigger)
  -l LANG, --lang LANG     set language for ocr tool (default: eng)
  -c COLOR, --color COLOR  set primary color for UI (default: #FF0000)
  -p PATH, --path PATH     set a path for storing images (default: None)
```

### Magics

"Magics" are like addons providing automated functionality. They get loaded in "parse" or "trigger" mode and perform tasks specific to the type of text, that was captured.

Each "magic" can perform three steps:

1. **Score:** Determine the likelihood of the detected text's type.
2. **Parse:** Format the text according to its type.
3. **Trigger:** Activate a built-in action to handle the detected text.

#### Single Line Magic

- **Score:** If single line is detected
- **Parse:** Trim unnecessary whitespace
- **Trigger:** Nothing (copy to clipboard only).

TODO: Screencast Single Line Magic

#### E-Mail Magic

- **Score:** Number of chars in email addresses vs. overall chars
- **Parse:** Transform to comma separated list
- **Trigger:** Open with default application for mailto-links

TODO: Screencast E-Mail Magic

#### URL Magic

- **Score:** Number of chars in URLs vs. overall chars
- **Parse:** Transform to line-break separated URLs
- **Trigger:** Open URLs in new tabs of default browser

TODO: Screencast URL Magic

### Why "NormCap"?

See [XKCD](https://xkcd.com):

<a href="https://xkcd.com/2116/"><img src="https://imgs.xkcd.com/comics/norm_normal_file_format.png" width="250px;"></a>

## Contribute

### Setup Environment

This requires an installation of **Python**, **Tesseract** (incl. **language data**) and on Linux also **XClip**.

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
- **Don't run as service**<br>As NormCap is (hopefully) not used too often, it shouldn't consume resources in the background, even if it leads to a slower start-up time.
- **Avoid text in UI**<br>This just avoids translations ;-) And I think it is feasible in such an simple application.
- **Avoid configuration file or settings UI**<br>Focus on simplicity and core functionality.
- **Dependencies**<br>The less dependencies, the better. Of course I have to compromise, but I'm always open to suggestions on how to further reduce dependencies.
- **Chain of Responsibility as main design pattern**<br>[See description on refactoring.guru](https://refactoring.guru/design-patterns/chain-of-responsibility)
- **Multi-Monitors**<br>Supports setups with two or more display.

## Credits

This projected uses the following non-standard libraries:

- [mss](https://pypi.org/project/mss/) *- taking screenshots*
- [pillow](https://pypi.org/project/Pillow/) *- manipulating images*
- [tesserocr](https://pypi.org/project/tesserocr/) *- interfacing various OCR tools*
- [pyperclip](https://pypi.org/project/pyperclip/) *- accessing clipboard*
- [pyinstaller](https://pypi.org/project/PyInstaller/) *- packaging for platforms*

And it depends on external software

- [tesseract](https://github.com/tesseract-ocr/tesseract) - *OCR engine*

Thanks to the maintainers of those nice libraries!

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)
