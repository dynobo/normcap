"""
"""
# Default
import pathlib
import datetime

# Own
from handler import AbstractHandler
from data_model import NormcapData


class StoreHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        if request.cli_args.path:
            self._logger.info("Saving images to {selection.cli_args.path}...")
            all_images = [request.image] + [s["image"] for s in request.shots]
            self.store_images(request.cli_args.path, all_images)

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def store_images(self, path, images):
        storage_path = pathlib.Path(path)
        now = datetime.datetime.now()

        for idx, image in enumerate(images):
            name = f"{now:%Y-%m-%d_%H:%M}_{idx}.png"
            image.save(storage_path / name)
