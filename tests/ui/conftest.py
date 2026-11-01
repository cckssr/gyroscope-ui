"""Fixtures of the UI tests: offscreen Qt and a configuration with test overrides."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from gyroscope_ui.infrastructure.config import load_config  # noqa: E402


@pytest.fixture
def config():
    return load_config(overrides={"session": {"debounce_s": 0.05}})
