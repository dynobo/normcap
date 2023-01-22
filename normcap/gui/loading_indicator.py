import math
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class LoadingIndicator(QtWidgets.QWidget):
    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        size: int = 128,
        center_on_parent: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setVisible(False)

        self.dots = 9
        self.dot_size_factor = 1.6
        self.max_opacity = 200
        self.framerate = 80

        self.counter = 0
        self.timer = None

        if size:
            self.setMinimumSize(size, size)
            self.setMaximumSize(size, size)

        if parent and center_on_parent:
            self._center_on_parent()

        self.raise_()

    @property
    def radius(self) -> int:
        return int(self.height() / self.dots * self.dot_size_factor)

    @property
    def opacities(self) -> list[int]:
        return [int((self.max_opacity / self.dots) * i) for i in range(self.dots)][::-1]

    def _center_on_parent(self) -> None:
        self.move(
            (self.parent().width() - self.height()) // 2,
            (self.parent().height() - self.width()) // 2,
        )

    def moveEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        self._center_on_parent()

    def paintEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
        for i in range(self.dots):
            opacity = self.opacities[(self.counter + i) % self.dots]
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 46, 136, opacity)))
            painter.drawEllipse(
                int(
                    self.width() / 2
                    + (self.width() / 2 - self.radius)
                    * math.cos(2 * math.pi * i / self.dots)
                    - self.radius / 2
                ),
                int(
                    self.height() / 2
                    + (self.width() / 2 - self.radius)
                    * math.sin(2 * math.pi * i / self.dots)
                    - self.radius / 2
                ),
                self.radius,
                self.radius,
            )
        painter.end()

    def showEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        self.timer = self.startTimer(self.framerate)

    def hideEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        if self.timer:
            self.killTimer(self.timer)
            self.timer = None

    def timerEvent(self, _: QtCore.QEvent) -> None:  # noqa: N802
        self.counter = self.counter + 1 if self.counter < self.dots - 1 else 0
        self.update()
