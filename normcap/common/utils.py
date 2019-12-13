"""Some utility functions."""

# Default
import logging
from typing import Union

# Own
from normcap.common.data_model import NormcapData


def log_dataclass(desc: str, data_class: NormcapData, return_string: bool = True):
    """Debug output of NormCap's session data.

    Arguments:
        desc {str} -- Description to print upfront
        data_class {NormcapData} -- NormCap's session data to output
    """
    logger = logging.getLogger(__name__)
    string = f"{desc}\n{'='*10} <dataclass> {'='*10}\n"
    for key in dir(data_class):
        if not key.startswith("_"):
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
