"""
"""
# Default
import tkinter
from collections import namedtuple

# Extra
import mss
from PIL import Image, ImageTk


class Fullscreen_Window:
    def __init__(self, root_window, current_window, shot):
        self.root_window = root_window
        self.tk = current_window
        self.tk.attributes("-fullscreen", True)
        self.shot = shot

        # Produces frame, useful for debug
        self.frame = tkinter.Frame(self.tk)
        self.frame.pack()

        # Create canvas
        self.canvas = tkinter.Canvas(
            self.tk,
            bg="red",
            width=self.shot.pos["width"],
            height=self.shot.pos["height"],
            highlightthickness=0,
            relief="flat",
            cursor="cross",
        )
        self.canvas.pack(expand=tkinter.YES, fill=tkinter.BOTH)

        # Add image to canvas
        tkimage = ImageTk.PhotoImage(shot.img)
        self.screen_gc = tkimage  # Prevent img being garbage collected
        self.canvas.create_image(0, 0, anchor="nw", image=tkimage)

        # Prepare rectangle
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.x = 0
        self.y = 0

        # Bindings
        self.tk.bind("<Escape>", self.end_fullscreen)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Set size & pos
        self.tk.geometry(
            f"{shot.pos['width']}x{shot.pos['height']}+{shot.pos['left']}+{shot.pos['top']}"
        )

    def end_fullscreen(self, result=None):
        self.root_window.result = result
        self.root_window.destroy()
        return result

    def on_button_press(self, event):
        # save mouse start position
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

        # create rectangle
        if not self.rect:
            self.rect = self.canvas.create_rectangle(
                self.x, self.y, 1, 1, outline="red"
            )

    def on_move_press(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)

        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)

        crop_args = {
            "monitor": self.shot.mon,
            "upper": min([cur_y, self.start_y]),
            "lower": max([cur_y, self.start_y]),
            "left": min([cur_x, self.start_x]),
            "right": max([cur_x, self.start_x]),
        }
        self.end_fullscreen(result=crop_args)


class Capture:
    def __init__(self, *args, **kwargs):
        self.clicks = []
        self.Shot = namedtuple("Shot", "mon img pos")
        self.shots = []
        return super().__init__(*args, **kwargs)

    def show_window(self):
        root = tkinter.Tk()
        for idx, shot in enumerate(self.shots[:2]):
            if idx == 0:
                Fullscreen_Window(root, root, shot)
            else:
                top = tkinter.Toplevel()
                Fullscreen_Window(root, top, shot)
        root.mainloop()
        print(root.result)
        self.crop_shot(root.result)

    def crop_shot(self, crop_args):
        crop_mon = self.shots[crop_args["monitor"]]
        cropped_img = crop_mon.img.crop(
            (
                crop_args["left"],
                crop_args["upper"],
                crop_args["right"],
                crop_args["lower"],
            )
        )
        cropped_img.save("cropped.png")

    def capture_screen(self, rectangle):
        with mss.mss() as sct:
            # Grab all screens
            for idx, position in enumerate(sct.monitors[1:]):
                # Capture
                temp_shot = sct.grab(position)
                # Convert to Pil
                temp_img = Image.frombytes(
                    "RGB", temp_shot.size, temp_shot.bgra, "raw", "BGRX"
                )
                # Append to results
                temp_shot = self.Shot(mon=idx, img=temp_img, pos=position)
                self.shots.append(temp_shot)

            # Save shots
            for idx, shot in enumerate(self.shots):
                shot.img.save(f"temp_m{idx}.png")

        return
