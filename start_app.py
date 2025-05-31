#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Startskript für die HRNGGUI-Anwendung.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """
    Startet die HRNGGUI-Anwendung.
    """
    # Wurzelverzeichnis des Projekts bestimmen
    project_root = Path(__file__).parent.absolute()

    # Zu verwendende Python-Umgebung finden
    python_cmd = sys.executable

    # Hauptskript pfad
    main_script = os.path.join(project_root, "main.py")

    print(f"Starte HRNGGUI-Anwendung aus {project_root}...")

    # Anwendung starten
    try:
        subprocess.run([python_cmd, main_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Starten der Anwendung: {e}")
        return 1
    except KeyboardInterrupt:
        print("Start der Anwendung abgebrochen.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
