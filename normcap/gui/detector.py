import logging

from PySide6 import QtCore, QtGui

from normcap.detection import detector
from normcap.detection.models import DetectionMode
from normcap.system import info

logger = logging.getLogger(__name__)


class Communicate(QtCore.QObject):
    on_result = QtCore.Signal(list)
    on_finished = QtCore.Signal()


class DetectionWorker(QtCore.QObject):
    """Worker to do the (potentially) long running text/code detection in a QThread."""

    def __init__(
        self,
        image: QtGui.QImage,
        detect_text: bool,
        detect_codes: bool,
        parse_text: bool,
        language: str,
    ) -> None:
        super().__init__()
        self.com = Communicate()

        self.image = image
        self.parse_text = parse_text
        self.language = language

        self.detection_mode = DetectionMode(0)
        if detect_codes:
            self.detection_mode |= DetectionMode.CODES
        if detect_text:
            self.detection_mode |= DetectionMode.TESSERACT

    def run_detection(self) -> None:
        tessdata_path = info.get_tessdata_path(
            config_directory=info.config_directory(),
            is_packaged=info.is_packaged(),
        )
        tesseract_bin_path = info.get_tesseract_bin_path(
            is_briefcase_package=info.is_briefcase_package()
        )

        try:
            results = detector.detect(
                image=self.image,
                tesseract_bin_path=tesseract_bin_path,
                tessdata_path=tessdata_path,
                language=self.language,
                detect_mode=self.detection_mode,
                parse_text=self.parse_text,
            )
        except Exception:
            logger.exception("Detection failed!")
            results = []

        self.com.on_result.emit(results)
        self.com.on_finished.emit()
