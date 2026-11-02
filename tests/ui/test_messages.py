"""Message texts: formatting never raises, keys fall back sensibly."""

from __future__ import annotations

from gyroscope_ui.infrastructure.config import load_config
from gyroscope_ui.ui.messages import error_text, message_text


class _KeyError(Exception):
    def __init__(self, key: str, detail: str = "", **fmt: object) -> None:
        super().__init__(key)
        self.key = key
        self.detail = detail
        self.fmt = fmt


def test_named_placeholders():
    config = load_config()
    assert "12345" in message_text(config, "device_port_in_use", port=12345)
    assert message_text(config, "storage_write_failed", path="a.csv", error="voll").startswith(
        "Speichern in a.csv"
    )


def test_missing_value_shows_dash_and_unknown_key_is_returned():
    config = load_config()
    assert "–" in message_text(config, "device_port_in_use")
    assert message_text(config, "no_such_key") == "no_such_key"


def test_error_text_uses_key_fmt_and_detail():
    config = load_config()
    assert "7" in error_text(config, _KeyError("device_port_in_use", port=7))
    assert "voll" in error_text(config, _KeyError("device_io_failed", detail="voll"))


def test_error_text_without_key_falls_back_to_io_failed():
    config = load_config()
    assert "kaputt" in error_text(config, RuntimeError("kaputt"))
