"""Status LED smoke test."""

from __future__ import annotations

import pytest

from gyroscope_ui.ui.widgets.status_led import StatusLed


def test_states(qtbot):
    led = StatusLed()
    qtbot.addWidget(led)
    assert led.state == "off"
    for state in ("ok", "busy", "warning", "error", "off"):
        led.set_state(state)
        assert led.state == state
    led.grab()  # paints without error


def test_unknown_state_is_rejected(qtbot):
    led = StatusLed()
    qtbot.addWidget(led)
    with pytest.raises(ValueError):
        led.set_state("purple")
