"""Write the German UI strings from config.json into the Designer ``.ui`` files.

At run time the texts are applied by ``gyroscope_ui.ui.i18n.apply_strings``; the forms themselves
carry no text, so Qt Creator / Designer shows empty buttons and labels. This tool copies the
strings that ``apply_strings`` would set into the matching ``.ui`` properties, so the forms are
readable while editing. ``config.json`` stays the source of truth: texts typed in Designer are
overwritten by the next run.

    .venv/bin/python -m gyroscope_ui.pyqt.sync_texts           # update the .ui files
    .venv/bin/python -m gyroscope_ui.pyqt.sync_texts --check   # exit 1 if a .ui file is out of date

``gyroscope_ui/pyqt/pyuic.sh`` runs this before regenerating the ``*_ui.py`` modules.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from gyroscope_ui.infrastructure.config import AppConfig, load_config

PYQT_DIR = Path(__file__).resolve().parent

# .ui file stem -> sections of the ``ui`` config that the code applies to it; the default is
# the stem itself.
SECTIONS: dict[str, tuple[str, ...]] = {}

# ``name@kind`` suffix -> Designer property.
_KIND_PROPERTIES = {
    "tooltip": "toolTip",
    "suffix": "suffix",
    "prefix": "prefix",
    "placeholder": "placeholderText",
    "title": "windowTitle",
}
_TITLE_CLASSES = {"QGroupBox", "QDockWidget"}


def _property_for(kind: str, class_name: str) -> str:
    if kind:
        return _KIND_PROPERTIES.get(kind, "")
    return "title" if class_name in _TITLE_CLASSES else "text"


def _set_string_property(element: ET.Element, name: str, text: str) -> None:
    for prop in element.findall("property"):
        if prop.get("name") == name:
            string = prop.find("string")
            if string is None:
                string = ET.SubElement(prop, "string")
            string.text = text
            string.attrib.pop("notr", None)
            return
    prop = ET.Element("property", name=name)
    ET.SubElement(prop, "string").text = text
    last = max((i for i, child in enumerate(element) if child.tag == "property"), default=-1)
    element.insert(last + 1, prop)


def sync_text(source: str, strings: dict[str, object]) -> str:
    """Return the ``.ui`` XML ``source`` with the plain-string entries of ``strings`` applied."""
    root = ET.fromstring(source)
    top = root.find("widget")
    elements = {
        element.get("name"): element
        for element in root.iter()
        if element.tag in ("widget", "action") and element.get("name")
    }
    for key, text in strings.items():
        name, _, kind = key.partition("@")
        if "_" in name or not isinstance(text, str):
            continue
        element = top if name == "self" else elements.get(name)
        if element is None:
            continue
        prop = _property_for(kind, element.get("class", "QAction"))
        if prop:
            _set_string_property(element, prop, text)
    ET.indent(root, space=" ")
    body = re.sub(r"<(\w+)([^<>]*?) />", r"<\1\2/>", ET.tostring(root, encoding="unicode"))
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{body}\n'


def synced_text(path: Path, config: AppConfig) -> str:
    strings: dict[str, object] = {}
    for section in SECTIONS.get(path.stem, (path.stem,)):
        strings.update(config.section("ui").get(section, {}))
    return sync_text(path.read_text(encoding="utf-8"), strings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="only report out-of-date files")
    args = parser.parse_args(argv)
    config = load_config()
    stale = 0
    for path in sorted(PYQT_DIR.glob("*.ui")):
        new = synced_text(path, config)
        if new == path.read_text(encoding="utf-8"):
            continue
        stale += 1
        if args.check:
            print(f"out of date: {path.name}")
        else:
            path.write_text(new, encoding="utf-8")
            print(f"updated {path.name}")
    return 1 if args.check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
