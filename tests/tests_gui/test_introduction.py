import pytest
from PySide6 import QtCore

from normcap.gui import introduction


@pytest.mark.parametrize("show_on_startup", [True, False])
def test_introduction_initialize_checkbox_state(show_on_startup):
    # GIVEN the introduction dialog
    # WHEN the dialog is instantiated with a certain argument
    dialog = introduction.IntroductionDialog(show_on_startup=show_on_startup)

    # THEN the checkbox should be set accordingly
    assert dialog.show_on_startup_checkbox.isChecked() is show_on_startup


@pytest.mark.gui()
@pytest.mark.parametrize(
    ("show_on_startup", "expected_return_code"),
    [(True, introduction.Choice.SHOW), (False, introduction.Choice.DONT_SHOW)],
)
def test_introduction_checkbox_sets_return_code(
    qtbot, show_on_startup, expected_return_code
):
    # GIVEN the dialog is initialized with a certain argument value
    dialog = introduction.IntroductionDialog(show_on_startup=show_on_startup)
    qtbot.addWidget(dialog)

    # WHEN the dialog is shown and the close button is clicked
    def close_dialog():
        while not dialog.isVisible():
            ...
        dialog.ok_button.click()

    QtCore.QTimer.singleShot(0, close_dialog)
    return_code = dialog.exec()

    # THEN the return code should be set accordingly
    assert return_code == expected_return_code


@pytest.mark.gui()
@pytest.mark.parametrize(
    ("show_on_startup", "expected_return_code"),
    [(False, introduction.Choice.SHOW), (True, introduction.Choice.DONT_SHOW)],
)
def test_introduction_toggle_checkbox_changes_return_code(
    qtbot, show_on_startup, expected_return_code
):
    # GIVEN the dialog is initialized with a certain argument value
    dialog = introduction.IntroductionDialog(show_on_startup=show_on_startup)
    qtbot.addWidget(dialog)

    # WHEN the dialog is shown and the close button is clicked
    def close_dialog():
        while not dialog.isVisible():
            ...
        dialog.show_on_startup_checkbox.click()
        dialog.ok_button.click()

    QtCore.QTimer.singleShot(0, close_dialog)
    return_code = dialog.exec()

    # THEN the return code should be set accordingly
    assert return_code == expected_return_code
