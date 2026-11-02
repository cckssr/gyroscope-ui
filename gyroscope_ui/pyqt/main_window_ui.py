# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
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
from PySide6.QtWidgets import (QApplication, QDockWidget, QFrame, QMainWindow,
    QScrollArea, QSizePolicy, QSpacerItem, QStatusBar,
    QTabWidget, QToolBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 720)
        self.actionConnect = QAction(MainWindow)
        self.actionConnect.setObjectName(u"actionConnect")
        self.actionConnect.setCheckable(False)
        self.actionStartStop = QAction(MainWindow)
        self.actionStartStop.setObjectName(u"actionStartStop")
        self.actionStartStop.setCheckable(False)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave.setCheckable(False)
        self.actionShortcuts = QAction(MainWindow)
        self.actionShortcuts.setObjectName(u"actionShortcuts")
        self.actionShortcuts.setCheckable(False)
        self.actionOpenDataFolder = QAction(MainWindow)
        self.actionOpenDataFolder.setObjectName(u"actionOpenDataFolder")
        self.actionOpenDataFolder.setCheckable(False)
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName(u"actionQuit")
        self.actionQuit.setCheckable(False)
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionAbout.setCheckable(False)
        self.tabs = QTabWidget(MainWindow)
        self.tabs.setObjectName(u"tabs")
        MainWindow.setCentralWidget(self.tabs)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)
        self.dockControls = QDockWidget(MainWindow)
        self.dockControls.setObjectName(u"dockControls")
        self.dockControls.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable|QDockWidget.DockWidgetFeature.DockWidgetFloatable|QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.dockControls.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea|Qt.DockWidgetArea.RightDockWidgetArea)
        self.dockControlsContents = QWidget()
        self.dockControlsContents.setObjectName(u"dockControlsContents")
        self.layoutDockControls = QVBoxLayout(self.dockControlsContents)
        self.layoutDockControls.setObjectName(u"layoutDockControls")
        self.layoutDockControls.setContentsMargins(0, 0, 0, 0)
        self.scrollControls = QScrollArea(self.dockControlsContents)
        self.scrollControls.setObjectName(u"scrollControls")
        self.scrollControls.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollControls.setWidgetResizable(True)
        self.controlsContent = QWidget()
        self.controlsContent.setObjectName(u"controlsContent")
        self.layoutControls = QVBoxLayout(self.controlsContent)
        self.layoutControls.setSpacing(6)
        self.layoutControls.setObjectName(u"layoutControls")
        self.layoutControls.setContentsMargins(4, 4, 4, 4)
        self.spacerControls = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layoutControls.addItem(self.spacerControls)

        self.scrollControls.setWidget(self.controlsContent)

        self.layoutDockControls.addWidget(self.scrollControls)

        self.dockControls.setWidget(self.dockControlsContents)
        MainWindow.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockControls)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.toolBar.addAction(self.actionConnect)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionStartStop)
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addAction(self.actionOpenDataFolder)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionShortcuts)
        self.toolBar.addAction(self.actionAbout)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionQuit)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Kreisel-GUI", None))
        self.actionConnect.setText(QCoreApplication.translate("MainWindow", u"Verbinden", None))
#if QT_CONFIG(tooltip)
        self.actionConnect.setToolTip(QCoreApplication.translate("MainWindow", u"Verbindung zum Ger\u00e4t herstellen oder trennen", None))
#endif // QT_CONFIG(tooltip)
        self.actionStartStop.setText(QCoreApplication.translate("MainWindow", u"Start", None))
#if QT_CONFIG(tooltip)
        self.actionStartStop.setToolTip(QCoreApplication.translate("MainWindow", u"Messung starten oder stoppen", None))
#endif // QT_CONFIG(tooltip)
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Speichern \u2026", None))
#if QT_CONFIG(tooltip)
        self.actionSave.setToolTip(QCoreApplication.translate("MainWindow", u"Messung in eine Datei speichern", None))
#endif // QT_CONFIG(tooltip)
        self.actionShortcuts.setText(QCoreApplication.translate("MainWindow", u"Tastenk\u00fcrzel", None))
#if QT_CONFIG(tooltip)
        self.actionShortcuts.setToolTip(QCoreApplication.translate("MainWindow", u"\u00dcbersicht aller Tastenk\u00fcrzel anzeigen", None))
#endif // QT_CONFIG(tooltip)
        self.actionOpenDataFolder.setText(QCoreApplication.translate("MainWindow", u"Datenordner \u00f6ffnen", None))
#if QT_CONFIG(tooltip)
        self.actionOpenDataFolder.setToolTip(QCoreApplication.translate("MainWindow", u"Den Ordner mit den gespeicherten Messungen im Dateimanager \u00f6ffnen", None))
#endif // QT_CONFIG(tooltip)
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", u"Beenden", None))
#if QT_CONFIG(tooltip)
        self.actionQuit.setToolTip(QCoreApplication.translate("MainWindow", u"Anwendung beenden", None))
#endif // QT_CONFIG(tooltip)
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"\u00dcber Kreisel-GUI", None))
#if QT_CONFIG(tooltip)
        self.actionAbout.setToolTip(QCoreApplication.translate("MainWindow", u"Version und Informationen zur Anwendung", None))
#endif // QT_CONFIG(tooltip)
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"Werkzeugleiste", None))
        self.dockControls.setWindowTitle(QCoreApplication.translate("MainWindow", u"Steuerung", None))
    # retranslateUi

