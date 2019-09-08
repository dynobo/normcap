"""MagicHandler loads available magics, get scores for every magic and takes appropriate action.
"""


# Own
from handlers.abstract_handler import AbstractHandler
from data_model import NormcapData


class MagicHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        if request.mode != "raw":  # Skip all magics, if raw mode enabled
            # Import magics here (to only load, when needed)!
            from magics.single_line_magic import SingleLineMagic
            from magics.email_magic import EmailMagic

            # Load Magics
            self._magics = {"email": EmailMagic(), "single_line": SingleLineMagic()}

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

    def _calc_scores(self, request):
        scores = {}
        for name, magic in self._magics.items():
            scores[name] = magic.score(request)
        self._logger.info(f"All scores: {scores}")
        return scores

    def _get_best_magic(self, scores):
        sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        best_magic = sorted_scores[0][0]
        best_score = sorted_scores[0][1]
        self._logger.info(f"Highest scored magic: {best_magic} ({best_score})")
        return best_magic
