# NormCap

***Intelligent OCR powered screen-capture tool to capture information instead of images*** by [dynobo](https://github.com/dynobo)

[Repo](TODO) - [Releases](TODO) - [Changelog](TODO) - [Roadmap](TODO)

Because...

-  there are people tending to send URLs, address information, tables (...) as screenshots instead of text.
- there are still some sadistic coders out there implementing alert windows with non selectable error messages (Dare you, if I find you!)
- in some rare situations it's really useful to capture text from video stills, photos, hover pop-ups, program menu entries, ...

![XKCD norm files](https://imgs.xkcd.com/comics/norm_normal_file_format.png)  
[Comic Source](https://xkcd.com/2116/)

## Install Prerequisites

### On Linux

**Install Tesseract and XClip:**

Debian/Ubuntu: `sudo apt-get install tesseract tesseract-eng xclip`

Arch: `sudo pacman -S `

**Explanation:**

 `tesseract` *(recommended)* or `cuneiform` needs to be installed for performing Optical Character Recognition. You most likely also want to install additional language files to improve the recognition of e.g. english or german language.

`xclip` *(recommended)* , `xsel`, `gtk` or `PyQt4` needs to be installed so NormCap can write to the clipboard. Most likely, one of these tools is already installed in your distribution.

### On Windows

**Install Tesseract for Optical Character Recognition:**

1. Download the latest 32bit version from [Tesseract Installer by UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
2. Follow the installer (which allows you to download additional languages).
3. Append the path to tesseract.exe to the `PATH` environment variable.
4. Create a new environment variable called `TESSDATA_PREFIX` and set it to the `YOUR_TESSERACT_DIR\tessdata`, which should contain the language data files.

(Alternatively you could try [Cuneiform](https://www.cuneiform-lang.org/download/) but that's untested.)

### On Mac


## "Install" & Run Normcap

NormCap itself currently get shipped as Binary, it doesn't need any installation an can be executed directly.

Download the appropriate archive file for your platform from the [release page](TODO), unpack and run the `normcap` executable.

If you feel uncomfortable running arbitrary binaries, feel free to execute NormCap from source or build your own binaries (see section "Development" below)

## Usage

### Basics

### CLI Arguments

### Magics


## Development

### Run from Source

(Aditionally to the prerequisites above, you'll need a valid Python installation)

1. Download Source of [release version](TODO) or [master](TODO)
2. Unpack and open project folder terminal
3. Install poetry: `pip install poetry`
4. Install project dependencies: `poetry install`
5. Run in poetry environment:  `poetry run python normcap/normcap.py`

### Pre-Commit Hook
Please setup pre-commit hook if you intend to contribute. It runs tests and linters to catch some issue upfront committing:

`pipenv run pre-commit install -t pre-commit`


### Design Patterns

[Chain of Responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility) pattern is used for the main logic, while the "magics" are provided through [depenency injection](TODO)


## Credits

This projected uses the following non-standard libraries:

- [mss](https://pypi.org/project/mss/) *- taking screenshots*
- [pillow](https://pypi.org/project/Pillow/) *- manipulating images*
- [pyocr](https://pypi.org/project/pyocr/) *- interfacing various OCR tools*
- [pyperclip](https://pypi.org/project/pyperclip/) *- accessing clipboard*
- [pyinstaller](https://pypi.org/project/PyInstaller/) *- packaging for platforms*

Thanks to the maintainers of those!


## Certificates and Badges

black TODO

womm TODO
