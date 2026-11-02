# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'live_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGroupBox, QLCDNumber,
    QLabel, QSizePolicy, QWidget)

class Ui_LivePanel(object):
    def setupUi(self, LivePanel):
        if not LivePanel.objectName():
            LivePanel.setObjectName(u"LivePanel")
        self.formLayout = QFormLayout(LivePanel)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.formLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.captionFrequency = QLabel(LivePanel)
        self.captionFrequency.setObjectName(u"captionFrequency")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.captionFrequency)

        self.lcdFrequency = QLCDNumber(LivePanel)
        self.lcdFrequency.setObjectName(u"lcdFrequency")
        self.lcdFrequency.setMinimumSize(QSize(120, 40))
        self.lcdFrequency.setDigitCount(8)
        self.lcdFrequency.setSmallDecimalPoint(True)
        self.lcdFrequency.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lcdFrequency)

        self.captionGyroZ = QLabel(LivePanel)
        self.captionGyroZ.setObjectName(u"captionGyroZ")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.captionGyroZ)

        self.lcdGyroZ = QLCDNumber(LivePanel)
        self.lcdGyroZ.setObjectName(u"lcdGyroZ")
        self.lcdGyroZ.setMinimumSize(QSize(120, 40))
        self.lcdGyroZ.setDigitCount(8)
        self.lcdGyroZ.setSmallDecimalPoint(True)
        self.lcdGyroZ.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lcdGyroZ)

        self.captionPoints = QLabel(LivePanel)
        self.captionPoints.setObjectName(u"captionPoints")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.captionPoints)

        self.lcdPoints = QLCDNumber(LivePanel)
        self.lcdPoints.setObjectName(u"lcdPoints")
        self.lcdPoints.setMinimumSize(QSize(120, 40))
        self.lcdPoints.setDigitCount(8)
        self.lcdPoints.setSmallDecimalPoint(True)
        self.lcdPoints.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.lcdPoints)

        self.captionDuration = QLabel(LivePanel)
        self.captionDuration.setObjectName(u"captionDuration")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.captionDuration)

        self.labelDuration = QLabel(LivePanel)
        self.labelDuration.setObjectName(u"labelDuration")
        self.labelDuration.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.labelDuration)


        self.retranslateUi(LivePanel)

        QMetaObject.connectSlotsByName(LivePanel)
    # setupUi

    def retranslateUi(self, LivePanel):
        LivePanel.setTitle(QCoreApplication.translate("LivePanel", u"Live-Messwerte", None))
        self.captionFrequency.setText(QCoreApplication.translate("LivePanel", u"Rotationsfrequenz (Hz)", None))
#if QT_CONFIG(tooltip)
        self.lcdFrequency.setToolTip(QCoreApplication.translate("LivePanel", u"Aktuelle Rotationsfrequenz der Kreiselscheibe in Hertz", None))
#endif // QT_CONFIG(tooltip)
        self.captionGyroZ.setText(QCoreApplication.translate("LivePanel", u"Z-Rotation (rad/s)", None))
#if QT_CONFIG(tooltip)
        self.lcdGyroZ.setToolTip(QCoreApplication.translate("LivePanel", u"Aktuelle Winkelgeschwindigkeit um die z-Achse in Radiant pro Sekunde", None))
#endif // QT_CONFIG(tooltip)
        self.captionPoints.setText(QCoreApplication.translate("LivePanel", u"Datenpunkte", None))
#if QT_CONFIG(tooltip)
        self.lcdPoints.setToolTip(QCoreApplication.translate("LivePanel", u"Anzahl der aufgezeichneten Messwerte", None))
#endif // QT_CONFIG(tooltip)
        self.captionDuration.setText(QCoreApplication.translate("LivePanel", u"Dauer (mm:ss)", None))
#if QT_CONFIG(tooltip)
        self.labelDuration.setToolTip(QCoreApplication.translate("LivePanel", u"Dauer der aktuellen Aufzeichnung", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

