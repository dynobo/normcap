"""Some utility functions."""

# Default
from typing import Union
import copy

# Extra
import pystray  # type: ignore
from importlib_resources import files  # type: ignore
from PIL import Image  # type: ignore

# Own
from normcap import __version__


def get_jaccard_sim(seq1: Union[list, str], seq2: Union[list, str]) -> float:
    """Calculates the jaccard similarity of two sequences.

    This is basically done by checking the intersections of the
    sets of elements of the sequences.
    In case strings are provided as sequences, the single chars will
    be taken as elements!

    Arguments:
        seq1 {list or str} -- One sequence
        seq2 {list or str} -- Another sequence

    Returns:
        float -- Similarity score between 0 and 1
    """
    set1 = set(seq1)
    set2 = set(seq2)
    equal = set1.intersection(set2)
    return len(equal) / (len(set1) + len(set2) - len(equal))


def run_in_tray(client_code, capture, normcap_data):
    """Wrap execution in systray icon.

    Args:
        client_code (function): Wrapper function to call
        capture (function): Chain of responsibilities
        normcap_data (NormcapData): Normcap data object

    Returns:
        NormcapData: Normcap data object
    """
    last_normcap_data = {}

    def _create_image():
        icon_path = files("normcap.ressources").joinpath("normcap.png")
        image = Image.open(icon_path)
        return image

    def on_capture():
        nonlocal last_normcap_data
        last_normcap_data = client_code(
            copy.deepcopy(capture), copy.deepcopy(normcap_data)
        )

    # def on_update(icon, item):
    #     pass

    def on_exit(icon):
        icon.stop()

    pystray.Icon(
        "Normcap",
        _create_image(),
        menu=pystray.Menu(
            pystray.MenuItem(f"Normcap v{__version__}", lambda x: x, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Capture", on_capture, default=True),
            # pystray.MenuItem("Check for Update", on_update),
            # pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", on_exit),
        ),
    ).run()

    return last_normcap_data
