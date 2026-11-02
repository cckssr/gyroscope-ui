"""Measurement files: golden CSV bytes, sidecar, atomicity, auto-save numbering, folder names."""

from __future__ import annotations

import csv
import json
import math
import os
from datetime import date

import pytest

from gyroscope_ui.core.csv_format import csv_rows
from gyroscope_ui.infrastructure.storage import (
    StorageError,
    auto_save_path,
    manual_save_dir,
    sidecar_path,
    write_measurement,
)

ROWS = csv_rows([0.0, 0.01, 12.3456789], [14.9876543, math.nan, 0.0], [2.1, -0.5, math.nan])
META = {"format": "gyroscope-ui-measurement/1", "subgroup": "Größe", "samples": 3, "z": [1, 2]}
DAY = date(2026, 11, 2)  # a Monday


def old_writer_bytes(tmp_path, rows) -> bytes:
    """The 1.1.x writer: ``open(path, "w", newline="", encoding="utf-8")`` + ``csv.writer``."""
    path = tmp_path / "old.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    return path.read_bytes()


def test_csv_bytes_equal_the_old_writer(tmp_path):
    target = tmp_path / "new.csv"
    assert write_measurement(target, ROWS, META) == target
    assert target.read_bytes() == old_writer_bytes(tmp_path, ROWS)
    assert target.read_bytes() == (
        b"Time (s),Disk rotation frequency (Hz),Gyro Z rate (rad/s)\r\n"
        b"0.000000,14.987654,2.100000\r\n"
        b"0.010000,,-0.500000\r\n"
        b"12.345679,0.000000,\r\n"
    )


def test_sidecar_content_and_format(tmp_path):
    target = tmp_path / "sub" / "m.csv"
    write_measurement(target, ROWS, META)
    sidecar = tmp_path / "sub" / "m.json"
    assert sidecar == sidecar_path(target)
    text = sidecar.read_text(encoding="utf-8")
    assert text == json.dumps(META, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    assert "Größe" in text and text.endswith("}\n") and "\r" not in text
    assert json.loads(text) == META
    assert sorted(p.name for p in sidecar.parent.iterdir()) == ["m.csv", "m.json"]


def test_existing_csv_is_not_overwritten_by_default(tmp_path):
    target = tmp_path / "m.csv"
    write_measurement(target, ROWS, META)
    with pytest.raises(StorageError) as caught:
        write_measurement(target, [["x"]], {"a": 1})
    assert caught.value.key == "file_exists" and caught.value.fmt == {"path": str(target)}
    assert target.read_bytes() == old_writer_bytes(tmp_path, ROWS)
    assert json.loads(sidecar_path(target).read_text(encoding="utf-8")) == META

    write_measurement(target, [["x"]], {"a": 1}, overwrite=True)
    assert target.read_bytes() == b"x\r\n"
    assert json.loads(sidecar_path(target).read_text(encoding="utf-8")) == {"a": 1}


def test_target_directory_is_a_file(tmp_path):
    blocker = tmp_path / "folder"
    blocker.write_text("i am a file")
    target = blocker / "m.csv"
    with pytest.raises(StorageError) as caught:
        write_measurement(target, ROWS, META)
    assert caught.value.key == "storage_write_failed"
    assert caught.value.fmt["path"] == str(target) and caught.value.fmt["error"]
    assert [p.name for p in tmp_path.iterdir()] == ["folder"]  # no temporary files


def test_failed_sidecar_removes_the_new_csv_and_leaves_no_temporary_files(tmp_path):
    target = tmp_path / "m.csv"
    sidecar_path(target).mkdir()  # the sidecar cannot replace a directory
    with pytest.raises(StorageError) as caught:
        write_measurement(target, ROWS, META)
    assert caught.value.key == "storage_write_failed"
    assert [p.name for p in tmp_path.iterdir()] == ["m.json"]  # the directory we created
    sidecar_path(target).rmdir()
    write_measurement(target, ROWS, META)  # a retry is possible


def test_failed_sidecar_keeps_a_replaced_csv_when_overwriting(tmp_path):
    target = tmp_path / "m.csv"
    target.write_bytes(b"old")
    sidecar_path(target).mkdir()
    with pytest.raises(StorageError):
        write_measurement(target, ROWS, META, overwrite=True)
    assert target.read_bytes() == old_writer_bytes(tmp_path, ROWS)


def test_unserialisable_metadata_writes_nothing(tmp_path):
    with pytest.raises(TypeError):
        write_measurement(tmp_path / "m.csv", ROWS, {"bad": object()})
    assert list(tmp_path.iterdir()) == []


def test_auto_save_path_numbering_continues(tmp_path):
    kwargs = {
        "day": DAY,
        "group": "a",
        "subterm": "Aufbau 1",
        "suffix": "",
        "measurement_name": "Messung",
    }
    first = auto_save_path(tmp_path, **kwargs)
    assert first == tmp_path / "A_Aufbau_1" / "2026_11_02-01-Messung.csv"
    assert not first.parent.exists()  # not created

    write_measurement(first, ROWS, META)
    second = auto_save_path(tmp_path, **kwargs)
    assert second.name == "2026_11_02-02-Messung.csv"
    write_measurement(second, ROWS, META)
    (first.parent / "2026_11_01-07-Messung.csv").write_text("other day")
    (first.parent / "notes.txt").write_text("unrelated")
    third = auto_save_path(tmp_path, **{**kwargs, "suffix": "Test"})
    assert third.name == "2026_11_02-03-Messung-Test.csv"
    assert auto_save_path(tmp_path, **{**kwargs, "day": date(2026, 11, 3)}).name == (
        "2026_11_03-01-Messung.csv"
    )


def test_auto_save_path_uses_the_subterm_length_limit(tmp_path):
    path = auto_save_path(
        tmp_path,
        day=DAY,
        group="B",
        subterm="Ein sehr langer Name der Gruppe",
        suffix="",
        measurement_name="Messung",
        subterm_max_length=10,
    )
    assert path.parent.name == "B_Ein_se_xxx"  # abbreviated, then cut (core.naming)
    assert len(path.parent.name) <= len("B_") + 10


@pytest.mark.skipif(
    os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="needs POSIX permissions and a non-root user",
)
def test_auto_save_path_unreadable_folder(tmp_path):
    folder = tmp_path / "A_x"
    folder.mkdir()
    folder.chmod(0)
    try:
        with pytest.raises(StorageError) as caught:
            auto_save_path(
                tmp_path, day=DAY, group="A", subterm="x", suffix="", measurement_name="M"
            )
        assert caught.value.key == "storage_write_failed"
    finally:
        folder.chmod(0o755)


def test_manual_save_dir(tmp_path):
    path = manual_save_dir(tmp_path, day=DAY, group="A", tk="TK8", subterm="Aufbau 1")
    assert path == tmp_path / "MoATK8-Aufbau_1"
    assert not path.exists()
    assert manual_save_dir(tmp_path, day=DAY, group="C", tk="TK8", subterm="").name == "MoCTK8"
    custom = manual_save_dir(
        tmp_path, day=DAY, group="A", tk="TK8", subterm="x", abbreviations=list("1234567")
    )
    assert custom.name == "1ATK8-x"
