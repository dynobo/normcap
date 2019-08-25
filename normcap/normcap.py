"""
"""
# Default

# Extra

# Own
from normcap.capture import Capture

if __name__ == "__main__":
    cap = Capture()
    # rect = cap.getRectangle()
    # print(rect)
    cap.capture_screen(2)
    cap.show_window()
