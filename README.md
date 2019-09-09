# NormCap

***Intelligent OCR powered screen-capture tool to capture information instead of images***

---

<p align="center">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/psf/black/blob/master/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
</p>

<p align="center">
<a href="https://github.com/dynobo/normcap/releases">Releases</a> |
<a href="https://github.com/dynobo/normcap/blob/master/CHANGELOG.md">Changelog</a> |
<a href="https://github.com/dynobo/normcap/labels/backlog">Roadmap</a> |
<a href="https://github.com/dynobo/normcap/">Repo</a>
</p>

## Introduction

Features:

- Extract textual information from screen or images via OCR
- Intelligently format the text
- Automatically trigger action fitting to the extract text

Usage examples:

- Extract URLs, tables, etc. that have been sent to you in screenshot.
- Copy non-selectable error messages from alert windows.
- Capture subtitles from video stills
- Easily extract text from menu entries or hover messages

Why "NormCap":

![XKCD norm files](https://imgs.xkcd.com/comics/norm_normal_file_format.png)  
[Comic Source](https://xkcd.com/2116/)

## Install Prerequisites

### On Linux

**Install Tesseract and XClip:**

Debian/Ubuntu:  
`sudo apt-get install tesseract tesseract-data-eng xclip`

Arch:  
`sudo pacman -S tesseract tesseract-data-eng xclip`

### On Windows

**Install Tesseract:**

1. Download the latest 32bit version from [Tesseract Installer by UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
2. Follow the installer (which allows you to download additional languages).
3. Append the path to tesseract.exe to the `PATH` environment variable.
4. Create a new environment variable called `TESSDATA_PREFIX` and set it to the `YOUR_TESSERACT_DIR\tessdata`, which should contain the language data files.

### On Mac

## "Install" & Run NormCap

NormCap itself currently get shipped as Binary, it doesn't need any installation an can be executed directly.

Download the appropriate archive file for your platform from the [release page](https://github.com/dynobo/normcap/releases), unpack and run the `normcap` executable.

If you feel uncomfortable running arbitrary binaries, feel free to execute NormCap from source or build your own binaries (see section "Development" below)

## Usage

### Basics

### CLI Arguments

### Magics

## Development

### Run from Source

(Additionally to the prerequisites above, you'll need a valid Python installation)

1. Download Source of [release version](https://github.com/dynobo/normcap/releases) or [master](https://github.com/dynobo/normcap/archive/master.zip)
2. Unpack and open project folder terminal
3. Install poetry: `pip install poetry`
4. Install project dependencies: `poetry install`
5. Run in poetry environment:  `poetry run python normcap/normcap.py`

### Pre-Commit Hook

Please setup pre-commit hook if you intend to contribute. It runs tests and linter to catch some issue upfront committing:

`pipenv run pre-commit install -t pre-commit`

### Design Patterns

[Chain of Responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility) pattern is used for the main logic.

## Credits

This projected uses the following non-standard libraries:

- [mss](https://pypi.org/project/mss/) *- taking screenshots*
- [pillow](https://pypi.org/project/Pillow/) *- manipulating images*
- [pyocr](https://pypi.org/project/pyocr/) *- interfacing various OCR tools*
- [pyperclip](https://pypi.org/project/pyperclip/) *- accessing clipboard*
- [pyinstaller](https://pypi.org/project/PyInstaller/) *- packaging for platforms*

Thanks to the maintainers of those!

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)
