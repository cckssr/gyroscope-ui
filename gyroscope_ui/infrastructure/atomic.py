"""Atomic file writes: temporary file next to the target, fsync, ``os.replace``."""

from __future__ import annotations

import contextlib
import os
import uuid
from collections.abc import Iterator
from pathlib import Path


def _fsync_file(path: Path) -> None:
    """Flush the file contents at ``path`` to stable storage."""
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(directory: Path) -> None:
    """Make a rename inside ``directory`` durable (POSIX; best effort, a no-op elsewhere)."""
    if os.name != "posix":
        return
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


@contextlib.contextmanager
def atomic_path(path: Path) -> Iterator[Path]:
    """Yield a temp path next to ``path``; on success it is fsynced and replaces ``path`` (the
    directory is fsynced too, best effort), else it is removed. The caller must have closed
    the temp file when the block ends."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        yield tmp
        _fsync_file(tmp)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    _fsync_dir(path.parent)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` atomically (temp file, fsync, ``os.replace``)."""
    with atomic_path(path) as tmp, tmp.open("wb") as fh:
        fh.write(data)


def atomic_write_text(path: Path, text: str) -> None:
    """UTF-8 text with ``\\n`` line endings, written atomically."""
    atomic_write_bytes(path, text.encode("utf-8"))
