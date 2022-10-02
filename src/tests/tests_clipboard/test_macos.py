from normcap import clipboard


def test_get_copy_func_with_pbcopy(monkeypatch):
    monkeypatch.setattr(clipboard.linux.shutil, "which", lambda *args: True)
    get_copy = clipboard.macos.get_copy_func()
    assert get_copy == clipboard.macos.pbcopy


def test_get_copy_func_without_pbcopy(monkeypatch):
    monkeypatch.setattr(clipboard.linux.shutil, "which", lambda *args: None)
    get_copy = clipboard.macos.get_copy_func()
    assert get_copy == clipboard.qt.copy
