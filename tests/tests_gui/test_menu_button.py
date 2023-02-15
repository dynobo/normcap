from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import menu_button


def test_menu_button_enable_language_manager(qtbot):
    settings = QtCore.QSettings()
    menu_btn = menu_button.MenuButton(settings=settings, language_manager=True)
    language_action = menu_btn.findChild(QtGui.QAction, "manage_languages")
    assert "add/remove" in language_action.text()

    with qtbot.wait_signal(menu_btn.com.on_manage_languages, timeout=5000) as result:
        language_action.trigger()
    assert result.signal_triggered


def test_menu_button_disable_language_manager(qtbot, monkeypatch):
    settings = QtCore.QSettings()
    menu_btn = menu_button.MenuButton(settings=settings, language_manager=False)
    language_action = menu_btn.findChild(QtGui.QAction, "show_help_languages")
    assert "need more" in language_action.text()

    mock_called = False

    def mocked_msg_exec():
        nonlocal mock_called
        mock_called = True

    monkeypatch.setattr(menu_btn.message_box, "exec_", mocked_msg_exec)
    language_action.trigger()
    assert mock_called


def test_languages_section_overflow(monkeypatch, qtbot):
    overflow_threshold = 8

    def mock_get_languages(count):
        return [str(i) for i in range(count)]

    # Test does _not_ overflow below threshold
    monkeypatch.setattr(
        menu_button.ocr.utils,
        "get_tesseract_languages",
        lambda **kwargs: mock_get_languages(overflow_threshold - 1),
    )

    settings = QtCore.QSettings()
    menu_btn = menu_button.MenuButton(settings=settings, language_manager=False)
    select_menu = menu_btn.findChild(QtWidgets.QMenu, "language_menu")
    assert not select_menu

    language_group = menu_btn.findChild(QtGui.QActionGroup, "language_group")
    assert language_group
    assert len(language_group.children()) == overflow_threshold - 1

    # Test does overflow on threshold
    monkeypatch.setattr(
        menu_button.ocr.utils,
        "get_tesseract_languages",
        lambda **kwargs: mock_get_languages(overflow_threshold),
    )

    menu_btn = menu_button.MenuButton(settings=settings, language_manager=False)
    select_menu = menu_btn.findChild(QtWidgets.QMenu, "language_menu")
    assert select_menu

    language_group = select_menu.findChild(QtGui.QActionGroup, "language_group")
    assert language_group
    assert len(language_group.children()) == overflow_threshold
