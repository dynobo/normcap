"""

"""
# Default
import logging
import tkinter
import sys
import os

# Extra
from PIL import ImageTk


class Crop:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def select_and_crop(self, selection):
        selection = self._select_region_with_gui(selection)
        selection = self._crop_image(selection)
        return selection

    def _select_region_with_gui(self, selection):

        # Create window for every monitor
        root = tkinter.Tk()
        for idx, shot in enumerate(selection.shots):
            if idx == 0:
                _FullscreenWindow(root, root, shot)
            else:
                top = tkinter.Toplevel()
                _FullscreenWindow(root, top, shot)
        root.mainloop()

        # Store result in selection class
        result = root.result
        if result:
            selection.bottom = result["lower"]
            selection.top = result["upper"]
            selection.left = result["left"]
            selection.right = result["right"]
            selection.monitor = result["monitor"]
            selection.mode = result["mode"]
        else:
            self.logger.info("Exiting. No selection available.")
            sys.exit(0)

        return selection

    def _crop_image(self, selection):
        crop_monitor = selection.shots[selection.monitor]
        cropped_image = crop_monitor["image"].crop(
            (selection.left, selection.top, selection.right, selection.bottom)
        )
        selection.image = cropped_image
        return selection


class _FullscreenWindow:
    def __init__(self, root, current_window, shot):
        self.logger = logging.getLogger(__name__)
        self.tk = current_window
        self.root = root

        if root == current_window:
            self.init_root_vars()

        self.tk.configure(bg="black")  # To hide top border on i3
        self.shot = shot

        self.show_windows()
        self.draw_border()
        self.set_bindings()
        self.set_window_geometry()
        self.set_fullscreen()

    def init_root_vars(self):
        self.root.active_canvas = None

        self.root.rect = None
        self.root.start_x = 0
        self.root.start_y = 0
        self.root.x = 0
        self.root.y = 0

        self.root.mode_indicator = None
        self.root.modes = ("raw", "parse", "trigger")
        # "☷" https://en.wikipedia.org/wiki/Miscellaneous_Symbols
        self.root.modes_chars = ("☰", "⚙", "★")
        self.root.current_mode = self.root.modes[0]

        self.root.area_thres = 400

    def set_fullscreen(self):
        # Set Fullscreen
        #    Behave different per OS, because:
        #    - with tk.attributes I couldn't move the windows to the correct screen on MS Windows
        #    - with overrideredirect I couldn't get the keybindings working on Linux
        if os.name == "nt":
            self.tk.overrideredirect(1)
        else:
            self.tk.attributes("-fullscreen", True)

    def next_mode(self):
        idx = self.root.modes.index(self.root.current_mode)
        idx += 1
        if idx >= len(self.root.modes):
            idx = 0
        self.root.current_mode = self.root.modes[idx]

    def get_mode_char(self):
        idx = self.root.modes.index(self.root.current_mode)
        return self.root.modes_chars[idx]

    def set_window_geometry(self):
        self.tk.geometry(
            f"{self.shot['position']['width']}x{self.shot['position']['height']}"
            + f"+{self.shot['position']['left']}+{self.shot['position']['top']}"
        )

    def set_bindings(self):
        self.root.bind_all("<Escape>", self.on_escape_press)
        self.root.bind_all("<space>", self.on_space_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_space_press(self, event):
        self.next_mode()
        if self.root.mode_indicator:
            self.root.active_canvas.itemconfig(
                self.root.mode_indicator, text=self.get_mode_char()
            )

    def show_windows(self):
        # Produces frame, useful for debug
        self.frame = tkinter.Frame(self.tk)
        self.frame.pack()

        # Create canvas
        self.canvas = tkinter.Canvas(
            self.tk,
            bg="red",
            width=self.shot["position"]["width"],
            height=self.shot["position"]["height"],
            highlightthickness=0,
            borderwidth=0,
            relief="flat",
            cursor="cross",
        )
        self.canvas.pack(expand=tkinter.YES, fill=tkinter.BOTH)

        # Add image to canvas
        tkimage = ImageTk.PhotoImage(self.shot["image"])
        self.screen_gc = tkimage  # Prevent img being garbage collected
        self.canvas.create_image(0, 0, anchor="nw", image=tkimage)

    def draw_border(self):
        self.canvas.create_rectangle(
            0,
            0,
            self.shot["position"]["width"] - 1,
            self.shot["position"]["height"] - 2,
            width=3,
            outline="red",
        )

    def on_escape_press(self, event):
        self.logger.info("ESC pressed: Aborting screen capture")
        self.end_fullscreen()

    def is_valid_selected_area(self, position):
        # Calculate selected area
        if position is not None:
            area = (position["lower"] - position["upper"]) * (
                position["right"] - position["left"]
            )
        else:
            area = 0

        # Check for threshold
        if area >= self.root.area_thres:
            large_enough = True
        else:
            large_enough = False
            self.logger.warn(
                f"Selection area of {area:.0f} px² is below threshold of {self.root.area_thres} px²]"
            )

        return large_enough

    def end_fullscreen(self, result=None):
        if self.is_valid_selected_area(result):
            self.root.result = result
        else:
            self.root.result = None
        self.root.destroy()

    def get_top_right(self):
        top = min([self.root.start_y, self.root.y])
        right = max([self.root.start_x, self.root.x])
        return top, right

    def on_button_press(self, event):
        # save mouse start position
        self.root.start_x = self.canvas.canvasx(event.x)
        self.root.start_y = self.canvas.canvasy(event.y)

        # create rectangle
        if not self.root.rect:
            # Draw outline
            self.root.rect = self.canvas.create_rectangle(
                self.root.x, self.root.y, 1, 1, outline="red"
            )
            # Draw indicator
            self.root.mode_indicator = self.canvas.create_text(
                self.root.start_x,
                self.root.start_y,
                anchor="se",
                text=self.get_mode_char(),
                fill="red",
                font=("Sans", 18),
            )
            self.root.active_canvas = self.canvas

    def on_move_press(self, event):
        self.root.x = self.canvas.canvasx(event.x)
        self.root.y = self.canvas.canvasy(event.y)

        # expand rectangle as you drag the mouse
        self.canvas.coords(
            self.root.rect,
            self.root.start_x,
            self.root.start_y,
            self.root.x,
            self.root.y,
        )
        # self.canvas.itemconfig(self.root.mode_indicator, text=self.get_mode_char())

        # Move indicator
        top, right = self.get_top_right()
        self.canvas.coords(self.root.mode_indicator, right, top)

    def on_button_release(self, event):
        self.root.x = self.canvas.canvasx(event.x)
        self.root.y = self.canvas.canvasy(event.y)

        crop_args = {
            "monitor": self.shot["monitor"],
            "upper": min([self.root.y, self.root.start_y]),
            "lower": max([self.root.y, self.root.start_y]),
            "left": min([self.root.x, self.root.start_x]),
            "right": max([self.root.x, self.root.start_x]),
            "mode": self.root.current_mode,
        }

        self.end_fullscreen(result=crop_args)
