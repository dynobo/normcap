<!-- markdownlint-disable MD013 MD026 MD033 -->

# NormCap

***Intelligent OCR powered screen-capture tool to capture information instead of images.***

TODO: Alpha Version Disclaimer

<p align="center">
<br>
<a href="https://saythanks.io/to/dynobo"><img alt="Say thanks!" src="https://camo.githubusercontent.com/33e33e9c0c5907ade76ad21b385bbc4ddeadd7f6/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f7361792d7468616e6b732d6666363962342e737667"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/psf/black/blob/master/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
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
<br><br>
</p>

## Introduction

**Features:**

- Extract textual information from screen or images via Optical Character Recognition (OCR).
- Intelligently format the text.
- Automatically trigger action fitting to the extract text.
- Works on Linux, Mac & Windows
- Support multi monitor setups

**Usage examples:**

- Extract URLs, tables, etc. that have been sent to you in screenshot.
- Copy non-selectable error messages from alert windows.
- Capture subtitles from video stills.
- Easily extract text from menu entries or hover messages.

**Why "NormCap":**

- See [XKCD](https://xkcd.com)  
<a href="https://xkcd.com/2116/"><img src="https://imgs.xkcd.com/comics/norm_normal_file_format.png" style="width: 250px;"></a>

## Installation

### On Linux

NormCap on Linux requires **Tesseract** (incl. **language data**) and **XClip**.

```sh
# Install requirements

## on Debian/Ubuntu  
sudo apt-get install tesseract-ocr tesseract-ocr-eng xclip

## on Arch:
sudo pacman -S tesseract tesseract-data-eng xclip

## others:
TODO:

# Download and extract released binary package
TODO:

# make executable
cd normcap
chmod +x ./normcap

# Run
./normcap
```

### On Windows

NormCap on Windows requires **Tesseract** (incl. **language data**):

1. Download the latest 32bit version from [Tesseract Installer by UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
2. Follow the installer (which allows you to download additional languages).
3. Append the path to tesseract.exe to the `PATH` environment variable.
4. Create a new environment variable called `TESSDATA_PREFIX` and set it to the `YOUR_TESSERACT_DIR\tessdata`, which should contain the language data files.
5. Reboot, and execute `tesseract.exe` in command prompt. If everything worked well, you should see an output describing the command line options.

After the requirements are installed, continue with **NormCap**:

1. Download the windows binary from the [release page](https://github.com/dynobo/normcap/releases)
2. Unpack the archive to any directory
3. Run `normcap.exe` to start the program (no installation needed)

### TODO: On Mac

## Usage

### Basics

NormCap is intended to be executed by custom keybinding or desktop shortcut, so it doesn't run as daemon and won't use memory while not in use. 

By default NormCap is "stateless": it copies recognized text to the systems clipboard, but doesn't save images or text on the disk.

1. Run `normcap`. This will instantly screenshot your monitor(s) and present the screenshots fullscreen (which is indicated by a red border).
2. Select your region of interest, from which you want to extract text, by holding down your primary mouse button.
3. Before letting go the mouse button, you optionally can press `space`-key to switch through different modes of normcap, indicated by a symbol:
   - **☰ (raw):** Copy detected text line by line, without further modification.
   - **⚙ (parse):** Try to autodetect type of text using [magics](#Magics) and format the text accordingly, before copying.
   - **★ (trigger):** "Parse" the text *and* trigger an action corresponding to the detected [magic](#Magics) (e.g. URLs are opened in new browser tabs).
4. After letting the mouse button go, character recognition will be triggered an the text will be copied to the system's clipboard.
5. (optional) in case you used *trigger* mode, an action will be performed depending on the detected content.
6. Paste the text from clipboard where ever you like using your systems keybinding (e.g. `ctrl` + `p`).



### Command line options

NormCap doesn't have a configuration file, instead it's behavior can be customized using command line arguments:

```sh
TODO: Add cli printout
```

### TODO: Magics

## Contribute

### TODO: Design principles

- Main design pattern: [Chain of Responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility)

### Setup Environment

This requires an installation of **Python**, **Tesseract** (incl. **language data**) and on Linux also **XClip**.

```sh
# Clone repository
git clone https://github.com/dynobo/normcap.git

# Change into project directory
cd normcap

# Install poetry (if not already installed)
pip install poetry

# Install project dependencies
poetry install

# Register pre-commit hook
pipenv run pre-commit install -t pre-commit

# Run normcap in poetry environment
poetry run python normcap/normcap.py
```

## Credits

This projected uses the following non-standard libraries:

- [mss](https://pypi.org/project/mss/) *- taking screenshots* (MIT)
- [pillow](https://pypi.org/project/Pillow/) *- manipulating images* (OSI appr.)
- [pyocr](https://pypi.org/project/pyocr/) *- interfacing various OCR tools* (GPLv3)
- [pyperclip](https://pypi.org/project/pyperclip/) *- accessing clipboard* (BSD3)
- [pyinstaller](https://pypi.org/project/PyInstaller/) *- packaging for platforms* (GPL, but free usage)
- TODO: tesseract

Thanks to the maintainers of those!

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)
