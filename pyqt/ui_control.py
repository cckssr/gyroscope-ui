# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'control.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QButtonGroup, QComboBox,
    QDial, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLCDNumber, QLabel, QLayout,
    QPushButton, QRadioButton, QSizePolicy, QSpinBox,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(301, 491)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.label_11 = QLabel(Form)
        self.label_11.setObjectName(u"label_11")
        font = QFont()
        font.setPointSize(16)
        font.setBold(False)
        font.setUnderline(True)
        self.label_11.setFont(font)
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)

        self.gridLayout.addWidget(self.label_11, 0, 0, 1, 1)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.formLayout_3.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_3.setContentsMargins(-1, -1, -1, 10)
        self.mode_label = QLabel(Form)
        self.mode_label.setObjectName(u"mode_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.mode_label.sizePolicy().hasHeightForWidth())
        self.mode_label.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.mode_label)

        self.sMode = QHBoxLayout()
        self.sMode.setObjectName(u"sMode")
        self.sMode.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        self.sMode.setContentsMargins(-1, -1, 0, -1)
        self.sModeSingle = QRadioButton(Form)
        self.buttonGroup = QButtonGroup(Form)
        self.buttonGroup.setObjectName(u"buttonGroup")
        self.buttonGroup.addButton(self.sModeSingle)
        self.sModeSingle.setObjectName(u"sModeSingle")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.sModeSingle.sizePolicy().hasHeightForWidth())
        self.sModeSingle.setSizePolicy(sizePolicy2)
        self.sModeSingle.setChecked(True)

        self.sMode.addWidget(self.sModeSingle)

        self.sModeMulti = QRadioButton(Form)
        self.buttonGroup.addButton(self.sModeMulti)
        self.sModeMulti.setObjectName(u"sModeMulti")
        sizePolicy2.setHeightForWidth(self.sModeMulti.sizePolicy().hasHeightForWidth())
        self.sModeMulti.setSizePolicy(sizePolicy2)

        self.sMode.addWidget(self.sModeMulti)


        self.formLayout_3.setLayout(0, QFormLayout.FieldRole, self.sMode)

        self.query_label = QLabel(Form)
        self.query_label.setObjectName(u"query_label")
        sizePolicy1.setHeightForWidth(self.query_label.sizePolicy().hasHeightForWidth())
        self.query_label.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.query_label)

        self.sQueryMode = QHBoxLayout()
        self.sQueryMode.setObjectName(u"sQueryMode")
        self.sQueryMode.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        self.sQModeMan = QRadioButton(Form)
        self.buttonGroup_2 = QButtonGroup(Form)
        self.buttonGroup_2.setObjectName(u"buttonGroup_2")
        self.buttonGroup_2.addButton(self.sQModeMan)
        self.sQModeMan.setObjectName(u"sQModeMan")
        sizePolicy2.setHeightForWidth(self.sQModeMan.sizePolicy().hasHeightForWidth())
        self.sQModeMan.setSizePolicy(sizePolicy2)
        self.sQModeMan.setChecked(True)

        self.sQueryMode.addWidget(self.sQModeMan)

        self.sQModeAuto = QRadioButton(Form)
        self.buttonGroup_2.addButton(self.sQModeAuto)
        self.sQModeAuto.setObjectName(u"sQModeAuto")
        sizePolicy2.setHeightForWidth(self.sQModeAuto.sizePolicy().hasHeightForWidth())
        self.sQModeAuto.setSizePolicy(sizePolicy2)

        self.sQueryMode.addWidget(self.sQModeAuto)


        self.formLayout_3.setLayout(1, QFormLayout.FieldRole, self.sQueryMode)

        self.duration_label = QLabel(Form)
        self.duration_label.setObjectName(u"duration_label")
        sizePolicy1.setHeightForWidth(self.duration_label.sizePolicy().hasHeightForWidth())
        self.duration_label.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.duration_label)

        self.sDuration = QComboBox(Form)
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.setObjectName(u"sDuration")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.sDuration.sizePolicy().hasHeightForWidth())
        self.sDuration.setSizePolicy(sizePolicy3)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.sDuration)

        self.volt_label = QLabel(Form)
        self.volt_label.setObjectName(u"volt_label")
        sizePolicy1.setHeightForWidth(self.volt_label.sizePolicy().hasHeightForWidth())
        self.volt_label.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.volt_label)

        self.sVolt = QHBoxLayout()
        self.sVolt.setObjectName(u"sVolt")
        self.sVolt.setContentsMargins(-1, -1, 0, -1)
        self.sVoltage = QSpinBox(Form)
        self.sVoltage.setObjectName(u"sVoltage")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.sVoltage.sizePolicy().hasHeightForWidth())
        self.sVoltage.setSizePolicy(sizePolicy4)
        self.sVoltage.setMinimumSize(QSize(0, 40))
        self.sVoltage.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.sVoltage.setMinimum(300)
        self.sVoltage.setMaximum(700)
        self.sVoltage.setSingleStep(10)
        self.sVoltage.setValue(500)

        self.sVolt.addWidget(self.sVoltage)

        self.voltDial = QDial(Form)
        self.voltDial.setObjectName(u"voltDial")
        self.voltDial.setMinimum(300)
        self.voltDial.setMaximum(700)
        self.voltDial.setSingleStep(5)
        self.voltDial.setValue(500)
        self.voltDial.setWrapping(False)
        self.voltDial.setNotchesVisible(True)

        self.sVolt.addWidget(self.voltDial)


        self.formLayout_3.setLayout(3, QFormLayout.FieldRole, self.sVolt)


        self.gridLayout.addLayout(self.formLayout_3, 7, 0, 1, 1)

        self.line = QFrame(Form)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 6, 0, 1, 1)

        self.controlButton = QPushButton(Form)
        self.controlButton.setObjectName(u"controlButton")
        self.controlButton.setEnabled(False)

        self.gridLayout.addWidget(self.controlButton, 10, 0, 1, 1)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setContentsMargins(-1, 5, -1, 0)
        self.label_8 = QLabel(Form)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.label_8)

        self.cVoltage = QLCDNumber(Form)
        self.cVoltage.setObjectName(u"cVoltage")
        self.cVoltage.setMinimumSize(QSize(0, 30))
        self.cVoltage.setDigitCount(3)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.cVoltage)

        self.label_9 = QLabel(Form)
        self.label_9.setObjectName(u"label_9")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.label_9)

        self.cDuration = QLCDNumber(Form)
        self.cDuration.setObjectName(u"cDuration")
        self.cDuration.setMinimumSize(QSize(0, 30))
        self.cDuration.setDigitCount(3)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.cDuration)

        self.label_10 = QLabel(Form)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.label_10)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.label)

        self.cVersion = QLabel(Form)
        self.cVersion.setObjectName(u"cVersion")
        self.cVersion.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.cVersion)

        self.cQueryMode = QLabel(Form)
        self.cQueryMode.setObjectName(u"cQueryMode")
        self.cQueryMode.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.cQueryMode)

        self.label_12 = QLabel(Form)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.label_12)

        self.cMode = QLabel(Form)
        self.cMode.setObjectName(u"cMode")
        self.cMode.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.cMode)


        self.gridLayout.addLayout(self.formLayout_2, 1, 0, 1, 1)


        self.retranslateUi(Form)
        self.voltDial.valueChanged.connect(self.sVoltage.setValue)
        self.sVoltage.valueChanged.connect(self.voltDial.setValue)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Kontrollfenster", None))
        self.label_11.setText(QCoreApplication.translate("Form", u"Aktuelle Einstellungen", None))
        self.mode_label.setText(QCoreApplication.translate("Form", u"Z\u00e4hl-Modus", None))
#if QT_CONFIG(tooltip)
        self.sModeSingle.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Stoppt die Messung nach Ablauf Z\u00e4hldauer</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.sModeSingle.setText(QCoreApplication.translate("Form", u"Einzel", None))
#if QT_CONFIG(tooltip)
        self.sModeMulti.setToolTip(QCoreApplication.translate("Form", u"<html><head/><body><p>Wiederholt die Messung automatisch nach Ablauf Z\u00e4hldauer</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.sModeMulti.setText(QCoreApplication.translate("Form", u"Wiederholung", None))
        self.query_label.setText(QCoreApplication.translate("Form", u"Abfragemodus", None))
        self.sQModeMan.setText(QCoreApplication.translate("Form", u"Manuell", None))
        self.sQModeAuto.setText(QCoreApplication.translate("Form", u"Automatik", None))
        self.duration_label.setText(QCoreApplication.translate("Form", u"Z\u00e4hldauer", None))
        self.sDuration.setItemText(0, QCoreApplication.translate("Form", u"unendlich", u"f0"))
        self.sDuration.setItemText(1, QCoreApplication.translate("Form", u"1 Sekunde", u"f1"))
        self.sDuration.setItemText(2, QCoreApplication.translate("Form", u"10 Sekunden", u"f2"))
        self.sDuration.setItemText(3, QCoreApplication.translate("Form", u"60 Sekunden", u"f3"))
        self.sDuration.setItemText(4, QCoreApplication.translate("Form", u"100 Sekunden", u"f4"))
        self.sDuration.setItemText(5, QCoreApplication.translate("Form", u"300 Sekunden", u"f5"))

#if QT_CONFIG(tooltip)
        self.sDuration.setToolTip(QCoreApplication.translate("Form", u"Wie lange der Z\u00e4hler misst", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.volt_label.setToolTip(QCoreApplication.translate("Form", u"Spannung des Geiger-M\u00fcller Z\u00e4hlrohrs", None))
#endif // QT_CONFIG(tooltip)
        self.volt_label.setText(QCoreApplication.translate("Form", u"GM-Spannung", None))
        self.sVoltage.setSuffix(QCoreApplication.translate("Form", u" V", None))
#if QT_CONFIG(tooltip)
        self.controlButton.setToolTip(QCoreApplication.translate("Form", u"Klicken um Einstellungen an Ger\u00e4t zu \u00fcbertragen. Nur w\u00e4hrend gestoppter Messung m\u00f6glich.", None))
#endif // QT_CONFIG(tooltip)
        self.controlButton.setText(QCoreApplication.translate("Form", u"Einstellungen \u00e4ndern", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"GM-Spannung / V", None))
#if QT_CONFIG(tooltip)
        self.cVoltage.setToolTip(QCoreApplication.translate("Form", u"Aktuelle GM-Spannung", None))
#endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("Form", u"Z\u00e4hldauer / s", None))
#if QT_CONFIG(tooltip)
        self.cDuration.setToolTip(QCoreApplication.translate("Form", u"Aktuelle eingestellte Z\u00e4hldauer. 999 f\u00fcr unendllich", None))
#endif // QT_CONFIG(tooltip)
        self.label_10.setText(QCoreApplication.translate("Form", u"Abfragemodus", None))
        self.label.setText(QCoreApplication.translate("Form", u"Version", None))
#if QT_CONFIG(tooltip)
        self.cVersion.setToolTip(QCoreApplication.translate("Form", u"GM-Z\u00e4hler Firmware", None))
#endif // QT_CONFIG(tooltip)
        self.cVersion.setText(QCoreApplication.translate("Form", u"unknown", None))
#if QT_CONFIG(tooltip)
        self.cQueryMode.setToolTip(QCoreApplication.translate("Form", u"Aktuell eingestellter Abfragemodus der Z\u00e4hlergebnisse", None))
#endif // QT_CONFIG(tooltip)
        self.cQueryMode.setText(QCoreApplication.translate("Form", u"unknown", None))
        self.label_12.setText(QCoreApplication.translate("Form", u"Z\u00e4hl-Modus", None))
#if QT_CONFIG(tooltip)
        self.cMode.setToolTip(QCoreApplication.translate("Form", u"Aktuell eingestellter Z\u00e4hlmodus", None))
#endif // QT_CONFIG(tooltip)
        self.cMode.setText(QCoreApplication.translate("Form", u"unknown", None))
    # retranslateUi

