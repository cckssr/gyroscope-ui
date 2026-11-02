"""``docs/SHORTCUTS.md`` is generated from the config defaults and must not drift from them.

Regenerate with ``.venv/bin/python -m gyroscope_ui.ui.shortcuts > docs/SHORTCUTS.md``."""

from __future__ import annotations

from pathlib import Path

from gyroscope_ui.infrastructure.config import load_config
from gyroscope_ui.ui.shortcuts import DOC_TABS, display_text, render_markdown, shortcut_rows

DOC = Path(__file__).resolve().parents[2] / "docs" / "SHORTCUTS.md"


def _table_rows(markdown: str) -> list[tuple[str, ...]]:
    """Cells of all table body rows (compare the cell texts, not the padding)."""
    rows = []
    for line in markdown.splitlines():
        if not line.startswith("|"):
            continue
        cells = tuple(c.strip().strip("`") for c in line.strip().strip("|").split("|"))
        if set("".join(cells)) <= set("- :") or cells[0] == "Funktion":
            continue
        rows.append(cells)
    return rows


def _headings(markdown: str) -> list[str]:
    return [line for line in markdown.splitlines() if line.startswith("#")]


def test_shortcuts_doc_is_in_sync_with_the_config_defaults():
    generated = render_markdown(load_config(), DOC_TABS)
    text = DOC.read_text(encoding="utf-8")
    assert _table_rows(text) == _table_rows(generated)
    assert _headings(text) == _headings(generated)


def test_every_configured_shortcut_appears_in_the_doc():
    config = load_config()
    text = DOC.read_text(encoding="utf-8").replace("`", "")
    entries = config.section("shortcuts")
    assert entries
    for name, sequence in entries.items():
        if name.endswith("_modifier"):
            continue  # a modifier, not a key: shown as part of the digit rows
        assert display_text(sequence, mac=True) in text, name
        assert display_text(sequence, mac=False) in text, name
    rows = {r.id: r for r in shortcut_rows(config, DOC_TABS)}
    assert rows["switch_tab"].text(False) in text and rows["switch_tab"].text(True) in text


def test_concept_shortcuts_are_present():
    """CONCEPT section 8."""
    shortcuts = load_config().section("shortcuts")
    expected = {
        "start_stop": "Space",
        "stop": "Esc",
        "save": "Ctrl+S",
        "reset": "Ctrl+R",
        "connect": "Ctrl+K",
        "auto_range": "Ctrl+Shift+A",
        "help": "F1",
    }
    for name, sequence in expected.items():
        assert shortcuts[name] == sequence, name


def test_every_action_has_a_row():
    config = load_config()
    ids = {row.id for row in shortcut_rows(config, DOC_TABS)}
    actions = {name for name in config.section("shortcuts") if not name.endswith("_modifier")}
    assert actions <= ids


def test_every_row_has_a_german_label_and_group_name():
    config = load_config()
    texts = config.section("ui")["shortcuts_dialog"]
    for row in shortcut_rows(config, DOC_TABS):
        assert texts["row_labels"].get(row.id), row.id
        assert texts["group_names"].get(row.group), row.group


def test_tab_digits_follow_the_tab_count():
    config = load_config()
    rows = {r.id: r for r in shortcut_rows(config, 3)}
    assert rows["switch_tab"].keys == ("Ctrl+1", "Ctrl+3")
    rows = {r.id: r for r in shortcut_rows(config, DOC_TABS)}
    assert rows["switch_tab"].keys == ("Ctrl+1",)


def test_macos_notation():
    assert display_text("Ctrl+Shift+A", mac=True) == "⇧⌘A"
    assert display_text("Ctrl+S", mac=True) == "⌘S"
    assert display_text("Space", mac=True) == "␣"
    assert display_text("Esc", mac=True) == "⎋"
    assert display_text("Ctrl+Shift+A", mac=False) == "Ctrl+Shift+A"
