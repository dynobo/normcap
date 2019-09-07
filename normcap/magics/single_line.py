from magics.base_magic import BaseMagic


class SingleLineMagic(BaseMagic):
    def score(self, request):
        self._final_score = 0.1

        lines = len(request.line_boxes)
        if lines == 1:
            self._final_score = 10

        # Check for single justified paragraph
        # - Similar right and left bounderies (not for last line)
        # - Similar vertical distance between lines

        # TODO: Move Stats to BaseClass!

        # line_distances = list(
        #     map(float.__sub__, positions_top[1:], positions_bottom[:-1])
        # )

        # Line heights shouldn't vary more than ~70%

        # request.line_boxes

        return self._final_score

    def transform(self, request):
        # Just use concatenated text for now.
        # TODO: Maybe remove unnecessary whitespace
        return request.text
