import subprocess
import sys
import uuid

import pytest

from normcap.clipboard.handlers import pbcopy


@pytest.mark.parametrize(
    ("platform", "result"),
    [
        ("darwin", True),
        ("win32", False),
        ("linux", False),
    ],
)
def test_pbcopy_is_compatible(monkeypatch, platform, result):
    monkeypatch.setattr(pbcopy.sys, "platform", platform)
    assert pbcopy.PbCopyHandler().is_compatible() == result


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_pbcopy_copy():
    text = f"this is a unique test {uuid.uuid4()}"
    result = pbcopy.PbCopyHandler().copy(text=text)

    with subprocess.Popen(
        ["pbpaste", "r"],  # noqa: S603, S607
        stdout=subprocess.PIPE,
    ) as p:
        stdout = p.communicate()[0]
    clipped = stdout.decode("utf-8")

    assert result is True
    assert text == clipped


@pytest.mark.skipif(sys.platform == "darwin", reason="Non-macOS specific test")
def test_pbcopy_copy_on_non_darwin():
    result = pbcopy.PbCopyHandler().copy(text="this is a test")
    assert result is False
