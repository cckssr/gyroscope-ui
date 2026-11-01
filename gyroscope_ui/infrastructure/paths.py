"""Application directories below the per-user data directory (CONCEPT sections 6 and 8)."""

from __future__ import annotations

from pathlib import Path

from gyroscope_ui.infrastructure.logging import user_data_dir


class AppPaths:
    """Directory layout of the application data; every property creates its directory."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    @classmethod
    def default(cls) -> AppPaths:
        """Layout in ``user_data_dir()``."""
        return cls(user_data_dir())

    @staticmethod
    def default_data_dir() -> Path:
        """Default folder for measurement files: ``~/Documents/Kreisel`` (or the home
        directory if there is no ``Documents``). Not created."""
        documents = Path.home() / "Documents"
        if documents.is_dir():
            return documents / "Kreisel"
        return Path.home()

    def _dir(self, name: str | None) -> Path:
        path = self.root / name if name else self.root
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def session_dir(self) -> Path:
        """Holds ``session.json`` (the root itself)."""
        return self._dir(None)

    @property
    def logs_dir(self) -> Path:
        return self._dir("logs")
