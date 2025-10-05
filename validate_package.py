#!/usr/bin/env python3
"""
Test-Skript zur Validierung der Paket-Konfiguration.
Führt verschiedene Checks durch, bevor das Paket gebaut wird.
"""

import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Führt einen Befehl aus und gibt das Ergebnis zurück."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"⚠️  Warnings/Errors:\n{result.stderr}")
    return result.returncode == 0


def check_file_exists(filepath, description):
    """Prüft, ob eine Datei existiert."""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def main():
    """Hauptfunktion für Paket-Validierung."""
    print("\n" + "=" * 60)
    print("📦 Gyroscope-UI Paket-Validierung")
    print("=" * 60)

    all_ok = True

    # 1. Check wichtige Dateien
    print("\n1️⃣  Prüfe wichtige Dateien...")
    files_to_check = [
        ("pyproject.toml", "Haupt-Konfiguration"),
        ("MANIFEST.in", "Package-Manifest"),
        ("README.md", "README"),
        ("LICENSE", "Lizenz"),
        ("setup.py", "Setup-Skript"),
        ("src/__init__.py", "Source __init__"),
        ("config.json", "Konfiguration"),
    ]

    for filepath, desc in files_to_check:
        if not check_file_exists(filepath, desc):
            all_ok = False

    # 2. Check GitHub Actions
    print("\n2️⃣  Prüfe GitHub Actions...")
    actions_files = [
        (".github/workflows/release.yml", "Release Workflow"),
        (".github/workflows/test-build.yml", "Test Build Workflow"),
    ]

    for filepath, desc in actions_files:
        if not check_file_exists(filepath, desc):
            all_ok = False

    # 3. Installiere Build-Tools
    print("\n3️⃣  Installiere Build-Tools...")
    if not run_command("pip install --upgrade build twine", "Build-Tools installieren"):
        all_ok = False

    # 4. Baue das Paket
    print("\n4️⃣  Baue das Paket...")
    if not run_command("python -m build", "Paket bauen"):
        all_ok = False
        print("❌ Build fehlgeschlagen!")
    else:
        print("✅ Build erfolgreich!")

    # 5. Prüfe das Paket
    print("\n5️⃣  Prüfe das gebaute Paket...")
    if not run_command("twine check dist/*", "Paket mit twine prüfen"):
        all_ok = False
        print("❌ Twine-Check fehlgeschlagen!")
    else:
        print("✅ Twine-Check erfolgreich!")

    # 6. Liste Build-Artefakte
    print("\n6️⃣  Build-Artefakte:")
    if Path("dist").exists():
        for file in Path("dist").iterdir():
            size = file.stat().st_size / 1024  # KB
            print(f"  📄 {file.name} ({size:.1f} KB)")

    # 7. Zeige Paket-Info
    print("\n7️⃣  Paket-Informationen:")
    run_command(
        "python -c \"import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project'])\" 2>/dev/null || "
        "python -c \"import toml; print(toml.load('pyproject.toml')['project'])\" 2>/dev/null || "
        "grep -A 20 '\\[project\\]' pyproject.toml",
        "Projekt-Metadaten",
    )

    # Zusammenfassung
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ Alle Checks erfolgreich!")
        print("\n📝 Nächste Schritte:")
        print("   1. git add .")
        print("   2. git commit -m 'Configure package distribution'")
        print("   3. git push origin main")
        print("\n   Die GitHub Action wird automatisch einen Release erstellen.")
        return 0
    else:
        print("❌ Einige Checks sind fehlgeschlagen!")
        print("   Bitte beheben Sie die Fehler vor dem Release.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
