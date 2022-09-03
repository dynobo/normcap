import os

TESTCASES = [
    {
        "id": 0,
        "lang": "eng",
        "image": "00_eng.png",
        "transformed": "Nothing is worse than having an itch you can never scratch!",
    },
    {
        "id": 1,
        "lang": "chi_sim",
        "image": "01_chi_sim.png",
        "transformed": "没有什么比瘙痒更糟糕的了,你永远不会抓挠!",
    },
    {
        "id": 2,
        "lang": "jpn",
        "image": "02_jpn.png",
        "transformed": f"痒いところに手が届かないなんて、最悪{os.linesep}ですよね。",
    },
]
