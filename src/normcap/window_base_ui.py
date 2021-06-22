# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'base_window.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_BaseWindow(object):
    def setupUi(self, BaseWindow):
        if not BaseWindow.objectName():
            BaseWindow.setObjectName(u"BaseWindow")
        BaseWindow.setEnabled(True)
        BaseWindow.resize(423, 588)
        icon = QIcon()
        icon.addFile(u"normcap.png", QSize(), QIcon.Normal, QIcon.Off)
        BaseWindow.setWindowIcon(icon)
        BaseWindow.setAutoFillBackground(True)
        BaseWindow.setStyleSheet(
            u"QMainWindow::separator {\n" "    background-color: #ddd;\n" "}"
        )
        BaseWindow.setAnimated(True)
        self.centralwidget = QWidget(BaseWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setEnabled(True)
        self.centralwidget.setAutoFillBackground(False)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setCursor(QCursor(Qt.CrossCursor))
        self.frame.setStyleSheet(
            u"QFrame {\n" "   border-width: 3px;\n" "   border-style: solid;\n" "}"
        )
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.frame.setLineWidth(0)

        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        BaseWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(BaseWindow)

        QMetaObject.connectSlotsByName(BaseWindow)

    # setupUi

    def retranslateUi(self, BaseWindow):
        BaseWindow.setWindowTitle(
            QCoreApplication.translate("BaseWindow", u"NormCap", None)
        )

    # retranslateUi
