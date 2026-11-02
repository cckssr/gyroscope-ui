# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'measurement_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

from gyroscope_ui.ui.widgets.elided_label import ElidedLabel

class Ui_MeasurementPanel(object):
    def setupUi(self, MeasurementPanel):
        if not MeasurementPanel.objectName():
            MeasurementPanel.setObjectName(u"MeasurementPanel")
        self.verticalLayout = QVBoxLayout(MeasurementPanel)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.layoutButtons = QHBoxLayout()
        self.layoutButtons.setObjectName(u"layoutButtons")
        self.buttonStartStop = QPushButton(MeasurementPanel)
        self.buttonStartStop.setObjectName(u"buttonStartStop")

        self.layoutButtons.addWidget(self.buttonStartStop)

        self.buttonReset = QPushButton(MeasurementPanel)
        self.buttonReset.setObjectName(u"buttonReset")

        self.layoutButtons.addWidget(self.buttonReset)


        self.verticalLayout.addLayout(self.layoutButtons)

        self.labelState = ElidedLabel(MeasurementPanel)
        self.labelState.setObjectName(u"labelState")

        self.verticalLayout.addWidget(self.labelState)


        self.retranslateUi(MeasurementPanel)

        QMetaObject.connectSlotsByName(MeasurementPanel)
    # setupUi

    def retranslateUi(self, MeasurementPanel):
        MeasurementPanel.setTitle(QCoreApplication.translate("MeasurementPanel", u"Messung", None))
        self.buttonStartStop.setText(QCoreApplication.translate("MeasurementPanel", u"Start", None))
#if QT_CONFIG(tooltip)
        self.buttonStartStop.setToolTip(QCoreApplication.translate("MeasurementPanel", u"Messung starten oder stoppen", None))
#endif // QT_CONFIG(tooltip)
        self.buttonReset.setText(QCoreApplication.translate("MeasurementPanel", u"Zur\u00fccksetzen", None))
#if QT_CONFIG(tooltip)
        self.buttonReset.setToolTip(QCoreApplication.translate("MeasurementPanel", u"Aktuelle Messreihe verwerfen und neu beginnen", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

