"""
"""
# Default
import os
from dataclasses import dataclass, field

# Extra
from PIL import Image


@dataclass()
class Selection:
    image: Image = None
    image_full: Image = None
    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0
    monitor: int = 0
    line_boxes: list = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join([l.content for l in self.line_boxes]).strip()

    @property
    def lines(self) -> str:
        return os.linesep.join([l.content.strip() for l in self.line_boxes])
