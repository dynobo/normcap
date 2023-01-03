"""Global constants."""

from normcap.gui.models import Setting, Urls

UPDATE_CHECK_INTERVAL_DAYS = 7

DESCRIPTION = (
    "OCR-powered screen-capture tool to capture information instead of images."
)

MESSAGE_LANGUAGES = (
    "You are not using the prebuild package version of NormCap. "
    "Please refer to the documentation of Tesseract for your "
    "operating system on how to install additional languages."
)

URLS = Urls(
    releases="https://github.com/dynobo/normcap/releases",
    changelog="https://github.com/dynobo/normcap/blob/main/CHANGELOG.md",
    pypi="https://pypi.org/pypi/normcap",
    github="https://github.com/dynobo/normcap",
    issues="https://github.com/dynobo/normcap/issues",
    faqs="https://dynobo.github.io/normcap/#faqs",
    website="https://dynobo.github.io/normcap",
    xcb_error="https://github.com/dynobo/normcap/blob/main/FAQ.md"
    + "#linux-could-not-load-the-qt-platform-plugin-xcb",
)

DEFAULT_SETTINGS = (
    Setting(
        key="color",
        flag="c",
        type_=str,
        value="#FF2E88",
        help="Set primary color for UI, e.g. '#FF2E88'",
        choices=None,
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="language",
        flag="l",
        type_=str,
        value="eng",
        help="Set language(s) for text recognition, e.g. '-l eng' or '-l eng deu'",
        choices=None,
        cli_arg=True,
        nargs="+",
    ),
    Setting(
        key="mode",
        flag="m",
        type_=str,
        value="parse",
        help="Set capture mode",
        choices=("raw", "parse"),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="notification",
        flag="n",
        type_=bool,
        value=True,
        help="Disable or enable notification after ocr detection",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="tray",
        flag="t",
        type_=bool,
        value=False,
        help="Disable or enable system tray",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="update",
        flag="u",
        type_=bool,
        value=False,
        help="Disable or enable check for updates",
        choices=(True, False),
        cli_arg=True,
        nargs=None,
    ),
    Setting(
        key="version",
        flag="c",
        type_=str,
        value="0.0.0",
        help="NormCap version number",
        choices=None,
        cli_arg=False,
        nargs=None,
    ),
    Setting(
        key="last-update-check",
        flag="d",
        type_=str,
        value="0",
        help="Date of last successful update check in format yyyy-mm-dd",
        choices=None,
        cli_arg=False,
        nargs=None,
    ),
)

LANGUAGES_BASE_URL = "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/"
# fmt: off
LANGUAGES = [
    {"abbrev": "afr", "name": "Afrikaans", "native": "Afrikaans"},
    {"abbrev": "amh", "name": "Amharic", "native": "አማርኛ"},
    {"abbrev": "ara", "name": "Arabic", "native": "العربية"}, # noqa: RUF001
    {"abbrev": "asm", "name": "Assamese", "native": "অসমীয়া"},
    {"abbrev": "aze", "name": "Azerbaijani", "native": "آذربایجان دیلی"}, # noqa: RUF001
    {"abbrev": "aze_cyrl", "name": "Azerbaijani (cyrillic)", "native": "Азәрбајҹан дили"}, # noqa: RUF001,E501
    {"abbrev": "bel", "name": "Belarusian", "native": "беларуская мова"}, # noqa: RUF001
    {"abbrev": "ben", "name": "Bengali", "native": "বাংলা"},
    {"abbrev": "bod", "name": "Tibetan", "native": "བོད་ཡིག"},
    {"abbrev": "bos", "name": "Bosnian", "native": "bosanski jezik"},
    {"abbrev": "bre", "name": "Breton", "native": "brezhoneg"},
    {"abbrev": "bul", "name": "Bulgarian", "native": "български език"}, # noqa: RUF001
    {"abbrev": "cat", "name": "Catalan; Valencian", "native": "català"},
    {"abbrev": "ceb", "name": "Cebuano", "native": "Sinugbuanong Binisayâ"},
    {"abbrev": "ces", "name": "Czech", "native": "čeština; český jazyk"},
    {"abbrev": "chi_sim", "name": "Chinese, simplified", "native": "中文; 汉语; 漢語"},
    {"abbrev": "chi_sim_vert", "name": "Chinese, simplified (vertical)", "native": "中文; 汉语; 漢語"}, # noqa: E501
    {"abbrev": "chi_tra", "name": "Chinese, traditional", "native": "中文; 汉语; 漢語"},
    {"abbrev": "chi_tra_vert", "name": "Chinese, traditional (vertical)", "native": "中文; 汉语; 漢語"}, # noqa: E501
    {"abbrev": "chr", "name": "Cherokee", "native": "ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ"}, # noqa: RUF001
    {"abbrev": "cos", "name": "Corsican", "native": "corsu"},
    {"abbrev": "cym", "name": "Welsh", "native": "Cymraeg"},
    {"abbrev": "dan", "name": "Danish", "native": "dansk"},
    {"abbrev": "dan_frak", "name": "Danish (Fraktur)", "native": "dansk"},
    {"abbrev": "deu", "name": "German", "native": "Deutsch"},
    {"abbrev": "deu_frak", "name": "German (Fraktur)", "native": "Deutsch"},
    {"abbrev": "div", "name": "Divehi; Dhivehi; Maldivian", "native": "ދިވެހި"},
    {"abbrev": "dzo", "name": "Dzongkha", "native": "རྫོང་ཁ"},
    {"abbrev": "ell", "name": "Greek", "native": "ελληνικά"}, # noqa: RUF001
    {"abbrev": "eng", "name": "English", "native": "English"},
    {"abbrev": "enm", "name": "Middle English (1100-1500)", "native": ""},
    {"abbrev": "epo", "name": "Esperanto", "native": "Esperanto"},
    {"abbrev": "equ", "name": "Equations; Math", "native": "f(x) = x² - 5"},
    {"abbrev": "est", "name": "Estonian", "native": "eesti keel"},
    {"abbrev": "eus", "name": "Basque", "native": "euskara; euskera"},
    {"abbrev": "fao", "name": "Faroese", "native": "føroyskt"},
    {"abbrev": "fas", "name": "Persian; Farsi", "native": "فارسی"}, # noqa: RUF001
    {"abbrev": "fil", "name": "Filipino", "native": "wikang filipino"},
    {"abbrev": "fin", "name": "Finnish", "native": "suomen kieli"},
    {"abbrev": "fra", "name": "French", "native": "français"},
    {"abbrev": "frk", "name": "Frankish", "native": ""},
    {"abbrev": "frm", "name": "Middle French (ca.1400-1600)", "native": ""},
    {"abbrev": "fry", "name": "Western Frisian", "native": "Frysk"},
    {"abbrev": "gla", "name": "Gaelic", "native": "Gàidhlig"},
    {"abbrev": "gle", "name": "Irish", "native": "Gaeilge"},
    {"abbrev": "glg", "name": "Galician", "native": "galego"},
    {"abbrev": "grc", "name": "Ancient Greek (to 1453)", "native": ""},
    {"abbrev": "guj", "name": "Gujarati", "native": "ગુજરાતી"},
    {"abbrev": "hat", "name": "Haitian", "native": "Kreyòl ayisyen"},
    {"abbrev": "heb", "name": "Hebrew", "native": "עברית"}, # noqa: RUF001
    {"abbrev": "hin", "name": "Hindi", "native": "हिन्दी; हिंदी"},
    {"abbrev": "hrv", "name": "Croatian", "native": "hrvatski jezik"},
    {"abbrev": "hun", "name": "Hungarian", "native": "magyar"},
    {"abbrev": "hye", "name": "Armenian", "native": "Հայերեն"}, # noqa: RUF001
    {"abbrev": "iku", "name": "Inuktitut", "native": "ᐃᓄᒃᑎᑐᑦ"},
    {"abbrev": "ind", "name": "Indonesian", "native": "Bahasa Indonesia"},
    {"abbrev": "isl", "name": "Icelandic", "native": "Íslenska"},
    {"abbrev": "ita", "name": "Italian", "native": "italiano"},
    {"abbrev": "ita_old", "name": "Italian (old)", "native": ""},
    {"abbrev": "jav", "name": "Javanese", "native": "ꦧꦱꦗꦮ"},
    {"abbrev": "jpn", "name": "Japanese", "native": "日本語; にほんご"},
    {"abbrev": "jpn_vert", "name": "Japanese (vertical)", "native": "日本語; にほんご"},
    {"abbrev": "kan", "name": "Kannada", "native": "ಕನ್ನಡ"},
    {"abbrev": "kat", "name": "Georgian", "native": "ქართული"},
    {"abbrev": "kat_old", "name": "Georgian (old)", "native": "ქართული"},
    {"abbrev": "kaz", "name": "Kazakh", "native": "қазақ тілі"}, # noqa: RUF001
    {"abbrev": "khm", "name": "Khmer", "native": "ខ្មែរ; ខេមរភាសា; ភាសាខ្មែរ"}, # noqa: E501
    {"abbrev": "kir", "name": "Kirghiz", "native": "Кыргыз тили"}, # noqa: RUF001
    {"abbrev": "kmr", "name": "Northern Kurdish", "native": ""},
    {"abbrev": "kor", "name": "Korean", "native": "한국어"},
    {"abbrev": "kor_vert", "name": "Korean (vertical)", "native": "한국어"},
    {"abbrev": "lao", "name": "Lao", "native": "ພາສາລາວ"},
    {"abbrev": "lat", "name": "Latin", "native": "lingua latina"},
    {"abbrev": "lav", "name": "Latvian", "native": "latviešu valoda"},
    {"abbrev": "lit", "name": "Lithuanian", "native": "lietuvių kalba"},
    {"abbrev": "ltz", "name": "Luxembourgish", "native": "Lëtzebuergesch"},
    {"abbrev": "mal", "name": "Malayalam", "native": "മലയാളം"}, # noqa: RUF001
    {"abbrev": "mar", "name": "Marathi", "native": "मराठी"},
    {"abbrev": "mkd", "name": "Macedonian", "native": "македонски јазик"}, # noqa: RUF001,E501
    {"abbrev": "mlt", "name": "Maltese", "native": "Malti"},
    {"abbrev": "mon", "name": "Mongolian", "native": "Монгол хэл"}, # noqa: RUF001
    {"abbrev": "mri", "name": "Maori", "native": "te reo Māori"},
    {"abbrev": "msa", "name": "Malay", "native": "bahasa Melayu; بهاس ملايو\u200e"}, # noqa: RUF001,E501
    {"abbrev": "mya", "name": "Burmese", "native": "ဗမာစာ"},
    {"abbrev": "nep", "name": "Nepali", "native": "नेपाली"},
    {"abbrev": "nld", "name": "Dutch; Flemish", "native": "Nederlands; Vlaams"},
    {"abbrev": "nor", "name": "Norwegian", "native": "Norsk"},
    {"abbrev": "oci", "name": "Occitan (post 1500)", "native": "occitan; lenga d'òc"},
    {"abbrev": "ori", "name": "Oriya", "native": "ଓଡ଼ିଆ"},
    {"abbrev": "osd", "name": "Orientation & Script Detection", "native": ""},
    {"abbrev": "pan", "name": "Panjabi; Punjabi", "native": "ਪੰਜਾਬੀ; پنجابی\u200e"}, # noqa: RUF001,E501
    {"abbrev": "pol", "name": "Polish", "native": "język polski"},
    {"abbrev": "por", "name": "Portuguese", "native": "português"},
    {"abbrev": "pus", "name": "Pushto; Pashto", "native": "پښتو"},
    {"abbrev": "que", "name": "Quechua", "native": "Runa Simi; Kichwa"},
    {"abbrev": "ron", "name": "Romanian; Moldavian", "native": "limba română"},
    {"abbrev": "rus", "name": "Russian", "native": "Русский"}, # noqa: RUF001
    {"abbrev": "san", "name": "Sanskrit; Saṁskṛta", "native": "संस्कृतम्"},
    {"abbrev": "sin", "name": "Sinhala; Sinhalese", "native": "සිංහල"}, # noqa: RUF001
    {"abbrev": "slk", "name": "Slovak", "native": "slovenský jazyk"},
    {"abbrev": "slk_frak", "name": "Slovak (Fraktur)", "native": "slovenský jazyk"},
    {"abbrev": "slv", "name": "Slovenian", "native": "slovenski jezik"},
    {"abbrev": "snd", "name": "Sindhi", "native": "सिन्धी; سنڌي، سندھی\u200e"}, # noqa: RUF001,E501
    {"abbrev": "spa", "name": "Spanish; Castilian", "native": "español"},
    {"abbrev": "spa_old", "name": "Spanish; Castilian (old)", "native": ""},
    {"abbrev": "sqi", "name": "Albanian", "native": "Shqip"},
    {"abbrev": "srp", "name": "Serbian", "native": "српски језик"}, # noqa: RUF001
    {"abbrev": "srp_latn", "name": "Serbian (latin)", "native": "српски језик"}, # noqa: RUF001,E501
    {"abbrev": "sun", "name": "Sundanese", "native": "Basa Sunda"},
    {"abbrev": "swa", "name": "Swahili", "native": "Kiswahili"},
    {"abbrev": "swe", "name": "Swedish", "native": "svenska"},
    {"abbrev": "syr", "name": "Syriac", "native": "ܠܫܢܐ ܣܘܪܝܝܐ"},
    {"abbrev": "tam", "name": "Tamil", "native": "தமிழ்"},
    {"abbrev": "tat", "name": "Tatar", "native": "татар теле; tatar tele"}, # noqa: RUF001,E501
    {"abbrev": "tel", "name": "Telugu", "native": "తెలుగు"},
    {"abbrev": "tgk", "name": "Tajik", "native": "тоҷикӣ; toçikī; تاجیکی\u200e"}, # noqa: RUF001,E501
    {"abbrev": "tgl", "name": "Tagalog", "native": "Wikang Tagalog"},
    {"abbrev": "tha", "name": "Thai", "native": "ไทย"},
    {"abbrev": "tir", "name": "Tigrinya", "native": "ትግርኛ"},
    {"abbrev": "ton", "name": "Tonga (Tonga Islands)", "native": "faka Tonga"},
    {"abbrev": "tur", "name": "Turkish", "native": "Türkçe"},
    {"abbrev": "uig", "name": "Uighur", "native": "ئۇيغۇرچە\u200e; Uyghurche"}, # noqa: RUF001,E501
    {"abbrev": "ukr", "name": "Ukrainian", "native": "Українська"}, # noqa: RUF001
    {"abbrev": "urd", "name": "Urdu", "native": "اردو"}, # noqa: RUF001
    {"abbrev": "uzb", "name": "Uzbek", "native": "أۇزبېك\u200e"},
    {"abbrev": "uzb_cyrl", "name": "Uzbek (cyrillic)", "native": "Ўзбек"}, # noqa: RUF001,E501
    {"abbrev": "vie", "name": "Vietnamese", "native": "Tiếng Việt"},
    {"abbrev": "yid", "name": "Yiddish", "native": "ייִדיש"}, # noqa: RUF001
    {"abbrev": "yor", "name": "Yoruba", "native": "Yorùbá"},
]
# fmt: on
