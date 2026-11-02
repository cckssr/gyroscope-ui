#!/bin/bash
# Regenerate the *_ui.py modules from the Qt Designer .ui files (run from the repository root).
# First copies the German strings from config.json into the .ui files (see sync_texts.py).
set -e
cd "$(dirname "$0")/../.."
.venv/bin/python -m gyroscope_ui.pyqt.sync_texts
shopt -s nullglob  # no .ui files yet: the loop body is skipped
for f in gyroscope_ui/pyqt/*.ui; do
    out="${f%.ui}_ui.py"
    .venv/bin/pyside6-uic "$f" -o "$out"
    echo "generated $out"
done
