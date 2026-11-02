"""Tests for scripts/release.py - run with: python -m unittest discover -s scripts"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release  # noqa: E402

PATHS = ("ROOT", "PYPROJECT", "CHANGELOG")
CHANGELOG = (
    "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- thing\n\n## [1.0.0] - 2026-01-01\n\nold\n"
)


class VersionMath(unittest.TestCase):
    def test_bumps(self):
        nv = release.next_version
        self.assertEqual(nv("2.0.0", "patch"), "2.0.1")
        self.assertEqual(nv("2.0.3", "minor"), "2.1.0")
        self.assertEqual(nv("2.1.3", "major"), "3.0.0")

    def test_prerelease_flow(self):
        nv = release.next_version
        self.assertEqual(nv("2.0.0", "minor", "rc", 1), "2.1.0rc1")
        self.assertEqual(nv("2.1.0rc1", "keep", "rc", 2), "2.1.0rc2")
        self.assertEqual(nv("2.1.0rc2", "graduate"), "2.1.0")

    def test_dev_version_graduates_to_the_first_release(self):
        self.assertEqual(release.parse_version("2.0.0.dev0"), (2, 0, 0, "dev", 0))
        self.assertEqual(release.next_version("2.0.0.dev0", "graduate"), "2.0.0")
        self.assertEqual(release.next_version("2.0.0.dev0", "keep", "rc", 1), "2.0.0rc1")

    def test_invalid_combinations(self):
        for args in (("2.0.0", "graduate"), ("2.0.0", "keep"), ("2.0.0rc1", "graduate", "rc")):
            with self.assertRaises(SystemExit):
                release.next_version(*args)
        for bad in ("2.0", "v2.0.0", "2.0.0-rc.1"):
            with self.assertRaises(SystemExit):
                release.parse_version(bad)


class RepoFixture(unittest.TestCase):
    """Runs bump/check against a throw-away pyproject.toml and CHANGELOG.md."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        shutil.copy(release.ROOT / "pyproject.toml", self.tmp / "pyproject.toml")
        (self.tmp / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
        original = {name: getattr(release, name) for name in PATHS}
        self.addCleanup(lambda: [setattr(release, k, v) for k, v in original.items()])
        release.ROOT = self.tmp
        release.PYPROJECT = self.tmp / "pyproject.toml"
        release.CHANGELOG = self.tmp / "CHANGELOG.md"
        release.write_version("1.0.0")

    def bump(self, *args: str) -> str:
        ns = release.argparse.Namespace(
            type=args[0],
            prerelease=args[1] if len(args) > 1 else "none",
            number=1,
            date="2026-02-03",
        )
        release.cmd_bump(ns)
        return release.read_version()

    def test_stable_bump_moves_unreleased(self):
        self.assertEqual(self.bump("minor"), "1.1.0")
        text = release.CHANGELOG.read_text(encoding="utf-8")
        self.assertIn("## [Unreleased]\n\n## [1.1.0] - 2026-02-03\n\n### Added\n\n- thing", text)
        self.assertIn("## [1.0.0] - 2026-01-01", text)

    def test_prerelease_bump_copies_unreleased(self):
        self.assertEqual(self.bump("minor", "rc"), "1.1.0rc1")
        text = release.CHANGELOG.read_text(encoding="utf-8")
        self.assertEqual(text.count("- thing"), 2)  # still under Unreleased for the final release

    def test_only_the_version_line_changes(self):
        before = (release.ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.bump("patch")
        after = (release.ROOT / "pyproject.toml").read_text(encoding="utf-8")
        lines = zip(before.splitlines(), after.splitlines(), strict=True)
        diff = [(a, b) for a, b in lines if a != b]
        self.assertEqual(diff, [('version = "1.0.0"', 'version = "1.0.1"')])

    def test_check(self):
        self.bump("patch")
        release.cmd_check(release.argparse.Namespace(tag="v1.0.1"))
        for tag in ("v1.0.2", "1.0.1", "v1.0"):
            with self.assertRaises(SystemExit):
                release.cmd_check(release.argparse.Namespace(tag=tag))

    def test_check_needs_a_changelog_section(self):
        release.write_version("1.0.5")
        with self.assertRaises(SystemExit):
            release.cmd_check(release.argparse.Namespace(tag="v1.0.5"))

    def test_notes_contain_changelog_sums_and_install_hint(self):
        self.bump("patch")
        dist = self.tmp / "dist"
        dist.mkdir()
        (dist / "SHA256SUMS").write_text(
            "aa  gyroscope_ui-1.0.1-py3-none-any.whl\nbb  gyroscope_ui-1.0.1.tar.gz\n",
            encoding="utf-8",
        )
        text = release.release_notes("1.0.1", "v1.0.1", dist)
        self.assertIn("- thing", text)
        self.assertIn("pip install gyroscope_ui-1.0.1-py3-none-any.whl", text)
        self.assertIn("| `gyroscope_ui-1.0.1.tar.gz` | `bb` |", text)
        self.assertNotIn("Pre-release", text)

    def test_notes_mark_prereleases(self):
        self.bump("minor", "rc")
        self.assertIn("Pre-release", release.release_notes("1.1.0rc1", "v1.1.0rc1"))


class Changelog(unittest.TestCase):
    def test_sections(self):
        text = CHANGELOG
        names = [n for n, _s, _e in release._sections(text)]
        self.assertEqual(names, ["Unreleased", "1.0.0"])


if __name__ == "__main__":
    unittest.main()
