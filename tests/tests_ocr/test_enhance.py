from collections import Counter
from pathlib import Path

import pytest
from PySide6 import QtGui

from normcap.ocr import enhance


def test_identify_most_frequent_edge_color():
    image = QtGui.QImage(Path(__file__).parent / "testimages" / "color.png")
    color = enhance._identify_most_frequent_edge_color(image)
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


@pytest.mark.parametrize("pixel", [(0, 0), (99, 99)])
def test_invert_image(pixel):
    img = QtGui.QImage(Path(__file__).parent / "testimages" / "color.png")
    img_result = enhance.invert_image(img.copy())

    points = [(x, y) for x in range(img.width()) for y in range(img.height())]
    img_orig_pixels = enhance._get_pixels(img, points=points)
    img_result_pixels = enhance._get_pixels(img_result, points=points)

    pixel_pairs = list(zip(img_orig_pixels, img_result_pixels))
    pixel_wise_sum = [list(map(sum, zip(*p))) for p in pixel_pairs]
    assert all(s == [255, 255, 255] for s in pixel_wise_sum)


def test_is_dark():
    img = QtGui.QImage(Path(__file__).parent / "testimages" / "dark.png")
    assert enhance.is_dark(img)
    img = QtGui.QImage(Path(__file__).parent / "testimages" / "light.png")
    assert not enhance.is_dark(img)


def test_preprocess():
    img = QtGui.QImage(Path(__file__).parent / "testimages" / "dark.png")
    factor = 2
    padding = 10
    img_result = enhance.preprocess(img.copy(), resize_factor=factor, padding=padding)
    assert img.width() * factor + padding * 2 == img_result.width()
    assert enhance._get_pixels(image=img_result, points=[(0, 0)])[0] == (255, 255, 255)
    assert enhance._get_pixels(image=img_result, points=[(99, 49)])[0] == (
        255,
        255,
        255,
    )
