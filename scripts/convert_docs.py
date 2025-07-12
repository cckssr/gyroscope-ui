#!/usr/bin/env python3
"""
Konvertiert Markdown-Dateien zu RST für Read the Docs
"""

import os
import re
from pathlib import Path


def convert_md_to_rst(md_content):
    """Konvertiert Markdown zu RST"""
    # Überschriften konvertieren
    rst_content = md_content

    # H1 - Überschrift mit Unterstreichung
    rst_content = re.sub(
        r"^# (.+)$",
        lambda m: f"{m.group(1)}\n{'=' * len(m.group(1))}",
        rst_content,
        flags=re.MULTILINE,
    )

    # H2 - Überschrift mit Unterstreichung
    rst_content = re.sub(
        r"^## (.+)$",
        lambda m: f"{m.group(1)}\n{'-' * len(m.group(1))}",
        rst_content,
        flags=re.MULTILINE,
    )

    # H3 - Überschrift mit Unterstreichung
    rst_content = re.sub(
        r"^### (.+)$",
        lambda m: f"{m.group(1)}\n{'~' * len(m.group(1))}",
        rst_content,
        flags=re.MULTILINE,
    )

    # H4 - Überschrift mit Unterstreichung
    rst_content = re.sub(
        r"^#### (.+)$",
        lambda m: f"{m.group(1)}\n{'^' * len(m.group(1))}",
        rst_content,
        flags=re.MULTILINE,
    )

    # Code-Blöcke konvertieren
    rst_content = re.sub(
        r"```(\w*)\n(.*?)\n```",
        r".. code-block:: \1\n\n\2\n",
        rst_content,
        flags=re.DOTALL,
    )

    # Inline-Code konvertieren
    rst_content = re.sub(r"`([^`]+)`", r"``\1``", rst_content)

    # Bold text konvertieren
    rst_content = re.sub(r"\*\*([^\*]+)\*\*", r"**\1**", rst_content)

    # Listen konvertieren
    rst_content = re.sub(r"^- (.+)$", r"* \1", rst_content, flags=re.MULTILINE)

    # Links konvertieren [text](url) -> `text <url>`_
    rst_content = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"`\1 <\2>`_", rst_content)

    # Tabellen - einfache Konvertierung (Markdown-Tabellen bleiben als Code-Block)
    table_pattern = r"(\|[^\n]+\|\n(\|[^\n]+\|\n)*)"
    tables = re.findall(table_pattern, rst_content)
    for table in tables:
        rst_content = rst_content.replace(
            table[0],
            f"\n.. csv-table::\n   :header-rows: 1\n   :widths: auto\n\n{table[0]}\n",
        )

    return rst_content


def convert_files():
    """Konvertiert alle relevanten Markdown-Dateien"""
    docs_path = Path("docs")

    # Liste der zu konvertierenden Dateien
    md_files = [
        "faq.md",
        "troubleshooting.md",
        "CHANGELOG.md",
        "ROADMAP.md",
        "installation.md",
        "quickstart.md",
        "configuration.md",
        "user-interface.md",
        "device-connection.md",
        "data-acquisition.md",
        "data-analysis.md",
        "export-save.md",
        "architecture.md",
        "code-structure.md",
        "license.md",
        "hardware/gm-counter-protocol.md",
        "hardware/arduino-integration.md",
        "hardware/radioactive-samples.md",
        "development/setup.md",
        "development/testing.md",
    ]

    converted_files = []

    for md_file in md_files:
        md_path = docs_path / md_file
        rst_path = docs_path / md_file.replace(".md", ".rst")

        if md_path.exists():
            print(f"📝 Konvertiere {md_file}...")

            # Lese Markdown-Datei
            content = md_path.read_text(encoding="utf-8")

            # Konvertiere zu RST
            rst_content = convert_md_to_rst(content)

            # Schreibe RST-Datei
            rst_path.parent.mkdir(parents=True, exist_ok=True)
            rst_path.write_text(rst_content, encoding="utf-8")

            converted_files.append((md_file, md_file.replace(".md", ".rst")))
            print(f"   ✅ {rst_path}")
        else:
            print(f"   ⚠️  {md_file} nicht gefunden")

    print(f"\n🎉 {len(converted_files)} Dateien konvertiert!")

    return converted_files


def update_sphinx_config():
    """Aktualisiert die Sphinx-Konfiguration"""
    print("\n🔧 Aktualisiere Sphinx-Konfiguration...")

    conf_path = Path("docs/conf.py")
    content = conf_path.read_text(encoding="utf-8")

    # Stelle sicher, dass RST als Standard verwendet wird
    if 'source_suffix = ".rst"' not in content:
        content = content.replace(
            'source_suffix = ".rst"', 'source_suffix = {".rst": None}'
        )

    conf_path.write_text(content, encoding="utf-8")
    print("   ✅ conf.py aktualisiert")


def clean_duplicate_files():
    """Entfernt überflüssige Dateien"""
    print("\n🧹 Bereinige überflüssige Dateien...")

    files_to_remove = [
        "docs/SUMMARY.md",  # Wird durch index.rst ersetzt
        "docs/README.md",  # Redundant zu index.rst
        "docs/notes.md",  # Entwicklungsnotizen
        "docs/api/README.md",  # Wird durch api.rst ersetzt
        "docs/theme/",  # Nicht mehr benötigt für RTD
        "docs/_static/",  # Wird von Sphinx generiert
        "docs/modules/",  # Wird von Sphinx generiert
    ]

    for file_path in files_to_remove:
        path = Path(file_path)
        if path.exists():
            if path.is_dir():
                import shutil

                shutil.rmtree(path)
                print(f"   🗑️  Verzeichnis entfernt: {file_path}")
            else:
                path.unlink()
                print(f"   🗑️  Datei entfernt: {file_path}")


def main():
    """Hauptfunktion"""
    print("🎯 Konvertierung für Read the Docs")
    print("=" * 50)

    os.chdir(Path(__file__).parent)

    # Konvertiere Markdown zu RST
    converted_files = convert_files()

    # Aktualisiere Sphinx-Konfiguration
    update_sphinx_config()

    # Bereinige überflüssige Dateien
    clean_duplicate_files()

    print("\n" + "=" * 50)
    print("✅ Konvertierung abgeschlossen!")
    print("\nKonvertierte Dateien:")
    for md_file, rst_file in converted_files:
        print(f"  📄 {md_file} → {rst_file}")

    print("\n📋 Nächste Schritte:")
    print("1. Bauen Sie die Dokumentation: python setup_readthedocs.py build")
    print("2. Prüfen Sie die Ausgabe: open docs/_build/html/index.html")
    print("3. Committen Sie die Änderungen für Read the Docs")


if __name__ == "__main__":
    main()
