"""
"""
# Default
import sys

# Extra
import mss
from pymouse import PyMouseEvent


class event(PyMouseEvent):
    def __init__(self):
        self.clicks = []
        super(event, self).__init__()

    def click(self, x, y, button, press):
        if press:
            self.clicks.append((x, y))
        if len(self.clicks) >= 2:
            sys.exit()  # Workaround, as self.stop() not responding on Linux


class Capture:
    def __init__(self, *args, **kwargs):
        self.clicks = []
        return super().__init__(*args, **kwargs)

    def captureScreen(self, rectangle):
        with mss.mss() as sct:
            output = "temp.png".format(**rectangle)

            sct_img = sct.grab(rectangle)

            # Save to the picture file
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
            print(output)

        return

    def clicksToRectangle(self, clicks):
        x1, y1 = clicks[0]
        x2, y2 = clicks[1]
        rectangle = {
            "top": min(y1, y2),
            "left": min(x1, x2),
            "width": abs(x1 - x2),
            "height": abs(y1 - y2),
        }
        return rectangle

    def getRectangle(self):
        e = event()
        e.capture = True
        e.daemon = False
        e.start()
        e.join()
        return self.clicksToRectangle(e.clicks)
