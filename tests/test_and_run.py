#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test- und Start-Skript für die HRNGGUI-Anwendung.

Dieses Skript führt alle Tests aus und startet dann die Anwendung,
wenn die Tests erfolgreich waren.
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse


def run_tests():
    """
    Führt alle Unit- und Integrationstests aus.

    Returns:
        bool: True wenn alle Tests erfolgreich waren, sonst False
    """
    print("Führe Tests aus...")

    # Pfad zum Testrunner
    test_runner = Path(__file__).parent / "run_tests.py"

    # Tests ausführen
    result = subprocess.run(
        [sys.executable, str(test_runner)], capture_output=True, text=True
    )

    # Ausgabe anzeigen
    print(result.stdout)
    if result.stderr:
        print("FEHLER:", result.stderr)

    return result.returncode == 0


def start_application():
    """
    Startet die HRNGGUI-Anwendung.
    """
    print("Starte HRNGGUI-Anwendung...")

    # Pfad zum Startskript
    start_script = Path(__file__).parent / "start_app.py"

    # Anwendung starten
    subprocess.run([sys.executable, str(start_script)])


def main():
    """
    Hauptfunktion: Verarbeitet die Kommandozeilenparameter und führt
    entsprechende Aktionen aus.
    """
    parser = argparse.ArgumentParser(description="HRNGGUI Test- und Start-Skript")
    parser.add_argument(
        "--no-tests", action="store_true", help="Überspringt die Ausführung der Tests"
    )
    parser.add_argument(
        "--tests-only",
        action="store_true",
        help="Führt nur Tests aus, ohne die Anwendung zu starten",
    )

    args = parser.parse_args()

    # Tests ausführen, wenn nicht deaktiviert
    tests_success = True
    if not args.no_tests:
        tests_success = run_tests()

        if not tests_success:
            print("\nWARNUNG: Einige Tests sind fehlgeschlagen!")
            if not args.tests_only:
                response = input("Möchten Sie die Anwendung trotzdem starten? (j/n): ")
                if response.lower() != "j":
                    print("Abbruch.")
                    return 1

    # Anwendung starten, wenn keine Tests-only angefordert wurden
    if not args.tests_only:
        start_application()

    return 0 if tests_success else 1


if __name__ == "__main__":
    sys.exit(main())
