from packaging.version import Version as PackagingVersion

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


def test_version_packaging_compatibility():
    assert Version("0.9.8") < PackagingVersion("1.0.0")
    assert Version("1.0.8") > PackagingVersion("1.0.0")
    assert Version("1.0.0") >= PackagingVersion("1.0.0")
    assert Version("1.0.0") <= PackagingVersion("1.0.0")
    assert Version("1.0.0") == PackagingVersion("1.0.0")
    assert Version("1.0.0beta1") < PackagingVersion("1.0.0")
    assert Version("1.0.0beta1") < PackagingVersion("1.0.0beta2")
    assert Version("1.0.0beta1") == PackagingVersion("1.0.00beta1")
