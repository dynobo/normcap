"""Barcode and QR Code detection."""

import logging
import os
from pathlib import Path
from typing import Optional

# TODO: Move the env setup
# Silence opencv warnings
os.environ["OPENCV_LOG_LEVEL"] = "OFF"

import cv2
import numpy as np
from PySide6 import QtGui

from normcap import resources
from normcap.detectors.codes.structures import Code

logger = logging.getLogger(__name__)

model_path = Path(resources.__file__).parent / "qr"


def _detect_barcodes_sr(mat: np.ndarray) -> list[str]:
    """Barcode detection using super resolution.

    Significantly slower but more accurate than w/o SR.
    """
    retval, bar_decoded, types, points = cv2.barcode.BarcodeDetector(
        str((model_path / "sr.prototxt").resolve()),
        str((model_path / "sr.caffemodel").resolve()),
    ).detectAndDecodeMulti(mat)
    return [s for s in bar_decoded if s]


def _detect_barcodes(mat: np.ndarray) -> list[str]:
    retval, bar_decoded, types, points = (
        cv2.barcode.BarcodeDetector().detectAndDecodeMulti(mat)
    )
    return [s for s in bar_decoded if s]


def _detect_qrcodes(mat: np.ndarray) -> list[str]:
    retval, qr_decoded, points, straight_qrcode = (
        cv2.QRCodeDetector().detectAndDecodeMulti(mat)
    )
    return [s for s in qr_decoded if s]


def _detect_qrcodes_wechat(mat: np.ndarray) -> list[str]:
    """Detect QR codes using WeChat's models.

    Similar accuracy to the default OpenCV model but faster on large images.
    """
    qr_decoded, image = cv2.wechat_qrcode.WeChatQRCode(
        str((model_path / "detect.prototxt").resolve()),
        str((model_path / "detect.caffemodel").resolve()),
        str((model_path / "sr.prototxt").resolve()),
        str((model_path / "sr.caffemodel").resolve()),
    ).detectAndDecode(mat)
    return [s for s in qr_decoded if s]


def _image_to_mat(image: QtGui.QImage) -> np.ndarray:
    ptr = image.constBits()
    arr = np.array(ptr).reshape(image.height(), image.width(), 4)
    return arr[:, :, :3]


def detect_codes(image: QtGui.QImage) -> Optional[tuple[str, Code]]:
    """Decode QR and barcodes from image.

    Args:
        image: Input image.

    Returns:
        URL(s), separated bye newline
    """
    logger.info("Detect Barcodes and QR Codes")

    mat = _image_to_mat(image)

    barcodes = _detect_barcodes_sr(mat=mat)
    qr_codes = _detect_qrcodes_wechat(mat=mat)

    codes = barcodes + qr_codes

    if not codes:
        return None

    if barcodes and not qr_codes:
        code_type = Code.BARCODE
    elif qr_codes and not barcodes:
        code_type = Code.QR
    else:
        code_type = Code.QR_AND_BARCODE

    return os.linesep.join(codes), code_type


if __name__ == "__main__":
    import os
    from pathlib import Path
    from timeit import timeit

    reps = 10

    image_file = (
        Path(__file__).parent.parent.parent
        / "tests"
        / "integration"
        / "testcases"
        / "13_qr_code_with_text.png"
    )
    image = QtGui.QImage(str(image_file.resolve()))
    mat = _image_to_mat(image)

    time_mat = timeit(lambda: _image_to_mat(image), globals=globals(), number=reps)
    time_qr = timeit(lambda: _detect_qrcodes(mat), globals=globals(), number=reps)
    time_qr_we = timeit(
        lambda: _detect_qrcodes_wechat(mat), globals=globals(), number=reps
    )
    time_bar = timeit(lambda: _detect_barcodes(mat), globals=globals(), number=reps)
    time_bar_sr = timeit(
        lambda: _detect_barcodes_sr(mat), globals=globals(), number=reps
    )

    qr_codes = _detect_qrcodes(mat)
    qr_codes_we = _detect_qrcodes_wechat(mat)
    barcodes_sr = _detect_barcodes_sr(mat)
    barcodes = _detect_barcodes(mat)

    print(  # noqa: T201
        f"{time_mat / reps:.7f} (convert to mat)\n"
        f"{time_qr / reps:.7f} ({len(qr_codes)} QR)\n"
        f"{time_qr_we / reps:.7f} ({len(qr_codes_we)} QR WeChat)\n"
        f"{time_bar / reps:.7f} ({len(barcodes_sr)} Barcodes)\n"
        f"{time_bar_sr / reps:.7f} ({len(barcodes_sr)} Barcodes SR)\n"
    )
