"""Configuration loading, dotted access, overrides and message formatting."""

from __future__ import annotations

import json

from gyroscope_ui.infrastructure.config import AppConfig, load_config


def test_loads_packaged_config():
    config = load_config()
    assert config.get("device.port") == 12345
    assert config.section("device")["host"] == "192.168.4.1"
    assert config.get("application.name") == "Gyroscope-UI"


def test_get_default_for_missing_path():
    config = AppConfig({"a": {"b": 1}})
    assert config.get("a.b") == 1
    assert config.get("a.c", 7) == 7
    assert config.get("a.b.c", "x") == "x"
    assert config.section("a") == {"b": 1}
    assert config.section("missing") == {}


def test_overrides_are_merged_deeply():
    config = load_config(overrides={"device": {"port": 1}})
    assert config.get("device.port") == 1
    assert config.get("device.host") == "192.168.4.1"


def test_with_overrides_does_not_modify_the_original():
    config = AppConfig({"a": {"b": 1, "c": 2}})
    other = config.with_overrides({"a": {"b": 3}})
    assert other.get("a.b") == 3 and other.get("a.c") == 2
    assert config.get("a.b") == 1


def test_missing_or_broken_file_gives_empty_config(tmp_path):
    assert load_config(tmp_path / "nope.json").data == {}
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert load_config(broken).data == {}


def test_text_and_message_fall_back_to_the_key():
    config = AppConfig(
        {"ui": {"tabs": {"measurement": "Messung"}}, "messages": {"hi": "Hallo {n}"}}
    )
    assert config.text("tabs.measurement") == "Messung"
    assert config.text("tabs.unknown") == "tabs.unknown"
    assert config.message("hi", n=3) == "Hallo 3"
    assert config.message("hi") == "Hallo {n}"  # missing argument: template as is
    assert config.message("unknown") == "unknown"


def test_utf8_file(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"messages": {"x": "Größe"}}, ensure_ascii=False), encoding="utf-8")
    assert load_config(path).message("x") == "Größe"
