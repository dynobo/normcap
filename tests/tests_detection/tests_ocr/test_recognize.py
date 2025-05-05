from difflib import SequenceMatcher

import pytest
from PySide6 import QtGui

from normcap.detection import ocr

from .testcases import testcases


@pytest.mark.parametrize("testcase", testcases)
def test_remove_spaces_in_chi(testcase, tesseract_cmd):
    image = QtGui.QImage(testcase.image_path)
    result = ocr.recognize.get_text_from_image(
        tesseract_bin_path=tesseract_cmd,
        image=image,
        languages=testcase.lang.split(","),
    )

    similarity = SequenceMatcher(None, result.text, testcase.transformed).ratio()

    is_equal = 1
    assert pytest.approx(similarity, abs=0.1) == is_equal, (
        result.text,
        testcase.transformed,
    )
