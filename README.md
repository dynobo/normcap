# NormCap

***Intelligent OCR powered screen-capture tool to capture information instead of images***

TODO: Alpha Version Disclaimer

<p align="center">
<br>
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

**Usage examples:**

- Extract URLs, tables, etc. that have been sent to you in screenshot.
- Copy non-selectable error messages from alert windows.
- Capture subtitles from video stills.
- Easily extract text from menu entries or hover messages.

**Why "NormCap":**

- See following [XKCD Comic:](https://xkcd.com/2116/)  
![XKCD norm files](https://imgs.xkcd.com/comics/norm_normal_file_format.png)  

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

### TODO: Basics

### TODO: Command line options

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

- [mss](https://pypi.org/project/mss/) *- taking screenshots*
- [pillow](https://pypi.org/project/Pillow/) *- manipulating images*
- [pyocr](https://pypi.org/project/pyocr/) *- interfacing various OCR tools*
- [pyperclip](https://pypi.org/project/pyperclip/) *- accessing clipboard*
- [pyinstaller](https://pypi.org/project/PyInstaller/) *- packaging for platforms*
- TODO: tesseract

Thanks to the maintainers of those!

## Certification

![WOMM](https://raw.githubusercontent.com/dynobo/lmdiag/master/badge.png)
