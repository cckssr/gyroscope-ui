# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLCDNumber, QLabel, QLayout, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QSpacerItem, QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(931, 702)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_3 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(10, -1, -1, 10)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.verticalLayout_2.setContentsMargins(0, -1, -1, 0)
        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        font = QFont()
        font.setPointSize(13)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_3 = QFormLayout(self.groupBox_2)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.cDataPoints = QLCDNumber(self.groupBox_2)
        self.cDataPoints.setObjectName(u"cDataPoints")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cDataPoints.sizePolicy().hasHeightForWidth())
        self.cDataPoints.setSizePolicy(sizePolicy)
        self.cDataPoints.setMinimumSize(QSize(100, 30))
        font1 = QFont()
        font1.setPointSize(15)
        self.cDataPoints.setFont(font1)
        self.cDataPoints.setFrameShape(QFrame.Shape.Box)
        self.cDataPoints.setFrameShadow(QFrame.Shadow.Raised)
        self.cDataPoints.setDigitCount(6)
        self.cDataPoints.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.cDataPoints)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label)

        self.cFrequency = QLCDNumber(self.groupBox_2)
        self.cFrequency.setObjectName(u"cFrequency")
        sizePolicy.setHeightForWidth(self.cFrequency.sizePolicy().hasHeightForWidth())
        self.cFrequency.setSizePolicy(sizePolicy)
        self.cFrequency.setMinimumSize(QSize(100, 30))
        self.cFrequency.setFont(font1)
        self.cFrequency.setDigitCount(6)
        self.cFrequency.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cFrequency)

        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.cZGyro = QLCDNumber(self.groupBox_2)
        self.cZGyro.setObjectName(u"cZGyro")
        sizePolicy.setHeightForWidth(self.cZGyro.sizePolicy().hasHeightForWidth())
        self.cZGyro.setSizePolicy(sizePolicy)
        self.cZGyro.setMinimumSize(QSize(100, 30))
        self.cZGyro.setFont(font1)
        self.cZGyro.setDigitCount(6)
        self.cZGyro.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.FieldRole, self.cZGyro)


        self.verticalLayout_2.addWidget(self.groupBox_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy1)
        self.groupBox.setMinimumSize(QSize(0, 50))
        self.groupBox.setFont(font)
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.formLayout_2.setContentsMargins(-1, -1, 0, 0)
        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.groupLetter = QComboBox(self.groupBox)
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.addItem("")
        self.groupLetter.setObjectName(u"groupLetter")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.groupLetter.sizePolicy().hasHeightForWidth())
        self.groupLetter.setSizePolicy(sizePolicy2)
        self.groupLetter.setMaxCount(24)
        self.groupLetter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.groupLetter)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.suffix = QLineEdit(self.groupBox)
        self.suffix.setObjectName(u"suffix")
        sizePolicy2.setHeightForWidth(self.suffix.sizePolicy().hasHeightForWidth())
        self.suffix.setSizePolicy(sizePolicy2)
        self.suffix.setText(u"")
        self.suffix.setMaxLength(20)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.suffix)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.buttonSave = QPushButton(self.groupBox)
        self.buttonSave.setObjectName(u"buttonSave")
        self.buttonSave.setEnabled(False)
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.buttonSave.sizePolicy().hasHeightForWidth())
        self.buttonSave.setSizePolicy(sizePolicy3)
        self.buttonSave.setMinimumSize(QSize(100, 30))
        self.buttonSave.setMaximumSize(QSize(1000, 40))

        self.verticalLayout.addWidget(self.buttonSave)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(-1, -1, 0, 0)
        self.autoSave = QCheckBox(self.groupBox)
        self.autoSave.setObjectName(u"autoSave")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.autoSave.sizePolicy().hasHeightForWidth())
        self.autoSave.setSizePolicy(sizePolicy4)
        self.autoSave.setMaximumSize(QSize(850, 16777215))
        self.autoSave.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.autoSave.setChecked(True)
        self.autoSave.setTristate(False)

        self.horizontalLayout_5.addWidget(self.autoSave)


        self.verticalLayout.addLayout(self.horizontalLayout_5)


        self.verticalLayout_2.addWidget(self.groupBox)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.buttonStart = QPushButton(self.centralwidget)
        self.buttonStart.setObjectName(u"buttonStart")
        self.buttonStart.setEnabled(False)
        self.buttonStart.setMinimumSize(QSize(75, 30))
        self.buttonStart.setMaximumSize(QSize(500, 40))

        self.horizontalLayout.addWidget(self.buttonStart)

        self.buttonStop = QPushButton(self.centralwidget)
        self.buttonStop.setObjectName(u"buttonStop")
        self.buttonStop.setEnabled(False)
        self.buttonStop.setMinimumSize(QSize(75, 30))
        self.buttonStop.setMaximumSize(QSize(500, 40))

        self.horizontalLayout.addWidget(self.buttonStop)

        self.line_2 = QFrame(self.centralwidget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line_2)

        self.buttonReset = QPushButton(self.centralwidget)
        self.buttonReset.setObjectName(u"buttonReset")
        self.buttonReset.setEnabled(False)

        self.horizontalLayout.addWidget(self.buttonReset)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.VLine)

        self.horizontalLayout_3.addWidget(self.line)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, -1, 0, -1)
        self.gridGroupBox = QGroupBox(self.centralwidget)
        self.gridGroupBox.setObjectName(u"gridGroupBox")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.gridGroupBox.sizePolicy().hasHeightForWidth())
        self.gridGroupBox.setSizePolicy(sizePolicy5)
        self.gridGroupBox.setFont(font)
        self.gridGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gridGroupBox.setFlat(False)
        self.gridLayout_2 = QGridLayout(self.gridGroupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setHorizontalSpacing(-1)
        self.gridLayout_2.setContentsMargins(-1, 12, -1, -1)
        self.plotWidget = QWidget(self.gridGroupBox)
        self.plotWidget.setObjectName(u"plotWidget")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(1)
        sizePolicy6.setHeightForWidth(self.plotWidget.sizePolicy().hasHeightForWidth())
        self.plotWidget.setSizePolicy(sizePolicy6)

        self.gridLayout_2.addWidget(self.plotWidget, 2, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.label_3 = QLabel(self.gridGroupBox)
        self.label_3.setObjectName(u"label_3")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy7)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_3)

        self.checkBox = QCheckBox(self.gridGroupBox)
        self.checkBox.setObjectName(u"checkBox")

        self.horizontalLayout_2.addWidget(self.checkBox)


        self.gridLayout_2.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)


        self.verticalLayout_3.addWidget(self.gridGroupBox)


        self.horizontalLayout_3.addLayout(self.verticalLayout_3)

        self.horizontalLayout_3.setStretch(2, 5)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 931, 24))
        MainWindow.setMenuBar(self.menubar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)

        self.groupLetter.setCurrentIndex(-1)
        self.buttonReset.setDefault(False)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"GM-Counter", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Live Messwerte", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Datenpunkte", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Rotationsfrequenz (Hz)", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Z-Rot. Geschw. (\u00b0 / s)", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Speicherung", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Gruppe*", None))
        self.groupLetter.setItemText(0, QCoreApplication.translate("MainWindow", u"A", None))
        self.groupLetter.setItemText(1, QCoreApplication.translate("MainWindow", u"B", None))
        self.groupLetter.setItemText(2, QCoreApplication.translate("MainWindow", u"C", None))
        self.groupLetter.setItemText(3, QCoreApplication.translate("MainWindow", u"D", None))
        self.groupLetter.setItemText(4, QCoreApplication.translate("MainWindow", u"E", None))
        self.groupLetter.setItemText(5, QCoreApplication.translate("MainWindow", u"F", None))
        self.groupLetter.setItemText(6, QCoreApplication.translate("MainWindow", u"G", None))
        self.groupLetter.setItemText(7, QCoreApplication.translate("MainWindow", u"H", None))
        self.groupLetter.setItemText(8, QCoreApplication.translate("MainWindow", u"I", None))
        self.groupLetter.setItemText(9, QCoreApplication.translate("MainWindow", u"J", None))
        self.groupLetter.setItemText(10, QCoreApplication.translate("MainWindow", u"K", None))
        self.groupLetter.setItemText(11, QCoreApplication.translate("MainWindow", u"L", None))
        self.groupLetter.setItemText(12, QCoreApplication.translate("MainWindow", u"M", None))
        self.groupLetter.setItemText(13, QCoreApplication.translate("MainWindow", u"N", None))
        self.groupLetter.setItemText(14, QCoreApplication.translate("MainWindow", u"O", None))
        self.groupLetter.setItemText(15, QCoreApplication.translate("MainWindow", u"P", None))

#if QT_CONFIG(tooltip)
        self.groupLetter.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Auswahl der GP Praktikumsgruppe <span style=\" color:#ff001a;\">(Pflichtfeld)</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Eigenes Suffix", None))
#if QT_CONFIG(tooltip)
        self.suffix.setToolTip(QCoreApplication.translate("MainWindow", u"Ein benutzerdefiniertes Suffix mit maximal 20 Zeichen", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.buttonSave.setToolTip(QCoreApplication.translate("MainWindow", u"Messung speichern (Dateidialog)", None))
#endif // QT_CONFIG(tooltip)
        self.buttonSave.setText(QCoreApplication.translate("MainWindow", u"Speichern", None))
#if QT_CONFIG(tooltip)
        self.autoSave.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Bei Aktivierung werden die Messungen automatisch im Format:</p><p>YYYY_MM_DD-<span style=\" font-style:italic;\">Radioaktive Probe</span>-<span style=\" font-style:italic;\">Suffix</span>.csv</p><p>im Ordner Dokumente/Geiger-Mueller/ gespeichert.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.autoSave.setText(QCoreApplication.translate("MainWindow", u"Automatische Speicherung. ", None))
#if QT_CONFIG(tooltip)
        self.buttonStart.setToolTip(QCoreApplication.translate("MainWindow", u"Start der Messung", None))
#endif // QT_CONFIG(tooltip)
        self.buttonStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
#if QT_CONFIG(tooltip)
        self.buttonStop.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuelle Messung stoppen", None))
#endif // QT_CONFIG(tooltip)
        self.buttonStop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.buttonReset.setText(QCoreApplication.translate("MainWindow", u"Reset", None))
        self.gridGroupBox.setTitle("")
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Live-Daten", None))
        self.checkBox.setText(QCoreApplication.translate("MainWindow", u"Auto-Scroll", None))
    # retranslateUi

