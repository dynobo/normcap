# Changelog

## v0.4.0 (2022-01-29)

- All: Remove support for Tesseract \< 5.0
- All: Faster startup if "Check for updates" is enabled.
- All: Refactor icon handling. Fixes a bug in the AUR package.
  ([#353](https://github.com/dynobo/normcap/issues/353))
- All: Fix crash if tesseract data for English is missing.
  ([#353](https://github.com/dynobo/normcap/issues/353))
- Linux: Fix FlatPak crashes due to missing permissions
  ([#320](https://github.com/dynobo/normcap/issues/320)).
- Prebuild packages: Add UI for downloading additional languages.
- Prebuild packages: Remove all default languages except English to reduce size.
- Prebuild packages (Windows): Switch to different tesseract binaries, which should work
  more reliable across systems. Unfortunately, it also enlarges the file size a lot.
  Would be great to [get your feedback](https://github.com/dynobo/normcap/discussions)
  on this! ([#254](https://github.com/dynobo/normcap/issues/254))

## v0.3.15 (2022-11-20)

- All: Add possibility to capture by left-clicking (or double-clicking) the tray icon.
  This also improves a bit the situation regarding
  [#306](https://github.com/dynobo/normcap/issues/306).
- All: Fix bug when running with Python 3.11
  [#311](https://github.com/dynobo/normcap/issues/311).
- Windows: Improve the msi-installer by doing a clean uninstallation that removes also
  log-folder and tessdata folder.

## v0.3.14 (2022-10-30)

- All: Add `--version` command line flag to easily print NormCap version.
- All: Slightly improved startup time.
- Windows: [Debug information](https://dynobo.github.io/normcap/#faqs-debug) can be
  printed on screen again. (No need for checking the log file anymore.)
- Linux: Fix FlatPak crashing when gtk3-nocsd is enabled, e.g. in Unity DE
  ([#190](https://github.com/dynobo/normcap/issues/190)).
- Linux: Fix full screen view in Unity DE
  ([#190](https://github.com/dynobo/normcap/issues/190)).
- Linux: Fix failing notifications if detected text starts with certain characters.

## v0.3.13 (2022-10-19)

- All: Reduce interval for (optional) update check to 7 days instead on every run to
  saves startup-time.
- macOS: Check for required screen recording permissions and warn if missing.
- macOS: Fix issue where NormCap process keeps running in background after exit.
- macOS: Work around failing screen recording permissions after installation of new
  NormCap version by resetting the permissions with every new NormCap version.

## v0.3.12 (2022-09-15)

- All: Change color of tray icon on successful copy to clipboard to improve usability in
  case the notifications are turned off or not working.
- All: Update dependencies.
- Linux: Fix multi monitor support on Wayland.

## v0.3.11 (2022-09-04)

- All: Improve removal of superfluous spaces in some eastern languages
  ([#158](https://github.com/dynobo/normcap/issues/158)).
- Linux: Fix notification issues on some KDE distros
  ([#260](https://github.com/dynobo/normcap/issues/260)). Thx,
  [@OLoKo64](https://github.com/OLoKo64).

## v0.3.10 (2022-09-03)

- All: Ensure backwards compatibility for Pillow \< 9.2.0
  ([#255](https://github.com/dynobo/normcap/issues/255)).
- Linux: Option to add additional languages to FlatPak
  ([#239](https://github.com/dynobo/normcap/issues/239)). Experimental, might not yet
  work!

## v0.3.9 (2022-08-28)

- All: Make update check more robust.
- Windows: Fix copy to clipboard ([#250](https://github.com/dynobo/normcap/issues/250)).
- Windows: Write log files for debugging
  ([see FAQs](https://dynobo.github.io/normcap/#faqs-windows-log)).
- macOS: Use `pbcopy` for more reliable copy to clipboard.
- Linux: Fix notifications not showing up in prebuild packages on some systems.

## v0.3.8 (2022-08-21)

- All: Further reduced file size of prebuild packages
  ([#238](https://github.com/dynobo/normcap/issues/238)). Thx,
  [@thecoder-001](https://github.com/thecoder-001)
- Linux: Fix clipboard issues on Wayland by using
  [wl-clipboard](https://github.com/bugaevc/wl-clipboard).
  ([#237](https://github.com/dynobo/normcap/issues/237))
- macOS: Indicate build architecture in filename (M1 is not supported!); Also add to
  FAQs ([#242](https://github.com/dynobo/normcap/issues/242)).

## v0.3.7 (2022-08-03)

- Linux: Fix `TypeError` crash during detection of appropriate screenshot method
  ([#235](https://github.com/dynobo/normcap/issues/235))

## v0.3.6 (2022-08-01)

- All: Hide UI while processing. Useful for larger sections of text or slower machines,
  where processing can take a while.
- All: Delay exit in case notification=on and tray=off to ensure notification is shown.
- Linux: Latest NormCap is now always available on FlatHub
  ([#147](https://github.com/dynobo/normcap/issues/147),
  [#225](https://github.com/dynobo/normcap/issues/225)). Thx,
  [@Tim453](https://github.com/Tim453).

## v0.3.5 (2022-07-27)

- All: Reduce the file size of prebuild packages.
- Windows: Fix bug causing a 5 seconds delay during recognition
  [#218](https://github.com/dynobo/normcap/issues/218).
- Docu: Add Python version required for installing package from PyPi
  [#221](https://github.com/dynobo/normcap/issues/221).

## v0.3.4 (2022-03-31)

- All: Various speed improvements.
- All: Smaller size by updating to PySide 6.3 without add-ons.
- Linux: Avoid crash on denied screenshot on Wayland.
- Docu: In README, complement dependencies for installing pip package. Thx,
  [@thecoder-001](https://github.com/thecoder-001) &
  [@faveoled](https://github.com/faveoled).
- Docu: Fix broken link in website Thx, [@LGro](https://github.com/LGro).

## v0.3.3 (2022-03-25)

- All: Fixes screenshots not updated when capturing from tray menu
  [#181](https://github.com/dynobo/normcap/issues/199).

## v0.3.2 (2022-03-23)

- macOS: Fixed crash in prebuild DMG package
  [#199](https://github.com/dynobo/normcap/issues/199).

## v0.3.1 (2022-03-20)

- All: Fix pasting to clipboard sometimes not working

## v0.3.0 (2022-03-20)

- All: Removed CLI options `-v, --verbose` and `-V, --very-verbose` in favor of the new
  `-v, --verbosity` which accepts on of the options: `{error, warning, info, debug}`.
- All: Update to PySide6 (Qt6) and Python 3.9
- All: Add support for Tesseract 5 with better OCR
  [#170](https://github.com/dynobo/normcap/issues/170)
- All: Improve image processing for better detection accuracy, especially for bright
  text on dark backgrounds.
- Prebuild packages: Switched to shipping "fast" language models to reduce package size.
- Linux: Add support for Gnome Shell 41+ (using Screenshot Portal)
  [#153](https://github.com/dynobo/normcap/issues/153)
  [#157](https://github.com/dynobo/normcap/issues/157)
- Linux: Fix issues with transparency / black window
  [#154](https://github.com/dynobo/normcap/issues/154)
  [#155](https://github.com/dynobo/normcap/issues/155)
- Linux: Fix crash on non Gnome Shell systems
  [#168](https://github.com/dynobo/normcap/issues/168)
- macOS: Full screen border and selection
  [#119](https://github.com/dynobo/normcap/issues/119)

## v0.2.10 (2021-12-27)

- All: Fix language settings not working if only a single language is selected
- macOS: Fix crash at start of prebuild package due to missing dependency

## v0.2.9 (2021-12-26)

- All: Mitigate superfluous spaces in Chinese languages
  [#158](https://github.com/dynobo/normcap/issues/158)
- Linux: Fix OCR not working on Gnome 41+ by using the official screenshot API
  [#159](https://github.com/dynobo/normcap/issues/159)

## v0.2.8 (2021-10-20)

- Linux: Fix language option in `settings.conf` not human-readable
  [#143](https://github.com/dynobo/normcap/issues/143)
- Prebuild packages: On Windows the MSI-installer will now upgrade existing versions
  [#148](https://github.com/dynobo/normcap/issues/148)

## v0.2.7 (2021-09-25)

- Fixed NormCap error in case of disabled notifications
  [#142](https://github.com/dynobo/normcap/issues/142)

## v0.2.6 (2021-08-27)

**Breaking changes:**

- All: NormCap settings will be reset on upgrade (due to changes in the settings
  system)!
- Prebuild packages: A different set of languages is shipped! `jpn`, `jpn_vert` & `fra`
  got removed, but you can now add them yourself (Settings → "open data folder")

**Other changes:**

- All: Use native settings storage
- All: Improve settings menu in case of many languages
- All: Slightly better performance
- Prebuild packages: Allow extending with additional languages
  [#137](https://github.com/dynobo/normcap/issues/137)
  [#127](https://github.com/dynobo/normcap/issues/127)
  [#104](https://github.com/dynobo/normcap/issues/104)
- macOS: Fix missing `libpng` in package
  [#128](https://github.com/dynobo/normcap/issues/128)
- Linux: Fix AttributeError: 'MainWindow' object has no attribute 'macos_border_window'
  [#139](https://github.com/dynobo/normcap/issues/139)
  [#138](https://github.com/dynobo/normcap/pull/138)
- Windows: Fix update check

## v0.2.5 (2021-08-07)

- Linux: Fix disappearing menu bar on gnome
  [#121](https://github.com/dynobo/normcap/issues/121)
- macOS: Fix update checking
- macOS: Draw border above menubar & dock
  [#119](https://github.com/dynobo/normcap/issues/119) (just cosmetic, both are still
  not selectable)
- All: Slightly better performance
- All: More useful error message for issues with QT
- All: Application can now be cancelled via `<ctrl>+c` in terminal
- All: Removed switching modes via `<space>`-key. Use the menu instead.

## v0.2.4 (2021-07-29)

- All: Improve robustness of settings
- Prebuild packages: Add languages `jpn` and `jpn_vert`
- macOS: Fix bug that prevented the selection of a region
- macOS: Catch `ImportError` of `urllib` in case update check is enabled

## v0.2.3 (2021-07-16)

- Fix styling issues with settings menu

## v0.2.2 (2021-07-15)

- Bug fixes related to update checking
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
- Try a fix for macOS dummy window issue

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

- Switch method to show full-screen Windows to fix
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

- Publishing to PyPi
- Add paragraph magic
- Adjust color

## v0.0.15 (2019-12-13)

- Switched to simple semantic versioning
- Prepared for publishing to PyPi

## v0.1a1 (2019-12-09)

- Switched to faster tesseract bindings
- Windows build now includes tesseract
- Automated build workflow

## v0.1a0 (2019-09-17)

**Please help to test and provide feedback!**

Any feedback is useful, whether you find bugs or everything works for you. Thank you!

- Initial working release
- Multi-monitor support
- Support Linux, Windows, Mac
- Add Magics for
  - Single Lines (unformatted text)
  - Email addresses
  - URLs.
