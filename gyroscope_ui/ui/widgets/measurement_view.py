"""Content of the "Messung" tab: the plots and the plot controls below them."""

from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QWidget

from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.pyqt.measurement_view_ui import Ui_MeasurementView
from gyroscope_ui.ui.i18n import apply_strings
from gyroscope_ui.ui.widgets.gyro_plot import GyroPlot


class MeasurementView(QWidget):
    """View only. The options are applied to the plot here and reported by signal (so the
    session state can store them); ``set_options`` restores them without emitting."""

    auto_scroll_changed = Signal(bool, float)  # enabled, window in s
    all_channels_toggled = Signal(bool)
    auto_range_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_MeasurementView()
        self.ui.setupUi(self)
        self.ui.checkAutoScroll.toggled.connect(self._on_auto_scroll)
        self.ui.spinScrollWindow.valueChanged.connect(self._on_auto_scroll)
        self.ui.checkAllChannels.toggled.connect(self._on_all_channels)
        self.ui.buttonAutoRange.clicked.connect(self._on_auto_range)

    @property
    def plot(self) -> GyroPlot:
        return self.ui.plot

    def apply_config(self, config: AppConfig) -> None:
        apply_strings(self, config.section("ui").get("measurement_view", {}))
        self.plot.apply_config(config)
        self.set_options(
            bool(config.get("display.auto_scroll", True)),
            float(config.get("display.scroll_window_s", 60)),
            bool(config.get("display.all_channels", False)),
        )

    def set_options(self, auto_scroll: bool, window_s: float, all_channels: bool) -> None:
        """Show the options (and apply them to the plot) without emitting signals."""
        with (
            QSignalBlocker(self.ui.checkAutoScroll),
            QSignalBlocker(self.ui.spinScrollWindow),
            QSignalBlocker(self.ui.checkAllChannels),
        ):
            self.ui.checkAutoScroll.setChecked(auto_scroll)
            self.ui.spinScrollWindow.setValue(round(window_s))
            self.ui.checkAllChannels.setChecked(all_channels)
        self.ui.spinScrollWindow.setEnabled(auto_scroll)
        self.plot.set_all_channels(all_channels)
        self.plot.set_auto_scroll(auto_scroll, float(self.ui.spinScrollWindow.value()))

    def _on_auto_scroll(self, *_args: object) -> None:
        enabled = self.ui.checkAutoScroll.isChecked()
        window_s = float(self.ui.spinScrollWindow.value())
        self.ui.spinScrollWindow.setEnabled(enabled)
        self.plot.set_auto_scroll(enabled, window_s)
        self.auto_scroll_changed.emit(enabled, window_s)

    def _on_all_channels(self, on: bool) -> None:
        self.plot.set_all_channels(on)
        self.all_channels_toggled.emit(on)

    def _on_auto_range(self) -> None:
        self.plot.auto_range()
        self.auto_range_requested.emit()
