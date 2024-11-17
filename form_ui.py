# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QLCDNumber,
    QLabel, QLayout, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QSpacerItem, QStatusBar, QTimeEdit,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1043, 677)
        MainWindow.setMinimumSize(QSize(1000, 500))
        font = QFont()
        font.setFamilies([u"Helvetica Neue"])
        font.setPointSize(14)
        MainWindow.setFont(font)
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.WeatherStorm))
        MainWindow.setWindowIcon(icon)
        self.actionHallo = QAction(MainWindow)
        self.actionHallo.setObjectName(u"actionHallo")
        self.actionmuhhh = QAction(MainWindow)
        self.actionmuhhh.setObjectName(u"actionmuhhh")
        self.demoMode = QAction(MainWindow)
        self.demoMode.setObjectName(u"demoMode")
        self.demoMode.setCheckable(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(15, 15, 15, 15)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widgetPlot = QWidget(self.centralwidget)
        self.widgetPlot.setObjectName(u"widgetPlot")
        self.widgetPlot.setMinimumSize(QSize(400, 0))
        self.widgetPlot.setAutoFillBackground(False)
        self.widgetPlot.setStyleSheet(u"background-color: rgba(255, 255, 255, 0);")

        self.horizontalLayout_2.addWidget(self.widgetPlot)

        self.line_4 = QFrame(self.centralwidget)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.VLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_2.addWidget(self.line_4)

        self.framePlot = QFrame(self.centralwidget)
        self.framePlot.setObjectName(u"framePlot")
        self.framePlot.setFrameShape(QFrame.Shape.Box)
        self.framePlot.setFrameShadow(QFrame.Shadow.Raised)
        self.framePlot.setLineWidth(0)
        self.verticalLayout_4 = QVBoxLayout(self.framePlot)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label = QLabel(self.framePlot)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_4.addWidget(self.label)

        self.currentData = QLCDNumber(self.framePlot)
        self.currentData.setObjectName(u"currentData")
        self.currentData.setEnabled(False)
        self.currentData.setMinimumSize(QSize(0, 40))
        self.currentData.setDigitCount(6)
        self.currentData.setSegmentStyle(QLCDNumber.SegmentStyle.Filled)
        self.currentData.setProperty(u"value", 30.000000000000000)
        self.currentData.setProperty(u"intValue", 30)

        self.verticalLayout_4.addWidget(self.currentData)

        self.lastData = QListWidget(self.framePlot)
        self.lastData.setObjectName(u"lastData")
        self.lastData.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.lastData.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lastData.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.lastData.setItemAlignment(Qt.AlignmentFlag.AlignLeading)

        self.verticalLayout_4.addWidget(self.lastData)

        self.line = QFrame(self.framePlot)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.line)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(-1, 0, -1, -1)
        self.labelTimer = QLabel(self.framePlot)
        self.labelTimer.setObjectName(u"labelTimer")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelTimer)

        self.inputTimer = QTimeEdit(self.framePlot)
        self.inputTimer.setObjectName(u"inputTimer")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.inputTimer)


        self.verticalLayout_4.addLayout(self.formLayout)

        self.verticalLayout_4.setStretch(0, 1)
        self.verticalLayout_4.setStretch(1, 1)
        self.verticalLayout_4.setStretch(2, 15)
        self.verticalLayout_4.setStretch(3, 1)
        self.verticalLayout_4.setStretch(4, 1)

        self.horizontalLayout_2.addWidget(self.framePlot)

        self.horizontalLayout_2.setStretch(0, 15)
        self.horizontalLayout_2.setStretch(2, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.line_3 = QFrame(self.centralwidget)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.labelSerial = QLabel(self.centralwidget)
        self.labelSerial.setObjectName(u"labelSerial")
        self.labelSerial.setMinimumSize(QSize(90, 30))
        self.labelSerial.setMaximumSize(QSize(80, 30))
        self.labelSerial.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.labelSerial)

        self.comboSerial = QComboBox(self.centralwidget)
        self.comboSerial.setObjectName(u"comboSerial")
        self.comboSerial.setMinimumSize(QSize(300, 0))

        self.horizontalLayout.addWidget(self.comboSerial)

        self.buttonRefreshSerial = QPushButton(self.centralwidget)
        self.buttonRefreshSerial.setObjectName(u"buttonRefreshSerial")
        self.buttonRefreshSerial.setMaximumSize(QSize(35, 40))
        icon1 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ViewRefresh))
        self.buttonRefreshSerial.setIcon(icon1)

        self.horizontalLayout.addWidget(self.buttonRefreshSerial)

        self.buttonConnect = QPushButton(self.centralwidget)
        self.buttonConnect.setObjectName(u"buttonConnect")
        self.buttonConnect.setMinimumSize(QSize(100, 40))
        self.buttonConnect.setMaximumSize(QSize(100, 40))
        icon2 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.GoNext))
        self.buttonConnect.setIcon(icon2)

        self.horizontalLayout.addWidget(self.buttonConnect)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.buttonStart = QPushButton(self.centralwidget)
        self.buttonStart.setObjectName(u"buttonStart")
        self.buttonStart.setEnabled(False)
        self.buttonStart.setMinimumSize(QSize(75, 30))
        self.buttonStart.setMaximumSize(QSize(75, 40))

        self.horizontalLayout.addWidget(self.buttonStart)

        self.buttonStop = QPushButton(self.centralwidget)
        self.buttonStop.setObjectName(u"buttonStop")
        self.buttonStop.setEnabled(False)
        self.buttonStop.setMinimumSize(QSize(75, 30))
        self.buttonStop.setMaximumSize(QSize(75, 40))

        self.horizontalLayout.addWidget(self.buttonStop)

        self.line_2 = QFrame(self.centralwidget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line_2)

        self.buttonSave = QPushButton(self.centralwidget)
        self.buttonSave.setObjectName(u"buttonSave")
        self.buttonSave.setEnabled(False)
        self.buttonSave.setMinimumSize(QSize(100, 30))
        self.buttonSave.setMaximumSize(QSize(75, 40))

        self.horizontalLayout.addWidget(self.buttonSave)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout.setStretch(0, 10)

        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.gridLayout.setRowStretch(0, 10)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        self.statusBar.setEnabled(True)
        MainWindow.setStatusBar(self.statusBar)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 1043, 24))
        self.menuTK47 = QMenu(self.menuBar)
        self.menuTK47.setObjectName(u"menuTK47")
        MainWindow.setMenuBar(self.menuBar)
#if QT_CONFIG(shortcut)
        self.labelTimer.setBuddy(self.inputTimer)
        self.labelSerial.setBuddy(self.comboSerial)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.comboSerial, self.buttonRefreshSerial)
        QWidget.setTabOrder(self.buttonRefreshSerial, self.buttonConnect)
        QWidget.setTabOrder(self.buttonConnect, self.inputTimer)
        QWidget.setTabOrder(self.inputTimer, self.buttonStart)
        QWidget.setTabOrder(self.buttonStart, self.buttonStop)
        QWidget.setTabOrder(self.buttonStop, self.buttonSave)
        QWidget.setTabOrder(self.buttonSave, self.lastData)

        self.menuBar.addAction(self.menuTK47.menuAction())
        self.menuTK47.addAction(self.demoMode)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"TK47 - Radioactivity", None))
        self.actionHallo.setText(QCoreApplication.translate("MainWindow", u"Hallo", None))
        self.actionmuhhh.setText(QCoreApplication.translate("MainWindow", u"muhhh", None))
        self.demoMode.setText(QCoreApplication.translate("MainWindow", u"Demomodus aktivieren", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Letzte Zeit / \u00b5s:", None))
        self.labelTimer.setText(QCoreApplication.translate("MainWindow", u"Timer:", None))
#if QT_CONFIG(tooltip)
        self.inputTimer.setToolTip(QCoreApplication.translate("MainWindow", u"F\u00fcr die Messung kann ein Timer eingestellt werden.", None))
#endif // QT_CONFIG(tooltip)
        self.labelSerial.setText(QCoreApplication.translate("MainWindow", u"Serielle Ports:", None))
#if QT_CONFIG(tooltip)
        self.comboSerial.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Kommunikation mit dem Arduino erfolgt \u00fcber die serielle Schnittstelle. </p><p>Wenn Arduino nicht erkannt wird, die Verbindung pr\u00fcfen und evtl. Treiber installieren.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.comboSerial.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Bitte Seriellen Port ausw\u00e4hlen", None))
#if QT_CONFIG(tooltip)
        self.buttonRefreshSerial.setToolTip(QCoreApplication.translate("MainWindow", u"Die Liste der Ports aktualisieren", None))
#endif // QT_CONFIG(tooltip)
        self.buttonRefreshSerial.setText("")
#if QT_CONFIG(tooltip)
        self.buttonConnect.setToolTip(QCoreApplication.translate("MainWindow", u"Nach Auswahl eines Ports kann eine Verbindung mit diesem hergestellt werden.", None))
#endif // QT_CONFIG(tooltip)
        self.buttonConnect.setText(QCoreApplication.translate("MainWindow", u"Verbinden", None))
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
        self.menuTK47.setTitle(QCoreApplication.translate("MainWindow", u"TK47 - Radioaktivit\u00e4t", None))
    # retranslateUi

