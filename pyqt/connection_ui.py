# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'connection.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(500, 320)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QSize(500, 320))
        Dialog.setMaximumSize(QSize(500, 320))
        Dialog.setSizeGripEnabled(True)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Open)

        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 1)

        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setWordWrap(True)

        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.horizontalLayout = QHBoxLayout()
#ifndef Q_OS_MAC
        self.horizontalLayout.setSpacing(-1)
#endif
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.comboSerial = QComboBox(Dialog)
        self.comboSerial.setObjectName(u"comboSerial")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comboSerial.sizePolicy().hasHeightForWidth())
        self.comboSerial.setSizePolicy(sizePolicy1)
        self.comboSerial.setMinimumSize(QSize(300, 40))
        self.comboSerial.setMaximumSize(QSize(16777215, 60))
        self.comboSerial.setBaseSize(QSize(0, 0))
        self.comboSerial.setFrame(True)

        self.horizontalLayout.addWidget(self.comboSerial)

        self.buttonRefreshSerial = QPushButton(Dialog)
        self.buttonRefreshSerial.setObjectName(u"buttonRefreshSerial")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.buttonRefreshSerial.sizePolicy().hasHeightForWidth())
        self.buttonRefreshSerial.setSizePolicy(sizePolicy2)
        self.buttonRefreshSerial.setMinimumSize(QSize(0, 40))
        self.buttonRefreshSerial.setMaximumSize(QSize(35, 40))
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ViewRefresh))
        self.buttonRefreshSerial.setIcon(icon)

        self.horizontalLayout.addWidget(self.buttonRefreshSerial)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy3)
        self.label_4.setMinimumSize(QSize(90, 20))
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.label_4)

        self.comboBox = QComboBox(Dialog)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        sizePolicy1.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy1)
        self.comboBox.setMinimumSize(QSize(0, 40))

        self.horizontalLayout_3.addWidget(self.comboBox)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.gridLayout.addLayout(self.verticalLayout, 3, 0, 1, 1)

        self.line = QFrame(Dialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 2, 0, 1, 1)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.formLayout.setContentsMargins(8, -1, -1, -1)
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(90, 0))
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.device_address = QLineEdit(Dialog)
        self.device_address.setObjectName(u"device_address")
        self.device_address.setEnabled(True)
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.device_address.sizePolicy().hasHeightForWidth())
        self.device_address.setSizePolicy(sizePolicy4)
        self.device_address.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.device_address.setMouseTracking(False)
        self.device_address.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.device_address.setAutoFillBackground(False)
        self.device_address.setText(u"")
        self.device_address.setFrame(False)
        self.device_address.setReadOnly(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.device_address)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(90, 0))
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.device_name = QLineEdit(Dialog)
        self.device_name.setObjectName(u"device_name")
        self.device_name.setEnabled(True)
        self.device_name.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.device_name.setFrame(False)
        self.device_name.setReadOnly(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.device_name)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(90, 0))
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.device_desc = QLineEdit(Dialog)
        self.device_desc.setObjectName(u"device_desc")
        self.device_desc.setEnabled(True)
        self.device_desc.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.device_desc.setFrame(False)
        self.device_desc.setReadOnly(True)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.device_desc)


        self.gridLayout.addLayout(self.formLayout, 5, 0, 1, 1)

        self.status_msg = QLabel(Dialog)
        self.status_msg.setObjectName(u"status_msg")
        self.status_msg.setWordWrap(True)

        self.gridLayout.addWidget(self.status_msg, 1, 0, 1, 1)


        self.retranslateUi(Dialog)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.buttonBox.accepted.connect(Dialog.accept)

        self.comboBox.setCurrentIndex(7)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Verbindung herstellen", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Einen Port und passende Baud-Rate ausw\u00e4hlen und mit \"\u00d6ffnen\" verbinden", None))
#if QT_CONFIG(tooltip)
        self.comboSerial.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Kommunikation mit dem Arduino erfolgt \u00fcber die serielle Schnittstelle. </p><p>Wenn Arduino nicht erkannt wird, die Verbindung pr\u00fcfen und evtl. Treiber installieren.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.comboSerial.setPlaceholderText(QCoreApplication.translate("Dialog", u"Bitte Seriellen Port ausw\u00e4hlen", None))
#if QT_CONFIG(tooltip)
        self.buttonRefreshSerial.setToolTip(QCoreApplication.translate("Dialog", u"Die Liste der Ports aktualisieren", None))
#endif // QT_CONFIG(tooltip)
        self.buttonRefreshSerial.setText("")
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Baud Rate", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("Dialog", u"2400", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("Dialog", u"4800", None))
        self.comboBox.setItemText(2, QCoreApplication.translate("Dialog", u"9600", None))
        self.comboBox.setItemText(3, QCoreApplication.translate("Dialog", u"14400", None))
        self.comboBox.setItemText(4, QCoreApplication.translate("Dialog", u"19200", None))
        self.comboBox.setItemText(5, QCoreApplication.translate("Dialog", u"38400", None))
        self.comboBox.setItemText(6, QCoreApplication.translate("Dialog", u"57600", None))
        self.comboBox.setItemText(7, QCoreApplication.translate("Dialog", u"115200", None))
        self.comboBox.setItemText(8, QCoreApplication.translate("Dialog", u"230400", None))
        self.comboBox.setItemText(9, QCoreApplication.translate("Dialog", u"460800", None))
        self.comboBox.setItemText(10, QCoreApplication.translate("Dialog", u"500000", None))
        self.comboBox.setItemText(11, QCoreApplication.translate("Dialog", u"921600", None))
        self.comboBox.setItemText(12, QCoreApplication.translate("Dialog", u"1000000", None))
        self.comboBox.setItemText(13, QCoreApplication.translate("Dialog", u"2000000", None))

        self.label.setText(QCoreApplication.translate("Dialog", u"Adresse", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Name", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Beschreibung", None))
        self.device_desc.setPlaceholderText("")
        self.status_msg.setText("")
    # retranslateUi

