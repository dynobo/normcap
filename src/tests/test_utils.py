from normcap import utils


def test_init_tessdata(tmp_path, monkeypatch):
    """Check if copying traineddata files works."""
    monkeypatch.setattr(utils.system_info, "config_directory", lambda: tmp_path)
    tessdata_path = tmp_path / "tessdata"

    traineddatas = list(tessdata_path.glob("*.traineddata"))
    txts = list(tessdata_path.glob("*.txt"))
    assert not traineddatas
    assert not txts

    for _ in range(3):
        utils.init_tessdata()

        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert traineddatas
        assert len(txts) == 1
