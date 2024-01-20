from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.screengrab import post_processing


def test_split_full_desktop_to_screens(monkeypatch):
    class MockedPrimaryScreen:
        def virtualGeometry(self) -> QtCore.QRect:  # noqa: N802
            return QtCore.QRect(0, 0, 300, 120)

    class MockedScreen:
        def __init__(self, left, top, width, height):
            self._geometry = QtCore.QRect(left, top, width, height)

        def geometry(self):
            return self._geometry

    def mocked_screens() -> list:
        return [
            MockedScreen(0, 0, 100, 100),
            MockedScreen(100, 10, 100, 100),
            MockedScreen(200, 20, 100, 100),
        ]

    def convert_to_pixels(image):
        image = image.convertToFormat(QtGui.QImage.Format.Format_RGB32)
        ptr = image.constBits()
        values = list(ptr)
        return [tuple(values[i : i + 4]) for i in range(0, len(values), 4)]

    monkeypatch.setattr(QtWidgets.QApplication, "primaryScreen", MockedPrimaryScreen)
    monkeypatch.setattr(QtWidgets.QApplication, "screens", mocked_screens)

    img_path = Path(__file__).parent / "split_full_desktop_to_screens.png"
    image = QtGui.QImage()
    image.load(str(img_path.resolve()))
    split_images = post_processing.split_full_desktop_to_screens(image)

    assert len(split_images) == len(mocked_screens())
    assert {split_images[i].size().toTuple() for i in range(3)} == {(100, 100)}

    assert set(convert_to_pixels(split_images[0])) == {(0, 0, 255, 255)}
    assert set(convert_to_pixels(split_images[1])) == {(0, 255, 0, 255)}
    assert set(convert_to_pixels(split_images[2])) == {(255, 0, 0, 255)}
