"""Atomic file writes."""

from __future__ import annotations

import os

import pytest

from gyroscope_ui.infrastructure import atomic


def test_write_text_and_bytes(tmp_path):
    atomic.atomic_write_text(tmp_path / "sub" / "a.txt", "grüß\n")
    atomic.atomic_write_bytes(tmp_path / "b.bin", b"\x00\x01")
    assert (tmp_path / "sub" / "a.txt").read_bytes() == "grüß\n".encode()
    assert (tmp_path / "b.bin").read_bytes() == b"\x00\x01"


def test_replaces_existing_file_and_leaves_no_temp_files(tmp_path):
    target = tmp_path / "x.txt"
    target.write_text("old")
    atomic.atomic_write_text(target, "new")
    assert target.read_text() == "new"
    assert [p.name for p in tmp_path.iterdir()] == ["x.txt"]


def test_failure_keeps_old_content_and_removes_temp_file(tmp_path):
    target = tmp_path / "x.txt"
    target.write_text("old")
    with pytest.raises(RuntimeError), atomic.atomic_path(target) as tmp:
        tmp.write_text("partial")
        raise RuntimeError("boom")
    assert target.read_text() == "old"
    assert [p.name for p in tmp_path.iterdir()] == ["x.txt"]


def test_fsyncs_the_temp_file_before_replacing(tmp_path, monkeypatch):
    events: list[tuple[str, str]] = []
    real_replace = os.replace
    monkeypatch.setattr(atomic, "_fsync_file", lambda p: events.append(("fsync", p.name)))
    monkeypatch.setattr(atomic, "_fsync_dir", lambda p: events.append(("fsync_dir", p.name)))

    def replace(src, dst):
        events.append(("replace", os.path.basename(src)))
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", replace)
    atomic.atomic_write_text(tmp_path / "x.txt", "hi")
    assert [e[0] for e in events] == ["fsync", "replace", "fsync_dir"]
    assert events[0][1] == events[1][1]  # the very file that is renamed
    assert (tmp_path / "x.txt").read_text() == "hi"
