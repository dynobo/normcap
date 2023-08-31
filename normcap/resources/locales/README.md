# Localization of NormCap

For localization, I basically followed
[this tutorial by Matt Layman](https://www.mattlayman.com/blog/2015/i18n/) which uses
the [babel](https://babel.pocoo.org/en/latest/)-package and Python's buildin module
[`gettext`](https://docs.python.org/3/library/gettext.html).

## Add support for a new language

_Prerequisite:_ Follow the general
[setup of the development environment](../../../README.md#Development) and activate the
virtual Python environment via `poetry shell`.

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
1. Compile the new `.po` file to the machine-readable `.mo` file:
   ```sh
   pybabel compile --directory ./normcap/resources/locales --locale=<LOCALE_NAME>
   ```
1. To test your translation, run NormCap with the `LANGUAGE` environment variable set:
   ```sh
   LANGUAGE=<LOCALE_NAME> python normcap/app.py
   ```
1. Propose the inclusion of your new `.po`-file via a pull request to `main`.

## Update template and languages files

This is only necessary, when translated strings got changed (created, modified or
deleted) in NormCap's source code.

1. Generate `.pot` file and update all existing `.po` files:
   ```sh
   ./l10n.py --update-all
   ```
