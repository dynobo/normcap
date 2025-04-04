"""Optimizes the captured image for OCR."""

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _identify_most_frequent_edge_color(img: np.ndarray) -> list[int]:
    """Heuristically find color for padding using cv2 functions."""
    # Extract edge pixels
    top_edge = img[0, :]
    bottom_edge = img[-1, :]
    left_edge = img[:, 0]
    right_edge = img[:, -1]

    # Combine all edge pixels
    edge_pixels = np.concatenate((top_edge, bottom_edge, left_edge, right_edge), axis=0)

    # Find the most frequent color using numpy
    edge_pixels = edge_pixels.reshape(-1, edge_pixels.shape[-1])
    unique, counts = np.unique(edge_pixels, axis=0, return_counts=True)
    most_frequent_edge_color = unique[np.argmax(counts)]
    return most_frequent_edge_color.tolist()


def _add_padding(img: np.ndarray, padding: int = 80) -> np.ndarray:
    """Pad the selected part of the image.

    Tesseract is optimized for e.g. scans or documents and therefore
    works better with a certain amount of padding around the content.

    Uses the most frequent edge color as background color.
    """
    logger.debug("Pad image by %spx", padding)

    background_color = _identify_most_frequent_edge_color(img)
    return cv2.copyMakeBorder(
        img,
        padding,
        padding,
        padding,
        padding,
        cv2.BORDER_CONSTANT,
        value=background_color,
    )


def _resize_image(image: np.ndarray, factor: float) -> np.ndarray:
    """Resize image to get equivalent of 300dpi.

    According to various sources, it seems like tesseract performs best when with
    capital letter of height 20px-50px. => A resize factor of 2 seems reasonable.

    References:
    https://groups.google.com/g/tesseract-ocr/c/Wdh_JJwnw94/m/24JHDYQbBQAJ
    https://willus.com/blog.shtml?tesseract_accuracy
    """
    logger.debug("Scale image x%s", factor)

    return cv2.resize(
        image,
        (int(image.shape[1] * factor), int(image.shape[0] * factor)),
        interpolation=cv2.INTER_LINEAR,
    )


def preprocess(
    image: np.ndarray, resize_factor: Optional[float], padding: Optional[int]
) -> np.ndarray:
    if resize_factor:
        image = _resize_image(image, factor=resize_factor)
    if padding:
        image = _add_padding(image, padding=padding)
    return image
