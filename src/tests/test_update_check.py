import pytest

from normcap.qt.update_check import UpdateChecker

# Allow pytest fixtures:
# pylint: disable=redefined-outer-name,protected-access


@pytest.mark.parametrize("packaged", [True, False])
def test_update_checker(qtbot, packaged):
    """Retrieve version information from github."""

    checker = UpdateChecker(None, packaged=packaged)

    with qtbot.waitSignal(checker.com.on_version_retrieved) as result:
        checker.check()
    version = result.args[0]

    assert isinstance(version, str)
    assert len(version) >= 5
    assert version[0].isdigit()
    assert version.count(".") == 2


@pytest.mark.parametrize(
    "packaged,text",
    [(True, "abc"), (False, '{"no relevant":"info"}'), (False, '{"invalid":"json"')],
)
def test_update_checker_cant_parse(caplog, packaged, text):
    """Retrieve version information from github."""

    checker = UpdateChecker(None, packaged=packaged)

    version = checker._parse_response(text)

    assert version == ""
    assert "ERROR" in caplog.text
