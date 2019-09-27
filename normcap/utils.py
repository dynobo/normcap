"""Some utility functions."""

# Default
import logging

# Own
from .data_model import NormcapData


def log_dataclass(desc: str, data_class: NormcapData):
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
