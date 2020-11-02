"""Some utility functions."""

# Default
from typing import Union

# Extra
import pystray  # type: ignore
from importlib_resources import files  # type: ignore
from PIL import Image  # type: ignore


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


def run_in_tray(func):
    def set_quit():
        pass

    def _create_image():
        icon_path = files("normcap.ressources").joinpath("normcap.png")
        image = Image.open(icon_path)
        return image

    state = 0

    def set_state(v):
        def inner(icon, item):
            global state
            state = v

        return inner

    def get_state(v):
        def inner(item):
            return state == v

        return inner

    normcap_data = {}
    pystray.Icon(
        "test",
        _create_image(),
        menu=pystray.Menu(
            lambda: (
                pystray.MenuItem(
                    "State %d" % i, set_state(i), checked=get_state(i), radio=True
                )
                for i in range(max(5, state + 2))
            )
        ),
    ).run()

    return normcap_data
