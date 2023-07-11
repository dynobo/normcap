from PySide6 import QtGui, QtWidgets


def test_enable_language_manager(qtbot, menu_btn):
    menu_btn.menu().aboutToShow.emit()

    language_action = menu_btn.findChild(QtGui.QAction, "manage_languages")
    assert "add/remove" in language_action.text()

    with qtbot.wait_signal(menu_btn.com.on_manage_languages, timeout=5000) as result:
        language_action.trigger()
    assert result.signal_triggered


def test_disable_language_manager(monkeypatch, menu_btn_without_lang_man):
    menu_btn = menu_btn_without_lang_man
    messages_shown = []

    def _mocked_show_message_box(text):
        messages_shown.append(text)

    monkeypatch.setattr(menu_btn, "_show_message_box", _mocked_show_message_box)
    menu_btn.menu().aboutToShow.emit()

    language_action = menu_btn.findChild(QtGui.QAction, "show_help_languages")
    assert "need more" in language_action.text()

    language_action.trigger()
    assert "you are not using the prebuilt" in messages_shown[0].lower()


def test_languages_section_does_overflow(qtbot, menu_btn):
    threshold = 8
    # Test does _not_ overflow below threshold
    menu_btn.on_languages_changed([str(i) for i in range(threshold - 1)])
    menu_btn.menu().aboutToShow.emit()

    select_menu = menu_btn.findChild(QtWidgets.QMenu, "language_menu")
    assert not select_menu

    language_group = menu_btn.findChild(QtGui.QActionGroup, "language_group")
    assert len(language_group.children()) == threshold - 1

    # Test _does_ overflow on threshold
    menu_btn.on_languages_changed([str(i) for i in range(threshold)])
    menu_btn.menu().aboutToShow.emit()

    select_menu = menu_btn.findChild(QtWidgets.QMenu, "language_menu")
    assert select_menu

    language_group = select_menu.findChild(QtGui.QActionGroup, "language_group")
    assert len(language_group.children()) == threshold


def test_close_triggered(qtbot, menu_btn):
    menu_btn.menu().aboutToShow.emit()

    action = menu_btn.findChild(QtGui.QAction, "close")
    with qtbot.wait_signal(menu_btn.com.on_close_in_settings, timeout=1000):
        action.trigger()


def test_open_url_triggered(qtbot, menu_btn):
    menu_btn.menu().aboutToShow.emit()

    action_group = menu_btn.findChild(QtGui.QActionGroup, "website_group")
    for action in action_group.children():
        if not action.isEnabled():
            continue
        with qtbot.wait_signal(menu_btn.com.on_open_url, timeout=1000):
            action.trigger()


def test_language_group(menu_btn):
    langs = ["afr", "deu", "eng"]
    menu_btn.on_languages_changed(langs)
    menu_btn.menu().aboutToShow.emit()

    # enabling all
    settings_group = menu_btn.findChild(QtGui.QActionGroup, "language_group")
    for action in settings_group.children():
        action.trigger()

    assert menu_btn.settings.value("language") == langs

    # disabling all should last one be enabled
    for action in settings_group.children():
        action.trigger()

    assert menu_btn.settings.value("language") == [langs[-1]]


def test_mode_group(menu_btn):
    menu_btn.menu().aboutToShow.emit()

    settings_group = menu_btn.findChild(QtGui.QActionGroup, "mode_group")
    for action in settings_group.children():
        action.trigger()
        assert menu_btn.settings.value("mode") == action.objectName()


def test_settings_group(menu_btn):
    menu_btn.menu().aboutToShow.emit()

    settings_group = menu_btn.findChild(QtGui.QActionGroup, "settings_group")
    for action in settings_group.children():
        action.trigger()
        setting_value = menu_btn.settings.value(action.objectName())
        assert str(setting_value).lower() == str(action.isChecked()).lower()
