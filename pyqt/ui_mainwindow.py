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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QButtonGroup, QCheckBox,
    QComboBox, QDial, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLCDNumber, QLabel, QLayout, QLineEdit,
    QMainWindow, QMenuBar, QProgressBar, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QStatusBar, QTabWidget, QTableView, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1084, 796)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_3 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.settings = QGroupBox(self.centralwidget)
        self.settings.setObjectName(u"settings")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.settings.sizePolicy().hasHeightForWidth())
        self.settings.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(13)
        self.settings.setFont(font)
        self.settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout = QFormLayout(self.settings)
        self.formLayout.setObjectName(u"formLayout")
        self.label_8 = QLabel(self.settings)
        self.label_8.setObjectName(u"label_8")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_8)

        self.cVoltage = QLCDNumber(self.settings)
        self.cVoltage.setObjectName(u"cVoltage")
        self.cVoltage.setMinimumSize(QSize(0, 30))
        self.cVoltage.setDigitCount(3)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.cVoltage)

        self.label_9 = QLabel(self.settings)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.cDuration = QLCDNumber(self.settings)
        self.cDuration.setObjectName(u"cDuration")
        self.cDuration.setMinimumSize(QSize(0, 30))
        self.cDuration.setDigitCount(3)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cDuration)

        self.query_label = QLabel(self.settings)
        self.query_label.setObjectName(u"query_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.query_label.sizePolicy().hasHeightForWidth())
        self.query_label.setSizePolicy(sizePolicy1)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.query_label)

        self.cQueryMode = QLabel(self.settings)
        self.cQueryMode.setObjectName(u"cQueryMode")
        sizePolicy1.setHeightForWidth(self.cQueryMode.sizePolicy().hasHeightForWidth())
        self.cQueryMode.setSizePolicy(sizePolicy1)
        self.cQueryMode.setMinimumSize(QSize(0, 20))

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.cQueryMode)

        self.label_12 = QLabel(self.settings)
        self.label_12.setObjectName(u"label_12")
        sizePolicy1.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy1)
        self.label_12.setMinimumSize(QSize(0, 20))

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_12)

        self.cMode = QLabel(self.settings)
        self.cMode.setObjectName(u"cMode")
        sizePolicy1.setHeightForWidth(self.cMode.sizePolicy().hasHeightForWidth())
        self.cMode.setSizePolicy(sizePolicy1)
        self.cMode.setMinimumSize(QSize(0, 20))

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.cMode)

        self.label = QLabel(self.settings)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setMinimumSize(QSize(0, 20))

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label)

        self.cVersion = QLabel(self.settings)
        self.cVersion.setObjectName(u"cVersion")
        sizePolicy1.setHeightForWidth(self.cVersion.sizePolicy().hasHeightForWidth())
        self.cVersion.setSizePolicy(sizePolicy1)
        self.cVersion.setMinimumSize(QSize(0, 20))

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.cVersion)

        self.line_3 = QFrame(self.settings)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShadow(QFrame.Shadow.Plain)
        self.line_3.setLineWidth(1)
        self.line_3.setFrameShape(QFrame.Shape.HLine)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.line_3)

        self.mode_label = QLabel(self.settings)
        self.mode_label.setObjectName(u"mode_label")
        sizePolicy1.setHeightForWidth(self.mode_label.sizePolicy().hasHeightForWidth())
        self.mode_label.setSizePolicy(sizePolicy1)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.mode_label)

        self.sMode = QHBoxLayout()
        self.sMode.setObjectName(u"sMode")
        self.sMode.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.sMode.setContentsMargins(-1, -1, 0, -1)
        self.sModeSingle = QRadioButton(self.settings)
        self.groupMode = QButtonGroup(MainWindow)
        self.groupMode.setObjectName(u"groupMode")
        self.groupMode.addButton(self.sModeSingle)
        self.sModeSingle.setObjectName(u"sModeSingle")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.sModeSingle.sizePolicy().hasHeightForWidth())
        self.sModeSingle.setSizePolicy(sizePolicy2)
        self.sModeSingle.setChecked(True)

        self.sMode.addWidget(self.sModeSingle)

        self.sModeMulti = QRadioButton(self.settings)
        self.groupMode.addButton(self.sModeMulti)
        self.sModeMulti.setObjectName(u"sModeMulti")
        sizePolicy2.setHeightForWidth(self.sModeMulti.sizePolicy().hasHeightForWidth())
        self.sModeMulti.setSizePolicy(sizePolicy2)

        self.sMode.addWidget(self.sModeMulti)


        self.formLayout.setLayout(6, QFormLayout.ItemRole.FieldRole, self.sMode)

        self.label_10 = QLabel(self.settings)
        self.label_10.setObjectName(u"label_10")
        sizePolicy1.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy1)
        self.label_10.setMinimumSize(QSize(0, 20))
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.formLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.label_10)

        self.sQueryMode = QHBoxLayout()
        self.sQueryMode.setObjectName(u"sQueryMode")
        self.sQueryMode.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        self.sQModeMan = QRadioButton(self.settings)
        self.groupQMode = QButtonGroup(MainWindow)
        self.groupQMode.setObjectName(u"groupQMode")
        self.groupQMode.addButton(self.sQModeMan)
        self.sQModeMan.setObjectName(u"sQModeMan")
        self.sQModeMan.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.sQModeMan.sizePolicy().hasHeightForWidth())
        self.sQModeMan.setSizePolicy(sizePolicy2)
        self.sQModeMan.setChecked(False)

        self.sQueryMode.addWidget(self.sQModeMan)

        self.sQModeAuto = QRadioButton(self.settings)
        self.groupQMode.addButton(self.sQModeAuto)
        self.sQModeAuto.setObjectName(u"sQModeAuto")
        self.sQModeAuto.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.sQModeAuto.sizePolicy().hasHeightForWidth())
        self.sQModeAuto.setSizePolicy(sizePolicy2)
        self.sQModeAuto.setChecked(True)

        self.sQueryMode.addWidget(self.sQModeAuto)


        self.formLayout.setLayout(7, QFormLayout.ItemRole.FieldRole, self.sQueryMode)

        self.duration_label = QLabel(self.settings)
        self.duration_label.setObjectName(u"duration_label")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.duration_label.sizePolicy().hasHeightForWidth())
        self.duration_label.setSizePolicy(sizePolicy3)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.duration_label)

        self.sDuration = QComboBox(self.settings)
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.addItem("")
        self.sDuration.setObjectName(u"sDuration")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.sDuration.sizePolicy().hasHeightForWidth())
        self.sDuration.setSizePolicy(sizePolicy4)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.sDuration)

        self.volt_label = QLabel(self.settings)
        self.volt_label.setObjectName(u"volt_label")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.volt_label.sizePolicy().hasHeightForWidth())
        self.volt_label.setSizePolicy(sizePolicy5)
        self.volt_label.setMinimumSize(QSize(0, 100))
        self.volt_label.setMaximumSize(QSize(16777215, 100))

        self.formLayout.setWidget(9, QFormLayout.ItemRole.LabelRole, self.volt_label)

        self.sVolt = QHBoxLayout()
        self.sVolt.setObjectName(u"sVolt")
        self.sVolt.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.sVolt.setContentsMargins(-1, -1, 0, -1)
        self.sVoltage = QSpinBox(self.settings)
        self.sVoltage.setObjectName(u"sVoltage")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.sVoltage.sizePolicy().hasHeightForWidth())
        self.sVoltage.setSizePolicy(sizePolicy6)
        self.sVoltage.setMinimumSize(QSize(0, 40))
        self.sVoltage.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.sVoltage.setMinimum(300)
        self.sVoltage.setMaximum(700)
        self.sVoltage.setSingleStep(10)
        self.sVoltage.setValue(500)

        self.sVolt.addWidget(self.sVoltage)

        self.voltDial = QDial(self.settings)
        self.voltDial.setObjectName(u"voltDial")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.voltDial.sizePolicy().hasHeightForWidth())
        self.voltDial.setSizePolicy(sizePolicy7)
        self.voltDial.setMinimumSize(QSize(100, 100))
        self.voltDial.setMaximumSize(QSize(100, 100))
        self.voltDial.setMinimum(300)
        self.voltDial.setMaximum(700)
        self.voltDial.setSingleStep(5)
        self.voltDial.setValue(500)
        self.voltDial.setWrapping(False)
        self.voltDial.setNotchesVisible(True)

        self.sVolt.addWidget(self.voltDial)


        self.formLayout.setLayout(9, QFormLayout.ItemRole.FieldRole, self.sVolt)

        self.buttonSetting = QPushButton(self.settings)
        self.buttonSetting.setObjectName(u"buttonSetting")
        self.buttonSetting.setAutoDefault(False)

        self.formLayout.setWidget(10, QFormLayout.ItemRole.SpanningRole, self.buttonSetting)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(11, QFormLayout.ItemRole.LabelRole, self.verticalSpacer)

        self.line_5 = QFrame(self.settings)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShadow(QFrame.Shadow.Plain)
        self.line_5.setFrameShape(QFrame.Shape.HLine)

        self.formLayout.setWidget(12, QFormLayout.ItemRole.SpanningRole, self.line_5)

        self.label_6 = QLabel(self.settings)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(13, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.radSample = QComboBox(self.settings)
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.addItem("")
        self.radSample.setObjectName(u"radSample")
        self.radSample.setEditable(True)
        self.radSample.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.formLayout.setWidget(13, QFormLayout.ItemRole.FieldRole, self.radSample)

        self.label_5 = QLabel(self.settings)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(14, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.suffix = QLineEdit(self.settings)
        self.suffix.setObjectName(u"suffix")
        self.suffix.setText(u"")
        self.suffix.setMaxLength(20)

        self.formLayout.setWidget(14, QFormLayout.ItemRole.FieldRole, self.suffix)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.buttonStart = QPushButton(self.settings)
        self.buttonStart.setObjectName(u"buttonStart")
        self.buttonStart.setEnabled(False)
        self.buttonStart.setMinimumSize(QSize(75, 30))
        self.buttonStart.setMaximumSize(QSize(75, 40))

        self.horizontalLayout.addWidget(self.buttonStart)

        self.buttonStop = QPushButton(self.settings)
        self.buttonStop.setObjectName(u"buttonStop")
        self.buttonStop.setEnabled(False)
        self.buttonStop.setMinimumSize(QSize(75, 30))
        self.buttonStop.setMaximumSize(QSize(75, 40))

        self.horizontalLayout.addWidget(self.buttonStop)

        self.line_4 = QFrame(self.settings)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShadow(QFrame.Shadow.Plain)
        self.line_4.setFrameShape(QFrame.Shape.VLine)

        self.horizontalLayout.addWidget(self.line_4)

        self.buttonSave = QPushButton(self.settings)
        self.buttonSave.setObjectName(u"buttonSave")
        self.buttonSave.setEnabled(False)
        self.buttonSave.setMinimumSize(QSize(100, 30))
        self.buttonSave.setMaximumSize(QSize(75, 40))

        self.horizontalLayout.addWidget(self.buttonSave)


        self.formLayout.setLayout(16, QFormLayout.ItemRole.SpanningRole, self.horizontalLayout)

        self.autoSave = QCheckBox(self.settings)
        self.autoSave.setObjectName(u"autoSave")
        self.autoSave.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.autoSave.setChecked(True)
        self.autoSave.setTristate(False)

        self.formLayout.setWidget(17, QFormLayout.ItemRole.FieldRole, self.autoSave)

        self.line_6 = QFrame(self.settings)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShadow(QFrame.Shadow.Sunken)
        self.line_6.setLineWidth(1)
        self.line_6.setMidLineWidth(0)
        self.line_6.setFrameShape(QFrame.Shape.HLine)

        self.formLayout.setWidget(15, QFormLayout.ItemRole.SpanningRole, self.line_6)

        self.label_10.raise_()
        self.label_8.raise_()
        self.cVoltage.raise_()
        self.label_9.raise_()
        self.cDuration.raise_()
        self.query_label.raise_()
        self.cQueryMode.raise_()
        self.label_12.raise_()
        self.cMode.raise_()
        self.label.raise_()
        self.cVersion.raise_()
        self.line_3.raise_()
        self.mode_label.raise_()
        self.duration_label.raise_()
        self.sDuration.raise_()
        self.volt_label.raise_()
        self.buttonSetting.raise_()
        self.line_5.raise_()
        self.label_6.raise_()
        self.radSample.raise_()
        self.label_5.raise_()
        self.suffix.raise_()
        self.autoSave.raise_()
        self.line_6.raise_()

        self.horizontalLayout_3.addWidget(self.settings)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.VLine)

        self.horizontalLayout_3.addWidget(self.line)

        self.gridGroupBox = QGroupBox(self.centralwidget)
        self.gridGroupBox.setObjectName(u"gridGroupBox")
        self.gridGroupBox.setFont(font)
        self.gridGroupBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gridGroupBox.setFlat(False)
        self.gridLayout_2 = QGridLayout(self.gridGroupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.line_2 = QFrame(self.gridGroupBox)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShadow(QFrame.Shadow.Plain)
        self.line_2.setFrameShape(QFrame.Shape.HLine)

        self.gridLayout_2.addWidget(self.line_2, 3, 0, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_2 = QLabel(self.gridGroupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_3 = QLabel(self.gridGroupBox)
        self.label_3.setObjectName(u"label_3")
        sizePolicy3.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy3)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label_3, 2, 1, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.statusLED = QLabel(self.gridGroupBox)
        self.statusLED.setObjectName(u"statusLED")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.statusLED.sizePolicy().hasHeightForWidth())
        self.statusLED.setSizePolicy(sizePolicy8)
        self.statusLED.setMinimumSize(QSize(20, 20))
        self.statusLED.setMaximumSize(QSize(20, 20))
        self.statusLED.setStyleSheet(u"background-color: rgb(255, 11, 3); border: 0px; padding: 4px; border-radius: 10px")
        self.statusLED.setFrameShape(QFrame.Shape.Box)
        self.statusLED.setText(u"")

        self.horizontalLayout_2.addWidget(self.statusLED)

        self.statusText = QLabel(self.gridGroupBox)
        self.statusText.setObjectName(u"statusText")
        sizePolicy9 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.statusText.sizePolicy().hasHeightForWidth())
        self.statusText.setSizePolicy(sizePolicy9)

        self.horizontalLayout_2.addWidget(self.statusText)


        self.gridLayout_3.addLayout(self.horizontalLayout_2, 0, 1, 1, 1)

        self.progressBar = QProgressBar(self.gridGroupBox)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)

        self.gridLayout_3.addWidget(self.progressBar, 1, 0, 1, 2)

        self.label_4 = QLabel(self.gridGroupBox)
        self.label_4.setObjectName(u"label_4")
        sizePolicy3.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy3)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label_4, 2, 0, 1, 1)

        self.currentCount = QLCDNumber(self.gridGroupBox)
        self.currentCount.setObjectName(u"currentCount")
        sizePolicy10 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(0)
        sizePolicy10.setHeightForWidth(self.currentCount.sizePolicy().hasHeightForWidth())
        self.currentCount.setSizePolicy(sizePolicy10)
        self.currentCount.setMinimumSize(QSize(300, 70))
        self.currentCount.setMaximumSize(QSize(0, 70))
        self.currentCount.setFrameShape(QFrame.Shape.Box)
        self.currentCount.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_3.addWidget(self.currentCount, 3, 1, 1, 1)

        self.lastCount = QLCDNumber(self.gridGroupBox)
        self.lastCount.setObjectName(u"lastCount")
        sizePolicy10.setHeightForWidth(self.lastCount.sizePolicy().hasHeightForWidth())
        self.lastCount.setSizePolicy(sizePolicy10)
        self.lastCount.setMinimumSize(QSize(300, 70))
        self.lastCount.setMaximumSize(QSize(0, 70))
        self.lastCount.setFrameShape(QFrame.Shape.Box)
        self.lastCount.setFrameShadow(QFrame.Shadow.Raised)

        self.gridLayout_3.addWidget(self.lastCount, 3, 0, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout_3, 0, 0, 1, 1)

        self.tabWidget = QTabWidget(self.gridGroupBox)
        self.tabWidget.setObjectName(u"tabWidget")
        self.timePlot = QWidget()
        self.timePlot.setObjectName(u"timePlot")
        self.tabWidget.addTab(self.timePlot, "")
        self.histogramm = QWidget()
        self.histogramm.setObjectName(u"histogramm")
        self.tabWidget.addTab(self.histogramm, "")
        self.list = QWidget()
        self.list.setObjectName(u"list")
        sizePolicy11 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy11.setHorizontalStretch(0)
        sizePolicy11.setVerticalStretch(0)
        sizePolicy11.setHeightForWidth(self.list.sizePolicy().hasHeightForWidth())
        self.list.setSizePolicy(sizePolicy11)
        self.gridLayout = QGridLayout(self.list)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tableView = QTableView(self.list)
        self.tableView.setObjectName(u"tableView")

        self.gridLayout.addWidget(self.tableView, 0, 0, 1, 1)

        self.tabWidget.addTab(self.list, "")

        self.gridLayout_2.addWidget(self.tabWidget, 4, 0, 1, 1)

        self.gridLayout_2.setRowStretch(0, 1)
        self.gridLayout_2.setRowStretch(4, 5)

        self.horizontalLayout_3.addWidget(self.gridGroupBox)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(2, 10)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1084, 24))
        MainWindow.setMenuBar(self.menubar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)
        self.voltDial.valueChanged.connect(self.sVoltage.setValue)
        self.sVoltage.valueChanged.connect(self.voltDial.setValue)

        self.buttonSetting.setDefault(False)
        self.radSample.setCurrentIndex(-1)
        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.settings.setTitle(QCoreApplication.translate("MainWindow", u"Einstellungen", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"GM-Spannung / V", None))
#if QT_CONFIG(tooltip)
        self.cVoltage.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuelle GM-Spannung", None))
#endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Z\u00e4hldauer / s", None))
#if QT_CONFIG(tooltip)
        self.cDuration.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuelle eingestellte Z\u00e4hldauer. 999 f\u00fcr unendllich", None))
#endif // QT_CONFIG(tooltip)
        self.query_label.setText(QCoreApplication.translate("MainWindow", u"Abfragemodus", None))
#if QT_CONFIG(tooltip)
        self.cQueryMode.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuell eingestellter Abfragemodus der Z\u00e4hlergebnisse", None))
#endif // QT_CONFIG(tooltip)
        self.cQueryMode.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Z\u00e4hl-Modus", None))
#if QT_CONFIG(tooltip)
        self.cMode.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuell eingestellter Z\u00e4hlmodus", None))
#endif // QT_CONFIG(tooltip)
        self.cMode.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Version", None))
#if QT_CONFIG(tooltip)
        self.cVersion.setToolTip(QCoreApplication.translate("MainWindow", u"GM-Z\u00e4hler Firmware", None))
#endif // QT_CONFIG(tooltip)
        self.cVersion.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.mode_label.setText(QCoreApplication.translate("MainWindow", u"Z\u00e4hl-Modus", None))
#if QT_CONFIG(tooltip)
        self.sModeSingle.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Stoppt die Messung nach Ablauf Z\u00e4hldauer</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.sModeSingle.setText(QCoreApplication.translate("MainWindow", u"Einzel", None))
#if QT_CONFIG(tooltip)
        self.sModeMulti.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Wiederholt die Messung automatisch nach Ablauf Z\u00e4hldauer</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.sModeMulti.setText(QCoreApplication.translate("MainWindow", u"Wiederholung", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Abfragemodus", None))
        self.sQModeMan.setText(QCoreApplication.translate("MainWindow", u"Manuell", None))
        self.sQModeAuto.setText(QCoreApplication.translate("MainWindow", u"Automatik", None))
        self.duration_label.setText(QCoreApplication.translate("MainWindow", u"Z\u00e4hldauer", None))
        self.sDuration.setItemText(0, QCoreApplication.translate("MainWindow", u"unendlich", u"f0"))
        self.sDuration.setItemText(1, QCoreApplication.translate("MainWindow", u"1 Sekunde", u"f1"))
        self.sDuration.setItemText(2, QCoreApplication.translate("MainWindow", u"10 Sekunden", u"f2"))
        self.sDuration.setItemText(3, QCoreApplication.translate("MainWindow", u"60 Sekunden", u"f3"))
        self.sDuration.setItemText(4, QCoreApplication.translate("MainWindow", u"100 Sekunden", u"f4"))
        self.sDuration.setItemText(5, QCoreApplication.translate("MainWindow", u"300 Sekunden", u"f5"))

#if QT_CONFIG(tooltip)
        self.sDuration.setToolTip(QCoreApplication.translate("MainWindow", u"Wie lange der Z\u00e4hler misst", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.volt_label.setToolTip(QCoreApplication.translate("MainWindow", u"Spannung des Geiger-M\u00fcller Z\u00e4hlrohrs", None))
#endif // QT_CONFIG(tooltip)
        self.volt_label.setText(QCoreApplication.translate("MainWindow", u"GM-Spannung", None))
        self.sVoltage.setSuffix(QCoreApplication.translate("MainWindow", u" V", None))
        self.buttonSetting.setText(QCoreApplication.translate("MainWindow", u"Einstellungen \u00e4ndern", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Radioaktive Probe", None))
        self.radSample.setItemText(0, QCoreApplication.translate("MainWindow", u"E00200", None))
        self.radSample.setItemText(1, QCoreApplication.translate("MainWindow", u"E03607", None))
        self.radSample.setItemText(2, QCoreApplication.translate("MainWindow", u"E23303", None))
        self.radSample.setItemText(3, QCoreApplication.translate("MainWindow", u"E30347", None))
        self.radSample.setItemText(4, QCoreApplication.translate("MainWindow", u"E32090", None))
        self.radSample.setItemText(5, QCoreApplication.translate("MainWindow", u"E34316", None))
        self.radSample.setItemText(6, QCoreApplication.translate("MainWindow", u"E38069", None))
        self.radSample.setItemText(7, QCoreApplication.translate("MainWindow", u"E43002", None))
        self.radSample.setItemText(8, QCoreApplication.translate("MainWindow", u"E44367", None))
        self.radSample.setItemText(9, QCoreApplication.translate("MainWindow", u"E52165", None))
        self.radSample.setItemText(10, QCoreApplication.translate("MainWindow", u"E54024", None))
        self.radSample.setItemText(11, QCoreApplication.translate("MainWindow", u"E55600", None))
        self.radSample.setItemText(12, QCoreApplication.translate("MainWindow", u"E62894", None))
        self.radSample.setItemText(13, QCoreApplication.translate("MainWindow", u"E63699", None))
        self.radSample.setItemText(14, QCoreApplication.translate("MainWindow", u"E67594", None))
        self.radSample.setItemText(15, QCoreApplication.translate("MainWindow", u"E75572", None))
        self.radSample.setItemText(16, QCoreApplication.translate("MainWindow", u"E76054", None))
        self.radSample.setItemText(17, QCoreApplication.translate("MainWindow", u"E78857", None))
        self.radSample.setItemText(18, QCoreApplication.translate("MainWindow", u"E80533", None))
        self.radSample.setItemText(19, QCoreApplication.translate("MainWindow", u"E82518", None))
        self.radSample.setItemText(20, QCoreApplication.translate("MainWindow", u"E87198", None))
        self.radSample.setItemText(21, QCoreApplication.translate("MainWindow", u"E89152", None))
        self.radSample.setItemText(22, QCoreApplication.translate("MainWindow", u"E92206", None))
        self.radSample.setItemText(23, QCoreApplication.translate("MainWindow", u"E93652", None))
        self.radSample.setItemText(24, QCoreApplication.translate("MainWindow", u"E93945", None))
        self.radSample.setItemText(25, QCoreApplication.translate("MainWindow", u"E95829", None))
        self.radSample.setItemText(26, QCoreApplication.translate("MainWindow", u"E96269", None))
        self.radSample.setItemText(27, QCoreApplication.translate("MainWindow", u"E99208", None))

#if QT_CONFIG(tooltip)
        self.radSample.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Auswahl der verwendeten Radioaktiven Probe <span style=\" color:#ff001a;\">(Pflichtfeld)</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.radSample.setCurrentText("")
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Eigenes Suffix", None))
#if QT_CONFIG(tooltip)
        self.suffix.setToolTip(QCoreApplication.translate("MainWindow", u"Ein benutzerdefiniertes Suffix mit maximal 20 Zeichen", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.buttonStart.setToolTip(QCoreApplication.translate("MainWindow", u"Start der Messung", None))
#endif // QT_CONFIG(tooltip)
        self.buttonStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
#if QT_CONFIG(tooltip)
        self.buttonStop.setToolTip(QCoreApplication.translate("MainWindow", u"Aktuelle Messung stoppen", None))
#endif // QT_CONFIG(tooltip)
        self.buttonStop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
#if QT_CONFIG(tooltip)
        self.buttonSave.setToolTip(QCoreApplication.translate("MainWindow", u"Messung speichern (Dateidialog)", None))
#endif // QT_CONFIG(tooltip)
        self.buttonSave.setText(QCoreApplication.translate("MainWindow", u"Speichern", None))
#if QT_CONFIG(tooltip)
        self.autoSave.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Bei Aktivierung werden die Messungen automatisch im Format:</p><p>YYYY_MM_DD-<span style=\" font-style:italic;\">Radioaktive Probe</span>-<span style=\" font-style:italic;\">Suffix</span>.csv</p><p>im Ordner Dokumente/Geiger-Mueller/ gespeichert.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.autoSave.setText(QCoreApplication.translate("MainWindow", u"Automatisch Speichern ", None))
        self.gridGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Live-Metriken", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Status:", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Aktuell", None))
        self.statusText.setText(QCoreApplication.translate("MainWindow", u"unknown", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Voriger Wert", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.timePlot), QCoreApplication.translate("MainWindow", u"Zeitverlauf", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.histogramm), QCoreApplication.translate("MainWindow", u"Histogramm", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.list), QCoreApplication.translate("MainWindow", u"Liste", None))
    # retranslateUi

