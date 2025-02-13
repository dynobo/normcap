import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OcrTestCase:
    lang: str
    image_path: Path
    transformed: str


image_dir = Path(__file__).parent

testcases = [
    OcrTestCase(
        lang="eng",
        image_path=image_dir / "00_eng.png",
        transformed="Nothing is worse than having an itch you can never scratch!",
    ),
    OcrTestCase(
        lang="chi_sim",
        image_path=image_dir / "01_chi_sim.png",
        transformed="没有什么比瘙痒更糟糕的了,你永远不会抓挠!",
    ),
    OcrTestCase(
        lang="jpn",
        image_path=image_dir / "02_jpn.png",
        transformed=f"痒いところに手が届かないなんて、最悪{os.linesep}ですよね。",
    ),
]
