from magics.base_magic import BaseMagic


class SingleLineMagic(BaseMagic):
    def score(self, request):
        lines = len(request.line_boxes)
        if lines == 1:
            self._final_score = 50

        return self._final_score

    def transform(self, request):
        # Just return concatenated text
        # TODO: Maybe remove unnecessary whitespace?
        return request.text
