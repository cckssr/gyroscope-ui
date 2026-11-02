"""Application paths."""

from __future__ import annotations

from gyroscope_ui.infrastructure.paths import AppPaths


def test_directories_created_on_demand(tmp_path):
    paths = AppPaths(tmp_path / "root")
    assert not (tmp_path / "root").exists()
    assert paths.logs_dir == tmp_path / "root" / "logs"
    assert paths.logs_dir.is_dir()
    assert paths.session_dir == tmp_path / "root"


def test_default_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    assert AppPaths.default_data_dir() == tmp_path
    (tmp_path / "Documents").mkdir()
    assert AppPaths.default_data_dir() == tmp_path / "Documents" / "Kreisel"


def test_default_uses_user_data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr("gyroscope_ui.infrastructure.paths.user_data_dir", lambda: tmp_path)
    assert AppPaths.default().root == tmp_path


def test_user_data_dir_name(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from gyroscope_ui.infrastructure.logging import user_data_dir

    assert user_data_dir().name == "gyroscope-ui"
