"""Handler to load available magics, get scores for every magic and takes appropriate action."""

from typing import Dict

from normcap.logger import logger
from normcap.magics.email_magic import EmailMagic
from normcap.magics.multi_line_magic import MultiLineMagic
from normcap.magics.paragraph_magic import ParagraphMagic
from normcap.magics.single_line_magic import SingleLineMagic
from normcap.magics.url_magic import UrlMagic
from normcap.models import Capture


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

    def __call__(self, capture: Capture) -> Capture:
        """Load magics, calculate score, execture magic with highest score.

        Arguments:
            AbstractHandler {class} -- self
            capture {Capture} -- NormCap's session data

        Returns:
            Capture -- Enriched NormCap's session data
        """
        if capture.mode == "raw":  # Skip all magics, if raw mode enabled
            capture.scores = {}
            capture.best_magic = "N/A"
            capture.transformed = capture.text
        else:
            # Get score per magic
            capture.scores = self._calc_scores(capture)

            # Select winning magic
            best_magic_name = self._get_best_magic(capture.scores)
            capture.best_magic = best_magic_name

            # Transform with best magic
            best_magic = self._magics[best_magic_name]
            capture.transformed = best_magic.transform(capture)

        return capture

    def _calc_scores(self, capture: Capture) -> Dict[str, float]:
        """Calculate score for every loaded magic.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns:
            dict -- Scores in format {<magic Name>: <score>}
        """
        scores = {}
        for name, magic in self._magics.items():
            scores[name] = magic.score(capture)

        logger.debug(f"All scores: {scores}")
        return scores

    @staticmethod
    def _get_best_magic(scores) -> str:
        """Get magic with highest score.

        Arguments:
            scores {dicr} -- Scores in format {<magic Name>: <score>}

        Returns:
            str -- Name of best magic
        """
        sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

        best_magic = sorted_scores[0][0]
        best_score = sorted_scores[0][1]
        logger.info(f"Highest scored magic: {best_magic} ({best_score})")

        return best_magic


apply_magic = ApplyMagic()
