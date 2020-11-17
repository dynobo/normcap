"""Some utility functions."""

# Default
from typing import Union


def get_jaccard_sim(seq1: Union[list, str], seq2: Union[list, str]) -> float:
    """Calculate the jaccard similarity of two sequences.

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
