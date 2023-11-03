from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets


@dataclass
class TestCase:
    image_path: Path
    expected_ocr_text: str
    expected_ocr_magics: list[str]
    expected_similarity: float = 0.98
    skip: bool = False

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
    TestCase(
        # https://www.gutenberg.org/cache/epub/1321/pg1321-images.html
        image_path=image_dir / "08_paragraphs.png",
        expected_ocr_text=(
            "Chapter 17\n"
            "The being finished speaking and fixed his looks upon me in the "
            "expectation of a reply. But I was bewildered, perplexed, and unable to "
            "arrange my ideas sufficiently to understand the full extent of his "
            "proposition. He continued,\n"
            "“You must create a female for me with whom I can live in the interchange "
            "of those sympathies necessary for my being. This you alone can do, and I "
            "demand it of you as a right which you must not refuse to concede.”\n"
            "The latter part of his tale had kindled anew in me the anger that had "
            "died away while he narrated his peaceful life among the cottagers, and as "
            "he said this I could no longer suppress the rage that burned within me."
        ),
        expected_ocr_magics=["ParagraphMagic"],
        expected_similarity=1,
    ),
    TestCase(
        image_path=image_dir / "09_two_columns.png",
        expected_ocr_text=(
            "Optical character recognition or optical character reader (OCR) is the "
            "electronic or mechanical conversion of images of typed, handwritten or "
            "printed text into machine-encoded text, whether from a scanned document, "
            "a photo of a document, a scene photo (for example the text on signs and "
            "billboards in a landscape photo) or from subtitle text superimposed on an "
            "image (for example: from a television broadcast).\n"
            "Widely used as a form of data entry from printed paper data records — "
            "whether passport documents, invoices, bank statements, computerized "
            "receipts, business cards, mail, printed data, or any suitable "
            "documentation — it is a common method of digitizing printed texts so that "
            "they can be electronically edited, searched, stored more compactly, "
            "displayed online, and used in machine processes such as cognitive "
            "computing, machine translation, (extracted) text-to-speech, key data and "
            "text mining. OCR is a field of research in pattern recognition, "
            "artificial intelligence and computer vision.\n"
            "Early versions needed to be trained with images of each character, and "
            "worked on one font at a time. Advanced systems capable of producing a "
            "high degree of accuracy for most fonts are now common, and with support "
            "for a variety of image file format inputs. Some systems are capable "
            "of reproducing formatted output that closely approximates the original "
            "page including images, columns, and other non-textual components."
        ),
        expected_ocr_magics=["ParagraphMagic"],
    ),
    TestCase(
        image_path=image_dir / "10_font_sizes.png",
        expected_ocr_text=(
            "Arial, 8 pt - You only live once, but if you do it right, once is enough."
            "\n"
            "Arial, 11 pt - You only live once, but if you do it right, once is enough."
            "\n"
            "Arial, 14 pt - You only live once, but if you do it right, once is enough."
            "\n"
            "Arial, 16 pt - You only live once, but if you do it right, once is enough."
            "\n"
            "Arial, 22 pt - You only live once, but if you do it right, once is enough."
        ),
        expected_ocr_magics=["ParagraphMagic"],
    ),
)
