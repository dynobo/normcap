"""
"""

# Own
from handlers.abstract_handler import AbstractHandler
from data_model import NormcapData


class EnhanceImgHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        self._logger.info("Applying enhancements to image...")

        request.image = self._enlarge_dpi(request.image)

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def _enlarge_dpi(self, img):
        # Most display are around ~100dpi
        # Tesseract works best ~300dpi
        # TODO: adapt factor based on actual screen resolution
        factor = 3
        width, height = img.size
        img = img.resize((width * factor, height * factor))
        self._logger.info(f"Resized screenshot by factor {factor}")

        return img
