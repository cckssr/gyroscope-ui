"""Deliver the result of a ``concurrent.futures.Future`` on the GUI thread.

Futures returned by the acquisition worker complete on the worker thread. ``FutureBridge.watch``
registers a callback that runs on the thread the bridge lives in (the GUI thread) once the
future is done, so slots never touch widgets from a worker thread.
"""

from __future__ import annotations

import itertools
import threading
from collections.abc import Callable
from concurrent.futures import Future

from PySide6.QtCore import QObject, Signal, Slot

from gyroscope_ui.infrastructure.logging import get_logger

_log = get_logger("future_bridge")


class FutureBridge(QObject):
    """Run ``callback(future)`` on the owner's thread when ``future`` is done."""

    _done = Signal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._callbacks: dict[int, tuple[Future, Callable[[Future], None]]] = {}
        self._ids = itertools.count()
        self._lock = threading.Lock()
        self._done.connect(self._on_done)

    def watch(self, future: Future, callback: Callable[[Future], None]) -> None:
        with self._lock:
            ident = next(self._ids)
            self._callbacks[ident] = (future, callback)
        future.add_done_callback(lambda _f, i=ident: self._done.emit(i))

    def cancel_all(self) -> None:
        """Forget all pending callbacks (e.g. after a disconnect)."""
        with self._lock:
            self._callbacks.clear()

    @Slot(int)
    def _on_done(self, ident: int) -> None:
        with self._lock:
            entry = self._callbacks.pop(ident, None)
        if entry is None:
            return
        future, callback = entry
        try:
            callback(future)
        except Exception:
            _log.exception("future callback failed")
