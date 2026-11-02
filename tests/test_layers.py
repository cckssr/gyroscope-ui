"""Layer rules (ARCHITECTURE section 1): ``ui/ -> infrastructure/ -> core/``.

AST scan of the sources; nothing is imported, so the test also covers modules that fail to
import for other reasons.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE = "gyroscope_ui"
ROOT = Path(__file__).resolve().parent.parent / PACKAGE
CORE_FILES = sorted((ROOT / "core").rglob("*.py"))
INFRA_FILES = sorted(
    p for p in (ROOT / "infrastructure").rglob("*.py") if p.name != "qt_threads.py"
)

QT_MODULES = {"PySide6", "pyqtgraph", "shiboken6"}
CORE_FORBIDDEN = QT_MODULES | {"socket"}
# Calls that perform file I/O when used on a pathlib.Path or the builtin ``open``.
FILE_CALLS = {"open", "write_text", "write_bytes", "read_text", "read_bytes", "mkdir", "unlink"}


def _module_name(path: Path) -> str:
    try:
        parts = list(path.relative_to(ROOT.parent).with_suffix("").parts)
    except ValueError:  # a file outside the package (scanner self-test)
        parts = [path.stem]
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _imports(path: Path) -> set[str]:
    """Absolute dotted names of everything the file imports (relative imports resolved)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = _module_name(path).split(".")
    if path.name != "__init__.py":
        package = package[:-1]
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - node.level + 1]
                module = ".".join([*base, node.module] if node.module else base)
            else:
                module = node.module or ""
            found.add(module)
            found.update(f"{module}.{alias.name}" for alias in node.names)
    return found


def _top_levels(names: set[str]) -> set[str]:
    return {name.split(".")[0] for name in names}


def _under(names: set[str], prefix: str) -> set[str]:
    return {n for n in names if n == prefix or n.startswith(prefix + ".")}


def _file_calls(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name in FILE_CALLS:
                calls.add(name)
    return calls


def _ids(paths: list[Path]) -> list[str]:
    return [str(p.relative_to(ROOT)) for p in paths]


def test_scan_finds_the_layer_files():
    assert CORE_FILES and INFRA_FILES


@pytest.mark.parametrize("path", CORE_FILES, ids=_ids(CORE_FILES))
def test_core_has_no_qt_sockets_or_file_io(path):
    names = _imports(path)
    assert not _top_levels(names) & CORE_FORBIDDEN
    assert not _file_calls(path)


@pytest.mark.parametrize("path", CORE_FILES, ids=_ids(CORE_FILES))
def test_core_does_not_import_upper_layers(path):
    names = _imports(path)
    assert not _under(names, f"{PACKAGE}.infrastructure")
    assert not _under(names, f"{PACKAGE}.ui")


@pytest.mark.parametrize("path", INFRA_FILES, ids=_ids(INFRA_FILES))
def test_infrastructure_has_no_qt_outside_qt_threads(path):
    assert not _top_levels(_imports(path)) & QT_MODULES


@pytest.mark.parametrize("path", INFRA_FILES, ids=_ids(INFRA_FILES))
def test_infrastructure_does_not_import_ui(path):
    assert not _under(_imports(path), f"{PACKAGE}.ui")


def test_qt_threads_does_not_import_ui():
    path = ROOT / "infrastructure" / "qt_threads.py"
    if path.exists():
        assert not _under(_imports(path), f"{PACKAGE}.ui")


def test_scanner_detects_violations(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("import socket\nfrom PySide6.QtCore import QObject\nopen('x')\n")
    assert _top_levels(_imports(bad)) == {"socket", "PySide6"}
    assert _file_calls(bad) == {"open"}
