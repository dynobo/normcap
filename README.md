# NormCap

***Intelligent screen-capture tool to capture information instead of images*** by dynobo <dynobo@mailbox.org>

![XKCD norm files](https://imgs.xkcd.com/comics/norm_normal_file_format.png)  
[Source](https://xkcd.com/2116/)

## Why?

Because

- People like to annoy other people by sending URLs, address information, (...) as screenshots instead of text.
- There are still some sadistic coders out there, implementing pop-up boxes with not selectable error messages.

## Setup Development

```sh
# Install dependencies
`poetry install`

# Setup pre-commit and pre-push hooks
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```
