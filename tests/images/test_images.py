TEST_IMAGES = [
    {
        "explanation": "Check if email addresses are correctely recognized and returned",
        "filename": "test_email_magic_1.jpg",
        "expected_result": "parker@test.com, HArDToReAd@test.com, 0815@test.com",
        "expected_similarity": 1,
        "expected_magic": "email",
        "position": {"left": 388, "right": 777, "top": 464, "bottom": 500},
        "cli_args": {"lang": "eng", "mode": "parse", "verbose": True, "path": None},
    },
    {
        "explanation": "Check if 'fake' addresses are correctely recognized as normal text",
        "filename": "test_email_magic_1.jpg",
        "expected_result": "To: Peter Parker <peter parker@test.com>, HArD To ReAd <HArDToReAd@test.com>; 0815 <0815@test.com>; Invalid_one <notvalid@test>; Invalid_two <also/not/valid/@test.com>; Invalid_three <@test.com> Subject: OCR testing image",
        "expected_similarity": 0.75,
        "expected_magic": "paragraph",
        "position": {"left": 388, "right": 1000, "top": 464, "bottom": 540},
        "cli_args": {"lang": "eng", "mode": "parse", "verbose": True, "path": None},
    },
    {
        "explanation": "Numbers and punctuation",
        "filename": "test_email_magic_1.jpg",
        "expected_result": "Sent: Tuesday, September 2, 2019 1:38 AM",
        "expected_similarity": 1,
        "expected_magic": "single_line",
        "position": {"left": 388, "right": 750, "top": 446, "bottom": 465},
        "cli_args": {"lang": "eng", "mode": "parse", "verbose": True, "path": None},
    },
    {
        "explanation": "Normal text",
        "filename": "test_email_magic_1_unscaled.jpg",
        "expected_result": "screenshot content",
        "expected_similarity": 1,
        "expected_magic": "single_line",
        "position": {"left": 272, "right": 376, "top": 11, "bottom": 37},
        "cli_args": {"lang": "eng", "mode": "parse", "verbose": True, "path": None},
    },
    {
        "explanation": "Single word, blue, with blue underline",
        "filename": "test_email_magic_1_unscaled.jpg",
        "expected_result": "dynobo@mailbox.org",
        "expected_similarity": 1,
        "expected_magic": "email",
        "position": {"left": 150, "right": 281, "top": 92, "bottom": 106},
        "cli_args": {"lang": "eng", "mode": "parse", "verbose": True, "path": None},
    },
    {
        "explanation": "Single word with red underline",
        "filename": "test_email_magic_1_unscaled.jpg",
        "expected_result": "Dynobo",
        "expected_similarity": 1,
        "expected_magic": "single_line",
        "position": {"left": 74, "right": 160, "top": 235, "bottom": 258},
        "cli_args": {"lang": "eng", "mode": "parse", "verbose": True, "path": None},
    },
    {
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
        "expected_similarity": 0.90,
        "expected_magic": "paragraph",
        "expected_doublelinebreaks": 2,  # Paragraph = Double line break
        "position": {"left": 210, "right": 920, "top": 330, "bottom": 550},
        "cli_args": {"lang": "eng", "mode": "parse", "verbose": True, "path": None},
    },
    {
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
        "cli_args": {"lang": "eng", "mode": "parse", "verbose": True, "path": None},
    },
]
