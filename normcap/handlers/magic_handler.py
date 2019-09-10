"""Handler to load available magics, get scores for every magic and takes appropriate action."""

# Own
from handlers.abstract_handler import AbstractHandler
from data_model import NormcapData


class MagicHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        """Load magics, calculate score, execture magic with highest score.

        Arguments:
            AbstractHandler {class} -- self
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- Enriched NormCap's session data
        """
        if request.mode != "raw":  # Skip all magics, if raw mode enabled
            # Import magics here (to only load, when needed)!
            from magics.single_line_magic import SingleLineMagic
            from magics.paragraph_magic import ParagraphMagic
            from magics.email_magic import EmailMagic
            from magics.url_magic import UrlMagic

            # Load Magics
            self._magics = {
                "single_line": SingleLineMagic(),
                "paragraph_magic": ParagraphMagic(),
                "email": EmailMagic(),
                "url_magic": UrlMagic(),
            }

            # Calculate scores
            scores = self._calc_scores(request)
            request.scores = scores

            # Select winning magic
            best_magic = self._get_best_magic(scores)

            # Transform with best magic
            request.transformed = self._magics[best_magic].transform(request)

            # In trigger mode, run magics action
            if request.mode == "trigger":
                self._magics[best_magic].trigger(request)

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def _calc_scores(self, request: NormcapData) -> dict:
        """Calculate score for every loaded magic.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            dict -- Scores in format {<magic Name>: <score>}
        """
        scores = {}
        for name, magic in self._magics.items():
            scores[name] = magic.score(request)
        self._logger.info(f"All scores: {scores}")
        return scores

    def _get_best_magic(self, scores) -> str:
        """Get magic with highest score.

        Arguments:
            scores {dicr} -- Scores in format {<magic Name>: <score>}

        Returns:
            str -- Name of best magic
        """
        sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

        best_magic = sorted_scores[0][0]
        best_score = sorted_scores[0][1]
        self._logger.info(f"Highest scored magic: {best_magic} ({best_score})")

        return best_magic
