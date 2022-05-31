# Changelog

## v0.3.4 (2022-03-31)

- All: Various speed improvements.
- All: Smaller size by updating to Pyside 6.3 without addons.
- All: In README, complement dependencies for installing pip package. Thx,
  [@thecoder-001](https://github.com/thecoder-001) &
  [@faveoled](https://github.com/faveoled).
- Linux: Avoid crash on denied screenshot on Wayland.

## v0.3.3 (2022-03-25)

- All: Fixes screenshots not updated when capturing from tray menu
  [#181](https://github.com/dynobo/normcap/issues/199).

## v0.3.2 (2022-03-23)

- MacOS: Fixed crash in prebuild dmg package
  [#199](https://github.com/dynobo/normcap/issues/199).

## v0.3.1 (2022-03-20)

- All: Fix pasting to clipboard sometimes not working

## v0.3.0 (2022-03-20)

- All: Removed cli options `-v, --verbose` and `-V, --very-verbose` in favor of the new
  `-v, --verbosity` which accepts on of the options: `{error, warning, info, debug}`.
- All: Update to PySide6 (Qt6) and Python 3.9
- All: Add support for Tesseract 5 with better OCR
  [#170](https://github.com/dynobo/normcap/issues/170)
- All: Improve image processing for better detection accuracy, especially for bright
  text on dark backgrounds.
- Pre-build packages: Switched to shipping "fast" language models to reduce package
  size.
- Linux: Add support for Gnome Shell 41+ (using Screenshot Portal)
  [#153](https://github.com/dynobo/normcap/issues/153)
  [#157](https://github.com/dynobo/normcap/issues/157)
- Linux: Fix issues with transparency / black window
  [#154](https://github.com/dynobo/normcap/issues/154)
  [#155](https://github.com/dynobo/normcap/issues/155)
- Linux: Fix crash on non Gnome Shell systems
  [#168](https://github.com/dynobo/normcap/issues/168)
- MacOS: Full screen border and selection
  [#119](https://github.com/dynobo/normcap/issues/119)

## v0.2.10 (2021-12-27)

- All: Fix language settings not working if only a single language is selected
- MacOS: Fix crash at start of prebuild package due to missing dependency

## v0.2.9 (2021-12-26)

- All: Mitigate superfluous spaces in chinese languages
  [#158](https://github.com/dynobo/normcap/issues/158)
- Linux: Fix OCR not working on Gnome 41+ by using the offical screenshot API
  [#159](https://github.com/dynobo/normcap/issues/159)

## v0.2.8 (2021-10-20)

- Linux: Fix language option in settings.conf not human readable
  [#143](https://github.com/dynobo/normcap/issues/143)
- Pre-build packages: On Windows the msi-installer will now upgrade existing versions
  [#148](https://github.com/dynobo/normcap/issues/148)

## v0.2.7 (2021-09-25)

- Fixed NormCap error in case of disabled notifications
  [#142](https://github.com/dynobo/normcap/issues/142)

## v0.2.6 (2021-08-27)

**Breaking changes:**

- All: NormCap settings will be reset on upgrade (due to changes in the settings
  system)!
- Pre-build packages: A different set of languages is shipped! `jpn`, `jpn_vert` & `fra`
  got removed, but you can now add them yourself (Settings -> "open data folder")

**Further changes:**

- All: Use native settings storage
- All: Improve settings menu in case of many languages
- All: Slightly better performance
- Pre-build packages: Allow extending with additional languages
  [#137](https://github.com/dynobo/normcap/issues/137)
  [#127](https://github.com/dynobo/normcap/issues/127)
  [#104](https://github.com/dynobo/normcap/issues/104)
- MacOS: Fix missing libpng in package
  [#128](https://github.com/dynobo/normcap/issues/128)
- Linux: Fix AttributeError: 'MainWindow' object has no attribute 'macos_border_window'
  [#139](https://github.com/dynobo/normcap/issues/139)
  [#138](https://github.com/dynobo/normcap/pull/138)
- Windows: Fix update check

## v0.2.5 (2021-08-07)

- Linux: Fix disappering menu bar on gnome
  [#121](https://github.com/dynobo/normcap/issues/121)
- MacOS: Fix update checking
- MacOS: Draw border above menubar & dock
  [#119](https://github.com/dynobo/normcap/issues/119) (just cosmetic, both are still
  not selectable)
- All: Slightly better performance
- All: More useful error message for issues with QT
- All: Application can now be cancelled via `<ctrl>+c` in terminal
- All: Removed switching modes via `<space>`-key. Use the menu instead.

## v0.2.4 (2021-07-29)

- All: Improve robustness of settings
- Pre-build packages: Add languages `jpn` and `jpn_vert`
- MacOS: Fix bug that prevented the selection of a region
- MacOS: Catch ImportError of urllib in case update check is enabled

## v0.2.3 (2021-07-16)

- Fix styling issues with settings menu

## v0.2.2 (2021-07-15)

- Bugfixes related to update checking
- Small UI improvements

## v0.2.1 (2021-07-13)

- Add settings menu
- Add check for updates on startup (experimental, needs opt-in)

## v0.2.0 (2021-06-23)

- (Almost) complete rewrite of NormCap (things might be different!)
- Provide easy to use binary package releases
- Better support for HiDPI and multi monitor setups
- Switch from Tk to Qt as UI Framework
- System tray support (experimental)

## v0.1.11 (2021-04-04)

- Switch to pyclip library for clipboard handling
- Try a fix for MacOS dummy window issue

## v0.1.10 (2021-03-20)

- Handle missing system dependencies for the notification more gracefully
- Update versions of python package dependencies

## v0.1.9 (2020-12-06)

- Add installer for MS Windows to enable notification management
- Fix crash caused by missing notification icon in certain setups

## v0.1.8 (2020-11-17)

- Removed experimental tray icon support introduced in v0.1.7 (has caused unexpected
  issues).

## v0.1.7 (2020-11-14)

- Switch method to show fullscreen Windows to fix
  [Issue #88](https://github.com/dynobo/normcap/issues/88)
- Introduce preview of [Tray Icon support](https://github.com/dynobo/normcap/issues/82).
  It is not stable yet, but you can test it using the new `--tray` command line switch.

## v0.1.6 (2020-11-01)

- Implements [Issue #27](https://github.com/dynobo/normcap/issues/27): Show system
  notification after OCR completed.

## v0.1.5 (2020-10-31)

- Fixes [Issue #81](https://github.com/dynobo/normcap/issues/81): Unhandled exception
  when user selected no region
- Related to the one above: Skip OCR if selected area is tiny (below 25 square pixels)
- Updates dependencies which also now get pinned
- Move away from pipenv, using plain setuptools and requirements.txt's instead.

## v0.1.4 (2020-04-25)

- Add fallback for Wayland DE on Linux, see
  [Issue 76](https://github.com/dynobo/normcap/issues/76#issue-605722434)

## v0.1.3 (2020-04-04)

- Use the development version of PyInstaller for building Windows binaries to get
  [the not yet released bugfix](https://github.com/pyinstaller/pyinstaller/commit/91481570517707fc70aa70dca9eb986c61eac35d)

## v0.1.2 (2020-03-31)

- Update Bleach Package to avoid potential vulnerability
- Switched to standard tesseract train-data for Windows
- Improve performance by skipping unnecessary tests

## v0.1.1 (2020-01-17)

- Update PyInstaller to avoid potential vulnerability

## v0.1.0 (2019-12-23)

- Publishing to pypi
- Add paragraph magic
- Adjust color

## v0.0.15 (2019-12-13)

- Switched to simple semantic versioning
- Prepared for publishing to pypi

## v0.1a1 (2019-12-09)

- Switched to faster tesseract bindings
- Windows build now includes tesseract
- Automated build workflow

## v0.1a0 (2019-09-17)

**Please help testing and provide feedback!**

Any feedback is useful, whether you find bugs or everything works for you. Thank you!

- Initial working release
- Multi-monitor support
- Support Linux, Windows, Mac
- Add Magics for
  - Single Lines (unformatted text)
  - Email addresses
  - URLs.
