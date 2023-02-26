from collections import Counter
from pathlib import Path

import pytest
from PIL import Image

from normcap.ocr import enhance


def test_identify_most_frequent_edge_color():
    image = Image.open(Path(__file__).parent / "testimages" / "color.png")
    color = enhance._identify_most_frequent_edge_color(image)
    assert color == (0, 0, 255)


def test_add_padding():
    padding = 33
    img = Image.open(Path(__file__).parent / "testimages" / "color.png")
    img_pad = enhance.add_padding(img, padding=padding)
    assert img.width == img_pad.width - padding * 2
    assert img.height == img_pad.height - padding * 2

    # Top and bottom edge
    colors = [img_pad.getpixel((x, 0)) for x in range(img_pad.width)]
    colors += [img_pad.getpixel((x, img_pad.height - 1)) for x in range(img_pad.width)]

    # Left and right edge
    colors += [img_pad.getpixel((0, y)) for y in range(img_pad.height)]
    colors += [img_pad.getpixel((img_pad.width - 1, y)) for y in range(img_pad.height)]

    color_count = Counter(colors)
    assert set(color_count.keys()) == {(0, 0, 255)}


def test_resize_image():
    factor = 2.5
    img = Image.open(Path(__file__).parent / "testimages" / "color.png")
    img_result = enhance.resize_image(img, factor=factor)
    assert img.width * factor == img_result.width
    assert img.height * factor == img_result.height


@pytest.mark.parametrize("pixel", ((0, 0), (99, 99)))
def test_invert_image(pixel):
    img = Image.open(Path(__file__).parent / "testimages" / "color.png")
    img_result = enhance.invert_image(img)

    pixel_values = zip(img.getpixel(pixel), img_result.getpixel(pixel))
    pixel_wise_sum = list(map(sum, pixel_values))
    assert pixel_wise_sum == [255, 255, 255]


def test_is_dark():
    img = Image.open(Path(__file__).parent / "testimages" / "dark.png")
    assert enhance.is_dark(img)
    img = Image.open(Path(__file__).parent / "testimages" / "light.png")
    assert not enhance.is_dark(img)


def test_preprocess():
    img = Image.open(Path(__file__).parent / "testimages" / "dark.png")
    factor = 2
    padding = 10
    img_result = enhance.preprocess(img, resize_factor=factor, padding=padding)
    assert img.width * factor + padding * 2 == img_result.width
    assert img_result.getpixel((0, 0)) == (255, 255, 255)
    assert img_result.getpixel((99, 49)) == (255, 255, 255)


def test_resize_select_resampling(monkeypatch):
    resamples = []

    def mocked_resize(size, resample):
        resamples.append(resample)
        return True

    img = Image.open(Path(__file__).parent / "testimages" / "dark.png")
    monkeypatch.setattr(img, "resize", mocked_resize)

    class MockedEnum:
        LANCZOS = 0
        LANCZOS_OLD = 1

    # New resampling enum
    monkeypatch.setattr(enhance.Image, "Resampling", MockedEnum)
    img_result = enhance.resize_image(img, factor=2)
    assert img_result is True
    assert resamples[0] == MockedEnum.LANCZOS

    # Old resampling enum
    monkeypatch.delattr(enhance.Image, "Resampling")
    monkeypatch.setattr(enhance.Image, "LANCZOS", MockedEnum.LANCZOS_OLD)
    img_result = enhance.resize_image(img, factor=2)
    assert img_result is True
    assert resamples[1] == MockedEnum.LANCZOS_OLD
