TESTCASES = [
    {
        "language": "eng",
        "image": "ocr_test.png",
        "tl": (46, 745),
        "br": (500, 950),
        "transformed": "\n".join(
            [
                "https://github.com/dynobo/normcap",
                "www.wikipedia.de",
                "www.python.com",
                "https://en.wikipedia.org/wiki/Tesseract",
            ]
        ),
    },
    {
        "language": "eng",
        "image": "ocr_test.png",
        "tl": (312, 550),
        "br": (470, 572),
        "transformed": "https://regex101.com",
    },
]
