# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'connection_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QWidget)

from gyroscope_ui.ui.widgets.elided_label import ElidedLabel
from gyroscope_ui.ui.widgets.status_led import StatusLed

class Ui_ConnectionPanel(object):
    def setupUi(self, ConnectionPanel):
        if not ConnectionPanel.objectName():
            ConnectionPanel.setObjectName(u"ConnectionPanel")
        self.formLayout = QFormLayout(ConnectionPanel)
        self.formLayout.setObjectName(u"formLayout")
        self.captionState = QLabel(ConnectionPanel)
        self.captionState.setObjectName(u"captionState")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.captionState)

        self.layoutState = QHBoxLayout()
        self.layoutState.setSpacing(6)
        self.layoutState.setObjectName(u"layoutState")
        self.ledLink = StatusLed(ConnectionPanel)
        self.ledLink.setObjectName(u"ledLink")

        self.layoutState.addWidget(self.ledLink)

        self.labelState = ElidedLabel(ConnectionPanel)
        self.labelState.setObjectName(u"labelState")

        self.layoutState.addWidget(self.labelState)


        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.layoutState)

        self.labelDevice = ElidedLabel(ConnectionPanel)
        self.labelDevice.setObjectName(u"labelDevice")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.labelDevice)

        self.labelHint = QLabel(ConnectionPanel)
        self.labelHint.setObjectName(u"labelHint")
        self.labelHint.setWordWrap(True)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.labelHint)

        self.checkSimulate = QCheckBox(ConnectionPanel)
        self.checkSimulate.setObjectName(u"checkSimulate")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.checkSimulate)

        self.buttonConnect = QPushButton(ConnectionPanel)
        self.buttonConnect.setObjectName(u"buttonConnect")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.buttonConnect)


        self.retranslateUi(ConnectionPanel)

        QMetaObject.connectSlotsByName(ConnectionPanel)
    # setupUi

    def retranslateUi(self, ConnectionPanel):
        ConnectionPanel.setTitle(QCoreApplication.translate("ConnectionPanel", u"Ger\u00e4t", None))
        self.captionState.setText(QCoreApplication.translate("ConnectionPanel", u"Status", None))
        self.labelState.setText(QCoreApplication.translate("ConnectionPanel", u"Getrennt", None))
        self.labelHint.setText(QCoreApplication.translate("ConnectionPanel", u"Rechner mit dem WLAN des Kreisels ({ssid}) verbinden und dann \u201eVerbinden\u201c w\u00e4hlen.", None))
        self.checkSimulate.setText(QCoreApplication.translate("ConnectionPanel", u"Simulation", None))
#if QT_CONFIG(tooltip)
        self.checkSimulate.setToolTip(QCoreApplication.translate("ConnectionPanel", u"Simuliertes Ger\u00e4t statt echter Hardware verwenden (nur im getrennten Zustand \u00e4nderbar)", None))
#endif // QT_CONFIG(tooltip)
        self.buttonConnect.setText(QCoreApplication.translate("ConnectionPanel", u"Verbinden", None))
#if QT_CONFIG(tooltip)
        self.buttonConnect.setToolTip(QCoreApplication.translate("ConnectionPanel", u"Verbindung zum Ger\u00e4t herstellen oder trennen", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

