"""Handler to load available magics, get scores for every magic and takes appropriate action."""

import logging

from normcap.ocr.magics.email_magic import EmailMagic
from normcap.ocr.magics.multi_line_magic import MultiLineMagic
from normcap.ocr.magics.paragraph_magic import ParagraphMagic
from normcap.ocr.magics.single_line_magic import SingleLineMagic
from normcap.ocr.magics.url_magic import UrlMagic
from normcap.ocr.models import OcrResult

logger = logging.getLogger(__name__)


class ApplyMagic:
    """Loads available magics, scores, and trigger magic with highest score.

    Arguments:
        AbstractHandler {[type]} -- [description]

    Returns:
        [type] -- [description]
    """

    _magics = {
        "SingleLineMagic": SingleLineMagic(),
        "MultiLineMagic": MultiLineMagic(),
        "ParagraphMagic": ParagraphMagic(),
        "EmailMagic": EmailMagic(),
        "UrlMagic": UrlMagic(),
    }

    def __call__(self, ocr_result: OcrResult) -> OcrResult:
        """Load magics, calculate score, execture magic with highest score.

        Arguments:
            AbstractHandler {class} -- self
            capture {Capture} -- NormCap's session data

        Returns:
            Capture -- Enriched NormCap's session data
        """
        # Get score per magic
        ocr_result.magic_scores = self._calc_scores(ocr_result)

        # Transform with best magic
        if best_magic_name := ocr_result.best_scored_magic:
            best_magic = self._magics[best_magic_name]
            ocr_result.transformed = best_magic.transform(ocr_result)

        ocr_result.transformed = self._post_process(ocr_result)
        return ocr_result

    @staticmethod
    def _post_process(ocr_result: OcrResult) -> str:
        """Apply postprocessing to transformed output."""
        transformed = ocr_result.transformed
        selected_languages = set(ocr_result.tess_args.lang)
        # TODO: Check if still necessary:
        # https://github.com/tesseract-ocr/tesseract/issues/2702
        languages_with_superfluous_spaces = {
            "chi_sim",
            "chi_sim_vert",
            "chi_tra",
            "chi_tra_vert",
        }
        if selected_languages.issubset(languages_with_superfluous_spaces):
            transformed = transformed.replace(" ", "")
        return transformed

    def _calc_scores(self, ocr_result: OcrResult) -> dict[str, float]:
        """Calculate score for every loaded magic.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns:
            dict -- Scores in format {<magic Name>: <score>}
        """
        scores = {name: magic.score(ocr_result) for name, magic in self._magics.items()}
        logger.debug("All scores: %s", scores)
        return scores


apply_magic = ApplyMagic()
