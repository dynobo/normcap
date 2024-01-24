import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.ocr.structures import Transformer


@dataclass
class TestCase:
    image_path: Path
    expected_ocr_text: str
    expected_ocr_transformers: list[Transformer]
    expected_similarity: float = 0.98
    skip: bool = False

    _image: Optional[QtGui.QImage] = None

    @property
    def _screen_size(self) -> QtCore.QSize:
        app = QtWidgets.QApplication.instance()
        if isinstance(app, QtGui.QGuiApplication):
            return app.primaryScreen().size() * self._device_pixel_ratio
        raise TypeError("Could not detect QGuiApplication")

    @property
    def _device_pixel_ratio(self) -> float:
        app = QtWidgets.QApplication.instance()
        if isinstance(app, QtGui.QGuiApplication):
            return app.primaryScreen().devicePixelRatio()
        raise TypeError("Could not detect QGuiApplication")

    @property
    def image(self) -> QtGui.QImage:
        if not self._image:
            self._image = QtGui.QImage(self.image_path)
        return self._image

    @property
    def screenshot(self) -> QtGui.QImage:
        """Provides image drawn on colored canvas with the size of the screen."""
        if self.image.size().toTuple() > self._screen_size.toTuple():
            raise ValueError(
                f"{self.image_path.name} with size {self.image.size().toTuple()} "
                f"is too large for screen size {self._screen_size.toTuple()}!"
            )

        pixmap = QtGui.QPixmap(self._screen_size)
        pixmap.fill(QtCore.Qt.GlobalColor.darkCyan)

        with QtGui.QPainter(pixmap) as painter:
            painter.drawImage(0, 0, self.image)
        return pixmap.toImage()

    @property
    def coords(self) -> tuple[QtCore.QPoint, QtCore.QPoint]:
        size = self.image.size() / self._device_pixel_ratio
        return (
            QtCore.QPoint(1, 1),
            QtCore.QPoint(size.width() - 1, size.height() - 1),
        )


image_dir = Path(__file__).parent

testcases: tuple[TestCase, ...] = (
    TestCase(
        image_path=image_dir / "00_parse_urls.png",
        expected_ocr_text=f"{os.linesep}".join(
            [
                "https://github.com/dynobo/normcap",
                "https://wikipedia.de",
                "https://www.python.com",
                "https://en.wikipedia.org/wiki/Tesseract",
                "https://pypi.org/project/lmdiag/",
            ]
        ),
        expected_ocr_transformers=[Transformer.URL],
    ),
    TestCase(
        image_path=image_dir / "01_parse_colored_url.png",
        expected_ocr_text="https://regex101.com",
        expected_ocr_transformers=[Transformer.URL],
    ),
    TestCase(
        image_path=image_dir / "02_detect_window_title.png",
        expected_ocr_text="*Untitled Document 1",
        expected_ocr_transformers=[Transformer.SINGLE_LINE],
    ),
    TestCase(
        image_path=image_dir / "03_parse_emails.png",
        expected_ocr_text="peter.parker@test.com, HArDToReAd@test.com, 0815@test.com",
        expected_ocr_transformers=[Transformer.MAIL],
    ),
    TestCase(
        image_path=image_dir / "04_parse_email_skip_invalid.png",
        expected_ocr_text=(
            "To: Peter Parker <peter.parker@test.com>; "
            f"HArD To ReAd{os.linesep}"
            "<HArDToReAd@test.com>; "
            "0815 <0815@test.com>; "
            f"Invalid_one <notvalid@test>;{os.linesep}"
            "Invalid_two <also/not/valid/@test.com>; "
            "Invalid_three <@test.com>"
        ),
        expected_ocr_transformers=[Transformer.PARAGRAPH, Transformer.MULTI_LINE],
    ),
    TestCase(
        image_path=image_dir / "05_detect_text_with_low_contrast.png",
        expected_ocr_text="Orange, the new black!",
        expected_ocr_transformers=[Transformer.SINGLE_LINE],
    ),
    TestCase(
        image_path=image_dir / "06_detect_special_characters.png",
        expected_ocr_text=(
            f"'One small step for Man'{os.linesep}"
            f'"Live long and prosper!"{os.linesep}'
            f"«Open the shuttlebay doors»{os.linesep}"
            '"May the Schwartz™ be with you!"'
        ),
        expected_ocr_transformers=[Transformer.PARAGRAPH],
    ),
    TestCase(
        image_path=image_dir / "07_parse_paragraphs_of_text.png",
        expected_ocr_text=(
            "You rent a hotel room. You put a book in the top drawer of the bedside "
            'table and go to sleep. You check out the next morning, but "forget" to '
            f"give back your key. You steal the key!{os.linesep}"
            "A week later, you return to the hotel, do not check in, sneak into your "
            "old room with your stolen key, and look in the drawer. Your book is still "
            f"there. Astonishing!{os.linesep}"
            "How can that be? Aren't the contents of a hotel room drawer inaccessible "
            "if you haven't rented the room?"
        ),
        expected_ocr_transformers=[Transformer.PARAGRAPH],
    ),
    TestCase(
        # https://www.gutenberg.org/cache/epub/1321/pg1321-images.html
        image_path=image_dir / "08_paragraphs.png",
        expected_ocr_text=(
            f"Chapter 17{os.linesep}"
            "The being finished speaking and fixed his looks upon me in the "
            "expectation of a reply. But I was bewildered, perplexed, and "
            "unable to arrange my ideas sufficiently to understand the full extent of "
            f"his proposition. He continued,{os.linesep}"
            '"You must create a female for me with whom I can live in the interchange '
            "of those sympathies necessary for my being. This you "
            "alone can do, and I demand it of you as a right which you must not refuse "
            f'to concede."{os.linesep}'
            "The latter part of his tale had kindled anew in me the anger that had "
            "died away while he narrated his peaceful life among the "
            "cottagers, and as he said this I could no longer suppress the rage that "
            "burned within me."
        ),
        expected_ocr_transformers=[Transformer.PARAGRAPH],
        expected_similarity=0.99,
    ),
    TestCase(
        image_path=image_dir / "09_two_columns.png",
        expected_ocr_text=(
            "Optical character recognition or optical character reader (OCR) is the "
            "electronic or mechanical conversion of images of typed, handwritten or "
            "printed text into machine-encoded text, whether from a scanned document, "
            "a photo of a document, a scene photo (for example the text on signs and "
            "billboards in a landscape photo) or from subtitle text superimposed on an "
            f"image (for example: from a television broadcast).{os.linesep}"
            "Widely used as a form of data entry from printed paper data records — "
            "whether passport documents, invoices, bank statements, computerized "
            "receipts, business cards, mail, printed data, or any suitable "
            "documentation — it is a common method of digitizing printed texts so that "
            "they can be electronically edited, searched, stored more compactly, "
            "displayed online, and used in machine processes such as cognitive "
            "computing, machine translation, (extracted) text-to-speech, key data and "
            "text mining. OCR is a field of research in pattern recognition, "
            f"artificial intelligence and computer vision.{os.linesep}"
            "Early versions needed to be trained with images of each character, and "
            "worked on one font at a time. Advanced systems capable of producing a "
            "high degree of accuracy for most fonts are now common, and with support "
            "for a variety of image file format inputs. Some systems are capable "
            "of reproducing formatted output that closely approximates the original "
            "page including images, columns, and other non-textual components."
        ),
        expected_ocr_transformers=[Transformer.PARAGRAPH],
    ),
    TestCase(
        image_path=image_dir / "10_font_sizes.png",
        expected_ocr_text=(
            "Arial, 8 pt - You only live once, but if you do it right, once is enough."
            f"{os.linesep}"
            "Arial, 11 pt - You only live once, but if you do it right, once is enough."
            f"{os.linesep}"
            "Arial, 14 pt - You only live once, but if you do it right, once is enough."
            f"{os.linesep}"
            "Arial, 16 pt - You only live once, but if you do it right, once is enough."
            f"{os.linesep}"
            "Arial, 22 pt - You only live once, but if you do it right, once is enough."
        ),
        expected_ocr_transformers=[Transformer.PARAGRAPH],
    ),
    TestCase(
        image_path=image_dir / "11_paragraph_with_bullet_points.png",
        expected_ocr_text=(
            f"The desired solution: (to be implemented){os.linesep}"
            'The "Paragraph" heuristic should be improved by taking the dimensions '
            f"of the detection boxes into account:{os.linesep}"
            '- Lines of similar length should indicate "Paragraphs", different length '
            f'indicate "Multilines"{os.linesep}'
            '- Relatively small gaps between lines should indicate "Paragraphs", '
            'larger gaps between lines indicate "Multilines"'
        ),
        expected_ocr_transformers=[Transformer.PARAGRAPH],
    ),
    TestCase(
        image_path=image_dir / "12_not_a_url.png",
        expected_ocr_text="www.normcap.gui",
        expected_ocr_transformers=[Transformer.SINGLE_LINE],
        expected_similarity=0.95,
    ),
)
