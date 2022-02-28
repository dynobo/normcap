"""Optimizes the captured image for OCR."""

import logging
from collections import Counter
from typing import cast

from PIL import Image

logger = logging.getLogger(__name__)


def _identify_most_frequent_edge_color(img: Image.Image) -> tuple:
    """Heuristically find color for padding."""
    edge_colors = []

    # Top and bottom edge
    for x in range(img.width):
        edge_colors.append(img.getpixel((x, 0)))
        edge_colors.append(img.getpixel((x, img.height - 1)))

    # Left and right edge
    for y in range(img.height):
        edge_colors.append(img.getpixel((0, y)))
        edge_colors.append(img.getpixel((img.width - 1, y)))

    color_count = Counter(edge_colors)

    return color_count.most_common()[0][0]


def add_padding(img: Image.Image, padding=80) -> Image.Image:
    """Pad the selected part of the image.

    Tesseract is optimized for e.g. scans or documents and therefore
    works better with a certain amount of padding around the content.

    Uses the most frequent edge color as background color.
    TODO: Test padding strategy where the edge colors are extended
            (might be useful in case of bars etc, but problematic on images)
    """
    logger.debug("Pad image by %s px", padding)

    bg_col = _identify_most_frequent_edge_color(img)

    padded_img = Image.new(
        cast("Image._Mode", img.mode),
        (img.width + padding * 2, img.height + padding * 2),
        bg_col,
    )
    padded_img.paste(img, (padding, padding))
    return padded_img


def resize_image(image: Image.Image, factor: float = 3.2) -> Image.Image:
    """Resize image to get equivalent of 300dpi.

    Useful because most displays are around ~100dpi, while Tesseract works best ~300dpi.
    """
    logger.debug("Resize screenshot by factor %s", factor)
    return image.resize(
        size=(int(image.width * factor), int(image.height * factor)),
        resample=Image.ANTIALIAS,
    )
