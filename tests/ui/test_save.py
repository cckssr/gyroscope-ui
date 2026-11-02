"""Manual and automatic saving (CONCEPT 6) from the main window."""

from __future__ import annotations

import json
from datetime import date

from ui_helpers import record

from gyroscope_ui.core.csv_format import CSV_HEADER


def _stopped(qtbot, window, group="B", subgroup="Aufbau 1"):
    window.context.session.update_save_fields(group=group, subgroup=subgroup)
    record(qtbot, window)
    window.context.measurement.stop()


def test_missing_fields_are_marked(qtbot, connected):
    record(qtbot, connected)
    connected.context.measurement.stop()
    assert connected.context.save.save_manual() is None
    ui = connected.save_panel.ui
    assert ui.comboGroup.property("missing") and ui.editSubgroup.property("missing")
    assert "erforderlichen Felder" in connected.message_log[-1][1]
    assert connected.context.measurement.state == "stopped"


def test_auto_save_on_stop(qtbot, connected, config):
    connected.context.session.set_auto_save(True)
    _stopped(qtbot, connected)
    saved = connected.context.save.last_saved
    data_dir = connected.context.session.data_dir
    today = date.today().strftime("%Y_%m_%d")
    assert saved == data_dir / "B_Aufbau_1" / f"{today}-01-Messung.csv"
    lines = saved.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(CSV_HEADER)
    assert len(lines) == len(connected.context.measurement.recording) + 1
    meta = json.loads(saved.with_suffix(".json").read_text(encoding="utf-8"))
    assert meta["group"] == "B" and meta["subgroup"] == "Aufbau 1"
    assert meta["device"]["simulated"] is True
    assert connected.context.measurement.state == "saved"
    # the next measurement gets the next number
    record(qtbot, connected)
    connected.context.measurement.stop()
    assert connected.context.save.last_saved.name == f"{today}-02-Messung.csv"


def test_manual_save_uses_dropbox_folder(qtbot, connected):
    asked = []

    def ask(directory, name):
        asked.append((directory, name))
        return directory / "eigene_datei"

    connected.context.save.ask_save_path = ask
    _stopped(qtbot, connected, group="C")
    path = connected.save_measurement()
    weekday = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")[date.today().weekday()]
    directory, proposal = asked[0]
    assert directory.name == f"{weekday}CTK8-Aufbau_1" and directory.is_dir()
    assert proposal.endswith("-01-Messung.csv")
    assert path == directory / "eigene_datei.csv" and path.exists()
    assert connected.save_panel.ui.labelLastSaved.text() == str(path)


def test_cancelled_dialog_keeps_data_unsaved(qtbot, connected):
    _stopped(qtbot, connected)
    assert connected.save_measurement() is None
    assert connected.context.measurement.has_unsaved


def test_save_failure_reports_and_keeps_data(qtbot, connected, tmp_path):
    blocker = tmp_path / "not_a_folder"
    blocker.write_text("x")
    connected.context.session.set_data_dir(blocker)
    connected.context.session.set_auto_save(True)
    _stopped(qtbot, connected)
    assert connected.context.save.last_saved is None
    assert connected.context.measurement.has_unsaved
    assert connected.message_log[-1][0] == "error"
