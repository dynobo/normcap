import PySide6
import pytest

from normcap.screengrab import _is_pyside6_64plus


@pytest.mark.parametrize("version,result", (("6.2.1", False), ("6.4.2", True)))
def test_is_pyside6_64plus(monkeypatch, version, result):
    monkeypatch.setattr(PySide6, "__version__", version)
    assert _is_pyside6_64plus() is result
