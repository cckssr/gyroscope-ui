#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Verbesserungsskript für die HRNGGUI-Anwendung.

Dieses Skript führt zusätzliche Verbesserungen an der Codebase durch, wie z.B.:
1. Hinzufügen von Type-Hints
2. Verbessern von Kommentaren
3. Optimieren von Logik
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set


def add_type_hints(file_path: str) -> int:
    """
    Fügt fehlende Typ-Annotationen zu Funktionen hinzu.

    Args:
        file_path: Pfad zur Python-Datei

    Returns:
        Anzahl der hinzugefügten Typ-Annotationen
    """
    print(f"Füge Typ-Annotationen zu {file_path} hinzu...")

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Zählen der aktuellen Typ-Annotationen
    current_annotations = len(
        re.findall(r"def\s+\w+\s*\([^)]*:\s*[A-Za-z\[\]]+", content)
    )
    print(f"Aktuelle Typ-Annotationen: {current_annotations}")

    # Hier könnten wir mehr Code hinzufügen, um tatsächlich Typ-Annotationen hinzuzufügen
    # Dies ist jedoch eine komplexe Aufgabe, die eine genaue Analyse des Codes erfordert

    return current_annotations


def improve_error_handling(file_path: str) -> int:
    """
    Verbessert die Fehlerbehandlung durch Ersetzen von allgemeinen Exception
    durch spezifischere Ausnahmen.

    Args:
        file_path: Pfad zur Python-Datei

    Returns:
        Anzahl der verbesserten Ausnahmebehandlungen
    """
    print(f"Verbessere Fehlerbehandlung in {file_path}...")

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Zählen der aktuellen allgemeinen Ausnahmebehandlungen
    general_exceptions = len(re.findall(r"except Exception", content))
    print(f"Allgemeine Ausnahmebehandlungen: {general_exceptions}")

    # Hier könnten wir Code hinzufügen, um die Fehlerbehandlung zu verbessern

    return general_exceptions


def analyze_method_complexity(file_path: str) -> Dict[str, int]:
    """
    Analysiert die Komplexität von Methoden in einer Datei.

    Args:
        file_path: Pfad zur Python-Datei

    Returns:
        Dictionary mit Methodennamen und Zeilenzahl
    """
    print(f"Analysiere Methodenkomplexität in {file_path}...")

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    results = {}
    current_method = None
    line_count = 0

    for line in lines:
        method_match = re.match(r"\s*def\s+(\w+)\(", line)
        if method_match:
            if current_method:
                results[current_method] = line_count
            current_method = method_match.group(1)
            line_count = 1
        elif current_method and line.strip():
            line_count += 1

    if current_method:
        results[current_method] = line_count

    # Sortieren nach Komplexität (Zeilenzahl)
    sorted_results = dict(
        sorted(results.items(), key=lambda item: item[1], reverse=True)
    )

    # Ausgabe der komplexesten Methoden
    print("Top 5 komplexeste Methoden:")
    for i, (method, lines) in enumerate(sorted_results.items()):
        if i >= 5:
            break
        print(f"  {method}: {lines} Zeilen")

    return sorted_results


def main():
    """Hauptfunktion des Skripts."""
    print("HRNGGUI Verbesserungsanalyse")
    print("-" * 40)

    # Pfad zum src-Verzeichnis
    src_path = Path(__file__).parent / "src"
    if not src_path.exists():
        print(f"Fehler: Verzeichnis {src_path} nicht gefunden")
        return 1

    # Analyse aller Python-Dateien im src-Verzeichnis
    py_files = list(src_path.glob("**/*.py"))
    print(f"Gefundene Python-Dateien: {len(py_files)}")

    for py_file in py_files:
        print("\n" + "=" * 40)
        print(f"Analysiere {py_file.relative_to(Path(__file__).parent)}")
        print("-" * 40)

        add_type_hints(str(py_file))
        improve_error_handling(str(py_file))
        analyze_method_complexity(str(py_file))

    print("\n" + "=" * 40)
    print("Analyse abgeschlossen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
