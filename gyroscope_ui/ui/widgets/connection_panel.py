"""Connection panel ("Gerät"): link LED and state, device identity, WiFi hint, simulation switch
and the Connect / Disconnect button."""

from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QGroupBox, QWidget

from gyroscope_ui.core.models import DeviceInfo, LinkState
from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.pyqt.connection_panel_ui import Ui_ConnectionPanel
from gyroscope_ui.ui.i18n import apply_strings

# LinkState -> StatusLed state (CONCEPT 4.1).
_LED_STATES: dict[LinkState, str] = {
    LinkState.DISCONNECTED: "off",
    LinkState.CONNECTING: "busy",
    LinkState.CONNECTED: "ok",
    LinkState.STALE: "warning",
    LinkState.LOST: "error",
    LinkState.ERROR: "error",
}
_IDLE_STATES = (LinkState.DISCONNECTED, LinkState.ERROR)


class ConnectionPanel(QGroupBox):
    """View only: emits user intents, shows the link state it is told about."""

    connect_requested = Signal()
    disconnect_requested = Signal()
    simulate_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_ConnectionPanel()
        self.ui.setupUi(self)
        self._config: AppConfig | None = None
        self._state = LinkState.DISCONNECTED
        self.ui.buttonConnect.clicked.connect(self._on_button)
        self.ui.checkSimulate.toggled.connect(self.simulate_toggled)

    def apply_config(self, config: AppConfig) -> None:
        self._config = config
        state_text = self.ui.labelState.text()  # keep what set_link() showed before
        apply_strings(self, config.section("ui").get("connection_panel", {}))
        ssid = str(config.get("device.ssid_pattern", ""))
        self.ui.labelHint.setText(config.text("connection_panel.labelHint", ssid=ssid))
        self.set_link(self._state.value, state_text)
        self.set_device(None)

    def set_link(self, state: str, text: str) -> None:
        """Show the link ``state`` (a ``LinkState`` value) with its status ``text``."""
        self._state = LinkState(state)
        self.ui.ledLink.set_state(_LED_STATES[self._state])
        self.ui.labelState.setText(text)
        key = "button_connect" if self._state in _IDLE_STATES else "button_disconnect"
        if self._config is not None:
            self.ui.buttonConnect.setText(self._config.text(f"connection_panel.{key}"))

    def set_device(self, info: DeviceInfo | None) -> None:
        """Show the identity of the connected device, a dash for ``None``."""
        if self._config is None:
            return
        if info is None:
            self.ui.labelDevice.setText(self._config.text("connection_panel.device_none"))
            return
        unknown = self._config.text("connection_panel.unknown_value")
        firmware = info.firmware_version or unknown
        protocol = unknown if info.protocol_version is None else str(info.protocol_version)
        self.ui.labelDevice.setText(
            self._config.text(
                "connection_panel.device_format",
                device_id=info.device_id,
                firmware=firmware,
                protocol=protocol,
            )
        )

    def set_simulate(self, on: bool) -> None:
        """Show the simulation switch without emitting ``simulate_toggled``."""
        with QSignalBlocker(self.ui.checkSimulate):
            self.ui.checkSimulate.setChecked(on)

    def set_simulate_enabled(self, enabled: bool) -> None:
        self.ui.checkSimulate.setEnabled(enabled)

    def _on_button(self) -> None:
        if self._state in _IDLE_STATES:
            self.connect_requested.emit()
        else:
            self.disconnect_requested.emit()
