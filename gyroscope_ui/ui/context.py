"""What every tab receives: configuration, paths, shared state and the controllers.

Extension points for later tabs (e.g. "Auswertung"):

- streamed data: ``connection.samples_ready`` (``SampleBatch`` on the GUI thread, ≈ 20 Hz) and
  ``measurement.recording`` / ``measurement.preview`` (read only);
- display refresh: ``measurement.refreshed`` (``display.rate_hz``), redraw there, not per batch;
- device calls: ``connection.run_device(fn)`` and ``connection.watch(future, callback)``;
- persistent tab state: ``session.ui_state(tab_id)`` + ``session.touch_ui_state(tab_id)``;
- status bar: ``session.message.emit(level, text)``.
"""

from __future__ import annotations

from dataclasses import dataclass

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.paths import AppPaths
from gyroscope_ui.ui.controllers.connection_controller import ConnectionController
from gyroscope_ui.ui.controllers.measurement_controller import MeasurementController
from gyroscope_ui.ui.controllers.save_controller import SaveController
from gyroscope_ui.ui.session_state import SessionState


@dataclass
class AppContext:
    config: AppConfig
    paths: AppPaths
    session: SessionState
    connection: ConnectionController
    measurement: MeasurementController
    save: SaveController
