"""Smoke test of the shortcut overview dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt

from gyroscope_ui.ui.shortcuts import shortcut_rows
from gyroscope_ui.ui.widgets.shortcuts_dialog import ShortcutsDialog


def test_dialog_lists_every_shortcut_in_german(qtbot, config):
    dialog = ShortcutsDialog(config, n_tabs=1)
    qtbot.addWidget(dialog)
    dialog.show()
    table = dialog.ui.tableShortcuts
    assert dialog.windowTitle() == "Tastenkürzel"
    assert [table.horizontalHeaderItem(i).text() for i in range(2)] == [
        "Funktion",
        "Tastenkürzel",
    ]
    rows = shortcut_rows(config, 1)
    groups = len({r.group for r in rows})
    assert table.rowCount() == len(rows) + groups
    cells = {table.item(r, 0).text() for r in range(table.rowCount())}
    labels = config.section("ui")["shortcuts_dialog"]["row_labels"]
    assert {labels[r.id] for r in rows} <= cells
    assert "Messung" in cells  # group header


def test_close_button_closes_the_dialog(qtbot, config):
    dialog = ShortcutsDialog(config, n_tabs=1)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.mouseClick(dialog.ui.buttonClose, Qt.MouseButton.LeftButton)
    assert not dialog.isVisible()
