TESTCASES = (
    {
        "id": 0,
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
        "id": 1,
        "image": "ocr_test_1.png",
        "tl": (312, 550),
        "br": (470, 572),
        "transformed": "https://regex101.com",
        "ocr_applied_magic": "UrlMagic",
    },
    {
        "id": 2,
        "image": "ocr_test_1.png",
        "tl": (1115, 530),
        "br": (1305, 570),
        "transformed": "*Untitled Document 1",
        "ocr_applied_magic": "SingleLineMagic",
    },
    {
        # First two rows of email addresses
        "id": 3,
        "image": "ocr_test_1.png",
        "tl": (50, 300),
        "br": (700, 342),
        "transformed": "peter_parker@test.com, HArDToReAd@test.com, 0815@test.com",
        "ocr_applied_magic": "EmailMagic",
    },
    {
        # All three rows of email addresses, 3rd row contains invalids
        "id": 4,
        "image": "ocr_test_1.png",
        "tl": (50, 300),
        "br": (700, 363),
        "transformed": "To: Peter Parker <peter_parker@test.com>; HArD To ReAd\n"
        + "<HArDToReAd@test.com>; 0815 <0815@test.com>; Invalid_one <notvalid@test>;\n"
        + "Invalid_two <also/not/valid/@test.com>; Invalid_three <@test.com>",
        "ocr_applied_magic": "MultiLineMagic",
    },
    # {
    #     # Low contrast with white background
    #     "id": 5,
    #     "image": "ocr_test_1.png",
    #     "tl": (1055, 680),
    #     "br": (1610, 830),
    #     "transformed": "Orange, the new black!",
    #     "ocr_applied_magic": "SingleLineMagic",
    # },
)
