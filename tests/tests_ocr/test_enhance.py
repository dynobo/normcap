from collections import Counter
from pathlib import Path

from PySide6 import QtCore, QtGui

from normcap.ocr import enhance


def test_identify_most_frequent_edge_color():
    image = QtGui.QImage(Path(__file__).parent / "testimages" / "color.png")
    color = enhance._identify_most_frequent_edge_color(image)
    assert color == (0, 0, 255)


def test_identify_most_frequent_edge_color_small_image():
    # GIVEN an image with small dimensions (border < max_sample_size)
    image = QtGui.QImage(Path(__file__).parent / "testimages" / "color.png")
    image = image.scaled(QtCore.QSize(40, 40))
    # WHEN the most frequent color is identified
    color = enhance._identify_most_frequent_edge_color(image)
    # THEN the result should be correct (blue)
    assert color == (0, 0, 255)


def test_add_padding():
    padding = 33
    img = QtGui.QImage(Path(__file__).parent / "testimages" / "color.png")
    img_pad = enhance.add_padding(img, padding=padding)
    assert img.width() == img_pad.width() - padding * 2
    assert img.height() == img_pad.height() - padding * 2

    points = [(x, 0) for x in range(img_pad.width())]  # top
    points += [(x, img_pad.height() - 1) for x in range(img_pad.width())]  # bottom
    points += [(0, x) for x in range(img_pad.height())]  # left
    points += [(img_pad.width() - 1, x) for x in range(img_pad.height())]  # right

    edge_pixels = enhance._get_pixels(image=img_pad, points=points)
    color_count = Counter(edge_pixels)
    assert set(color_count.keys()) == {(0, 0, 255)}


def test_resize_image():
    factor = 2.5
    img = QtGui.QImage(Path(__file__).parent / "testimages" / "color.png")
    img_result = enhance.resize_image(img.copy(), factor=factor)
    assert img.width() * factor == img_result.width()
    assert img.height() * factor == img_result.height()


def test_preprocess():
    img = QtGui.QImage(Path(__file__).parent / "testimages" / "dark.png")
    factor = 2
    padding = 10
    img_result = enhance.preprocess(img.copy(), resize_factor=factor, padding=padding)
    assert img.width() * factor + padding * 2 == img_result.width()
    assert enhance._get_pixels(image=img_result, points=[(0, 0)])[0] == (0, 0, 0)
    assert enhance._get_pixels(image=img_result, points=[(99, 49)])[0] == (0, 0, 0)
