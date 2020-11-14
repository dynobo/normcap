TEST_IMAGES = [
    {
        "test_id": "T_001",
        "explanation": "Check if email addresses are correctely recognized and returned",
        "filename": "test_email_magic_1_unscaled.jpg",
        "expected_result": "peter.parker@test.com, HArDToReAd@test.com, 0815@test.com",
        "expected_similarity": 1,
        "expected_magic": "email",
        "position": {"left": 20, "right": 440, "top": 277, "bottom": 320},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_002",
        "explanation": "Check if 'fake' addresses are correctely recognized as normal text",
        "filename": "test_email_magic_1.jpg",
        "expected_result": "To: Peter Parker <peter parker@test.com>, HArD To ReAd <HArDToReAd@test.com>; 0815 <0815@test.com>; Invalid_one <notvalid@test>; Invalid_two <also/not/valid/@test.com>; Invalid_three <@test.com> Subject: OCR testing image",
        "expected_similarity": 0.75,
        "expected_magic": "paragraph",
        "position": {"left": 388, "right": 1000, "top": 464, "bottom": 540},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_003",
        "explanation": "Numbers and punctuation",
        "filename": "test_email_magic_1.jpg",
        "expected_result": "Sent: Tuesday, September 2, 2019 1:38 AM",
        "expected_similarity": 1,
        "expected_magic": "single_line",
        "position": {"left": 388, "right": 750, "top": 446, "bottom": 465},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_004",
        "explanation": "Normal text",
        "filename": "test_email_magic_1_unscaled.jpg",
        "expected_result": "screenshot content",
        "expected_similarity": 1,
        "expected_magic": "single_line",
        "position": {"left": 272, "right": 376, "top": 11, "bottom": 37},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_005",
        "explanation": "Single word, blue, with blue underline",
        "filename": "test_email_magic_1_unscaled.jpg",
        "expected_result": "dynobo@mailbox.org",
        "expected_similarity": 1,
        "expected_magic": "email",
        "position": {"left": 150, "right": 281, "top": 92, "bottom": 106},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_006",
        "explanation": "Single word with red underline",
        "filename": "test_email_magic_1_unscaled.jpg",
        "expected_result": "Dynobo",
        "expected_similarity": 1,
        "expected_magic": "single_line",
        "position": {"left": 74, "right": 160, "top": 235, "bottom": 258},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_007",
        "explanation": "Text and linebreaks",
        "filename": "test_paragraph_magic_1_unscaled.jpg",
        "expected_result": (
            "If in 1959 Derrida was addressing this question of genesis and structure to Husserl,"
            ' that is, to phenomenology, then in "Structure, Sign, and Play in the Discourse of'
            ' the Human Sciences" (also in Writing and Difference; see below), he addresses these'
            " same questions to Lévi-Strauss and the structuralists. This is clear from the very first"
            " line of the paper (p. 278):"
            ""
            "Perhaps something has occurred in the history of the concept of structure that could be"
            ' called an "event," if this loaded word did not entail a meaning which it is precisely'
            " the function of structural—or structuralist—thought to reduce or to suspect. "
            ""
            "Between these two papers is staked Derrida's philosophical ground, if not indeed his"
            " step beyond or outside philosophy."
        ),
        "expected_similarity": 0.85,
        "expected_magic": "paragraph",
        "expected_doublelinebreaks": 2,  # Paragraph = Double line break
        "position": {"left": 210, "right": 920, "top": 330, "bottom": 550},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_008",
        "explanation": "Headline, Text and linebreaks",
        "filename": "test_paragraph_magic_2_unscaled.jpg",
        "expected_result": (
            "C++ is not a safe language. It will cheerfully allow you to break the"
            " rules of the system. If you try to do something illegal and foolish"
            " like going back into a room you're not authorized to be in and rummaging"
            " through a desk that might not even be there anymore, C++ is not going"
            " to stop you. Safer languages than C++ solve this problem by restricting"
            " your power -- by having much stricter control over keys, for example."
            ""
            "UPDATE"
            ""
            "Holy goodness, this answer is getting a lot of attention. (I'm not sure why"
            ' -- I considered it to be just a "fun" little analogy, but whatever.)'
        ),
        "expected_similarity": 0.85,
        "expected_magic": "paragraph",
        "expected_doublelinebreaks": 2,  # Paragraph = Double line break
        "position": {"left": 220, "right": 930, "top": 750, "bottom": 950},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_009",
        "explanation": "Detect sans serif URL between unknown symbols",
        "filename": "test_url_magic_1_unscaled.jpg",
        "expected_result": "https://github.com/dynobo/normcap",
        "expected_similarity": 1,
        "expected_magic": "url",
        "position": {"left": 200, "right": 700, "top": 26, "bottom": 60},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_010",
        "explanation": "Detect mono space URL and correct misdetected whitespace",
        "filename": "test_url_magic_1_unscaled.jpg",
        "expected_result": "https://github.com/dynobo/normcap.git",
        "expected_similarity": 1,
        "expected_magic": "url",
        "position": {"left": 180, "right": 530, "top": 290, "bottom": 310},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
    {
        "test_id": "T_011",
        "explanation": "4 URLs, 2 with missing prefix currently ignored",
        "filename": "test_url_magic_2_unscaled.jpg",
        "expected_result": (
            "https://github.com/dynobo/normcap"
            " www.python.com"
            " https://en.wikipedia.org/wiki/Tesseract"
        ),
        "expected_similarity": 1,
        "expected_magic": "url",
        "position": {"left": 6, "right": 400, "top": 220, "bottom": 400},
        "cli_args": {
            "lang": "eng",
            "mode": "parse",
            "verbose": True,
            "path": None,
            "tray": None,
        },
    },
]
