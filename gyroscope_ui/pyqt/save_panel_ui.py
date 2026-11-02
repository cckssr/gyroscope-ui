# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'save_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QToolButton, QWidget)

from gyroscope_ui.ui.widgets.elided_label import ElidedLabel

class Ui_SavePanel(object):
    def setupUi(self, SavePanel):
        if not SavePanel.objectName():
            SavePanel.setObjectName(u"SavePanel")
        self.formLayout = QFormLayout(SavePanel)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.captionGroup = QLabel(SavePanel)
        self.captionGroup.setObjectName(u"captionGroup")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.captionGroup)

        self.comboGroup = QComboBox(SavePanel)
        self.comboGroup.setObjectName(u"comboGroup")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.comboGroup)

        self.captionSubgroup = QLabel(SavePanel)
        self.captionSubgroup.setObjectName(u"captionSubgroup")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.captionSubgroup)

        self.editSubgroup = QLineEdit(SavePanel)
        self.editSubgroup.setObjectName(u"editSubgroup")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.editSubgroup)

        self.captionSuffix = QLabel(SavePanel)
        self.captionSuffix.setObjectName(u"captionSuffix")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.captionSuffix)

        self.editSuffix = QLineEdit(SavePanel)
        self.editSuffix.setObjectName(u"editSuffix")
        self.editSuffix.setMaxLength(20)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.editSuffix)

        self.captionDataDir = QLabel(SavePanel)
        self.captionDataDir.setObjectName(u"captionDataDir")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.captionDataDir)

        self.layoutDataDir = QHBoxLayout()
        self.layoutDataDir.setObjectName(u"layoutDataDir")
        self.editDataDir = QLineEdit(SavePanel)
        self.editDataDir.setObjectName(u"editDataDir")
        self.editDataDir.setReadOnly(True)

        self.layoutDataDir.addWidget(self.editDataDir)

        self.buttonBrowse = QToolButton(SavePanel)
        self.buttonBrowse.setObjectName(u"buttonBrowse")

        self.layoutDataDir.addWidget(self.buttonBrowse)


        self.formLayout.setLayout(3, QFormLayout.ItemRole.FieldRole, self.layoutDataDir)

        self.checkAutoSave = QCheckBox(SavePanel)
        self.checkAutoSave.setObjectName(u"checkAutoSave")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.checkAutoSave)

        self.buttonSave = QPushButton(SavePanel)
        self.buttonSave.setObjectName(u"buttonSave")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.buttonSave)

        self.captionLastSaved = QLabel(SavePanel)
        self.captionLastSaved.setObjectName(u"captionLastSaved")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.captionLastSaved)

        self.labelLastSaved = ElidedLabel(SavePanel)
        self.labelLastSaved.setObjectName(u"labelLastSaved")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.labelLastSaved)


        self.retranslateUi(SavePanel)

        QMetaObject.connectSlotsByName(SavePanel)
    # setupUi

    def retranslateUi(self, SavePanel):
        SavePanel.setTitle(QCoreApplication.translate("SavePanel", u"Speichern", None))
        self.captionGroup.setText(QCoreApplication.translate("SavePanel", u"Gruppe *", None))
#if QT_CONFIG(tooltip)
        self.comboGroup.setToolTip(QCoreApplication.translate("SavePanel", u"Buchstabe der Praktikumsgruppe (Pflichtfeld)", None))
#endif // QT_CONFIG(tooltip)
        self.captionSubgroup.setText(QCoreApplication.translate("SavePanel", u"Untergruppe *", None))
#if QT_CONFIG(tooltip)
        self.editSubgroup.setToolTip(QCoreApplication.translate("SavePanel", u"Untergruppen-Bezeichnung zur Identifikation der Messung (Pflichtfeld). Wird in den Metadaten und im Ordnernamen gespeichert. Sonderzeichen werden durch '_' ersetzt. Maximale L\u00e4nge im Ordnernamen: 20 Zeichen.", None))
#endif // QT_CONFIG(tooltip)
        self.editSubgroup.setPlaceholderText(QCoreApplication.translate("SavePanel", u"z. B. Aufbau 1", None))
        self.captionSuffix.setText(QCoreApplication.translate("SavePanel", u"Suffix", None))
#if QT_CONFIG(tooltip)
        self.editSuffix.setToolTip(QCoreApplication.translate("SavePanel", u"Optionaler Zusatz im Dateinamen beim automatischen Speichern (h\u00f6chstens 20 Zeichen)", None))
#endif // QT_CONFIG(tooltip)
        self.editSuffix.setPlaceholderText(QCoreApplication.translate("SavePanel", u"optional", None))
        self.captionDataDir.setText(QCoreApplication.translate("SavePanel", u"Datenordner", None))
#if QT_CONFIG(tooltip)
        self.editDataDir.setToolTip(QCoreApplication.translate("SavePanel", u"Ordner, in dem die Messungen gespeichert werden", None))
#endif // QT_CONFIG(tooltip)
        self.buttonBrowse.setText(QCoreApplication.translate("SavePanel", u"\u2026", None))
#if QT_CONFIG(tooltip)
        self.buttonBrowse.setToolTip(QCoreApplication.translate("SavePanel", u"Datenordner w\u00e4hlen", None))
#endif // QT_CONFIG(tooltip)
        self.checkAutoSave.setText(QCoreApplication.translate("SavePanel", u"Automatisch speichern", None))
#if QT_CONFIG(tooltip)
        self.checkAutoSave.setToolTip(QCoreApplication.translate("SavePanel", u"Bei Aktivierung wird die Messung beim Stoppen automatisch gespeichert, im Format:\n"
"JJJJ_MM_TT-NN-Messung[-Suffix].csv\n"
"in einem Unterordner Gruppe_Untergruppe des Datenordners (Standard: Dokumente/Kreisel/).", None))
#endif // QT_CONFIG(tooltip)
        self.buttonSave.setText(QCoreApplication.translate("SavePanel", u"Speichern \u2026", None))
#if QT_CONFIG(tooltip)
        self.buttonSave.setToolTip(QCoreApplication.translate("SavePanel", u"Messung in eine Datei speichern (Dateidialog)", None))
#endif // QT_CONFIG(tooltip)
        self.captionLastSaved.setText(QCoreApplication.translate("SavePanel", u"Zuletzt", None))
        self.labelLastSaved.setText(QCoreApplication.translate("SavePanel", u"\u2013", None))
    # retranslateUi

