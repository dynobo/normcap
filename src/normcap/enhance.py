"""Responsible to optimize the captured image for OCR."""

from collections import Counter

from PySide2 import QtCore, QtGui

from normcap import utils
from normcap.logger import logger
from normcap.models import Capture


class EnhanceImage:
    """Helper to apply image transformation to increase recogntion accuracy."""

    def __call__(self, capture: Capture) -> Capture:
        """Execute chain of optimizations."""
        logger.info("Applying enhancements to image")

        # Currently, the image is only enlarged
        # for other strategies see: https://stackoverflow.com/a/50762612
        if capture.image:
            capture.image = self._enlarge_dpi(capture.image)
            utils.save_image_in_tempfolder(capture.image, postfix="_enlarged")

            capture.image = self._add_padding(capture.image)
            utils.save_image_in_tempfolder(capture.image, postfix="_padded")
        return capture

    @staticmethod
    def _strech_contrast(img: QtGui.QImage) -> QtGui.QImage:
        # TODO: to be implemented
        return img

    @staticmethod
    def _add_padding(img: QtGui.QImage, padding=80) -> QtGui.QImage:
        """Pad the selected part of the image.

        Tesseract is optimized for e.g. scans or documents and therefore
        works better with a certain amount of padding around the content.

        Uses the most frequent edge color as background color.
        TODO: Test padding strategy where the edge colors are extended
              (might be useful in case of bars etc, but problematic on images)
        """

        bg_col = EnhanceImage._most_frequent_edge_color(img)

        padded_img = img.scaled(img.width() + padding * 2, img.height() + padding * 2)
        padded_img.fill(bg_col)

        painter = QtGui.QPainter(padded_img)
        painter.drawImage(padding, padding, img)

        return padded_img

    @staticmethod
    def _most_frequent_edge_color(img: QtGui.QImage) -> QtGui.QColor:
        edge_colors = []

        # Top edge
        for x in range(0, img.width()):
            edge_colors.append(img.pixelColor(x, 0).name())

        # Bottom edge
        for x in range(0, img.width()):
            edge_colors.append(img.pixelColor(x, img.height() - 1).name())

        # Left edge
        for y in range(0, img.height()):
            edge_colors.append(img.pixelColor(0, y).name())

        # Right edge
        for y in range(0, img.height()):
            edge_colors.append(img.pixelColor(img.width() - 1, y).name())

        color_count = Counter(edge_colors)
        most_frequent_color = color_count.most_common()[0][0]

        return QtGui.QColor(most_frequent_color)

    @staticmethod
    def _enlarge_dpi(img: QtGui.QImage, factor: float = 3.2) -> QtGui.QImage:
        """Resize image to get equivalent of 300dpi.
        Reason: Most display are around ~100dpi, while Tesseract works best ~300dpi.

        Arguments:
            img - Input image to enlarge

        Returns:
            Enlarged image
        """
        img = img.scaled(
            int(img.width() * factor),
            int(img.height() * factor),
            QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        logger.debug(f"Resized screenshot by factor {factor}")

        return img


enhance_image = EnhanceImage()
