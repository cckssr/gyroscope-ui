"""Main window: control dock (panels), tab registry, toolbar, menus and status bar."""

from __future__ import annotations

import base64
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QByteArray, QObject, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractButton,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
)

from gyroscope_ui import __version__
from gyroscope_ui.core.models import LinkStats
from gyroscope_ui.infrastructure.config import AppConfig
from gyroscope_ui.infrastructure.logging import get_logger
from gyroscope_ui.infrastructure.paths import AppPaths
from gyroscope_ui.pyqt.main_window_ui import Ui_MainWindow
from gyroscope_ui.ui.context import AppContext
from gyroscope_ui.ui.controllers.connection_controller import ConnectionController, DeviceFactory
from gyroscope_ui.ui.controllers.measurement_controller import MeasurementController
from gyroscope_ui.ui.controllers.save_controller import SaveController
from gyroscope_ui.ui.controllers.shortcut_controller import ShortcutController
from gyroscope_ui.ui.controllers.simulation_controller import SimulationController
from gyroscope_ui.ui.i18n import apply_strings
from gyroscope_ui.ui.session_state import SessionState
from gyroscope_ui.ui.shortcuts import key_hint, native_text, with_digit
from gyroscope_ui.ui.tabs import TabBase, TabRegistry
from gyroscope_ui.ui.widgets.connection_panel import ConnectionPanel
from gyroscope_ui.ui.widgets.live_panel import LivePanel
from gyroscope_ui.ui.widgets.measurement_panel import MeasurementPanel
from gyroscope_ui.ui.widgets.save_panel import SavePanel
from gyroscope_ui.ui.widgets.shortcuts_dialog import ShortcutsDialog
from gyroscope_ui.ui.widgets.simulation_panel import SimulationPanel
from gyroscope_ui.ui.widgets.vscroll import lock_vertical_scroll

_log = get_logger("main_window")
_MESSAGE_MS = 6000
_MESSAGE_LOG_SIZE = 200

# Tooltips get the key appended: widget / action name -> entries of the ``shortcuts`` section.
_HINT_ENTRIES = {
    "buttonStartStop": ("start_stop", "stop"),
    "buttonReset": ("reset",),
    "buttonSave": ("save",),
    "buttonConnect": ("connect",),
    "buttonAutoRange": ("auto_range",),
    "actionStartStop": ("start_stop",),
    "actionSave": ("save",),
    "actionConnect": ("connect",),
    "actionShortcuts": ("help",),
}

# Answers of the "unsaved data" question when the window closes.
SAVE, DISCARD, CANCEL = "save", "discard", "cancel"


class MainWindow(QMainWindow):
    """``paths`` and ``config`` are injectable for tests; ``device_factory`` replaces device
    creation and ``persist=False`` keeps the session in memory only."""

    def __init__(
        self,
        config: AppConfig,
        simulate: bool = False,
        *,
        paths: AppPaths | None = None,
        device_factory: DeviceFactory | None = None,
        persist: bool = True,
    ) -> None:
        super().__init__()
        self._shut_down = False
        self.config = config
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        apply_strings(self, config.section("ui").get("main_window", {}))
        self.setWindowTitle(f"{config.text('main_window.window_title')} {__version__}")
        self.message_log: list[tuple[str, str]] = []

        paths = paths or AppPaths.default()
        session = SessionState(config, paths, parent=self, persist=persist)
        kwargs = {"factory": device_factory} if device_factory is not None else {}
        connection = ConnectionController(config, parent=self, **kwargs)
        measurement = MeasurementController(config, connection, parent=self)
        save = SaveController(config, session, connection, measurement, parent=self)
        self._simulation = SimulationController(config, connection, parent=self)
        self.context = AppContext(config, paths, session, connection, measurement, save)
        self._install_dialogs()

        self._build_panels()
        for source in (session, connection, measurement, save):
            source.message.connect(self._show_message)
        self._build_tabs()
        self._build_status_bar()
        self._connect_actions()
        self._shortcut_dialog: ShortcutsDialog | None = None
        self.shortcuts = ShortcutController(config, self.context, self, parent=self)
        self._annotate_shortcuts()
        connection.set_simulate(simulate)
        self._restore_layout()
        self.shortcuts.install()

    # ---- construction --------------------------------------------------------------------
    def _install_dialogs(self) -> None:
        """Dialogs of the controllers; tests replace these attributes."""
        cfg, ctx = self.config, self.context
        ctx.measurement.confirm = self._confirm
        ctx.save.ask_save_path = self._ask_save_path
        ctx.save.ask_directory = self._ask_directory
        self.ask_unsaved_on_close: Callable[[], str] = self._ask_unsaved_on_close
        self._title = cfg.text("main_window.window_title")

    def _build_panels(self) -> None:
        """Panels of the control dock, top to bottom; the dock never scrolls horizontally."""
        cfg, ctx, ui = self.config, self.context, self.ui
        self.connection_panel = ConnectionPanel()
        self.live_panel = LivePanel()
        self.measurement_panel = MeasurementPanel()
        self.save_panel = SavePanel()
        self.simulation_panel = SimulationPanel()
        layout = ui.layoutControls
        for i, panel in enumerate(
            (
                self.connection_panel,
                self.simulation_panel,
                self.live_panel,
                self.measurement_panel,
                self.save_panel,
            )
        ):
            panel.apply_config(cfg)
            layout.insertWidget(i, panel)
        ctx.connection.bind_panel(self.connection_panel)
        self._simulation.bind_panel(self.simulation_panel)
        ctx.measurement.bind_panels(self.measurement_panel, self.live_panel)
        ctx.save.bind_panel(self.save_panel)
        width = lock_vertical_scroll(ui.scrollControls)
        ui.dockControls.setMinimumWidth(width + 2)

    def _build_tabs(self) -> None:
        self.tabs: dict[str, TabBase] = {}
        tab_widget = self.ui.tabs
        for tab_class in TabRegistry.tabs():
            tab = tab_class(self.context)
            self.tabs[tab_class.tab_id] = tab
            tab_widget.addTab(tab, self.config.text(tab_class.title_key))
        tab_widget.currentChanged.connect(self._on_tab_changed)
        self._active_tab: TabBase | None = tab_widget.currentWidget()  # type: ignore[assignment]
        if self._active_tab is not None:
            self._active_tab.on_activated()

    def _build_status_bar(self) -> None:
        bar = self.statusBar()
        self._label_rate = QLabel()
        self._label_quality = QLabel()
        for label in (self._label_rate, self._label_quality):
            bar.addPermanentWidget(label)
        self.context.connection.stats_ready.connect(self._on_stats)
        self.context.connection.state_changed.connect(self._on_link_for_status)
        self._on_stats(None)

    def _connect_actions(self) -> None:
        ui, ctx = self.ui, self.context
        ui.actionConnect.triggered.connect(ctx.connection.toggle)
        ui.actionStartStop.triggered.connect(ctx.measurement.toggle)
        ui.actionSave.triggered.connect(self.save_measurement)
        ui.actionShortcuts.triggered.connect(self.toggle_shortcut_help)
        ui.actionOpenDataFolder.triggered.connect(self._open_data_folder)
        ui.actionQuit.triggered.connect(self.close)
        ui.actionAbout.triggered.connect(self._show_about)
        ctx.connection.state_changed.connect(lambda _s, _t: self._update_actions())
        ctx.measurement.state_changed.connect(lambda _s: self._update_actions())
        self._update_actions()

    # ---- layout --------------------------------------------------------------------------
    def _restore_layout(self) -> None:
        state = self.context.session.ui_state("window")
        try:
            if isinstance(state.get("geometry"), str):
                self.restoreGeometry(QByteArray(base64.b64decode(state["geometry"])))
            if isinstance(state.get("state"), str):
                self.restoreState(QByteArray(base64.b64decode(state["state"])))
        except ValueError as exc:
            _log.warning("cannot restore the window layout: %s", exc)

    def _save_layout(self) -> None:
        state = self.context.session.ui_state("window")
        state["geometry"] = base64.b64encode(bytes(self.saveGeometry())).decode("ascii")
        state["state"] = base64.b64encode(bytes(self.saveState())).decode("ascii")

    # ---- shortcuts (called by the ShortcutController) ------------------------------------
    def _annotate_shortcuts(self) -> None:
        """Append the shortcut to the tooltips of everything that has one."""
        cfg = self.config
        for name, ids in _HINT_ENTRIES.items():
            hint = key_hint(cfg, *ids)
            target = self.findChild(QObject, name)
            if not hint or target is None:
                continue
            tip = target.toolTip()  # type: ignore[attr-defined]
            if not tip and isinstance(target, (QAbstractButton, QAction)):
                tip = target.text()
            target.setToolTip(f"{tip}{hint}" if tip else hint.strip(" ()"))  # type: ignore[attr-defined]
        modifier = cfg.get("shortcuts.tab_modifier", "Ctrl")
        for i in range(min(self.ui.tabs.count(), 9)):
            tab_key = native_text(with_digit(modifier, i + 1))
            self.ui.tabs.setTabToolTip(i, f"{self.ui.tabs.tabText(i)} ({tab_key})")

    def select_tab(self, index: int) -> None:
        if 0 <= index < self.ui.tabs.count():
            self.ui.tabs.setCurrentIndex(index)

    def auto_range(self) -> None:
        tab = self.tabs.get("measurement")
        if tab is not None:
            tab.plot.auto_range()  # type: ignore[attr-defined]

    def toggle_shortcut_help(self) -> None:
        """F1: show the overview of the shortcuts, or hide it again."""
        if self._shortcut_dialog is None:
            self._shortcut_dialog = ShortcutsDialog(self.config, self.ui.tabs.count(), self)
        dialog = self._shortcut_dialog
        if dialog.isVisible():
            dialog.close()
        else:
            dialog.show()
            dialog.raise_()

    def save_measurement(self) -> Path | None:
        return self.context.save.save_manual()

    # ---- dialogs -------------------------------------------------------------------------
    def _confirm(self, text: str) -> bool:
        answer = QMessageBox.question(
            self,
            self._title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _ask_save_path(self, directory: Path, file_name: str) -> Path | None:
        cfg = self.config
        path, _ = QFileDialog.getSaveFileName(
            self,
            cfg.text("main_window.save_dialog_title"),
            str(directory / file_name),
            cfg.text("main_window.file_filter_csv"),
        )
        return Path(path) if path else None

    def _ask_directory(self, current: Path) -> Path | None:
        chosen = QFileDialog.getExistingDirectory(
            self, self.config.text("main_window.choose_data_dir"), str(current)
        )
        return Path(chosen) if chosen else None

    def _ask_unsaved_on_close(self) -> str:
        cfg = self.config
        buttons = QMessageBox.StandardButton
        answer = QMessageBox.question(
            self,
            cfg.message("close_unsaved_data_title"),
            cfg.message("close_unsaved_data_question"),
            buttons.Save | buttons.Discard | buttons.Cancel,
            buttons.Save,
        )
        return {buttons.Save: SAVE, buttons.Discard: DISCARD}.get(answer, CANCEL)

    def _open_data_folder(self) -> None:
        folder = self.context.session.data_dir
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _log.warning("cannot create the data folder %s: %s", folder, exc)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _show_about(self) -> None:
        cfg = self.config
        QMessageBox.about(
            self,
            cfg.text("main_window.about_title"),
            cfg.text("main_window.about_text", version=__version__),
        )

    # ---- slots ---------------------------------------------------------------------------
    def _on_tab_changed(self, index: int) -> None:
        if self._active_tab is not None:
            self._active_tab.on_deactivated()
        self._active_tab = self.ui.tabs.widget(index)  # type: ignore[assignment]
        if self._active_tab is not None:
            self._active_tab.on_activated()

    def _update_actions(self) -> None:
        ui, ctx, cfg = self.ui, self.context, self.config
        idle = ctx.connection.state in ("disconnected", "error")
        ui.actionConnect.setText(
            cfg.text("main_window.action_connect" if idle else "main_window.action_disconnect")
        )
        m = ctx.measurement
        ui.actionStartStop.setText(
            cfg.text("main_window.action_stop" if m.is_recording else "main_window.action_start")
        )
        ui.actionStartStop.setEnabled(m.is_recording or m.can_start)
        ui.actionSave.setEnabled(m.can_save)

    def _show_message(self, level: str, text: str) -> None:
        self.statusBar().showMessage(text, _MESSAGE_MS)
        self.message_log.append((level, text))
        del self.message_log[:-_MESSAGE_LOG_SIZE]
        {"error": _log.error, "warning": _log.warning}.get(level, _log.info)(text)

    def _on_stats(self, stats: LinkStats | None) -> None:
        cfg = self.config
        if stats is None or stats.received == 0:
            self._label_rate.setText(cfg.text("main_window.status_rate_none"))
            self._label_quality.setText("")
            return
        self._label_rate.setText(cfg.text("main_window.status_rate", rate=stats.rate_hz))
        self._label_quality.setText(
            cfg.text("main_window.status_invalid", invalid=stats.invalid) if stats.invalid else ""
        )
        self._update_actions()  # Start becomes possible once data flow

    def _on_link_for_status(self, state: str, _text: str) -> None:
        if state in ("disconnected", "error"):
            self._on_stats(None)

    # ---- shutdown ------------------------------------------------------------------------
    def shutdown(self) -> None:
        """Stop the measurement, join every worker thread, then save the session.

        Idempotent; called from :meth:`closeEvent` and from ``QApplication.aboutToQuit`` so no
        ``QThread`` is destroyed while it still runs, however the application ends.
        """
        if self._shut_down:
            return
        self._shut_down = True
        try:
            self.shortcuts.uninstall()
            self.context.measurement.shutdown()
            try:
                self._save_layout()
            except Exception:
                _log.exception("cannot save the window layout")
        finally:
            try:
                self.context.connection.shutdown()
            finally:
                self.context.session.shutdown()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        m = self.context.measurement
        if not self._shut_down:
            if m.is_recording:
                m.stop()  # an auto-save may follow
            if m.has_unsaved:
                answer = self.ask_unsaved_on_close()
                if answer == CANCEL or (answer == SAVE and self.save_measurement() is None):
                    event.ignore()
                    return
        self.shutdown()
        super().closeEvent(event)
