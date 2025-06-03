import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manual_checklist import load_checklist


def test_load_checklist(tmp_path):
    md = """# Test\n- [ ] Item A\n- [ ] Item B\n"""
    p = tmp_path / "test.md"
    p.write_text(md, encoding="utf-8")
    items = load_checklist(str(p))
    assert items == ["Item A", "Item B"]
