"""Logging setup: console plus rotating file log in the user data directory."""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from types import TracebackType

APP_DIR_NAME = "gyroscope-ui"
LOGGER_NAME = "gyroscope_ui"

_LEVELS = {
    "off": logging.CRITICAL + 10,
    "error": logging.ERROR,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "verbose": logging.DEBUG,
}


def user_data_dir() -> Path:
    """Per-user writable application directory (created on demand)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logger(name: str | None = None) -> logging.Logger:
    """Return the application logger or one of its children."""
    return logging.getLogger(f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME)


def setup_logging(
    level: str = "info", log_dir: Path | None = None, console: bool = True
) -> Path | None:
    """Set up the ``gyroscope_ui`` logger; return the log file (None if file logging failed)."""
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(_LEVELS.get(level.lower(), logging.INFO))
    logger.propagate = False
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    if console:
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(fmt)
        logger.addHandler(stream)

    log_file: Path | None = None
    try:
        directory = log_dir if log_dir is not None else user_data_dir() / "logs"
        directory.mkdir(parents=True, exist_ok=True)
        log_file = directory / "gyroscope_ui.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError as exc:
        logger.warning("File logging disabled: %s", exc)
        log_file = None
    return log_file


def exception_hook(
    exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None
) -> None:
    """``sys.excepthook`` replacement that logs unhandled exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc, tb)
        return
    get_logger().critical("Unhandled exception", exc_info=(exc_type, exc, tb))
