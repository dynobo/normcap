import sys
from pathlib import Path

import Levenshtein
import pytest
from normcap import ocr
from PIL import Image

from .testcases.data import TESTCASES


@pytest.mark.parametrize("data", TESTCASES)
def test_remove_spaces_in_chi(data):
    if sys.platform == "win32":
        pytest.xfail("Default windows installer misses required languages.")

    image = Image.open(Path(__file__).parent / "testcases" / data["image"])
    result = ocr.recognize(image=image, languages=data["lang"].split(","))

    similarity = Levenshtein.ratio(result.transformed, data["transformed"])
    assert similarity >= 0.90, (result.transformed, data["transformed"])
