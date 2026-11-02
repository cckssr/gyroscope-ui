"""Helpers of the UI tests (imported by the tests and the conftest)."""

from __future__ import annotations


def connect(qtbot, window, timeout_ms: int = 10_000) -> None:
    """Connect to the simulation and wait until data flow."""
    window.context.connection.connect_device(True)
    qtbot.waitUntil(lambda: window.context.connection.state == "connected", timeout=timeout_ms)
    qtbot.waitUntil(lambda: len(window.context.measurement.preview) > 0, timeout=timeout_ms)


def record(qtbot, window, samples: int = 20, timeout_ms: int = 10_000) -> None:
    """Start a measurement and wait for ``samples`` recorded samples."""
    assert window.context.measurement.start()
    qtbot.waitUntil(
        lambda: len(window.context.measurement.recording) >= samples, timeout=timeout_ms
    )
