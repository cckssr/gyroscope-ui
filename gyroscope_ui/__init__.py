"""Gyroscope-UI: PySide6 application for the Kreisel (gyroscope) experiment of the lab course."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gyroscope-ui")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "0+unknown"
