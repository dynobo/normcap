"""Logger used accross all modules."""

import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)-7s - %(name)s.%(module)-14s - L:%(lineno)-3d - %(message)s",
    datefmt="%H:%M:%S",
    level="WARNING",
)
logger = logging.getLogger(__name__.split(".", maxsplit=1)[0])
