import json
from pathlib import Path
from typing import List


def load_checklist(file_path: str) -> List[str]:
    """Parse checklist items from a markdown file."""
    path = Path(file_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    items = []
    for line in lines:
        line = line.strip()
        if line.startswith("- [ ]"):
            items.append(line[5:].strip())
    return items


def run_checklist(items: List[str]) -> List[dict]:
    """Interactively ask the user to verify each checklist item."""
    results = []
    for item in items:
        answer = input(f"{item}? (y/n): ").strip().lower()
        results.append({"item": item, "ok": answer in {"y", "yes"}})
    return results


def save_results(results: List[dict], output_file: str) -> None:
    Path(output_file).write_text(json.dumps(results, indent=2), encoding="utf-8")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Manuelle GUI-Checkliste")
    parser.add_argument(
        "--file", default="tests/testplan.md", help="Pfad zur Checklisten-Datei"
    )
    parser.add_argument(
        "--output", default="checklist_results.json", help="Ausgabedatei"
    )
    args = parser.parse_args()

    items = load_checklist(args.file)
    results = run_checklist(items)
    save_results(results, args.output)
    print(f"Ergebnisse gespeichert in {args.output}")


if __name__ == "__main__":
    main()
