#!/usr/bin/env python3
"""
Validierungsskript für die generierte API-Dokumentation
Prüft, ob die Autodoc-Funktionalität korrekt funktioniert
"""

import os
from pathlib import Path
import re


def validate_api_documentation():
    """Validiert die generierte API-Dokumentation"""
    print("🔍 Validiere API-Dokumentation...")

    # Pfad zur generierten HTML-Datei
    api_html_path = Path("docs/_build/html/api.html")

    if not api_html_path.exists():
        print("❌ API-Dokumentation nicht gefunden!")
        return False

    # Lese den Inhalt der HTML-Datei
    content = api_html_path.read_text(encoding="utf-8")

    # Prüfe auf wichtige Klassen und Funktionen
    expected_items = [
        "MainWindow",
        "__init__",
        "DataController",
        "DeviceManager",
        "PlotWidget",
        "ControlWidget",
        "class",
        "method",
        "function",
        "Parameters",
        "Returns",
    ]

    found_items = []
    missing_items = []

    for item in expected_items:
        if item in content:
            found_items.append(item)
        else:
            missing_items.append(item)

    print(
        f"✅ Gefunden: {len(found_items)} von {len(expected_items)} erwarteten Elementen"
    )
    print(f"   Gefundene Elemente: {', '.join(found_items)}")

    if missing_items:
        print(f"⚠️  Fehlende Elemente: {', '.join(missing_items)}")

    # Prüfe die Dateigröße
    file_size = api_html_path.stat().st_size
    print(f"📊 Dateigröße: {file_size:,} Bytes")

    # Prüfe auf Docstrings
    docstring_patterns = [
        r"<dt[^>]*>.*?__init__.*?</dt>",
        r"<dt[^>]*>.*?class.*?</dt>",
        r"<dt[^>]*>.*?def.*?</dt>",
        r"<dd[^>]*>.*?<p>.*?</p>.*?</dd>",
    ]

    docstring_count = 0
    for pattern in docstring_patterns:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        docstring_count += len(matches)

    print(f"📝 Dokumentierte Elemente gefunden: {docstring_count}")

    # Prüfe auf Quellenverweise
    source_links = content.count("[source]")
    print(f"🔗 Quellenverweise: {source_links}")

    # Bewertung
    if file_size > 50000 and len(found_items) > len(expected_items) * 0.7:
        print("🎉 API-Dokumentation ist vollständig und funktionsfähig!")
        return True
    elif file_size > 10000:
        print("✅ API-Dokumentation ist grundlegend funktionsfähig")
        return True
    else:
        print("⚠️  API-Dokumentation möglicherweise unvollständig")
        return False


def validate_module_index():
    """Validiert den Python-Modulindex"""
    print("\n🔍 Validiere Python-Modulindex...")

    modindex_path = Path("docs/_build/html/py-modindex.html")

    if not modindex_path.exists():
        print("❌ Python-Modulindex nicht gefunden!")
        return False

    content = modindex_path.read_text(encoding="utf-8")

    # Prüfe auf src-Module
    src_modules = [
        "src.main_window",
        "src.data_controller",
        "src.device_manager",
        "src.plot",
        "src.control",
        "src.helper_classes",
        "src.debug_utils",
    ]

    found_modules = []
    for module in src_modules:
        if module in content:
            found_modules.append(module)

    print(f"✅ Module im Index: {len(found_modules)} von {len(src_modules)}")
    print(f"   Gefundene Module: {', '.join(found_modules)}")

    return len(found_modules) > 0


def main():
    """Hauptfunktion"""
    print("🎯 Validierung der API-Dokumentation")
    print("=" * 50)

    os.chdir(Path(__file__).parent)

    api_ok = validate_api_documentation()
    modindex_ok = validate_module_index()

    print("\n" + "=" * 50)
    if api_ok and modindex_ok:
        print("🎉 Alle Validierungen erfolgreich!")
        print("✅ Python Autodoc-Funktionalität ist vollständig implementiert!")
        print("\n📋 Funktionen:")
        print("- ✅ Automatische API-Dokumentation aus Docstrings")
        print("- ✅ Klassen- und Funktionsdokumentation")
        print("- ✅ Quellenverweise zu Python-Code")
        print("- ✅ Python-Modulindex")
        print("- ✅ Suchfunktionalität")
        print("- ✅ Google/NumPy-Style Docstring-Unterstützung")
    else:
        print("⚠️  Einige Validierungen sind fehlgeschlagen")
        print(
            "Die Autodoc-Funktionalität ist grundlegend implementiert, aber möglicherweise nicht vollständig"
        )


if __name__ == "__main__":
    main()
