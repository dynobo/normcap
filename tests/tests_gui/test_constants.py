from normcap.gui import constants


def test_languages_dimensions():
    for lang in constants.LANGUAGES:
        assert len(lang) == 4
