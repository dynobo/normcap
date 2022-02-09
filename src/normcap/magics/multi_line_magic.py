"""Magic Class to handle multi line text selection."""

from normcap.magics.base_magic import BaseMagic
from normcap.models import Capture


class MultiLineMagic(BaseMagic):
    """Format multi line text."""

    def score(self, capture: Capture) -> float:
        """Calc score based on amount of lines and breaks

        Arguments:
            BaseMagic {class} -- Base class for magics
            capture {Capture} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        if (
            (capture.num_lines > 1)
            and (capture.num_blocks == 1)
            and (capture.num_pars == 1)
        ):
            self._final_score = 50.0

        return self._final_score

    def transform(self, capture: Capture) -> str:
        """Just transform into multiple lines of text.

        Arguments:
            capture {Capture} -- NormCap's session data

        Returns:
            str -- Lines of text
        """
        # Just return concatenated text
        return capture.lines
