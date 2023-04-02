"""Optimizes the captured image for OCR."""

import logging
import random
from collections import Counter
from collections.abc import Iterable
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter

logger = logging.getLogger(__name__)


def _get_pixels(
    image: QImage, points: Iterable[tuple[int, int]]
) -> list[tuple[int, ...]]:
    pixel_size = 4  ## One pixel consists of 4 values: R,G,B,A
    ptr = image.bits()
    width = image.width()

    pixel = []
    for left, top in points:
        start = (left + width * top) * pixel_size
        rgb = tuple(ptr[x] for x in range(start + 2, start - 1, -1))
        pixel.append(rgb)

    return pixel


def _identify_most_frequent_edge_color(img: QImage) -> tuple[int, ...]:
    """Heuristically find color for padding."""
    points = [(x, 0) for x in range(img.width())]  # top
    points += [(x, img.height() - 1) for x in range(img.width())]  # bottom
    points += [(0, x) for x in range(img.height())]  # left
    points += [(img.width() - 1, x) for x in range(img.height())]  # right

    sample_size = 400
    points = random.sample(points, sample_size)
    edge_pixels = _get_pixels(image=img, points=points)

    color_count = Counter(edge_pixels)
    return color_count.most_common()[0][0]


def add_padding(img: QImage, padding: int = 80) -> QImage:
    """Pad the selected part of the image.

    Tesseract is optimized for e.g. scans or documents and therefore
    works better with a certain amount of padding around the content.

    Uses the most frequent edge color as background color.
    """
    logger.debug("Pad image by %spx", padding)

    padded_img = QImage(
        img.width() + padding * 2,
        img.height() + padding * 2,
        QImage.Format.Format_RGB32,
    )

    bg_col = _identify_most_frequent_edge_color(img)
    padded_img.fill(QColor(*bg_col))

    painter = QPainter(padded_img)
    painter.drawImage(padding, padding, img)

    return padded_img


def resize_image(image: QImage, factor: float = 3.2) -> QImage:
    """Resize image to get equivalent of 300dpi.

    Useful because most displays are around ~100dpi, while Tesseract works best ~300dpi.
    """
    logger.debug("Scale image x%s", factor)

    image = image.scaled(
        int(image.width() * factor),
        int(image.height() * factor),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return image


def invert_image(image: QImage) -> QImage:
    """Invert image.

    Improves detection in case of bright text on dark background.
    """
    logger.debug("Invert image")
    image.invertPixels()
    return image


def is_dark(image: QImage) -> bool:
    """Detect if mean pixel brightness is below 125."""
    i = 400  # points to sample
    x = tuple(random.randint(0, image.width() - 1) for _ in range(i))  # noqa: S311
    y = tuple(random.randint(0, image.height() - 1) for _ in range(i))  # noqa: S311
    points = tuple(zip(x, y))

    pixels = _get_pixels(image=image, points=points)

    mean_color_value = sum(sum(p) for p in pixels) / 3 / len(points)
    middle_grey = 125

    return mean_color_value < middle_grey


def preprocess(
    image: QImage, resize_factor: Optional[float], padding: Optional[int]
) -> QImage:
    image = image.convertToFormat(QImage.Format.Format_RGB32)
    if resize_factor:
        image = resize_image(image, factor=resize_factor)
    if padding:
        image = add_padding(image, padding=padding)
    if is_dark(image):
        image = invert_image(image)
    return image
