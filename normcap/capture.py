"""
"""
# Default

# Extra
import mss
import pyautogui


class Capture:
    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def captureScreen(self):
        with mss.mss() as sct:
            filename = sct.shot(mon=-1, output="fullscreen.png")
            print(filename)
        return

    def getMousePos(self):
        return pyautogui.position()

    def captureScreenWx(self):
        # See https://wiki.wxpython.org/WorkingWithImages#A_Flexible_Screen_Capture_App
        pass
