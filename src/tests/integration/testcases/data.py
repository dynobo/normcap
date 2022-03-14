TESTCASES = [
    {
        "image": "ocr_test_1.png",
        "tl": (46, 745),
        "br": (500, 950),
        "transformed": "\n".join(
            [
                "https://github.com/dynobo/normcap",
                "https://wikipedia.de",
                "https://www.python.com",
                "https://en.wikipedia.org/wiki/Tesseract",
                "https://pypi.org/project/lmdiag/",
            ]
        ),
        "ocr_applied_magic": "UrlMagic",
    },
    {
        "image": "ocr_test_1.png",
        "tl": (312, 550),
        "br": (470, 572),
        "transformed": "https://regex101.com",
        "ocr_applied_magic": "UrlMagic",
    },
]
