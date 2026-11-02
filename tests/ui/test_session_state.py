"""Session persistence: values survive a restart; the group fields only for one day."""

from __future__ import annotations

import json
from datetime import date, timedelta

from gyroscope_ui.ui.session_state import SessionState


def _session(config, paths, today):
    return SessionState(config, paths, today=lambda: today)


def test_roundtrip_same_day(qtbot, config, paths, tmp_path):
    day = date(2026, 11, 2)
    s = _session(config, paths, day)
    s.update_save_fields(group="D", subgroup="Aufbau 2", suffix="x")
    s.set_data_dir(tmp_path / "elsewhere")
    s.set_auto_save(True)
    s.update_display(all_channels=True, scroll_window_s=120.0)
    s.ui_state("window")["geometry"] = "abc"
    s.shutdown()
    r = _session(config, paths, day)
    assert (r.save_fields.group, r.save_fields.subgroup) == ("D", "Aufbau 2")
    assert r.save_fields.suffix == ""  # the suffix does not survive a restart
    assert r.data_dir == tmp_path / "elsewhere" and r.auto_save
    assert r.display.all_channels and r.display.scroll_window_s == 120.0
    assert r.ui_state("window") == {"geometry": "abc"}


def test_suffix_in_an_older_session_file_is_ignored(qtbot, config, paths):
    day = date(2026, 11, 2)
    s = _session(config, paths, day)
    s.update_save_fields(group="D", subgroup="Aufbau 2")
    s.shutdown()
    file = paths.session_dir / "session.json"
    data = json.loads(file.read_text(encoding="utf-8"))
    assert "suffix" not in data["save_fields"]
    data["save_fields"]["suffix"] = "old"  # written by an earlier version
    file.write_text(json.dumps(data), encoding="utf-8")
    r = _session(config, paths, day)
    assert r.save_fields.subgroup == "Aufbau 2" and r.save_fields.suffix == ""


def test_group_fields_expire_next_day(qtbot, config, paths, tmp_path):
    day = date(2026, 11, 2)
    s = _session(config, paths, day)
    s.update_save_fields(group="D", subgroup="Aufbau 2")
    s.set_data_dir(tmp_path / "kept")
    s.shutdown()
    r = _session(config, paths, day + timedelta(days=1))
    assert r.save_fields.group == "" and r.save_fields.subgroup == ""
    assert r.data_dir == tmp_path / "kept"


def test_debounced_save(qtbot, config, paths):
    s = SessionState(config, paths)
    s.set_auto_save(True)
    qtbot.waitUntil(lambda: (paths.session_dir / "session.json").exists(), timeout=2_000)


def test_damaged_file_does_not_block(qtbot, config, paths):
    (paths.session_dir / "session.json").write_text("{broken", encoding="utf-8")
    s = SessionState(config, paths)
    assert s.save_fields.group == ""
    assert (paths.session_dir / "session.json.bak").exists()


def test_restored_values_reach_the_window(qtbot, make_window):
    first = make_window()
    first.context.session.update_save_fields(group="F", subgroup="Gruppe F1")
    first.close()
    second = make_window()
    ui = second.save_panel.ui
    assert ui.comboGroup.currentText() == "F" and ui.editSubgroup.text() == "Gruppe F1"


def test_invalid_restored_group_is_dropped(qtbot, config, paths):
    day = date(2026, 11, 2)
    s = _session(config, paths, day)
    s.update_save_fields(group="ab", subgroup="Aufbau 2")
    s.shutdown()
    r = _session(config, paths, day)
    assert r.save_fields.group == "" and r.save_fields.subgroup == "Aufbau 2"
