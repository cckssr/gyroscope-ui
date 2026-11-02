"""Overview of the keyboard shortcuts (F1): a table built from the ``shortcuts`` config."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QHeaderView, QTableWidgetItem, QWidget

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.pyqt.shortcuts_dialog_ui import Ui_ShortcutsDialog
from gyroscope_ui.ui.i18n import apply_strings
from gyroscope_ui.ui.shortcuts import shortcut_rows


class ShortcutsDialog(QDialog):
    """Non-modal list "function | key" with the keys in the notation of the running platform
    (⌥← on macOS, ``Alt+Left`` elsewhere), grouped by area."""

    def __init__(self, config: AppConfig, n_tabs: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_ShortcutsDialog()
        self.ui.setupUi(self)
        texts = config.section("ui").get("shortcuts_dialog", {})
        apply_strings(self, texts)
        labels, groups = texts.get("row_labels", {}), texts.get("group_names", {})
        columns = texts.get("table_columns", ["Funktion", "Tastenkürzel"])
        table = self.ui.tableShortcuts
        table.setHorizontalHeaderLabels(columns)
        rows = shortcut_rows(config, n_tabs)
        table.setRowCount(len(rows) + len(dict.fromkeys(r.group for r in rows)))
        bold = QFont(self.font())
        bold.setBold(True)
        mono = QFont(self.font())
        mono.setFamilies(["Menlo", "Consolas", "monospace"])
        n = 0
        last_group = None
        for r in rows:
            if r.group != last_group:
                last_group = r.group
                header = QTableWidgetItem(groups.get(r.group, r.group))
                header.setFont(bold)
                header.setFlags(Qt.ItemFlag.ItemIsEnabled)
                table.setItem(n, 0, header)
                table.setSpan(n, 0, 1, 2)
                n += 1
            table.setItem(n, 0, QTableWidgetItem(labels.get(r.id, r.id)))
            keys = QTableWidgetItem(r.native())
            keys.setFont(mono)
            table.setItem(n, 1, keys)
            n += 1
        head = table.horizontalHeader()
        head.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        head.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.buttonClose.clicked.connect(self.close)
