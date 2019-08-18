from normcap import __version__, normcap


def test_version():
    assert __version__ == "0.1.0"


def test_normcap():
    assert normcap.Capture() is not None
