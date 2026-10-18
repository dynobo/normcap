"""Tests for barcode/QR detection in normcap.detection.codes.detector."""

import logging
from types import SimpleNamespace

import pytest
import zxingcpp
from PySide6 import QtGui

from normcap.detection.codes import detector
from normcap.detection.models import TextDetector, TextType

QR_CONTENT = "https://github.com/dynobo/normcap"

# QImage formats the zxingcpp python wrapper maps to an ImageFormat itself.
SUPPORTED_FORMATS = [
    QtGui.QImage.Format.Format_RGB32,
    QtGui.QImage.Format.Format_ARGB32,
    QtGui.QImage.Format.Format_RGB888,
    QtGui.QImage.Format.Format_BGR888,
    QtGui.QImage.Format.Format_RGBA8888,
    QtGui.QImage.Format.Format_Grayscale8,
]

# QImage formats the wrapper's internal fallback fails on, because it
# calls `convertToFormat(24)` with a plain int instead of a QImage.Format enum.
UNSUPPORTED_FORMATS = [
    QtGui.QImage.Format.Format_ARGB32_Premultiplied,
    QtGui.QImage.Format.Format_RGBX8888,
    QtGui.QImage.Format.Format_Indexed8,
    QtGui.QImage.Format.Format_RGB16,
    QtGui.QImage.Format.Format_Mono,
]


def _render_qr_image(
    text: str = QR_CONTENT,
    *,
    scale: int = 4,
    quiet_zone: int = 12,
    extra_width: int = 0,
    image_format: QtGui.QImage.Format | None = None,
) -> QtGui.QImage:
    """Build a QImage with a QR code in it, without requiring numpy or a QApplication.

    `extra_width` widens the canvas so that Qt has to pad the row stride, which is the
    case the previous `memoryview` conversion had to strip manually.
    """
    source = zxingcpp.create_barcode(text, zxingcpp.BarcodeFormat.QRCode).to_image(
        scale=scale
    )
    src_width, src_height = source.shape[1], source.shape[0]
    gray = bytes(memoryview(source))

    width = src_width + 2 * quiet_zone + extra_width
    height = src_height + 2 * quiet_zone
    image = QtGui.QImage(width, height, QtGui.QImage.Format.Format_RGB888)
    image.fill(QtGui.QColor("white"))

    buffer = memoryview(image.bits())
    row_stride = image.bytesPerLine()
    for y in range(src_height):
        row = gray[y * src_width : (y + 1) * src_width]
        offset = (y + quiet_zone) * row_stride + quiet_zone * 3
        buffer[offset : offset + 3 * src_width] = bytes(
            byte for value in row for byte in (value, value, value)
        )

    if image_format is None:
        return image
    return image.convertToFormat(image_format)


@pytest.mark.parametrize("image_format", SUPPORTED_FORMATS, ids=lambda f: f.name)
def test_detect_codes_qimage_formats_mapped_by_zxing(image_format):
    """Formats the wrapper understands natively are handed over unchanged."""
    results = detector.detect_codes(_render_qr_image(image_format=image_format))

    assert len(results) == 1
    assert results[0].text == QR_CONTENT
    assert results[0].text_type == TextType.URL


@pytest.mark.parametrize("image_format", UNSUPPORTED_FORMATS, ids=lambda f: f.name)
def test_detect_codes_qimage_formats_not_mapped_by_zxing(image_format):
    """Formats the wrapper chokes on must be converted before being passed on."""
    results = detector.detect_codes(_render_qr_image(image_format=image_format))

    assert len(results) == 1
    assert results[0].text == QR_CONTENT


def test_detect_codes_with_padded_row_stride():
    """QImage pads rows for alignment, the decoder has to honor the row stride."""
    image = _render_qr_image(extra_width=3)

    assert image.bytesPerLine() > image.width() * 3

    results = detector.detect_codes(image)

    assert [result.text for result in results] == [QR_CONTENT]


def test_detect_codes_passes_qimage_to_zxing_without_copying(monkeypatch):
    """A supported QImage must be decoded in place, not copied into a buffer."""
    received = []
    read_barcodes = zxingcpp.read_barcodes

    def spy(image, *args, **kwargs):
        received.append(image)
        return read_barcodes(image, *args, **kwargs)

    monkeypatch.setattr(detector.zxingcpp, "read_barcodes", spy)

    image = _render_qr_image(image_format=QtGui.QImage.Format.Format_RGB32)
    detector.detect_codes(image)

    assert received
    assert received[0] is image


def test_detect_codes_normalizes_unsupported_format_before_decoding(monkeypatch):
    """Unsupported formats are converted once, then handed to zxing as QImage."""
    received = []
    read_barcodes = zxingcpp.read_barcodes

    def spy(image, *args, **kwargs):
        received.append(image)
        return read_barcodes(image, *args, **kwargs)

    monkeypatch.setattr(detector.zxingcpp, "read_barcodes", spy)

    image = _render_qr_image(
        image_format=QtGui.QImage.Format.Format_ARGB32_Premultiplied
    )
    detector.detect_codes(image)

    assert len(received) == 1
    passed = received[0]
    assert isinstance(passed, QtGui.QImage)
    assert passed is not image
    assert passed.format() == QtGui.QImage.Format.Format_RGB888


def test_detect_codes_returns_empty_list_without_codes():
    blank = QtGui.QImage(400, 400, QtGui.QImage.Format.Format_RGB888)
    blank.fill(QtGui.QColor("white"))

    assert detector.detect_codes(blank) == []


def _fake_zxing_result(
    text, barcode_format, *, valid=True, error=None
) -> SimpleNamespace:
    """Mimic a `zxingcpp.Barcode` as returned with `return_errors=True`."""
    return SimpleNamespace(text=text, format=barcode_format, valid=valid, error=error)


def test_real_zxing_result_provides_attributes_used_by_detector():
    """Guard the attribute contract the stubbed tests below rely on."""
    result = zxingcpp.read_barcodes(_render_qr_image())[0]

    assert result.valid is True
    assert result.error is None
    assert result.format == zxingcpp.BarcodeFormat.QRCode
    assert result.text == QR_CONTENT


def test_detect_codes_skips_invalid_and_empty_results(monkeypatch, caplog):
    """Results without usable text must not break or shift the remaining ones.

    With `return_errors=True`, zxingcpp returns invalid results whose `text` is empty.
    Those used to be filtered out of the texts but not out of the formats, so that
    `zip(..., strict=True)` raised `ValueError`.
    """
    invalid_empty = _fake_zxing_result(
        "", zxingcpp.BarcodeFormat.Code128, valid=False, error="Checksum"
    )
    valid_empty = _fake_zxing_result("", zxingcpp.BarcodeFormat.Code128)
    qr_code = _fake_zxing_result(QR_CONTENT, zxingcpp.BarcodeFormat.QRCode)
    barcode = _fake_zxing_result("1234567890128", zxingcpp.BarcodeFormat.EAN13)

    monkeypatch.setattr(
        detector.zxingcpp,
        "read_barcodes",
        lambda *_, **__: [invalid_empty, valid_empty, qr_code, barcode],
    )

    with caplog.at_level(logging.WARNING, logger=detector.logger.name):
        results = detector.detect_codes(_render_qr_image())

    assert [result.text for result in results] == [QR_CONTENT, "1234567890128"]
    assert [result.detector for result in results] == [
        TextDetector.QR,
        TextDetector.BARCODE,
    ]
    assert [result.text_type for result in results] == [
        TextType.URL,
        TextType.SINGLE_LINE,
    ]
    assert f"Invalid {zxingcpp.BarcodeFormat.Code128} result" in caplog.text


def test_detect_codes_returns_empty_list_if_all_results_unusable(monkeypatch):
    unusable = _fake_zxing_result(
        "", zxingcpp.BarcodeFormat.QRCode, valid=False, error="Checksum"
    )
    monkeypatch.setattr(detector.zxingcpp, "read_barcodes", lambda *_, **__: [unusable])

    assert detector.detect_codes(_render_qr_image()) == []
