from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets


@dataclass
class TestCase:
    name: str
    image_path: Path
    left_top: tuple[int, int]
    right_bottom: tuple[int, int]
    expected_ocr_text: str
    expected_ocr_magics: list[str]

    @property
    def image(self) -> QtGui.QImage:
        return QtGui.QImage(self.image_path)

    @property
    def screen_size(self) -> QtCore.QSize:
        app = QtWidgets.QApplication.instance()
        if isinstance(app, QtGui.QGuiApplication):
            return app.primaryScreen().size()
        raise TypeError("Could not detect QGuiApplication")

    @property
    def _scale_factor(self) -> float:
        if (
            self.screen_size.width() == self.image.width()
            and self.screen_size.height() == self.image.height()
        ):
            return 1

        x_factor = self.image.width() / self.screen_size.width()
        y_factor = self.image.height() / self.screen_size.height()
        return max(x_factor, y_factor)

    @property
    def coords_scaled(self) -> tuple[QtCore.QPoint, QtCore.QPoint]:
        return (
            QtCore.QPoint(*self.left_top) / self._scale_factor,  # type: ignore # *
            QtCore.QPoint(*self.right_bottom) / self._scale_factor,  # type: ignore # *
        )
        # (*) It think __div__ is not correctly specified in PySide6

    @property
    def image_scaled(self) -> QtGui.QImage:
        if self._scale_factor == 1:
            return self.image

        image = self.image.scaled(
            int(self.image.width() / self._scale_factor),
            int(self.image.height() / self._scale_factor),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        image_full = QtGui.QImage(self.screen_size, image.format())
        image_full.fill(QtGui.qRgb(50, 50, 50))
        with QtGui.QPainter(image_full) as p:
            p.drawImage(0, 0, image)

        return image_full


image_dir = Path(__file__).parent

testcases: tuple[TestCase, ...] = (
    # 0
    TestCase(
        name="0: ParseUrls",
        image_path=image_dir / "ocr_test_1.png",
        left_top=(46, 745),
        right_bottom=(500, 950),
        expected_ocr_text="\n".join(
            [
                "https://github.com/dynobo/normcap",
                "https://wikipedia.de",
                "https://www.python.com",
                "https://en.wikipedia.org/wiki/Tesseract",
                "https://pypi.org/project/lmdiag/",
            ]
        ),
        expected_ocr_magics=["UrlMagic"],
    ),
    # 1
    TestCase(
        name="1: ParseColoredUrl",
        image_path=image_dir / "ocr_test_1.png",
        left_top=(312, 548),
        right_bottom=(470, 568),
        expected_ocr_text="https://regex101.com",
        expected_ocr_magics=["UrlMagic"],
    ),
    # 2
    TestCase(
        name="2: WindowTitle",
        image_path=image_dir / "ocr_test_1.png",
        left_top=(1115, 530),
        right_bottom=(1305, 570),
        expected_ocr_text="*Untitled Document 1",
        expected_ocr_magics=["SingleLineMagic"],
    ),
    # 3
    TestCase(
        # First two rows of email addresses
        name="3: DifficultMailAddresses",
        image_path=image_dir / "ocr_test_1.png",
        left_top=(50, 301),
        right_bottom=(700, 342),
        expected_ocr_text="peter.parker@test.com, HArDToReAd@test.com, 0815@test.com",
        expected_ocr_magics=["EmailMagic"],
    ),
    # 4
    TestCase(
        # All three rows of email addresses, 3rd row contains invalids
        name="4: MailAddressesWithInvalid",
        image_path=image_dir / "ocr_test_1.png",
        left_top=(50, 299),
        right_bottom=(700, 363),
        expected_ocr_text=(
            "To: Peter Parker <peter.parker@test.com>; "
            "HArD To ReAd\n"
            "<HArDToReAd@test.com>; "
            "0815 <0815@test.com>; "
            "Invalid_one <notvalid@test>;\n"
            "Invalid_two <also/not/valid/@test.com>; "
            "Invalid_three <@test.com>"
        ),
        expected_ocr_magics=["ParagraphMagic", "MultiLineMagic"],
    ),
    # 5
    TestCase(
        # Low contrast
        name="5: TextWithLowContrast",
        image_path=image_dir / "ocr_test_1.png",
        left_top=(1080, 720),
        right_bottom=(1570, 800),
        expected_ocr_text="Orange, the new black!",
        expected_ocr_magics=["SingleLineMagic"],
    ),
    # 6
    TestCase(
        # Includes special characters to test encoding issues
        name="6: TextWithSpecialChars",
        image_path=image_dir / "ocr_test_1.png",
        left_top=(1080, 870),
        right_bottom=(1610, 1030),
        expected_ocr_text=(
            "‘One small step for Man’\n“Live long and prosper!”\n"  # noqa: RUF001
            '«Open the shuttlebay doors»\n"May the Schwartz™ be with you!"'
        ),
        expected_ocr_magics=["ParagraphMagic"],
    ),
)
