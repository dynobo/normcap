"""Optimizes the captured image for OCR."""

import logging
from collections import Counter
from typing import Optional, cast

from PIL import Image, ImageOps, ImageStat

logger = logging.getLogger(__name__)


def _identify_most_frequent_edge_color(img: Image.Image) -> tuple[int, int, int]:
    """Heuristically find color for padding."""
    # Top and bottom edge
    edge_colors = [img.getpixel((x, 0)) for x in range(img.width)]
    edge_colors += [img.getpixel((x, img.height - 1)) for x in range(img.width)]

    # Left and right edge
    edge_colors += [img.getpixel((0, y)) for y in range(img.height)]
    edge_colors += [img.getpixel((img.width - 1, y)) for y in range(img.height)]

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
        resample=Image.Resampling.LANCZOS,  # type: ignore
    )


def invert_image(image: Image.Image) -> Image.Image:
    """Invert image.

    Improves detection in case of bright text on dark background.
    """
    logger.debug("Inverting screenshot")
    return ImageOps.invert(image)


def is_dark(image: Image.Image) -> Image.Image:
    """Detect if mean pixel brightness is below 125."""
    image_grayscale = image.convert("L")
    stat = ImageStat.Stat(image_grayscale)
    return stat.mean[0] < 125


def preprocess(
    image: Image.Image, resize_factor: Optional[float], padding: Optional[int]
) -> Image.Image:
    image = image.convert("RGB")
    if resize_factor:
        image = resize_image(image, factor=resize_factor)
    if padding:
        image = add_padding(image, padding=padding)
    if is_dark(image):
        image = invert_image(image)
    return image
