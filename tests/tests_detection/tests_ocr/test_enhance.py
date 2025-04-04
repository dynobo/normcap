from pathlib import Path

import cv2
import numpy as np

from normcap.detection.ocr import enhance

TESTIMAGES_PATH = Path(__file__).parent / "testimages"


def test_identify_most_frequent_edge_color():
    image = cv2.imread(str((TESTIMAGES_PATH / "color.png").resolve()))
    color = enhance._identify_most_frequent_edge_color(image)
    assert color == [255, 0, 0]


def test_identify_most_frequent_edge_color_small_image():
    # GIVEN an image with small dimensions (border < max_sample_size)
    image = cv2.imread(str((TESTIMAGES_PATH / "color.png").resolve()))
    image = cv2.resize(src=image, dsize=(40, 40))
    # WHEN the most frequent color is identified
    color = enhance._identify_most_frequent_edge_color(image)
    # THEN the result should be correct (blue)
    assert color == [255, 0, 0]


def test_add_padding():
    padding = 33
    img = cv2.imread(str((TESTIMAGES_PATH / "color.png").resolve()))
    img_pad = enhance._add_padding(img, padding=padding)
    assert img.shape[0] == img_pad.shape[0] - padding * 2
    assert img.shape[1] == img_pad.shape[1] - padding * 2
    assert img.shape[2] == img_pad.shape[2]

    top_edge = img_pad[0, :]
    bottom_edge = img_pad[-1, :]
    left_edge = img_pad[:, 0]
    right_edge = img_pad[:, -1]

    # Combine all edge pixels
    edge_pixels = np.concatenate((top_edge, bottom_edge, left_edge, right_edge), axis=0)

    expected_edge_pixels = np.full(
        edge_pixels.shape, [255, 0, 0], dtype=edge_pixels.dtype
    )

    assert np.array_equal(edge_pixels, expected_edge_pixels)


def test_resize_image():
    factor = 2.5
    img = cv2.imread(str((TESTIMAGES_PATH / "color.png").resolve()))
    img_result = enhance._resize_image(img.copy(), factor=factor)
    assert img.shape[0] * factor == img_result.shape[0]
    assert img.shape[1] * factor == img_result.shape[1]
    assert img.shape[2] == img_result.shape[2]


def test_preprocess():
    img = cv2.imread(str((TESTIMAGES_PATH / "dark.png").resolve()))
    factor = 2
    padding = 10
    img_result = enhance.preprocess(img.copy(), resize_factor=factor, padding=padding)
    assert img.shape[1] * factor + padding * 2 == img_result.shape[1]
    assert img_result[0, 0, :].tolist() == [0, 0, 0]
    assert img_result[99, 49, :].tolist() == [0, 0, 0]
