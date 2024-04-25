import math
from typing import cast

from PySide6 import QtCore, QtGui, QtWidgets


class LoadingIndicator(QtWidgets.QWidget):
    def __init__(
        self, parent: QtWidgets.QWidget, size: int = 128, center_on_parent: bool = True
    ) -> None:
        super().__init__(parent=parent)

        self.dot_count = 9
        self.dot_size_factor = 1.6
        self.dot_color: tuple[int, int, int] = (255, 46, 136)
        self.max_opacity = 200
        self.framerate = 12

        self.counter = 0
        self.timer = None

        self.setVisible(False)

        if size:
            self.setMinimumSize(size, size)
            self.setMaximumSize(size, size)

        if parent and center_on_parent:
            self._center_on_parent()

        self.raise_()

    @property
    def radius(self) -> int:
        """Radius of a single dot."""
        return int(self.height() / self.dot_count * self.dot_size_factor / 2)

    @property
    def opacities(self) -> list[int]:
        """List of opacities, decreasing for each dot."""
        return [
            int((self.max_opacity / self.dot_count) * i) for i in range(self.dot_count)
        ][::-1]

    def _center_on_parent(self) -> None:
        parent = cast(QtWidgets.QWidget, self.parent())
        self.move(
            (parent.width() - self.height()) // 2,
            (parent.height() - self.width()) // 2,
        )

    def moveEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        self._center_on_parent()

    def paintEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
        for i in range(self.dot_count):
            opacity = self.opacities[(self.counter + i) % self.dot_count]
            painter.setBrush(QtGui.QBrush(QtGui.QColor(*self.dot_color, opacity)))
            painter.drawEllipse(
                int(
                    self.width() / 2
                    + (self.width() / 2 - self.radius * 2)
                    * math.cos(2 * math.pi * i / self.dot_count)
                    - self.radius
                ),
                int(
                    self.height() / 2
                    + (self.width() / 2 - self.radius * 2)
                    * math.sin(2 * math.pi * i / self.dot_count)
                    - self.radius
                ),
                self.radius * 2,
                self.radius * 2,
            )
        painter.end()

    def showEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        self.timer = self.startTimer(1000 // self.framerate)

    def hideEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        if self.timer:
            self.killTimer(self.timer)
            self.timer = None

    def timerEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        self.counter = self.counter + 1 if self.counter < self.dot_count - 1 else 0
        self.update()
