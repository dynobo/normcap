"""Magic Class to handle multi line text selection."""

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
        """Just transform into multiple lines of text.

        TODO: I think in most cases, the user expect to retrieve a single
        line without the linebreaks in between. I should try to distinguish that
        based on the line lengths.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            str -- Lines of text
        """
        # Just return concatenated text
        return request.lines
