from normcap.gui import constants


def test_languages_dimensions():
    language_dims = {len(lang) for lang in constants.LANGUAGES}
    assert len(constants.LANGUAGES) > 120
    assert language_dims == {4}
