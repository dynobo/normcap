import logging


def log_dataclass(data_class):
    logger = logging.getLogger(__name__)
    string = f"\n{'='*10} <dataclass> {'='*10}\n"
    for key in dir(data_class):
        if not key.startswith("_"):
            string += f"{key}: {getattr(data_class, key)}\n"
    string += f"{'='*10} </dataclass> {'='*9}"
    logger.debug(string)
