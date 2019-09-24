"""Handler responsible to optimize the captured image for OCR."""

# Extra
import PIL

# Own
from handlers.abstract_handler import AbstractHandler
from data_model import NormcapData


class EnhanceImgHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        """Execute chain of optimizations.

        Arguments:
            AbstractHandler {class} -- self
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- NormCap's session data with optimized image
        """
        self._logger.info("Applying enhancements to image...")

        # Currently, the image is only enlarged
        request.image = self._enlarge_dpi(request.image)

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def _enlarge_dpi(self, img: PIL.Image) -> PIL.Image:
        """Resize image to get equivalent of 300dpi.
        Reason: Most display are around ~100dpi, while Tesseract works best ~300dpi.

        Arguments:
            img {PIL.Image} -- [Input image to enlarge

        Returns:
            PIL.Image -- Enlarged image
        """
        # TODO: adapt factor based on actual screen resolution
        factor = 3
        width, height = img.size
        img = img.resize((width * factor, height * factor))
        self._logger.info("Resized screenshot by factor %s", factor)

        return img
