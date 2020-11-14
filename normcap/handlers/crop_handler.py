"""Handler to show screenshots and gui to select region of interest."""

# Default
import logging
import time
import tkinter
import sys
from dataclasses import dataclass
from typing import Optional
import webbrowser

# Extra
from PIL import ImageTk  # type: ignore

# Own
from normcap import __version__
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
        # Create dummy window plus one for every monitor
        root = _RootWindow(request.cli_args, request.platform)
        for shot in request.shots:
            _CropWindow(root, shot)
        root.mainloop()

        # Store result in request class
        result = root.props.crop_result
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

    @staticmethod
    def _crop_image(request: NormcapData) -> NormcapData:
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


@dataclass()
class WindowProps:
    """Stores data relevant to the gui interaction."""

    platform: str = ""
    monitor: Optional[int] = None
    active_canvas = None
    rect = None

    start_mouse_x: int = 0
    start_mouse_y: int = 0
    mouse_x: int = 0
    mouse_y: int = 0

    mode_indicator = None
    modes = ("raw", "parse")
    modes_chars = ("☰", "☶")

    current_mode: str = "parse"
    color: str = "#ff0000"
    img_path: Optional[str] = None

    @property
    def mode_char(self) -> str:
        """Return mod_char of current_mode from modes_chars."""
        idx = self.modes.index(self.current_mode)
        return self.modes_chars[idx]

    @property
    def crop_result(self) -> Optional[dict]:
        """Return dict which is passed into NormcapData as result of crop handler."""
        if self.monitor is not None:
            return {
                "monitor": self.monitor,
                "upper": min([self.mouse_y, self.start_mouse_y]),
                "lower": max([self.mouse_y, self.start_mouse_y]),
                "left": min([self.mouse_x, self.start_mouse_x]),
                "right": max([self.mouse_x, self.start_mouse_x]),
                "mode": self.current_mode,
            }
        return None


class _RootWindow(tkinter.Tk):
    """Dummy Root Window.

    This is necessary, because when in Mac and Linux windows are started
    with overrideredict(1) they can't receive keyboard events anymore.
    This dummy window should stay in the background and receive those events,
    while the "main" windows showing the screenshots should overlay it on
    top.
    """

    def __init__(self, cli_args, platform):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.props = WindowProps()
        self.props.current_mode = cli_args["mode"]
        self.props.color = cli_args["color"]
        self.props.img_path = cli_args["path"]
        self.props.platform = platform

        self._show_dummy_window()
        self._set_bindings()
        self._set_window_geometry()

    def _show_dummy_window(self):
        tkinter.Label(
            self, text=f"Normcap v{__version__} ({self.props.platform})"
        ).pack()
        tkinter.Label(
            self,
            text=(
                "This is a dummy window and should not be visible to you."
                "If you see it nevertheless, please file an issue on:"
            ),
        ).pack()
        link_label = tkinter.Label(
            self,
            text=r"https://github.com/dynobo/normcap/issues",
            fg="blue",
            cursor="hand2",
        )
        link_label.pack()
        link_label.bind("<Button-1>", self._open_github_issues)

    @staticmethod
    def _open_github_issues(event):
        webbrowser.open_new(event.widget.cget("text"))

    def _set_window_geometry(self):
        self.geometry("150x100+10+10")

    def _set_bindings(self):
        self.bind_all("<Escape>", self._on_escape_press)
        self.bind_all("<space>", self._on_space_press)

    def _next_mode(self):
        idx = self.props.modes.index(self.props.current_mode)
        idx += 1
        if idx >= len(self.props.modes):
            idx = 0
        self.props.current_mode = self.props.modes[idx]

    def _on_escape_press(self, _):
        self.logger.info("ESC pressed: Aborting screen capture")
        self.withdraw()
        time.sleep(0.2)
        self.destroy()

    def _on_space_press(self, _):
        self._next_mode()
        if self.props.mode_indicator:
            self.props.active_canvas.itemconfig(
                self.props.mode_indicator, text=self.props.mode_char
            )


class _CropWindow(tkinter.Toplevel):
    def __init__(self, root, shot):
        super().__init__()
        # self.tk = tkinter.Toplevel()
        self.root = root

        self.configure(bg="black")  # To hide top border on i3
        self.shot = shot

        self._show_window()
        self._draw_border()
        self._set_bindings()
        self._set_window_geometry()
        self._set_fullscreen()

    def _set_fullscreen(self):
        # Set Fullscreen
        #    Behaves different per OS, because:
        #    - with attributes I couldn't move the windows to the correct screen on MS Windows
        #    - with overrideredirect I couldn't get the keybindings working on Linux
        if self.root.props.platform.startswith("win"):
            self.overrideredirect(1)
            self.attributes("-topmost", 1)

        if self.root.props.platform.startswith("darwin"):
            self.overrideredirect(1)
            self.attributes("-fullscreen", 1)
            self.attributes("-topmost", 1)
            # os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "python" to true' ''')
            # self.focus_force()
            # self.call("::tk::unsupported::MacWindowStyle", "style", self._w, "plain", "none")

        if self.root.props.platform.startswith("linux"):
            self.overrideredirect(1)
            self.attributes("-fullscreen", 1)

    def _show_window(self):
        # Produces frame, useful for debug
        self.frame = tkinter.Frame(self)
        self.frame.pack()

        # Create canvas
        self.canvas = tkinter.Canvas(
            self,
            bg=self.root.props.color,
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
            width=5,
            outline=self.root.props.color,
        )

    def _set_window_geometry(self):
        self.geometry(
            f"{self.shot['position']['width']}x{self.shot['position']['height']}"
            + f"+{self.shot['position']['left']}+{self.shot['position']['top']}"
        )

    def _set_bindings(self):
        self.canvas.bind("<B1-Motion>", self._on_move_press)
        self.canvas.bind("<ButtonPress-1>", self._on_button_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)

    def _get_top_right(self):
        top = min([self.root.props.start_mouse_y, self.root.props.mouse_y])
        right = max([self.root.props.start_mouse_x, self.root.props.mouse_x])
        return top, right

    def _on_button_press(self, event):
        # save mouse start position
        self.root.props.start_mouse_x = self.canvas.canvasx(event.x)
        self.root.props.start_mouse_y = self.canvas.canvasy(event.y)

        # Draw outline
        self.root.props.rect = self.canvas.create_rectangle(
            self.root.props.mouse_x,
            self.root.props.mouse_y,
            1,
            1,
            outline=self.root.props.color,
            width=2,
        )
        # Draw indicator
        self.root.props.mode_indicator = self.canvas.create_text(
            self.root.props.start_mouse_x,
            self.root.props.start_mouse_y,
            anchor="se",
            text=self.root.props.mode_char,
            fill=self.root.props.color,
            font=("Sans", 18),
        )
        self.root.props.active_canvas = self.canvas

    def _on_move_press(self, event):
        # Save current mouse position
        self.root.props.mouse_x = self.canvas.canvasx(event.x)
        self.root.props.mouse_y = self.canvas.canvasy(event.y)

        # Expand rectangle as mouse is dragged
        self.canvas.coords(
            self.root.props.rect,
            self.root.props.start_mouse_x,
            self.root.props.start_mouse_y,
            self.root.props.mouse_x,
            self.root.props.mouse_y,
        )

        # Move also mode indicator
        top, right = self._get_top_right()
        self.canvas.coords(self.root.props.mode_indicator, right, top)

    def _on_button_release(self, event):
        # Update position and destroy window
        self.root.props.mouse_x = self.canvas.canvasx(event.x)
        self.root.props.mouse_y = self.canvas.canvasy(event.y)
        self.root.props.monitor = self.shot["monitor"]
        self.root.withdraw()
        time.sleep(0.2)
        self.root.destroy()
