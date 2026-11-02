"""Applying the German strings of config.json to Designer-style widgets."""

from __future__ import annotations

from PySide6.QtWidgets import QDoubleSpinBox, QGroupBox, QLabel, QLineEdit, QPushButton, QWidget

from gyroscope_ui.ui.i18n import apply_strings


def _form(qtbot) -> QWidget:
    root = QWidget()
    qtbot.addWidget(root)
    box = QGroupBox(root)
    box.setObjectName("groupDevice")
    button = QPushButton(root)
    button.setObjectName("buttonStart")
    label = QLabel(root)
    label.setObjectName("labelFrequency")
    spin = QDoubleSpinBox(root)
    spin.setObjectName("spinWindow")
    edit = QLineEdit(root)
    edit.setObjectName("editSubterm")
    return root


def test_texts_tooltips_suffixes_placeholders_and_titles(qtbot):
    root = _form(qtbot)
    apply_strings(
        root,
        {
            "self@title": "Kreisel-GUI",
            "groupDevice": "Gerät",
            "buttonStart": "Start",
            "buttonStart@tooltip": "Messung starten",
            "labelFrequency": "Frequenz",
            "spinWindow@suffix": " s",
            "spinWindow@prefix": "~",
            "editSubterm@placeholder": "z.B. Aufbau 1",
        },
    )
    assert root.windowTitle() == "Kreisel-GUI"
    assert root.findChild(QGroupBox, "groupDevice").title() == "Gerät"
    button = root.findChild(QPushButton, "buttonStart")
    assert button.text() == "Start" and button.toolTip() == "Messung starten"
    assert root.findChild(QLabel, "labelFrequency").text() == "Frequenz"
    spin = root.findChild(QDoubleSpinBox, "spinWindow")
    assert spin.suffix() == " s" and spin.prefix() == "~"
    assert root.findChild(QLineEdit, "editSubterm").placeholderText() == "z.B. Aufbau 1"


def test_underscore_keys_and_unknown_objects_are_skipped(qtbot):
    root = _form(qtbot)
    apply_strings(root, {"plain_text": "ignored", "doesNotExist": "x", "buttonStart": "Start"})
    assert root.findChild(QPushButton, "buttonStart").text() == "Start"
