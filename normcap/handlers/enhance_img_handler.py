"""Handler responsible to optimize the captured image for OCR."""

# Extra
from PIL import Image, ImageOps  # type: ignore

# Own
from normcap.common.data_model import NormcapData
from normcap.handlers.abstract_handler import AbstractHandler


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
        if request.image:
            request.image = self._enlarge_dpi(request.image)
        # request.image = self._add_padding(request.image)
        # request.image = self._strech_contrast(request.image)

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def _grayscale(self, img: Image.Image) -> Image.Image:
        img = img.convert("L")
        return img

    def _strech_contrast(self, img: Image.Image) -> Image.Image:
        img = ImageOps.autocontrast(img)
        return img

    def _add_padding(self, img: Image.Image) -> Image.Image:
        bg_col = self._most_frequent_colour(img)
        img = ImageOps.expand(img, border=20, fill=bg_col)
        return img

    def _most_frequent_colour(self, img):
        w, h = img.size
        pixels = img.getcolors(w * h)
        most_frequent_pixel = pixels[0]
        for count, colour in pixels:
            if count > most_frequent_pixel[0]:
                most_frequent_pixel = (count, colour)
        return most_frequent_pixel[1]

    def _enlarge_dpi(self, img: Image.Image) -> Image.Image:
        """Resize image to get equivalent of 300dpi.
        Reason: Most display are around ~100dpi, while Tesseract works best ~300dpi.

        Arguments:
            img {PIL.Image} -- [Input image to enlarge

        Returns:
            PIL.Image -- Enlarged image
        """
        # TODO: adapt factor based on actual screen resolution
        factor = 4
        width, height = img.size
        img = img.resize((width * factor, height * factor))
        self._logger.info("Resized screenshot by factor %s", factor)

        return img
