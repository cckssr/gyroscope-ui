"""Structure and message rules of the packaged config.json."""

from __future__ import annotations

import json
import string
from pathlib import Path

import pytest

CONFIG_PATH = Path(__file__).resolve().parent.parent / "gyroscope_ui" / "config.json"
SECTIONS = [
    "application",
    "debug",
    "device",
    "acquisition",
    "simulation",
    "display",
    "storage",
    "session",
    "shortcuts",
    "messages",
    "ui",
]
ERROR_KEYS = [
    "device_port_in_use",
    "device_not_open",
    "device_open_failed",
    "device_io_failed",
    "device_timeout",
    "device_no_data",
    "device_lost",
    "device_reconnected",
    "storage_write_failed",
    "file_exists",
    "session_damaged",
    "recording_limit_reached",
]


@pytest.fixture(scope="module")
def data() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_sections_are_exactly_the_documented_ones(data):
    assert list(data) == SECTIONS


def test_no_version_in_config(data):
    assert "version" not in data["application"]


def test_group_letters_and_weekdays(data):
    assert data["storage"]["group_letters"] == list(string.ascii_uppercase)
    assert data["storage"]["weekday_abbreviations"] == ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def test_every_message_is_a_string_with_named_placeholders(data):
    formatter = string.Formatter()
    for key, text in data["messages"].items():
        assert isinstance(text, str) and text, key
        for _literal, field, _spec, _conv in formatter.parse(text):
            if field is None:
                continue
            assert field != "", f"positional placeholder in {key}"
            assert field.isidentifier(), f"bad placeholder {field!r} in {key}"


def test_error_keys_have_messages(data):
    for key in ERROR_KEYS:
        assert key in data["messages"], key


def test_message_keys_are_snake_case(data):
    for key in data["messages"]:
        assert key == key.lower() and " " not in key, key
