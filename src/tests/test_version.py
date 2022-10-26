from normcap.version import Version


def test_version():
    assert (
        Version("9")
        > Version("8.9.1")
        > Version("8.9")
        > Version("8.8.9")
        > Version("8.8.9beta2")
        > Version("8.8.9beta1")
    )
