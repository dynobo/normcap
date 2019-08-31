import logging


def log_dataclass(data_class):
    logger = logging.getLogger(__name__)
    string = "Content of dataclass:\n"
    string += f"{'='*10} <dataclass> {'='*10}\n"
    for key in dir(data_class):
        if not key.startswith("_"):
            string += f"{key}: {getattr(data_class, key)}\n"
    string += f"{'='*10} </dataclass> {'='*9}"
    logger.debug(string)


def store_images(path, images):
    import pathlib
    import datetime

    storage_path = pathlib.Path(path)
    now = datetime.datetime.now()

    for idx, image in enumerate(images):
        name = f"{now:%Y-%m-%d_%H:%M}_{idx}.png"
        image.save(storage_path / name)
