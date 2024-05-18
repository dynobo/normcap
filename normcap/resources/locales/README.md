# Localization of NormCap

**Contents:**

- [Status](#status)
- [Proofread existing translations](#proofread-existing-translations)
- [Test existing translations in NormCap](#test-existing-translations-in-normcap)
- [Improve existing translations](#improve-existing-translations)
- [Add new translation](#add-new-translation)
- [Update template and language files](#update-template-and-languages-files)

## Status

<!-- Generated automatically! -->

| Locale                                   | Progress | Translated |
| :--------------------------------------- | -------: | ---------: |
| [de_DE](./de_DE/LC_MESSAGES/messages.po) |     100% |   68 of 68 |
| [es_ES](./es_ES/LC_MESSAGES/messages.po) |     100% |   68 of 68 |
| [fr_FR](./fr_FR/LC_MESSAGES/messages.po) |     100% |   68 of 68 |
| [hi_IN](./hi_IN/LC_MESSAGES/messages.po) |       8% |    6 of 68 |
| [it_IT](./it_IT/LC_MESSAGES/messages.po) |     100% |   68 of 68 |
| [pl_PL](./pl_PL/LC_MESSAGES/messages.po) |       8% |    6 of 68 |
| [pt_BR](./pt_BR/LC_MESSAGES/messages.po) |     100% |   68 of 68 |
| [pt_PT](./pt_PT/LC_MESSAGES/messages.po) |       8% |    6 of 68 |
| [ru_RU](./ru_RU/LC_MESSAGES/messages.po) |     100% |   68 of 68 |
| [sv_SE](./sv_SE/LC_MESSAGES/messages.po) |     100% |   68 of 68 |
| [uk_UA](./uk_UA/LC_MESSAGES/messages.po) |     100% |   68 of 68 |
| [zh_CN](./zh_CN/LC_MESSAGES/messages.po) |       8% |    6 of 68 |

## Proofread existing translations

1. Open one of the translations (`.po`-files) linked in the "Status" table above.
1. In the file, each string is represented by its English text (`msgid`-field), its
   translation into the target language (`msgstr`-field) and maybe a translator
   comment (`#` lines above).
1. Read the `msgstr`'s one by one and check them for wording, spelling and punctuation.
1. Propose any changes preferably right away as Pull Request, or if you don't feel
   comfortable in doing that, report your finding as
   [new issue](https://github.com/dynobo/normcap/issues/new).

_NOTE:_: Details about the `.po`-file format can be found in the
[official specification](https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html), if needed.

## Test existing translations in NormCap

1. Pick a translation from the "Status" table which is fairly complete
1. Run NormCap (>= `v0.5.0beta1`) with that language, either by changing your system's
   language to the target language or by starting NormCap with an environment variable
   set:
    - on Linux:
        - Python package:
          ```
          LANGUAGE=<LOCALE_NAME> normcap
          ```
        - AppImage:
          ```
          LANGUAGE=<LOCALE_NAME> NormCap-[...].AppImage
          ```
        - FlatPak:
          ```
          LANGUAGE=<LOCALE_NAME> flatpak run --command=normcap com.github.dynobo.normcap
          ```
    - on macOS:
        - DMG:
          ```
          LANG=<LOCALE_NAME> /Applications/NormCap.app/Contents/MacOS/NormCap
          ```
    - on Windows:
        - Python package:
          ```
          set LANG=<LOCALE_NAME>
          normcap
          ```
        - MSI installed:
          ```
          set LANG=<LOCALE_NAME>
          %LOCALAPPDATA%\Programs\NormCap\NormCap.exe
          ```
1. Navigate through the user interface and proofread any text. Pay special attention to
   whether the presentation of the text looks good. (E.g. strings are too long/short,
   wrong line breaks, ...)
1. Propose any changes preferably right away as Pull Request, or if you don't feel
   comfortable in doing that, report your finding as
   [new issue](https://github.com/dynobo/normcap/issues/new).

## Improve existing translations

1. Identify the file that corresponds to the local you want to edit. You can click the
   link in the table above, or you can navigate manually to the file at
   `./normcap/resources/locales/<LOCALE_NAME>/LC_MESSAGES/messages.po`
1. Open this `messages.po` file and edit the translations. If you like, use the
   [Free PO-Editor](https://pofile.net/free-po-editor) for easier editing.
   \
   **Important:**
    - Never translate any variables which are written in curly brackets, e.g. `{count}`!
    - Don't bother with updating the header section at the top, it will get overwritten
      automatically.
1. Propose the changed file in a new Pull Request. \
   (In case you are not familiar with
   git, you can also always propose a correction or change via a
   [new issue](https://github.com/dynobo/normcap/issues/new).)

## Add new translation

_Important:_ If you want to contribute with a new locale, but the process below seems to
complicated for you, do not hesitate to request the creation of a new, empty `.po` file
via [opening a new issue](https://github.com/dynobo/normcap/issues/new)!

_Prerequisite:_ Follow the general
[setup of the development environment](../../../README.md#Development) and activate the
virtual Python environment via `hatch shell`.

_Note_: All commands should be run in the repository's root directory.

1. Research the `LOCALE_NAME` (e.g. `en_EN` or `de_AT`) of the language which shall be
   added. `gettext`'s
   [locale names](https://www.gnu.org/software/gettext/manual/html_node/Locale-Names.html)
   should be specified in the format `<language-code>_<COUNTRY_CODE>`. Visit the
   lists of available
   [language codes](https://www.gnu.org/software/gettext/manual/html_node/Usual-Language-Codes.html)
   and
   [country codes](https://www.gnu.org/software/gettext/manual/html_node/Country-Codes.html)
   to identify possible values.
1. Run the following command to create an initial `messages.po`-file for the language.
   Make sure to replace `<LOCALE_NAME>` by the string identified in step 1.
   ```sh
   hatch run create-locale <LOCALE_NAME>
   ```
1. Edit the file `./normcap/resources/locales/<LOCALE_NAME>/LC_MESSAGES/messages.po`
   which was created in step 2. Add your translations as the respective `msgstr`. If
   you like, use the [Free PO-Editor](https://pofile.net/free-po-editor) for easier
   editing. \
   **Important:**
    - Never translate any variables which are written in curly brackets, e.g. `{count}`!
    - Don't bother with updating the header section at the top, it will get overwritten
      automatically.
1. Compile the new `.po` file to the machine-readable `.mo` file:
   ```sh
   hatch run locales-compile
   ```
1. To test your translation, run NormCap with the `LANGUAGE` environment variable set:
   ```sh
   LANGUAGE=<LOCALE_NAME> python normcap/app.py
   ```
1. Propose the inclusion of your new `.po`-file via a pull request to `main`.

## Update template and languages files

This is only necessary, when translatable strings in NormCap's source code got changed
(created, modified or deleted).

1. Generate `.pot` file and update all existing `.po` files:
   ```sh
   hatch run locales-update
   ```
