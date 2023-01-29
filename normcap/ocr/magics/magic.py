"""Handle loading of available magics, get scores for every magic & apply top scored."""

import logging

from normcap.ocr.magics.email_magic import EmailMagic
from normcap.ocr.magics.multi_line_magic import MultiLineMagic
from normcap.ocr.magics.paragraph_magic import ParagraphMagic
from normcap.ocr.magics.single_line_magic import SingleLineMagic
from normcap.ocr.magics.url_magic import UrlMagic
from normcap.ocr.models import OcrResult

logger = logging.getLogger(__name__)


class Magic:
    """Load available magics, scores, and trigger magic with highest score.

    Arguments:
        AbstractHandler {[type]} -- [description]

    Returns
    -------
        [type] -- [description]
    """

    _magics = {
        "SingleLineMagic": SingleLineMagic(),
        "MultiLineMagic": MultiLineMagic(),
        "ParagraphMagic": ParagraphMagic(),
        "EmailMagic": EmailMagic(),
        "UrlMagic": UrlMagic(),
    }

    def apply(self, ocr_result: OcrResult) -> OcrResult:
        """Load magics, calculate score, execture magic with highest score.

        Arguments:
            AbstractHandler {class} -- self
            capture {Capture} -- NormCap's session data

        Returns
        -------
            Capture -- Enriched NormCap's session data
        """
        # Get score per magic
        ocr_result.magic_scores = self._calc_scores(ocr_result)

        # Transform with best magic
        if best_magic_name := ocr_result.best_scored_magic:
            best_magic = self._magics[best_magic_name]
            ocr_result.parsed = best_magic.transform(ocr_result)

        ocr_result.parsed = self._post_process(ocr_result)
        return ocr_result

    @staticmethod
    def _post_process(ocr_result: OcrResult) -> str:
        """Apply postprocessing to transformed output."""
        transformed = ocr_result.parsed
        # TODO: Check tesseract issue if whitespace workaround still necessary:
        # https://github.com/tesseract-ocr/tesseract/issues/2702
        if ocr_result.tess_args.is_language_without_spaces():
            transformed = transformed.replace(" ", "")
        return transformed

    def _calc_scores(self, ocr_result: OcrResult) -> dict[str, float]:
        """Calculate score for every loaded magic.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns
        -------
            dict -- Scores in format {<magic Name>: <score>}
        """
        scores = {name: magic.score(ocr_result) for name, magic in self._magics.items()}
        logger.debug("Magic scores:\n%s", scores)
        return scores
