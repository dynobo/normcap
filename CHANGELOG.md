# Changelog

## v0.165 (2020-11-01)

**Changes:**

- Implements [Issue #27](https://github.com/dynobo/normcap/issues/27): Show system notification after OCR completed.

## v0.1.5 (2020-10-31)

**Changes:**

- Fixes [Issue #81](https://github.com/dynobo/normcap/issues/81): Unhandled exception when user selected no region
- Related to the one above: Skip OCR if selected area is tiny (below 25 square pixels)

**Development related:**
- Updates dependencies which also now get pinned
- Move away from pipenv, using plain setuptools and requirements.txt's instead.

## v0.1.4 (2020-04-25)

**Changes:**

- Add fallback for Wayland DE on Linux, see [Issue 76](https://github.com/dynobo/normcap/issues/76#issue-605722434)

## v0.1.3 (2020-04-04)

**Changes:**

- Use the development version of PyInstaller for building Windows binaries to get [the not yet released bugfix](https://github.com/pyinstaller/pyinstaller/commit/91481570517707fc70aa70dca9eb986c61eac35d)

## v0.1.2 (2020-03-31)

**Changes:**

- Update Bleach Package to avoid potential vulnerability
- Switched to standard tesseract train-data for Windows
- Improve performance by skipping unnecessary tests

## v0.1.1 (2020-01-17)

**Changes:**

- Update PyInstaller to avoid potential vulnerability

## v0.1.0 (2019-12-23)

**First public beta. Please test and provide feedback!**

**Changes:**

- Publishing to pypi
- Add paragraph magic
- Adjust color

## v0.0.15 (2019-12-13)

**Changes:**

- Switched to simple semantic versioning
- Prepared for publishing to pypi

## v0.1a1 (2019-12-09)

**Changes:**

- Switched to faster tesseract bindings
- Windows build now includes tesseract
- Automated build workflow

## v0.1a0 (2019-09-17)

**Please help testing and provide feedback!**

Any feedback is useful, whether you find bugs or everything works for you. Thank you!

**Changes:**

- Initial working release
- Multi-monitor support
- Support Linux, Windows, Mac
- Add Magics for
  - Single Lines (unformatted text)
  - Email addresses
  - URLs.
