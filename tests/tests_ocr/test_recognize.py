import sys
from difflib import SequenceMatcher
from pathlib import Path

import pytest
from PySide6 import QtGui

from normcap import ocr
from normcap.gui import system_info

from .testcases.data import TESTCASES


@pytest.mark.parametrize("data", TESTCASES)
def test_remove_spaces_in_chi(data):
    if sys.platform == "win32":
        pytest.xfail("Default windows installer misses required languages.")

    image = QtGui.QImage(Path(__file__).parent / "testcases" / data["image"])
    result = ocr.recognize(
        tesseract_cmd=system_info.get_tesseract_path(),
        image=image,
        languages=data["lang"].split(","),
    )

    similarity = SequenceMatcher(None, result.parsed, data["transformed"]).ratio()

    is_equal = 1
    assert pytest.approx(similarity, abs=0.1) == is_equal, (
        result.parsed,
        data["transformed"],
    )
