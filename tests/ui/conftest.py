"""Fixtures of the UI tests: offscreen Qt, a fast configuration and main windows on the mock."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from ui_helpers import connect  # noqa: E402

from gyroscope_ui.infrastructure.config import load_config  # noqa: E402
from gyroscope_ui.infrastructure.paths import AppPaths  # noqa: E402
from gyroscope_ui.ui.windows.main_window import DISCARD, MainWindow  # noqa: E402

# Fast simulation and timers. Windows default to the simulation and never auto-connect, so the
# real device (UDP port 12345) is never touched.
FAST = {
    "session": {"debounce_s": 0.05},
    "simulation": {"time_scale": 0.1},
    "acquisition": {"batch_interval_s": 0.02, "stats_interval_s": 0.1},
    "display": {"rate_hz": 50},
    "device": {"data_timeout_s": 0.5, "lost_after_s": 1.0},
}


@pytest.fixture
def config(tmp_path):
    return load_config(
        overrides={
            **FAST,
            "application": {"data_dir": str(tmp_path / "data"), "auto_connect": False},
        }
    )


@pytest.fixture
def paths(tmp_path):
    return AppPaths(tmp_path / "appdata")


@pytest.fixture
def make_window(qtbot, config, paths):
    """``make_window(**kwargs)`` builds a main window on the shared test paths (restore tests
    build a second one); every window is closed at teardown without dialogs."""
    windows: list[MainWindow] = []

    def make(cfg=None, simulate: bool = True, **kwargs) -> MainWindow:
        window = MainWindow(cfg or config, simulate=simulate, paths=paths, **kwargs)
        window.ask_unsaved_on_close = lambda: DISCARD
        window.context.measurement.confirm = lambda _text: True
        # never open a real (modal) file dialog in a test
        window.context.save.ask_save_path = lambda _directory, _name: None
        window.context.save.ask_directory = lambda _current: None
        qtbot.addWidget(window)
        windows.append(window)
        return window

    yield make
    for window in windows:
        window.ask_unsaved_on_close = lambda: DISCARD
        window.close()


@pytest.fixture
def window(make_window):
    return make_window()


@pytest.fixture
def connected(qtbot, window):
    connect(qtbot, window)
    return window
