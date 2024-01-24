import os

from normcap.ocr.structures import OEM, PSM, TessArgs


def test_ocr_result(ocr_result):
    """Check if calculated properties are working correctly."""
    assert ocr_result.text == f"one{os.linesep}two{os.linesep * 2}three"

    assert ocr_result.num_chars == 11
    assert ocr_result.num_blocks == 2
    assert ocr_result.num_pars == 3
    assert ocr_result.num_lines == 2

    assert ocr_result.mean_conf == 30
    ocr_result.words = []
    assert ocr_result.mean_conf == 0

    assert ocr_result.best_scored_transformer is None
    ocr_result.transformer_scores = {"email": 1.0, "url": 0.7, "paragraph": 0}
    assert ocr_result.best_scored_transformer == "email"


def test_tess_args_jpn():
    tess_args = TessArgs(
        tessdata_path="./tessdata", lang="jpn", oem=OEM.DEFAULT, psm=PSM.COUNT
    )
    args = " ".join(tess_args.as_list())
    assert "--tessdata-dir ./tessdata" in args
    assert "-c preserve_interword_spaces=1" in args
    assert "--oem 3" in args
    assert "--psm 14" in args
    assert tess_args.is_language_without_spaces()


def test_tess_args_eng():
    tess_args = TessArgs(tessdata_path=None, lang="eng", oem=OEM.DEFAULT, psm=PSM.COUNT)
    args = " ".join(tess_args.as_list())
    assert "--oem 3" in args
    assert "--psm 14" in args
    assert "--tessdata-dir" not in args
    assert "-c preserve_interword_spaces=1" not in args
    assert not tess_args.is_language_without_spaces()
