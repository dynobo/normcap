from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets


@dataclass
class TestCase:
    image_path: Path
    expected_ocr_text: str
    expected_ocr_magics: list[str]

    _image: QtGui.QImage | None = None

    @property
    def image(self) -> QtGui.QImage:
        if not self._image:
            self._image = QtGui.QImage(self.image_path)
        return self._image

    @property
    def screenshot(self) -> QtGui.QImage:
        """Provides image drawn on colored canvas with the size of the screen."""
        pixmap = QtGui.QPixmap(self.screen_size)
        pixmap.fill(QtCore.Qt.GlobalColor.darkCyan)
        with QtGui.QPainter(pixmap) as painter:
            painter.drawImage(0, 0, self.image)
        return pixmap.toImage()

    @property
    def screen_size(self) -> QtCore.QSize:
        app = QtWidgets.QApplication.instance()
        if isinstance(app, QtGui.QGuiApplication):
            return app.primaryScreen().size()
        raise TypeError("Could not detect QGuiApplication")

    @property
    def coords(self) -> tuple[QtCore.QPoint, QtCore.QPoint]:
        return (
            QtCore.QPoint(1, 1),
            QtCore.QPoint(self.image.width() - 1, self.image.height() - 1),
        )


image_dir = Path(__file__).parent

testcases: tuple[TestCase, ...] = (
    TestCase(
        image_path=image_dir / "00_parse_urls.png",
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
    TestCase(
        image_path=image_dir / "01_parse_colored_url.png",
        expected_ocr_text="https://regex101.com",
        expected_ocr_magics=["UrlMagic"],
    ),
    TestCase(
        image_path=image_dir / "02_detect_window_title.png",
        expected_ocr_text="*Untitled Document 1",
        expected_ocr_magics=["SingleLineMagic"],
    ),
    TestCase(
        image_path=image_dir / "03_parse_emails.png",
        expected_ocr_text="peter.parker@test.com, HArDToReAd@test.com, 0815@test.com",
        expected_ocr_magics=["EmailMagic"],
    ),
    TestCase(
        image_path=image_dir / "04_parse_email_skip_invalid.png",
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
    TestCase(
        image_path=image_dir / "05_detect_text_with_low_contrast.png",
        expected_ocr_text="Orange, the new black!",
        expected_ocr_magics=["SingleLineMagic"],
    ),
    TestCase(
        image_path=image_dir / "06_detect_special_characters.png",
        expected_ocr_text=(
            "‘One small step for Man’\n“Live long and prosper!”\n"  # noqa: RUF001
            '«Open the shuttlebay doors»\n"May the Schwartz™ be with you!"'
        ),
        expected_ocr_magics=["ParagraphMagic"],
    ),
    TestCase(
        image_path=image_dir / "07_parse_paragraphs_of_text.png",
        expected_ocr_text=(
            "You rent a hotel room. You put a book in the top drawer of the bedside "
            'table and go to sleep. You check out the next morning, but "forget" to '
            "give back your key. You steal the key!\n"
            "A week later, you return to the hotel, do not check in, sneak into your "
            "old room with your stolen key, and look in the drawer. Your book is still "
            "there. Astonishing!\n"
            "How can that be? Aren't the contents of a hotel room drawer inaccessible "
            "if you haven't rented the room?"
        ),
        expected_ocr_magics=["ParagraphMagic"],
    ),
)
