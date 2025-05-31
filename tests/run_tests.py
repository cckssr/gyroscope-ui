#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test-Runner für die HRNGGUI-Anwendung.

Führt alle Unit-Tests im 'tests'-Verzeichnis aus und gibt einen detaillierten Bericht aus.
"""

import unittest
import sys
import os
from pathlib import Path


def run_all_tests():
    """
    Führt alle Tests im 'tests'-Verzeichnis aus.
    """
    # Sicherstellen, dass das Hauptverzeichnis im Python-Pfad ist
    sys.path.insert(0, str(Path(__file__).parent))

    # Alle Tests laden und ausführen
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests", pattern="*_test.py")

    # Textbasiertes Testrunner mit detailliertem Bericht
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Rückgabewert für CI-Systeme: 0 bei Erfolg, 1 bei Fehlschlag
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
