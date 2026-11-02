# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'measurement_view.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

from gyroscope_ui.ui.widgets.gyro_plot import GyroPlot

class Ui_MeasurementView(object):
    def setupUi(self, MeasurementView):
        if not MeasurementView.objectName():
            MeasurementView.setObjectName(u"MeasurementView")
        self.verticalLayout = QVBoxLayout(MeasurementView)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.plot = GyroPlot(MeasurementView)
        self.plot.setObjectName(u"plot")

        self.verticalLayout.addWidget(self.plot)

        self.layoutOptions = QHBoxLayout()
        self.layoutOptions.setObjectName(u"layoutOptions")
        self.checkAutoScroll = QCheckBox(MeasurementView)
        self.checkAutoScroll.setObjectName(u"checkAutoScroll")
        self.checkAutoScroll.setChecked(True)

        self.layoutOptions.addWidget(self.checkAutoScroll)

        self.spinScrollWindow = QSpinBox(MeasurementView)
        self.spinScrollWindow.setObjectName(u"spinScrollWindow")
        self.spinScrollWindow.setMinimum(5)
        self.spinScrollWindow.setMaximum(999999)
        self.spinScrollWindow.setValue(60)

        self.layoutOptions.addWidget(self.spinScrollWindow)

        self.checkAllChannels = QCheckBox(MeasurementView)
        self.checkAllChannels.setObjectName(u"checkAllChannels")

        self.layoutOptions.addWidget(self.checkAllChannels)

        self.buttonAutoRange = QPushButton(MeasurementView)
        self.buttonAutoRange.setObjectName(u"buttonAutoRange")

        self.layoutOptions.addWidget(self.buttonAutoRange)

        self.spacerOptions = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutOptions.addItem(self.spacerOptions)


        self.verticalLayout.addLayout(self.layoutOptions)


        self.retranslateUi(MeasurementView)

        QMetaObject.connectSlotsByName(MeasurementView)
    # setupUi

    def retranslateUi(self, MeasurementView):
        self.checkAutoScroll.setText(QCoreApplication.translate("MeasurementView", u"Auto-Scroll", None))
#if QT_CONFIG(tooltip)
        self.checkAutoScroll.setToolTip(QCoreApplication.translate("MeasurementView", u"Wenn aktiviert, zeigen die Diagramme die neuesten Messwerte und f\u00fchren die Zeitachse mit", None))
#endif // QT_CONFIG(tooltip)
        self.spinScrollWindow.setSuffix(QCoreApplication.translate("MeasurementView", u" s", None))
#if QT_CONFIG(tooltip)
        self.spinScrollWindow.setToolTip(QCoreApplication.translate("MeasurementView", u"Breite des mitlaufenden Zeitfensters in Sekunden", None))
#endif // QT_CONFIG(tooltip)
        self.checkAllChannels.setText(QCoreApplication.translate("MeasurementView", u"Alle Kan\u00e4le", None))
#if QT_CONFIG(tooltip)
        self.checkAllChannels.setToolTip(QCoreApplication.translate("MeasurementView", u"Zus\u00e4tzlich Beschleunigung und die \u00fcbrigen Drehraten anzeigen", None))
#endif // QT_CONFIG(tooltip)
        self.buttonAutoRange.setText(QCoreApplication.translate("MeasurementView", u"Auto-Range", None))
#if QT_CONFIG(tooltip)
        self.buttonAutoRange.setToolTip(QCoreApplication.translate("MeasurementView", u"Achsen automatisch an die Daten anpassen", None))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

