"""Show a Designer form on its own, without controllers, devices or data.

The ``.ui`` file is compiled on the fly (no ``pyuic.sh`` run needed) and the German strings from
``config.json`` are applied, so the window looks like the running application minus the logic:
combo boxes, tables and plots that the code fills stay empty.

    .venv/bin/python -m gyroscope_ui.pyqt.preview                 # list the forms
    .venv/bin/python -m gyroscope_ui.pyqt.preview main_window     # show one form
    .venv/bin/python -m gyroscope_ui.pyqt.preview main_window --watch   # reload on save
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6 import QtWidgets
from PySide6.QtCore import QFileSystemWatcher, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from gyroscope_ui.infrastructure.config import load_config
from gyroscope_ui.pyqt.sync_texts import PYQT_DIR, SECTIONS
from gyroscope_ui.ui.i18n import apply_strings


def uic_executable() -> str:
    """The ``pyside6-uic`` of the running interpreter (``which`` adds ``.exe`` on Windows; the
    scripts folder of a venv is not on ``PATH`` unless the venv is activated)."""
    found = shutil.which("pyside6-uic", path=str(Path(sys.executable).parent))
    found = found or shutil.which("pyside6-uic")
    if found is None:
        raise FileNotFoundError("pyside6-uic not found next to the Python interpreter or on PATH")
    return found


def compile_form(form: Path) -> str:
    """The Python module ``pyside6-uic`` generates from the ``.ui`` file ``form``."""
    result = subprocess.run(
        [uic_executable(), str(form)], capture_output=True, text=True, check=True
    )
    return result.stdout


def load_form_class(form: Path) -> tuple[type, type]:
    """``(Ui_<Name>, widget base class)`` of a ``.ui`` file, compiled on the fly (what
    ``QtUiTools.loadUiType`` does, which returns ``None`` when it cannot find ``uic``)."""
    namespace: dict[str, object] = {}
    exec(compile(compile_form(form), str(form), "exec"), namespace)  # noqa: S102
    ui_class = next(v for k, v in namespace.items() if k.startswith("Ui_"))
    base_name = ET.parse(form).getroot().find("widget").get("class")  # type: ignore[union-attr]
    return ui_class, getattr(QtWidgets, str(base_name))  # type: ignore[return-value]


def build_form(name: str) -> QWidget:
    """Instantiate the form ``name`` (a ``.ui`` file stem) with the configured UI strings."""
    form_class, base_class = load_form_class(PYQT_DIR / f"{name}.ui")

    class Preview(form_class, base_class):  # type: ignore[misc, valid-type]
        def __init__(self) -> None:
            super().__init__()
            self.setupUi(self)

    widget = Preview()
    ui_config = load_config().section("ui")
    for section in SECTIONS.get(name, (name,)):
        apply_strings(widget, ui_config.get(section, {}))
    return widget


def main(argv: list[str] | None = None) -> int:
    forms = sorted(path.stem for path in PYQT_DIR.glob("*.ui"))
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument("form", nargs="?", choices=forms, help="stem of the .ui file")
    parser.add_argument("--watch", action="store_true", help="reload when the .ui file changes")
    args = parser.parse_args(argv)
    if args.form is None:
        print("\n".join(forms))
        return 0

    app = QApplication(sys.argv[:1])
    windows: list[QWidget] = [build_form(args.form)]
    windows[0].show()

    if args.watch:
        path = str(PYQT_DIR / f"{args.form}.ui")
        watcher = QFileSystemWatcher([path])

        def reload() -> None:
            old = windows.pop()
            try:
                new = build_form(args.form)
            except Exception as error:  # a half-saved or invalid file must not end the preview
                print(f"reload failed: {error}", file=sys.stderr)
                windows.append(old)
            else:
                new.setGeometry(old.geometry())
                new.show()
                old.close()
                windows.append(new)
            if path not in watcher.files():  # editors replace the file on save
                watcher.addPath(path)

        watcher.fileChanged.connect(lambda _: QTimer.singleShot(200, reload))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
