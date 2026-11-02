# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'shortcuts_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_ShortcutsDialog(object):
    def setupUi(self, ShortcutsDialog):
        if not ShortcutsDialog.objectName():
            ShortcutsDialog.setObjectName(u"ShortcutsDialog")
        ShortcutsDialog.resize(420, 460)
        self.verticalLayout = QVBoxLayout(ShortcutsDialog)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.labelIntro = QLabel(ShortcutsDialog)
        self.labelIntro.setObjectName(u"labelIntro")
        self.labelIntro.setWordWrap(True)

        self.verticalLayout.addWidget(self.labelIntro)

        self.tableShortcuts = QTableWidget(ShortcutsDialog)
        if (self.tableShortcuts.columnCount() < 2):
            self.tableShortcuts.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableShortcuts.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableShortcuts.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tableShortcuts.setObjectName(u"tableShortcuts")
        self.tableShortcuts.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableShortcuts.setAlternatingRowColors(True)
        self.tableShortcuts.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tableShortcuts.setShowGrid(False)
        self.tableShortcuts.setWordWrap(False)
        self.tableShortcuts.setColumnCount(2)
        self.tableShortcuts.horizontalHeader().setStretchLastSection(False)
        self.tableShortcuts.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.tableShortcuts)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.spacerButtons = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.spacerButtons)

        self.buttonClose = QPushButton(ShortcutsDialog)
        self.buttonClose.setObjectName(u"buttonClose")

        self.buttonLayout.addWidget(self.buttonClose)


        self.verticalLayout.addLayout(self.buttonLayout)


        self.retranslateUi(ShortcutsDialog)

        self.buttonClose.setDefault(True)


        QMetaObject.connectSlotsByName(ShortcutsDialog)
    # setupUi

    def retranslateUi(self, ShortcutsDialog):
        ShortcutsDialog.setWindowTitle(QCoreApplication.translate("ShortcutsDialog", u"Tastenk\u00fcrzel", None))
        self.labelIntro.setText(QCoreApplication.translate("ShortcutsDialog", u"Die Tastenk\u00fcrzel gelten im ganzen Fenster, auch wenn gerade ein Eingabefeld den Fokus hat. Die Leertaste bedient dagegen eine fokussierte Schaltfl\u00e4che bzw. ein Textfeld selbst. Esc stoppt die Messung.", None))
        ___qtablewidgetitem = self.tableShortcuts.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ShortcutsDialog", u"Funktion", None))
        ___qtablewidgetitem1 = self.tableShortcuts.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ShortcutsDialog", u"Tastenk\u00fcrzel", None))
        self.buttonClose.setText(QCoreApplication.translate("ShortcutsDialog", u"Schlie\u00dfen", None))
    # retranslateUi

