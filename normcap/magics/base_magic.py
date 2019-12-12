"""Base class for templating magics."""

# Default
import logging

# Own
from normcap.common.data_model import NormcapData


class BaseMagic:
    name = "base"

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._final_score = 0  # Initial score

    def score(self, request: NormcapData) -> float:
        """Calculate the score of a magic.

        Score should be between 0-100, where 0 means 'should never be handled
        by this magic' and 100 mean 'should certainly handled by this magic'.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            float -- score between 0-100 (100 = more likely)
        """
        return 0.0

    def transform(self, request: NormcapData) -> str:
        """Transform detected lineboxes into single(!) string.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            str -- String to be copied to clipboard
        """
        return ""


# from statistics import variance

# class LineBoxStats:
#     def __init__(self):
#         self._logger = logging.getLogger(self.__class__.__name__)

#     # TODO: Move stats to data_model?
#     def get_line_heights(self, request):
#         line_boxes = request.line_boxes  # shorthand
#         line_heights = [l.position[1][1] - l.position[0][1] for l in line_boxes]
#         self._logger.info(f"{line_heights}, {variance(line_heights)}")
#         return line_heights

#     def get_line_distances(self, request):
#         line_boxes = request.line_boxes  # shorthand

#         positions_top = [l.position[0][1] for l in line_boxes]
#         positions_bottom = [l.position[1][1] for l in line_boxes]
#         positions_left = [l.position[0][0] for l in line_boxes]
#         positions_right = [l.position[1][0] for l in line_boxes]

#         line_distances = list(
#             map(float.__sub__, positions_top[1:], positions_bottom[:-1])
#         )

#         self._logger.info(f"{line_distances}, {variance(line_distances)}")
#         self._logger.info(positions_top)
#         self._logger.info(positions_bottom)
#         self._logger.info(f"{positions_left}, {variance(positions_left)}")
#         self._logger.info(f"{positions_right}, {variance(positions_right)}")

#         return line_distances
