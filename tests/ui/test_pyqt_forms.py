"""Designer forms: the German texts in the ``.ui`` files match config.json, and every form has a
generated ``*_ui.py`` that is exactly what ``pyside6-uic`` produces from the form."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from gyroscope_ui.infrastructure.config import load_config
from gyroscope_ui.pyqt.preview import compile_form
from gyroscope_ui.pyqt.sync_texts import PYQT_DIR, SECTIONS, synced_text

FORMS = sorted(PYQT_DIR.glob("*.ui"))
EXPECTED = {
    "connection_panel",
    "live_panel",
    "main_window",
    "measurement_panel",
    "measurement_view",
    "save_panel",
    "shortcuts_dialog",
    "simulation_panel",
}


def test_forms_exist():
    assert {p.stem for p in FORMS} >= EXPECTED


@pytest.mark.parametrize("form", FORMS, ids=lambda p: p.stem)
def test_ui_texts_are_in_sync_with_config(form: Path):
    config = load_config()
    assert synced_text(form, config) == form.read_text(encoding="utf-8"), (
        f"{form.name} is out of date: run gyroscope_ui/pyqt/pyuic.sh"
    )


@pytest.mark.parametrize("form", FORMS, ids=lambda p: p.stem)
def test_every_config_text_has_a_widget(form: Path):
    """A key of ``ui.<form>`` without an underscore names an object of the form (or ``self``)."""
    names = {
        element.get("name")
        for element in ET.parse(form).getroot().iter()
        if element.tag in ("widget", "action")
    }
    config = load_config().section("ui")
    for section in SECTIONS.get(form.stem, (form.stem,)):
        for key in config.get(section, {}):
            name = key.partition("@")[0]
            if "_" in name:
                continue
            assert name == "self" or name in names, f"ui.{section}.{key} has no widget"


@pytest.mark.parametrize("form", FORMS, ids=lambda p: p.stem)
def test_generated_module_exists(form: Path):
    assert form.with_name(f"{form.stem}_ui.py").exists()


@pytest.mark.parametrize("form", FORMS, ids=lambda p: p.stem)
def test_generated_module_matches_the_form(form: Path):
    """A fresh ``pyside6-uic`` run reproduces the committed module."""
    out = compile_form(form)
    committed = form.with_name(f"{form.stem}_ui.py").read_text(encoding="utf-8")
    assert out == committed, f"{form.stem}_ui.py is stale: run gyroscope_ui/pyqt/pyuic.sh"


@pytest.mark.parametrize("form", FORMS, ids=lambda p: p.stem)
def test_forms_carry_no_shortcut_properties(form: Path):
    """Key bindings live in config.json (one event filter), not in the forms (D1)."""
    assert 'name="shortcut"' not in form.read_text(encoding="utf-8")
