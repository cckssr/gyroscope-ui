import pytest
from src.helper_classes import SaveManager


def test_filename_auto_basic():
    manager = SaveManager()
    rad_sample = "TestSample"
    result = manager.filename_auto(rad_sample)
    assert result.endswith("-TestSample.csv")
    assert result.count("-TestSample.csv") == 1


def test_filename_auto_with_suffix():
    manager = SaveManager()
    rad_sample = "Sample"
    suffix = "run1"
    result = manager.filename_auto(rad_sample, suffix)
    assert result.endswith("-Sample-run1.csv")
    assert "-run1.csv" in result


def test_filename_auto_with_suffix_dash():
    manager = SaveManager()
    rad_sample = "Sample"
    suffix = "-run2"
    result = manager.filename_auto(rad_sample, suffix)
    assert result.endswith("-Sample-run2.csv")
    assert "-run2.csv" in result


def test_filename_auto_empty_sample(monkeypatch):
    manager = SaveManager()
    # Patch Debug.error to avoid unwanted output
    monkeypatch.setattr("src.helper_classes.Debug.error", lambda msg: None)
    result = manager.filename_auto("")
    assert result == ""
