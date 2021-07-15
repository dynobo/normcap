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
        BaseWindow.resize(835, 588)
        icon = QIcon()
        icon.addFile(u"normcap.png", QSize(), QIcon.Normal, QIcon.Off)
        BaseWindow.setWindowIcon(icon)
        BaseWindow.setAutoFillBackground(True)
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
        self.frame.setLayoutDirection(Qt.RightToLeft)
        self.frame.setStyleSheet(
            u"QFrame {\n" "   border-width: 3px;\n" "   border-style: solid;\n" "}"
        )
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.frame.setLineWidth(0)
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalSpacer = QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.gridLayout_2.addItem(self.horizontalSpacer, 1, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(
            0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.gridLayout_2.addItem(self.verticalSpacer, 2, 1, 1, 1)

        self.top_right_frame = QFrame(self.frame)
        self.top_right_frame.setObjectName(u"top_right_frame")
        self.top_right_frame.setMinimumSize(QSize(38, 72))
        self.top_right_frame.setStyleSheet(u"border:none;")
        self.top_right_frame.setFrameShape(QFrame.StyledPanel)
        self.top_right_frame.setFrameShadow(QFrame.Raised)

        self.gridLayout_2.addWidget(self.top_right_frame, 1, 0, 1, 1)

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
