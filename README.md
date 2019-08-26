# NormCap

***Intelligent screen-capture tool to capture information instead of images*** by [dynobo](https://github.com/dynobo)

![XKCD norm files](https://imgs.xkcd.com/comics/norm_normal_file_format.png)  
[Comic Source](https://xkcd.com/2116/)

## Why?

Because...

- people like to annoy other people by sending URLs, address information, (...) as screenshots instead of text.
- there are still some sadistic coders out there, implementing pop-up boxes with not selectable error messages.
- in rare situations it's really useful to capture text from video stills, hover pop-ups, program menu entries, ...

## Install

### Dependencies

On all platforms, you'll need *one* of the following tools setup on your machine for OCR:

- Tesseract ([see downloads](https://github.com/tesseract-ocr/tesseract/wiki/Downloads)) *(recommended)*
- Libtesseract
- Cuneiform ([see downloads](https://www.cuneiform-lang.org/download/))

On Linux you'll need *one* of the following packages for clipboard support:
- `xclip` *(recommended)*, `xsel`, `gtk`, `PyQt4`

#### Installing Tesseract on Windows

1. Download the latest 32bit version from [Tesseract Installer by UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
2. Follow the installer (which allows you to download additional languages)
3. Append the path to tesseract.exe to the `PATH` environment variable
4. Create a new environment variable called `TESSDATA_PREFIX` and set it to the `YOUR_TESSERACT_DIR\tessdata`, which should contain the language data files

## Setup Development

```sh
# Install dependencies
poetry install

# Setup pre-commit and pre-push hooks
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

## Credits

This projected uses the following non-standard libraries:

- [mss](https://pypi.org/project/mss/) *- taking screenshots*
- [pillow](https://pypi.org/project/Pillow/) *- manipulating images*
- [pyocr](https://pypi.org/project/pyocr/) *- interfacing various OCR tools*
- [pyperclip](https://pypi.org/project/pyperclip/) *- accessing clipboard*
- [pyinstaller](https://pypi.org/project/PyInstaller/) *- packaging for platforms*

Thanks to the maintainers of those!
