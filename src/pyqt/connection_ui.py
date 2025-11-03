# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'connection.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QSizePolicy, QSpacerItem,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(500, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QSize(500, 200))
        Dialog.setMaximumSize(QSize(500, 200))
        Dialog.setSizeGripEnabled(True)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Open|QDialogButtonBox.StandardButton.Retry)

        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 1)

        self.status_msg = QLabel(Dialog)
        self.status_msg.setObjectName(u"status_msg")
        self.status_msg.setWordWrap(True)

        self.gridLayout.addWidget(self.status_msg, 2, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 3, 0, 1, 1)

        self.desc = QLabel(Dialog)
        self.desc.setObjectName(u"desc")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.desc.sizePolicy().hasHeightForWidth())
        self.desc.setSizePolicy(sizePolicy1)
        self.desc.setTextFormat(Qt.TextFormat.PlainText)
        self.desc.setWordWrap(True)

        self.gridLayout.addWidget(self.desc, 0, 0, 2, 1)


        self.retranslateUi(Dialog)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.buttonBox.accepted.connect(Dialog.accept)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Verbindung herstellen", None))
        self.status_msg.setText("")
        self.desc.setText(QCoreApplication.translate("Dialog", u"Verbinden Sie den Computer mit dem WiFi {ssid} des Arduinos und warten Sie einen kurzen Moment. \n"
"\n"
"Bei erfolgreicher Verbindung wird das Fenster automatisch geschlossen.", None))
    # retranslateUi

