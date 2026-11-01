"""Session store: round trip, missing and damaged files, foreign format."""

from __future__ import annotations

import json

from gyroscope_ui.infrastructure.session_store import SESSION_FORMAT, SessionStore

DATA = {"group": "A", "subterm": "Größe", "window": {"w": 800, "h": 600}, "auto_save": True}


def test_round_trip_and_file_content(tmp_path):
    store = SessionStore(tmp_path / "s")
    store.save(DATA)
    text = store.json_path.read_text(encoding="utf-8")
    assert json.loads(text) == {"format": SESSION_FORMAT, "data": DATA}
    assert SESSION_FORMAT == "gyroscope-ui-session/1"
    assert text.endswith("\n") and "Größe" in text
    assert text.index('"data"') < text.index('"format"') and text.index('"auto_save"') < text.index(
        '"group"'
    )  # sorted keys
    assert SessionStore(tmp_path / "s").load() == DATA
    assert [p.name for p in (tmp_path / "s").iterdir()] == ["session.json"]


def test_save_replaces_the_previous_content(tmp_path):
    store = SessionStore(tmp_path)
    store.save({"a": 1})
    store.save({"b": 2})
    assert store.load() == {"b": 2}


def test_missing_file_gives_empty_data(tmp_path):
    assert SessionStore(tmp_path / "nothing").load() == {}


def test_damaged_file_is_kept_as_bak(tmp_path):
    store = SessionStore(tmp_path)
    store.json_path.write_text("{ not json", encoding="utf-8")
    assert store.load() == {}
    assert not store.json_path.exists()
    assert (tmp_path / "session.json.bak").read_text(encoding="utf-8") == "{ not json"
    assert store.load() == {}  # the second start has nothing left to complain about
    store.save(DATA)
    assert store.load() == DATA


def test_binary_garbage_and_non_object_documents(tmp_path):
    store = SessionStore(tmp_path)
    for content in (b"\xff\xfe\x00\x01", b"[1, 2]", b'"text"', b""):
        store.json_path.write_bytes(content)
        assert store.load() == {}
        assert (tmp_path / "session.json.bak").read_bytes() == content


def test_foreign_format_is_kept_as_bak(tmp_path):
    store = SessionStore(tmp_path)
    for document in (
        {"format": "spectrum-ui-session/1", "data": {"x": 1}},
        {"format": SESSION_FORMAT, "data": [1]},
        {"x": 1},
    ):
        store.json_path.write_text(json.dumps(document), encoding="utf-8")
        assert store.load() == {}
        assert json.loads((tmp_path / "session.json.bak").read_text(encoding="utf-8")) == document
        assert not store.json_path.exists()


def test_a_new_damaged_file_replaces_an_older_bak(tmp_path):
    store = SessionStore(tmp_path)
    (tmp_path / "session.json.bak").write_text("old backup", encoding="utf-8")
    store.json_path.write_text("garbage", encoding="utf-8")
    store.load()
    assert (tmp_path / "session.json.bak").read_text(encoding="utf-8") == "garbage"
