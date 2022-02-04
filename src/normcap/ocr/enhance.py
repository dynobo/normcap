"""Optimizes the captured image for OCR."""

import logging
from collections import Counter

from PySide6 import QtCore, QtGui

from normcap.gui import utils
from normcap.models import Capture

logger = logging.getLogger(__name__)


def _add_padding(img: QtGui.QImage, padding=80) -> QtGui.QImage:
    """Pad the selected part of the image.

    Tesseract is optimized for e.g. scans or documents and therefore
    works better with a certain amount of padding around the content.

    Uses the most frequent edge color as background color.
    TODO: Test padding strategy where the edge colors are extended
            (might be useful in case of bars etc, but problematic on images)
    """
    bg_col = _identify_most_frequent_edge_color(img)

    padded_img = img.scaled(img.width() + padding * 2, img.height() + padding * 2)
    padded_img.fill(bg_col)

    painter = QtGui.QPainter(padded_img)
    painter.drawImage(padding, padding, img)

    return padded_img


def _identify_most_frequent_edge_color(img: QtGui.QImage) -> QtGui.QColor:
    """Heuristically find color for padding."""
    edge_colors = []

    # Top and bottom edge
    for x in range(img.width()):
        edge_colors.append(img.pixelColor(x, 0).name())
        edge_colors.append(img.pixelColor(x, img.height() - 1).name())

    # Left and right edge
    for y in range(img.height()):
        edge_colors.append(img.pixelColor(0, y).name())
        edge_colors.append(img.pixelColor(img.width() - 1, y).name())

    color_count = Counter(edge_colors)
    most_frequent_color = color_count.most_common()[0][0]

    return QtGui.QColor(most_frequent_color)


def _enlarge_dpi(image: QtGui.QImage, factor: float = 3.2) -> QtGui.QImage:
    """Resize image to get equivalent of 300dpi.

    Useful because most displays are around ~100dpi, while Tesseract works best ~300dpi.
    """
    logger.debug("Resize screenshot by factor %s", factor)
    return image.scaled(
        int(image.width() * factor),
        int(image.height() * factor),
        QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
        QtCore.Qt.TransformationMode.SmoothTransformation,
    )


def enhance_image(capture: Capture) -> Capture:
    """Execute chain of optimizations."""
    logger.info("Apply enhancements to image")

    # Currently, the image is only enlarged and padded.
    # for other strategies see: https://stackoverflow.com/a/50762612
    if capture.image:
        capture.image = _enlarge_dpi(capture.image)
        utils.save_image_in_tempfolder(capture.image, postfix="_enlarged")

        capture.image = _add_padding(capture.image)
        utils.save_image_in_tempfolder(capture.image, postfix="_padded")
    return capture
