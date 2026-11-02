# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'simulation_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QFormLayout, QGroupBox,
    QLabel, QPushButton, QSizePolicy, QWidget)

class Ui_SimulationPanel(object):
    def setupUi(self, SimulationPanel):
        if not SimulationPanel.objectName():
            SimulationPanel.setObjectName(u"SimulationPanel")
        self.formLayout = QFormLayout(SimulationPanel)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.captionStartFrequency = QLabel(SimulationPanel)
        self.captionStartFrequency.setObjectName(u"captionStartFrequency")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.captionStartFrequency)

        self.spinStartFrequency = QDoubleSpinBox(SimulationPanel)
        self.spinStartFrequency.setObjectName(u"spinStartFrequency")
        self.spinStartFrequency.setDecimals(1)
        self.spinStartFrequency.setMinimum(1.000000000000000)
        self.spinStartFrequency.setMaximum(60.000000000000000)
        self.spinStartFrequency.setSingleStep(0.500000000000000)
        self.spinStartFrequency.setValue(15.000000000000000)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.spinStartFrequency)

        self.buttonKick = QPushButton(SimulationPanel)
        self.buttonKick.setObjectName(u"buttonKick")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.buttonKick)


        self.retranslateUi(SimulationPanel)

        QMetaObject.connectSlotsByName(SimulationPanel)
    # setupUi

    def retranslateUi(self, SimulationPanel):
        SimulationPanel.setTitle(QCoreApplication.translate("SimulationPanel", u"Simulation", None))
        self.captionStartFrequency.setText(QCoreApplication.translate("SimulationPanel", u"Startfrequenz", None))
        self.spinStartFrequency.setSuffix(QCoreApplication.translate("SimulationPanel", u" Hz", None))
#if QT_CONFIG(tooltip)
        self.spinStartFrequency.setToolTip(QCoreApplication.translate("SimulationPanel", u"Rotationsfrequenz, mit der die simulierte Scheibe angeworfen wird", None))
#endif // QT_CONFIG(tooltip)
        self.buttonKick.setText(QCoreApplication.translate("SimulationPanel", u"Anwerfen", None))
#if QT_CONFIG(tooltip)
        self.buttonKick.setToolTip(QCoreApplication.translate("SimulationPanel", u"Simulierte Scheibe mit der Startfrequenz neu anwerfen", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

