import logging
from statistics import variance


class BaseMagic:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._final_score = 0
        self._stats = LineBoxStats()

    def score(self, request):
        pass

    def transform(self, request):
        pass

    def trigger(self, request):
        pass


class LineBoxStats:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    # TODO: Move stats to data_model?
    def get_line_heights(self, request):
        line_boxes = request.line_boxes  # shorthand
        line_heights = [l.position[1][1] - l.position[0][1] for l in line_boxes]
        self._logger.info(f"{line_heights}, {variance(line_heights)}")
        return line_heights

    def get_line_distances(self, request):
        line_boxes = request.line_boxes  # shorthand

        positions_top = [l.position[0][1] for l in line_boxes]
        positions_bottom = [l.position[1][1] for l in line_boxes]
        positions_left = [l.position[0][0] for l in line_boxes]
        positions_right = [l.position[1][0] for l in line_boxes]

        line_distances = list(
            map(float.__sub__, positions_top[1:], positions_bottom[:-1])
        )

        self._logger.info(f"{line_distances}, {variance(line_distances)}")
        self._logger.info(positions_top)
        self._logger.info(positions_bottom)
        self._logger.info(f"{positions_left}, {variance(positions_left)}")
        self._logger.info(f"{positions_right}, {variance(positions_right)}")

        return line_distances
