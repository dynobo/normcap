"""Some utility functions."""

# Default
import logging
from typing import Union

# Own
from normcap.common.data_model import NormcapData


def _format_list_of_dicts_output(list_of_dicts: list) -> str:
    string = ""
    for d in list_of_dicts:
        for key, val in d.items():
            if key in ["left", "top", "width", "height"]:
                string += f"{key}:{val: <5}| "
            elif key == "text":
                string += f"{key}:{val}"
            else:
                string += f"{key}:{val: <3}| "
        string += "\n"
    return string


def log_dataclass(desc: str, data_class: NormcapData, return_string: bool = True):
    """Debug output of NormCap's session data.

    Arguments:
        desc {str} -- Description to print upfront
        data_class {NormcapData} -- NormCap's session data to output
    """
    logger = logging.getLogger(__name__)
    string = f"{desc}\n{'='*10} <dataclass> {'='*10}\n"
    for key in dir(data_class):
        # Skip internal classes
        if key.startswith("_"):
            continue
        # Nicer format tesseract output
        if key == "words":
            string += (
                f"{key}: \n{_format_list_of_dicts_output(getattr(data_class, key))}\n"
            )
            continue
        # Per default just print
        string += f"{key}: {getattr(data_class, key)}\n"
    string += f"{'='*10} </dataclass> {'='*9}"
    logger.debug(string)

    if return_string:  # Mainly used for testing
        return string


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
