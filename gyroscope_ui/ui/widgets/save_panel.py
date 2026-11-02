"""Save panel: group, sub-group, suffix, data folder, auto-save switch and the Save button."""

from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QGroupBox, QWidget

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.pyqt.save_panel_ui import Ui_SavePanel
from gyroscope_ui.ui.i18n import apply_strings

# Required fields that ``mark_missing`` can highlight.
MISSING_FIELDS = ("group", "subgroup")
_MISSING_STYLE = """
QLineEdit[missing="true"], QComboBox[missing="true"] {
    border: 1px solid #d03030;
    border-radius: 3px;
    padding: 1px 2px;
}
"""


class SavePanel(QGroupBox):
    """View only: emits user intents and edits; values come back through ``set_values``."""

    save_requested = Signal()
    group_changed = Signal(str)
    subgroup_changed = Signal(str)
    suffix_changed = Signal(str)
    auto_save_toggled = Signal(bool)
    browse_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_SavePanel()
        self.ui.setupUi(self)
        self._config: AppConfig | None = None
        self._dir_tooltip = ""
        self._fields = {"group": self.ui.comboGroup, "subgroup": self.ui.editSubgroup}
        self.setStyleSheet(_MISSING_STYLE)
        self.ui.comboGroup.currentTextChanged.connect(self._on_group)
        self.ui.editSubgroup.textEdited.connect(self._on_subgroup)
        self.ui.editSuffix.textEdited.connect(self.suffix_changed)
        self.ui.checkAutoSave.toggled.connect(self.auto_save_toggled)
        self.ui.buttonBrowse.clicked.connect(self.browse_requested)
        self.ui.buttonSave.clicked.connect(self.save_requested)
        self.ui.buttonSave.setEnabled(False)

    def apply_config(self, config: AppConfig) -> None:
        self._config = config
        apply_strings(self, config.section("ui").get("save_panel", {}))
        self._dir_tooltip = self.ui.editDataDir.toolTip()
        combo = self.ui.comboGroup
        current = combo.currentText()
        with QSignalBlocker(combo):
            combo.clear()
            combo.addItems([str(letter) for letter in config.get("storage.group_letters", [])])
            combo.setCurrentIndex(max(combo.findText(current), 0))
        self.set_last_saved(None)

    def set_values(
        self, group: str, subgroup: str, suffix: str, data_dir: str, auto_save: bool
    ) -> None:
        """Show the stored values without emitting any change signal."""
        combo = self.ui.comboGroup
        with QSignalBlocker(combo):
            index = combo.findText(group)
            if index >= 0:
                combo.setCurrentIndex(index)
        for edit, text in (
            (self.ui.editSubgroup, subgroup),
            (self.ui.editSuffix, suffix),
            (self.ui.editDataDir, data_dir),
        ):
            with QSignalBlocker(edit):
                edit.setText(text)
        self.ui.editDataDir.setToolTip(f"{self._dir_tooltip}\n{data_dir}".strip())
        with QSignalBlocker(self.ui.checkAutoSave):
            self.ui.checkAutoSave.setChecked(auto_save)

    def set_can_save(self, enabled: bool) -> None:
        self.ui.buttonSave.setEnabled(enabled)

    def set_inputs_enabled(self, enabled: bool) -> None:
        """Group, sub-group, suffix and folder can only change while no measurement runs."""
        for widget in (
            self.ui.comboGroup,
            self.ui.editSubgroup,
            self.ui.editSuffix,
            self.ui.buttonBrowse,
        ):
            widget.setEnabled(enabled)

    def set_last_saved(self, path: str | None) -> None:
        """Show the path of the last saved file; ``None`` shows the placeholder dash."""
        if path:
            self.ui.labelLastSaved.setText(path)
        elif self._config is not None:
            self.ui.labelLastSaved.setText(self._config.text("save_panel.no_last_saved"))

    def mark_missing(self, fields: set[str]) -> None:
        """Highlight the required fields in ``fields`` (``group``, ``subgroup``) with a red
        border; an empty set clears all marks."""
        for name, widget in self._fields.items():
            self._set_missing(widget, name in fields)

    def _set_missing(self, widget: QWidget, missing: bool) -> None:
        if bool(widget.property("missing")) == missing:
            return
        widget.setProperty("missing", missing)
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)

    def _on_group(self, text: str) -> None:
        self._set_missing(self.ui.comboGroup, False)
        self.group_changed.emit(text)

    def _on_subgroup(self, text: str) -> None:
        if text.strip():
            self._set_missing(self.ui.editSubgroup, False)
        self.subgroup_changed.emit(text)
