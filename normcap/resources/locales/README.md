# Localization of NormCap

## Status

<!-- Generated automatically! -->

| Locale                                   | Progress | Translated |
| :--------------------------------------- | -------: | ---------: |
| [de_DE](./de_DE/LC_MESSAGES/messages.po) |     100% |   67 of 67 |
| [es_ES](./es_ES/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [fr_FR](./fr_FR/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [hi_IN](./hi_IN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [pt_PT](./pt_PT/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [ru_RU](./ru_RU/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [zh_CN](./zh_CN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |

## Improve existing locale

1. Identify the file that corresponds to the local you want to edit. You can click the
   link in the table above, or you can navigate manually to the file at
   `./normcap/resources/locales/<LOCALE_NAME>/LC_MESSAGES/messages.po`
1. Open this `messages.po` file and edit the translations. If you like, use the
   [Free PO-Editor](https://pofile.net/free-po-editor) for easier editing.
   \
   **Important:** Never translate any variables which are written in curly brackets,
   e.g. `{count}`!
1. Propose the changed file in a new Pull Request. \
   (In case you are not familiar with
   git, you can also always propose a correction/change via a
   [new issue](https://github.com/dynobo/normcap/issues/new).)

## Add new locale

_Prerequisite:_ Follow the general
[setup of the development environment](../../../README.md#Development) and activate the
virtual Python environment via `poetry shell`.

_Note_: All commands should be run in the repository's root directory.

1. Research the `LOCALE_NAME` (e.g. `en_EN` or `de_AT`) of the language which shall be
   added. `gettext`'s
   [locale names](https://www.gnu.org/software/gettext/manual/html_node/Locale-Names.html)
   should be specified in the format `<language-code>_<COUNTRY_CODE>`. The values can be
   looked up in the lists of available
   [language codes](https://www.gnu.org/software/gettext/manual/html_node/Usual-Language-Codes.html)
   and
   [country codes](https://www.gnu.org/software/gettext/manual/html_node/Country-Codes.html).
1. Run the following command to create an initial `messages.po`-file for the language.
   Make sure to replace `<LOCALE_NAME>` by the string identified in step 1.
   ```sh
   pybabel init --input-file=./normcap/resources/locales/messages.pot --output-dir=./normcap/resources/locales --locale <LOCALE_NAME>
   ```
1. Edit the file `./normcap/resources/locales/<LOCALE_NAME>/LC_MESSAGES/messages.po`
   which was created in step 2. Add your translations as the respective `msgstr`. If you
   like, use the [Free PO-Editor](https://pofile.net/free-po-editor) for easier editing.
   \
   **Important:** Never translate any variables which are written in curly brackets,
   e.g. `{count}`!
1. Compile the new `.po` file to the machine-readable `.mo` file:
   ```sh
   python l10n.py
   ```
1. To test your translation, run NormCap with the `LANGUAGE` environment variable set:
   ```sh
   LANGUAGE=<LOCALE_NAME> python normcap/app.py
   ```
1. Propose the inclusion of your new `.po`-file via a pull request to `main`.

| Locale                                   | Progress | Translated |
| :--------------------------------------- | -------: | ---------: |
| [de_DE](./de_DE/LC_MESSAGES/messages.po) |     100% |   67 of 67 |
| [es_ES](./es_ES/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [fr_FR](./fr_FR/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [hi_IN](./hi_IN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [pt_PT](./pt_PT/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [ru_RU](./ru_RU/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [zh_CN](./zh_CN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |

| Locale                                   | Progress | Translated |
| :--------------------------------------- | -------: | ---------: |
| [de_DE](./de_DE/LC_MESSAGES/messages.po) |     100% |   67 of 67 |
| [es_ES](./es_ES/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [fr_FR](./fr_FR/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [hi_IN](./hi_IN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [pt_PT](./pt_PT/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [ru_RU](./ru_RU/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [zh_CN](./zh_CN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |

| Locale                                   | Progress | Translated |
| :--------------------------------------- | -------: | ---------: |
| [de_DE](./de_DE/LC_MESSAGES/messages.po) |     100% |   67 of 67 |
| [es_ES](./es_ES/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [fr_FR](./fr_FR/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [hi_IN](./hi_IN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [pt_PT](./pt_PT/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [ru_RU](./ru_RU/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [zh_CN](./zh_CN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |

| Locale                                   | Progress | Translated |
| :--------------------------------------- | -------: | ---------: |
| [de_DE](./de_DE/LC_MESSAGES/messages.po) |     100% |   67 of 67 |
| [es_ES](./es_ES/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [fr_FR](./fr_FR/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [hi_IN](./hi_IN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [pt_PT](./pt_PT/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [ru_RU](./ru_RU/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [zh_CN](./zh_CN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |

| Locale                                   | Progress | Translated |
| :--------------------------------------- | -------: | ---------: |
| [de_DE](./de_DE/LC_MESSAGES/messages.po) |     100% |   67 of 67 |
| [es_ES](./es_ES/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [fr_FR](./fr_FR/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [hi_IN](./hi_IN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [pt_PT](./pt_PT/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [ru_RU](./ru_RU/LC_MESSAGES/messages.po) |       8% |    6 of 67 |
| [zh_CN](./zh_CN/LC_MESSAGES/messages.po) |       8% |    6 of 67 |

## Update template and languages files

This is only necessary, when translated strings got changed (created, modified or
deleted) in NormCap's source code.

1. Generate `.pot` file and update all existing `.po` files:
   ```sh
   python l10n.py --update-all
   ```
