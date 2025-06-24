from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.helper_classes import SaveManager


def test_create_metadata(tmp_path):
    manager = SaveManager(base_dir=tmp_path)
    start = datetime(2023, 1, 1, 12, 0)
    end = datetime(2023, 1, 1, 12, 5)
    meta = manager.create_metadata(start, end, "Autor", "Probe")
    assert meta["dc:creator"] == "Autor"
    assert meta["start_time"] == start.isoformat()
    assert meta["end_time"] == end.isoformat()


def test_save_measurement_creates_files(tmp_path):
    manager = SaveManager(base_dir=tmp_path)
    data = [["a", "b"], ["1", "2"]]
    meta = manager.create_metadata(datetime.now(), datetime.now(), "A", "S")
    path = manager.save_measurement("file.csv", data, meta)
    assert path.exists()
    assert path.with_suffix(".json").exists()


def test_unsaved_flag(tmp_path):
    manager = SaveManager(base_dir=tmp_path)
    manager.mark_unsaved()
    assert manager.has_unsaved()
    meta = manager.create_metadata(datetime.now(), datetime.now(), "A", "S")
    manager.save_measurement("t.csv", [["i"]], meta)
    assert not manager.has_unsaved()
