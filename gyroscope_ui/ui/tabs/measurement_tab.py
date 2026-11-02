"""The "Messung" tab: frequency and angular rate over time (plots and plot options).

Outside a measurement the plots show a rolling preview of the last ``display.preview_s``
seconds, or of the scrolling window if that is longer (time relative to now), so the students
see that the device works before they press Start; during and after a measurement they show
the recording. Redrawn on ``measurement.refreshed`` (``display.rate_hz``), never per sample
batch.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QVBoxLayout, QWidget

from gyroscope_ui.core.models import CHANNELS
from gyroscope_ui.ui.context import AppContext
from gyroscope_ui.ui.tabs.registry import TabBase, TabRegistry
from gyroscope_ui.ui.widgets.gyro_plot import GyroPlot
from gyroscope_ui.ui.widgets.measurement_view import MeasurementView


@TabRegistry.register
class MeasurementTab(TabBase):
    tab_id = "measurement"
    title_key = "tabs.measurement"
    order = 10

    def __init__(self, context: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(context, parent)
        self.view = MeasurementView(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        cfg = context.config
        self.view.apply_config(cfg)
        self._preview_s = float(cfg.get("display.preview_s", 30))
        self._label_time = cfg.text("gyro_plot.label_time")
        self._label_preview = cfg.text("gyro_plot.label_time_preview")
        self._mode = ""
        self._span_s = self._preview_s
        display = context.session.display
        self.view.set_options(display.auto_scroll, display.scroll_window_s, display.all_channels)
        self._set_scroll(display.auto_scroll, display.scroll_window_s)
        self.view.auto_scroll_changed.connect(self._on_auto_scroll_changed)
        self.view.all_channels_toggled.connect(
            lambda on: context.session.update_display(all_channels=on)
        )
        context.measurement.refreshed.connect(self.redraw)
        context.measurement.state_changed.connect(lambda _s: self.redraw())

    def _on_auto_scroll_changed(self, on: bool, window_s: float) -> None:
        self.context.session.update_display(auto_scroll=on, scroll_window_s=window_s)
        self._set_scroll(on, window_s)

    def _set_scroll(self, auto_scroll: bool, window_s: float) -> None:
        """The preview has to reach back as far as the scrolling window shows."""
        self._span_s = max(self._preview_s, window_s) if auto_scroll else self._preview_s
        self.context.measurement.set_preview_span_s(self._span_s)

    @property
    def plot(self) -> GyroPlot:
        return self.view.plot

    def redraw(self) -> None:
        m = self.context.measurement
        if m.state == "empty":
            self._show_preview()
        else:
            self._show_recording()

    def _set_mode(self, mode: str) -> None:
        if mode != self._mode:
            self._mode = mode
            self.plot.set_x_label(self._label_preview if mode == "preview" else self._label_time)
            self.plot.auto_range()

    def _show_recording(self) -> None:
        self._set_mode("recording")
        rec = self.context.measurement.recording
        curves = self.plot.curves
        # Each column is a copy of the whole recording: only build the visible ones.
        columns = {name: rec.column(name) for name in CHANNELS if curves[name].isVisible()}
        self.plot.set_data(rec.column("elapsed_s"), columns)

    def _show_preview(self) -> None:
        self._set_mode("preview")
        buffer = self.context.measurement.preview
        host_t = buffer.column("host_time_s")
        if len(host_t) == 0:
            self.plot.clear()
            return
        t = host_t - host_t[-1]
        keep = t >= -self._span_s
        columns = {name: buffer.column(name)[keep] for name in CHANNELS}
        self.plot.set_data(np.ascontiguousarray(t[keep]), columns)
