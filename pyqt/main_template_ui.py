# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_template.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLayout, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
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
        self.demoMode = QAction(MainWindow)
        self.demoMode.setObjectName(u"demoMode")
        self.demoMode.setCheckable(True)
        self.controlWindow = QAction(MainWindow)
        self.controlWindow.setObjectName(u"controlWindow")
        self.controlWindow.setCheckable(True)
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

        self.horizontalLayout_2.setStretch(0, 15)

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
        QWidget.setTabOrder(self.buttonStart, self.buttonStop)
        QWidget.setTabOrder(self.buttonStop, self.buttonSave)

        self.menuBar.addAction(self.menuTK47.menuAction())
        self.menuTK47.addAction(self.controlWindow)
        self.menuTK47.addSeparator()

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"TK47 - Radioactivity", None))
        self.demoMode.setText(QCoreApplication.translate("MainWindow", u"Demomodus aktivieren", None))
        self.controlWindow.setText(QCoreApplication.translate("MainWindow", u"Kontroll-Fenster", None))
#if QT_CONFIG(tooltip)
        self.controlWindow.setToolTip(QCoreApplication.translate("MainWindow", u"\u00d6ffnet ein neues Kontroll-Fenster", None))
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
        self.menuTK47.setTitle(QCoreApplication.translate("MainWindow", u"TK47 - Radioaktivit\u00e4t", None))
    # retranslateUi

