"""Application entry point: ``python -m gyroscope_ui [--simulate]``."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from gyroscope_ui import __version__
from gyroscope_ui.infrastructure.config import load_config
from gyroscope_ui.infrastructure.logging import exception_hook, get_logger, setup_logging


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Gyroscope-UI: live data and measurements of the Kreisel experiment"
    )
    parser.add_argument(
        "--simulate", action="store_true", help="start with the simulated gyroscope"
    )
    parser.add_argument(
        "--no-connect", action="store_true", help="do not connect automatically on start"
    )
    return parser.parse_known_args(argv)


def install_cleanup(app: Any, window: Any) -> None:
    """Join all worker threads when the application quits, also when the quit did not come
    through a close event of the window (e.g. ``app.quit()``)."""
    app.aboutToQuit.connect(window.shutdown)


def main(argv: list[str] | None = None) -> int:
    args, qt_args = parse_args(sys.argv[1:] if argv is None else argv)
    config = load_config()
    setup_logging(config.get("debug.level", "info"))
    sys.excepthook = exception_hook
    log = get_logger()

    from PySide6.QtWidgets import QApplication

    from gyroscope_ui.ui.windows.main_window import MainWindow

    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName(config.get("application.name", "Gyroscope-UI"))
    app.setApplicationVersion(__version__)
    window = MainWindow(config, simulate=args.simulate)
    install_cleanup(app, window)
    window.show()
    log.info("Gyroscope-UI %s started (simulate=%s)", __version__, args.simulate)
    if args.simulate or (config.get("application.auto_connect", True) and not args.no_connect):
        window.context.connection.connect_device()
    code = app.exec()
    window.shutdown()  # no-op after aboutToQuit; keeps threads joined before interpreter exit
    return code


if __name__ == "__main__":
    sys.exit(main())
