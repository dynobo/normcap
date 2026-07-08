from PySide6 import QtCore, QtWidgets

from normcap.gui.loading_indicator import LoadingIndicator


class ProcessingDialog(QtWidgets.QDialog):
    def __init__(self, parent: "QtWidgets.QWidget | None" = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("NormCap")

        window_size = 100
        self.setFixedSize(window_size, window_size)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)

        label = QtWidgets.QLabel("NormCap", self)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

        self.loading_indicator = LoadingIndicator(size=window_size, parent=self)
        self.loading_indicator.show()
