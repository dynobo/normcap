# NormCap

***Intelligent screen-capture tool to capture information instead of images*** by dynobo <dynobo@mailbox.org>

![XKCD norm files](https://imgs.xkcd.com/comics/norm_normal_file_format.png)  
[Source](https://xkcd.com/2116/)

## Why?

Because

- People like to annoy other people by sending URLs, address information, (...) as screenshots instead of text.
- There are still some sadistic coders out there, implementing pop-up boxes with not selectable error messages.

## Install

### Dependencies

For OCR you'll need one of the following tools setup on your machine:

- Libtesseract (Python bindings for the C API)
- Tesseract (wrapper: fork + exec)
- Cuneiform (wrapper: fork + exec)

For clipboard support in Linux you'll need on of the following packages:

- xclip: `sudo apt-get install xclip`
- xsel: `sudo apt-get install xsel`
- gtk
- PyQt4

## Setup Development

```sh
# Install dependencies
`poetry install`

# Setup pre-commit and pre-push hooks
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

## Credits

This projected uses the following non-standard libraries:

- [mss](https://pypi.org/project/mss/) *for taking screenshots*
- [pillow](https://pypi.org/project/Pillow/) *for image manipulation*
- [pyocr](https://pypi.org/project/pyocr/) *as interface to various OCR tools*
- [pyperclip](https://pypi.org/project/pyperclip/) *for accessing clipboard*

Thanks to the maintainers of those!
