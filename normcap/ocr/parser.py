"""Handle loading of available magics, get scores for every magic & apply top scored."""

import logging
import re
from typing import ClassVar

from normcap.ocr.magics.base_magic import BaseMagic
from normcap.ocr.magics.email_magic import EmailMagic
from normcap.ocr.magics.multi_line_magic import MultiLineMagic
from normcap.ocr.magics.paragraph_magic import ParagraphMagic
from normcap.ocr.magics.single_line_magic import SingleLineMagic
from normcap.ocr.magics.url_magic import UrlMagic
from normcap.ocr.models import Magic, OcrResult

logger = logging.getLogger(__name__)


class Parser:
    """Load available magics, scores, and trigger magic with highest score.

    Arguments:
        AbstractHandler {[type]} -- [description]
    """

    _magics: ClassVar[dict[Magic, BaseMagic]] = {
        Magic.SINGLE_LINE: SingleLineMagic(),
        Magic.MULTI_LINE: MultiLineMagic(),
        Magic.PARAGRAPH: ParagraphMagic(),
        Magic.MAIL: EmailMagic(),
        Magic.URL: UrlMagic(),
    }

    def apply(self, ocr_result: OcrResult) -> OcrResult:
        """Load magics, calculate score, execute magic with highest score.

        Args:
            ocr_result: Recognized text and meta information.

        Returns:
            Enriched NormCap's session data.
        """
        # Get score per magic
        ocr_result.magic_scores = self._calc_scores(ocr_result)

        # Transform with best magic
        if best_magic_name := ocr_result.best_scored_magic:
            best_magic = self._magics[best_magic_name]
            ocr_result.parsed = best_magic.transform(ocr_result)

        ocr_result.parsed = self._post_process(ocr_result)
        return ocr_result

    def _post_process(self, ocr_result: OcrResult) -> str:
        """Apply postprocessing to transformed output."""
        text = ocr_result.parsed
        text = self.clean(text)
        # ONHOLD: Check tesseract issue if whitespace workaround still necessary:
        # https://github.com/tesseract-ocr/tesseract/issues/2702
        if ocr_result.tess_args.is_language_without_spaces():
            text = text.replace(" ", "")
        return text

    @staticmethod
    def clean(text: str) -> str:
        """Replace commonly used some utf-8 chars by simplified ones."""
        # Double quotations marks and primes
        text = re.sub(r"[„”“‟″‶ʺ]", '"', text)
        # Singe quotation marks
        text = re.sub(r"[‚‘’‛]", "'", text)  # noqa: RUF001  # ambiguous string
        return text  # noqa: RET504  # unnecessary return for clarity

    def _calc_scores(self, ocr_result: OcrResult) -> dict[Magic, float]:
        """Calculate score for every loaded magic.

        Arguments:
            ocr_result: Recognized text and meta information.

        Returns:
            Scores in format {<magic Name>: <score>}.
        """
        scores = {name: magic.score(ocr_result) for name, magic in self._magics.items()}
        logger.debug("Magic scores:\n%s", scores)
        return scores
