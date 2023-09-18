from difflib import SequenceMatcher

import pytest
from PySide6 import QtGui

from normcap import ocr
from normcap.gui import system_info

from .testcases import testcases


@pytest.mark.parametrize("testcase", testcases)
def test_remove_spaces_in_chi(testcase):
    image = QtGui.QImage(testcase.image_path)
    result = ocr.recognize.get_text_from_image(
        tesseract_cmd=system_info.get_tesseract_path(),
        image=image,
        languages=testcase.lang.split(","),
    )

    similarity = SequenceMatcher(None, result.parsed, testcase.transformed).ratio()

    is_equal = 1
    assert pytest.approx(similarity, abs=0.1) == is_equal, (
        result.parsed,
        testcase.transformed,
    )
