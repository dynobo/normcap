"""Handler to show screenshots and gui to select region of interest."""

# Default
import logging
import tkinter
import sys

# Extra
from PIL import ImageTk  # type: ignore

# Own
from normcap.common.data_model import NormcapData
from normcap.handlers.abstract_handler import AbstractHandler


class CropHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        """Show GUI to select region and return selected image.

        Arguments:
            AbstractHandler {class} -- self
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- Enriched NormCap's session data
        """
        if not request.test_mode:
            self._logger.info("Starting GUI for area selection...")
            request = self._select_region_with_gui(request)
        else:
            self._logger.info("Test mode. Skipping gui selection...")

        self._logger.info("Cropping image...")
        request = self._crop_image(request)  # Test should jump in here

        self._logger.debug("Dataclass after image cropped:%s", request)

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def _select_region_with_gui(self, request: NormcapData) -> NormcapData:
        """Show window(s) with screenshots and select region.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            dict -- Selected region {"bottom": <int>,
                                     "top": <int>,
                                     "left": <int>,
                                     "right": <int>,
                                     "monitor": <int>,
                                     "mode": <int>}
        """
        # Create window for every monitor
        root = tkinter.Tk()
        for idx, shot in enumerate(request.shots):
            if idx == 0:
                _CropWindow(root, root, shot, request.cli_args)
            else:
                top = tkinter.Toplevel()
                _CropWindow(root, top, shot, request.cli_args)
        root.mainloop()

        # Store result in request class
        result = root.result
        if result:
            request.bottom = result["lower"]
            request.top = result["upper"]
            request.left = result["left"]
            request.right = result["right"]
            request.monitor = result["monitor"]
            request.mode = result["mode"]
        else:
            self._logger.info("Exiting. No selection done.")
            sys.exit(0)

        return request

    def _crop_image(self, request: NormcapData) -> NormcapData:
        """Crop monitor's image and append to session data.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- Enriched NormCap's session data
        """
        img = request.shots[request.monitor]
        cropped_img = img["image"].crop(
            (request.left, request.top, request.right, request.bottom)
        )
        request.image = cropped_img
        return request


class _CropWindow:
    # TODO: Docstrings
    def __init__(self, root, current_window, shot, cli_args):
        self.logger = logging.getLogger(__name__)
        self.tk = current_window
        self.root = root
        self.cli_args = cli_args

        if root == current_window:
            self.root = self._init_root_vars(self.root)

        self.tk.configure(bg="black")  # To hide top border on i3
        self.shot = shot

        self._show_window()
        self._draw_border()
        self._set_bindings()
        self._set_window_geometry()
        self._set_fullscreen()

    def _init_root_vars(self, root):
        root.active_canvas = None

        root.rect = None
        root.start_x = 0
        root.start_y = 0
        root.x = 0
        root.y = 0

        root.mode_indicator = None
        root.modes = ("raw", "parse")
        root.modes_chars = ("☰", "☶")
        root.current_mode = self.cli_args["mode"]

        root.color = self.cli_args["color"]
        root.img_path = self.cli_args["path"]

        return root

    def _set_fullscreen(self):
        # Set Fullscreen
        #    Behave different per OS, because:
        #    - with tk.attributes I couldn't move the windows to the correct screen on MS Windows
        #    - with overrideredirect I couldn't get the keybindings working on Linux
        # TODO: Move platform detection to beginning, add to dataclass
        if sys.platform.startswith("win"):
            self.tk.overrideredirect(1)

        if sys.platform.startswith("darwin"):
            self.tk.overrideredirect(1)
            self.tk.attributes("-fullscreen", 1)
            self.tk.attributes("-topmost", 1)
            # os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "python" to true' ''')
            # self.tk.focus_force()
            # self.tk.call("::tk::unsupported::MacWindowStyle", "style", self.tk._w, "plain", "none")

        if sys.platform.startswith("linux"):
            self.tk.attributes("-fullscreen", True)

    def _show_window(self):
        # Produces frame, useful for debug
        self.frame = tkinter.Frame(self.tk)
        self.frame.pack()

        # Create canvas
        self.canvas = tkinter.Canvas(
            self.tk,
            bg=self.root.color,
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

    def _draw_border(self):
        self.canvas.create_rectangle(
            0,
            0,
            self.shot["position"]["width"] - 1,
            self.shot["position"]["height"] - 2,
            width=3,
            outline=self.root.color,
        )

    def _set_window_geometry(self):
        self.tk.geometry(
            f"{self.shot['position']['width']}x{self.shot['position']['height']}"
            + f"+{self.shot['position']['left']}+{self.shot['position']['top']}"
        )

    def _set_bindings(self):
        self.root.bind_all("<Escape>", self._on_escape_press)
        self.root.bind_all("<space>", self._on_space_press)
        self.canvas.bind("<B1-Motion>", self._on_move_press)
        self.canvas.bind("<ButtonPress-1>", self._on_button_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)

    def _end_fullscreen(self, result=None):
        self.root.result = result
        self.root.destroy()

    def _next_mode(self):
        idx = self.root.modes.index(self.root.current_mode)
        idx += 1
        if idx >= len(self.root.modes):
            idx = 0
        self.root.current_mode = self.root.modes[idx]

    def _get_mode_char(self):
        idx = self.root.modes.index(self.root.current_mode)
        return self.root.modes_chars[idx]

    def _get_top_right(self):
        top = min([self.root.start_y, self.root.y])
        right = max([self.root.start_x, self.root.x])
        return top, right

    def _on_escape_press(self, event):
        self.logger.info("ESC pressed: Aborting screen capture")
        self._end_fullscreen()

    def _on_space_press(self, event):
        self._next_mode()
        if self.root.mode_indicator:
            self.root.active_canvas.itemconfig(
                self.root.mode_indicator, text=self._get_mode_char()
            )

    def _on_button_press(self, event):
        # save mouse start position
        self.root.start_x = self.canvas.canvasx(event.x)
        self.root.start_y = self.canvas.canvasy(event.y)

        # initially create rectangle
        if not self.root.rect:
            # Draw outline
            self.root.rect = self.canvas.create_rectangle(
                self.root.x, self.root.y, 1, 1, outline=self.root.color
            )
            # Draw indicator
            self.root.mode_indicator = self.canvas.create_text(
                self.root.start_x,
                self.root.start_y,
                anchor="se",
                text=self._get_mode_char(),
                fill=self.root.color,
                font=("Sans", 18),
            )
            self.root.active_canvas = self.canvas

    def _on_move_press(self, event):
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

        # Move indicator
        top, right = self._get_top_right()
        self.canvas.coords(self.root.mode_indicator, right, top)

    def _on_button_release(self, event):
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

        self._end_fullscreen(result=crop_args)
