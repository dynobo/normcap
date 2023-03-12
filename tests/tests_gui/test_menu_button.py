from PySide6 import QtGui, QtWidgets

from normcap.gui import menu_button


def test_enable_language_manager(qtbot, temp_settings):
    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=True)
    language_action = menu_btn.findChild(QtGui.QAction, "manage_languages")
    assert "add/remove" in language_action.text()

    with qtbot.wait_signal(menu_btn.com.on_manage_languages, timeout=5000) as result:
        language_action.trigger()
    assert result.signal_triggered


def test_disable_language_manager(qtbot, monkeypatch, temp_settings):
    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=False)
    language_action = menu_btn.findChild(QtGui.QAction, "show_help_languages")
    assert "need more" in language_action.text()

    mock_called = False

    def mocked_msg_exec():
        nonlocal mock_called
        mock_called = True

    monkeypatch.setattr(menu_btn.message_box, "exec_", mocked_msg_exec)
    language_action.trigger()
    assert mock_called


def test_languages_section_does_overflow(monkeypatch, qtbot, temp_settings):
    threshold = 8
    # Test does _not_ overflow below threshold
    monkeypatch.setattr(
        menu_button.ocr.tesseract,
        "get_languages",
        lambda **kwargs: [str(i) for i in range(threshold - 1)],
    )

    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=False)
    select_menu = menu_btn.findChild(QtWidgets.QMenu, "language_menu")
    assert not select_menu

    language_group = menu_btn.findChild(QtGui.QActionGroup, "language_group")
    assert len(language_group.children()) == threshold - 1

    # Test _does_ overflow on threshold
    monkeypatch.setattr(
        menu_button.ocr.tesseract,
        "get_languages",
        lambda **kwargs: [str(i) for i in range(threshold)],
    )

    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=False)
    select_menu = menu_btn.findChild(QtWidgets.QMenu, "language_menu")
    assert select_menu

    language_group = select_menu.findChild(QtGui.QActionGroup, "language_group")
    assert len(language_group.children()) == threshold


def test_close_triggered(qtbot, monkeypatch, temp_settings):
    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=False)

    action = menu_btn.findChild(QtGui.QAction, "close")
    with qtbot.wait_signal(menu_btn.com.on_close_in_settings, timeout=1000):
        action.trigger()


def test_open_url_triggered(qtbot, monkeypatch, temp_settings):
    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=False)

    action_group = menu_btn.findChild(QtGui.QActionGroup, "website_group")
    for action in action_group.children():
        if not action.isEnabled():
            continue
        with qtbot.wait_signal(menu_btn.com.on_open_url, timeout=1000):
            action.trigger()


def test_language_group(monkeypatch, qtbot, temp_settings):
    langs = ["afr", "deu", "eng"]
    monkeypatch.setattr(
        menu_button.ocr.tesseract, "get_languages", lambda **kwargs: langs
    )
    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=False)

    # enabling all
    settings_group = menu_btn.findChild(QtGui.QActionGroup, "language_group")
    for action in settings_group.children():
        action.trigger()

    assert temp_settings.value("language") == langs

    # disabling all should last one be enabled
    for action in settings_group.children():
        action.trigger()

    assert temp_settings.value("language") == [langs[-1]]


def test_mode_group(monkeypatch, qtbot, temp_settings):
    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=False)

    settings_group = menu_btn.findChild(QtGui.QActionGroup, "mode_group")
    for action in settings_group.children():
        action.trigger()
        assert temp_settings.value("mode") == action.objectName()


def test_settings_group(monkeypatch, qtbot, temp_settings):
    menu_btn = menu_button.MenuButton(settings=temp_settings, language_manager=False)

    settings_group = menu_btn.findChild(QtGui.QActionGroup, "settings_group")
    for action in settings_group.children():
        action.trigger()
        setting_value = temp_settings.value(action.objectName())
        assert str(setting_value).lower() == str(action.isChecked()).lower()
