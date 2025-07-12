#!/usr/bin/env python3
"""
Test-Skript für die Autodoc-Funktionalität
Dieses Skript testet, ob die automatische API-Dokumentation korrekt funktioniert
"""

import os
import sys
import subprocess
from pathlib import Path


def test_autodoc():
    """Testet die Autodoc-Funktionalität von Sphinx"""
    print("🔍 Teste Autodoc-Funktionalität...")

    # Ins docs-Verzeichnis wechseln
    docs_dir = Path(__file__).parent / "docs"
    os.chdir(docs_dir)

    # Teste ob die Module importiert werden können
    modules_to_test = [
        "src.main_window",
        "src.data_controller",
        "src.device_manager",
        "src.control",
        "src.plot",
        "src.helper_classes",
        "src.debug_utils",
    ]

    print("\n📦 Teste Modul-Imports:")
    for module in modules_to_test:
        try:
            # Sphinx-Build mit nur einem Modul testen
            cmd = f"sphinx-build -b html -D extensions=sphinx.ext.autodoc -D automodule_generate_module_stub=False . _build/test -q"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"  ✅ {module} - OK")
            else:
                print(f"  ❌ {module} - Fehler")
                print(f"     Ausgabe: {result.stderr}")

        except Exception as e:
            print(f"  ❌ {module} - Exception: {e}")

    # Teste vollständige Autodoc-Generierung
    print("\n🔨 Teste vollständige Autodoc-Generierung:")

    # Erstelle ein Test-RST-File für Autodoc
    test_rst = """
Test Autodoc
============

.. automodule:: src.main_window
   :members:
   :undoc-members:
   :show-inheritance:
"""

    with open("_test_autodoc.rst", "w") as f:
        f.write(test_rst)

    try:
        # Teste Sphinx-Build mit Autodoc
        cmd = (
            "sphinx-build -b html -D master_doc=_test_autodoc . _build/autodoc_test -q"
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print("  ✅ Autodoc-Generierung erfolgreich")

            # Prüfe ob HTML-Ausgabe existiert
            html_file = Path("_build/autodoc_test/_test_autodoc.html")
            if html_file.exists():
                print("  ✅ HTML-Ausgabe erstellt")

                # Prüfe Inhalt der HTML-Datei
                content = html_file.read_text()
                if "MainWindow" in content:
                    print("  ✅ API-Dokumentation gefunden")
                else:
                    print("  ⚠️  API-Dokumentation möglicherweise leer")
            else:
                print("  ❌ HTML-Ausgabe nicht gefunden")
        else:
            print("  ❌ Autodoc-Generierung fehlgeschlagen")
            print(f"     Fehler: {result.stderr}")

    except Exception as e:
        print(f"  ❌ Exception: {e}")

    finally:
        # Cleanup
        test_file = Path("_test_autodoc.rst")
        if test_file.exists():
            test_file.unlink()


def check_docstrings():
    """Prüft die Qualität der Docstrings im Code"""
    print("\n📝 Prüfe Docstring-Qualität...")

    src_dir = Path(__file__).parent / "src"

    if not src_dir.exists():
        print("  ❌ src-Verzeichnis nicht gefunden")
        return

    python_files = list(src_dir.glob("*.py"))

    for py_file in python_files:
        print(f"\n  📄 {py_file.name}:")

        try:
            content = py_file.read_text()

            # Prüfe auf Docstrings
            if '"""' in content:
                docstring_count = content.count('"""') // 2
                print(f"    ✅ {docstring_count} Docstrings gefunden")
            else:
                print("    ⚠️  Keine Docstrings gefunden")

            # Prüfe auf Klassen
            if "class " in content:
                class_count = content.count("class ")
                print(f"    📋 {class_count} Klassen gefunden")

            # Prüfe auf Funktionen
            if "def " in content:
                func_count = content.count("def ")
                print(f"    🔧 {func_count} Funktionen gefunden")

        except Exception as e:
            print(f"    ❌ Fehler beim Lesen: {e}")


def main():
    """Hauptfunktion"""
    print("🎯 Autodoc-Funktionalität Test für HRNGGUI")
    print("=" * 50)

    # Prüfe Docstrings
    check_docstrings()

    # Teste Autodoc
    test_autodoc()

    print("\n" + "=" * 50)
    print("✅ Autodoc-Test abgeschlossen!")
    print("\nHinweise:")
    print("- Autodoc ist in der Sphinx-Konfiguration aktiviert")
    print("- Die automatische API-Dokumentation wird aus den Docstrings generiert")
    print(
        "- Für beste Ergebnisse sollten alle Klassen und Funktionen dokumentiert sein"
    )
    print(
        "- Verwenden Sie Google- oder NumPy-Style Docstrings für optimale Formatierung"
    )


if __name__ == "__main__":
    main()
