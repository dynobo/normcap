"""Magic Class to handle very simple single line text selection."""

# Own
from normcap.magics.base_magic import BaseMagic
from normcap.common.data_model import NormcapData


class MultiLineMagic(BaseMagic):

    name = "multi_line"

    def score(self, request: NormcapData) -> float:
        """Calc score based on amount of lines and breaks

        Arguments:
            BaseMagic {class} -- Base class for magics
            request {NormcapData} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        if (
            (request.num_lines > 1)
            and (request.num_blocks == 1)
            and (request.num_pars == 1)
        ):
            self._final_score = 50.0

        return self._final_score

    def transform(self, request: NormcapData) -> str:
        """Just transform into single line of text.

        I think in most cases, the user expect to retrieve a single
        line without the linebreaks in between.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            str -- Single line of text
        """
        # Just return concatenated text
        return request.text
