from magics.base_magic import BaseMagic


class ParagraphMagic(BaseMagic):
    def score(self, request):
        lines = len(request.line_boxes)
        self._final_score = 100 - (1 / lines * 100)

        # TODO: Handle Paragraphs
        #  E.g. check for single justified paragraph
        # - Similar right and left bounderies (not for last line)
        # - Similar vertical distance between lines

        return self._final_score

    def transform(self, request):
        # Just use concatenated text for now.
        # TODO: Maybe remove unnecessary whitespace
        return request.text
