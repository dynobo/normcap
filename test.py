from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image

state = False
im = Image.new(mode="RGB", size=(200, 200), color=(153, 153, 255))


def on_clicked(icon, item):
    global state
    state = not item.checked


icon(
    "test", im, menu=menu(item("Checkable", on_clicked, checked=lambda item: state))
).run()
