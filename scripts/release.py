#!/usr/bin/env python3
"""Release tooling for the GitHub Actions workflows (stdlib only, no third-party deps).

Subcommands
-----------
current   print the current version (single source of truth: pyproject.toml)
bump      compute the next version, rewrite pyproject.toml + CHANGELOG.md,
          print the new version on stdout (everything else goes to stderr)
check     verify that a tag matches pyproject.toml and the changelog
notes     write the GitHub Release body (changelog section, SHA-256 sums, compare link)

Version scheme: SemVer ``X.Y.Z`` with an optional PEP 440 pre-release suffix (``a`` / ``b`` /
``rc`` + number, e.g. ``2.0.0rc1``). A ``.devN`` version (``2.0.0.dev0``, the state of the
branch before its first release) counts as a pre-release of its ``X.Y.Z`` and can be
graduated to ``2.0.0``.

The version lives in ``pyproject.toml`` only; ``gyroscope_ui.__version__`` reads the installed
package metadata. The firmware (``Arduino-Gyroscope``) has its own version and is not touched.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"

PROJECT_TITLE = "Gyroscope-UI"

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+)|\.(dev)(\d+))?$")
STABLE_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+((a|b|rc)\d+|\.dev\d+)?$")


# ── Version arithmetic ────────────────────────────────────────────────────────
def parse_version(text: str) -> tuple[int, int, int, str | None, int | None]:
    """``(major, minor, patch, pre, number)``; ``pre`` is ``a``, ``b``, ``rc``, ``dev`` or None."""
    m = VERSION_RE.match(text)
    if not m:
        raise SystemExit(f"error: {text!r} is not X.Y.Z[a|b|rc N | .devN]")
    major, minor, patch, pre, num, dev, dev_num = m.groups()
    pre, num = (pre, num) if pre else (dev, dev_num)
    return int(major), int(minor), int(patch), pre, int(num) if num else (0 if pre else None)


def next_version(current: str, bump: str, prerelease: str = "none", number: int = 1) -> str:
    major, minor, patch, cur_pre, _ = parse_version(current)
    if bump == "graduate":
        if not cur_pre:
            raise SystemExit(f"error: {current} is not a pre-release; nothing to graduate")
        if prerelease != "none":
            raise SystemExit("error: 'graduate' cannot be combined with a pre-release suffix")
    elif bump == "keep":
        if prerelease == "none":
            raise SystemExit("error: 'keep' needs a pre-release kind (e.g. rc1 -> rc2)")
    elif bump == "major":
        major, minor, patch = major + 1, 0, 0
    elif bump == "minor":
        minor, patch = minor + 1, 0
    elif bump == "patch":
        patch += 1
    else:
        raise SystemExit(f"error: unknown bump type {bump!r}")
    new = f"{major}.{minor}.{patch}"
    return f"{new}{prerelease}{number}" if prerelease != "none" else new


# ── Version file ──────────────────────────────────────────────────────────────
_VERSION_LINE = re.compile(r'^version\s*=\s*"([^"]*)"', re.MULTILINE)


def read_version() -> str:
    m = _VERSION_LINE.search(PYPROJECT.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"error: no version in {PYPROJECT}")
    return m.group(1)


def write_version(version: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    updated, n = _VERSION_LINE.subn(f'version = "{version}"', text, count=1)
    if n != 1:
        raise SystemExit(f"error: could not update version in {PYPROJECT}")
    PYPROJECT.write_text(updated, encoding="utf-8")


def version_problems(version: str) -> list[str]:
    """Mismatches between ``version`` and the version file and the changelog."""
    problems = []
    if read_version() != version:
        problems.append(f"pyproject.toml has {read_version()}, expected {version}")
    if changelog_section(version) is None:
        problems.append(f"CHANGELOG.md has no '## [{version}]' section")
    return problems


# ── Changelog ─────────────────────────────────────────────────────────────────
_HEADING = re.compile(r"^## \[(?P<name>[^\]]+)\].*$", re.MULTILINE)


def _sections(text: str) -> list[tuple[str, int, int]]:
    """(name, start-of-body, end-of-body) for every '## [name]' section."""
    heads = list(_HEADING.finditer(text))
    return [
        (
            h.group("name"),
            h.end(),
            heads[i + 1].start() if i + 1 < len(heads) else len(text),
        )
        for i, h in enumerate(heads)
    ]


def changelog_section(version: str) -> str | None:
    text = CHANGELOG.read_text(encoding="utf-8")
    for name, start, end in _sections(text):
        if name == version:
            return text[start:end].strip()
    return None


def git(*args: str, check: bool = True) -> str:
    res = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise SystemExit(f"error: git {' '.join(args)}: {res.stderr.strip()}")
    return res.stdout.strip()


def last_stable_tag() -> str | None:
    tags = [
        t
        for t in git("tag", "--list", "v*", "--sort=-v:refname").splitlines()
        if STABLE_TAG_RE.match(t)
    ]
    return tags[0] if tags else None


def commits_since_last_release() -> str:
    """Bullet list of commit subjects since the last stable tag (changelog fallback)."""
    tag = last_stable_tag()
    rng = f"{tag}..HEAD" if tag else "HEAD"
    subjects = git("log", "--no-merges", "--format=%s", rng).splitlines()
    subjects = [s for s in subjects if s and not s.startswith("chore: bump version")]
    return "\n".join(f"- {s}" for s in subjects)


def update_changelog(version: str, date: str) -> None:
    """Cut a release section out of '## [Unreleased]'.

    Stable releases move the Unreleased notes; pre-releases copy them, so the final release
    still carries everything. If Unreleased is empty, the notes are generated from commit
    subjects since the last stable tag.
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    unreleased = next(((s, e) for n, s, e in _sections(text) if n.lower() == "unreleased"), None)
    if unreleased is None:
        raise SystemExit("error: CHANGELOG.md has no '## [Unreleased]' section")
    start, end = unreleased
    body = text[start:end].strip()
    if not body:
        body = "### Changes\n\n" + (commits_since_last_release() or "- No notable changes.")
        print("note: [Unreleased] was empty; generated notes from commit subjects", file=sys.stderr)
    is_pre = parse_version(version)[3] is not None
    kept = f"\n\n{body}\n\n" if is_pre else "\n\n"
    new_section = f"## [{version}] - {date}\n\n{body}\n\n"
    CHANGELOG.write_text(
        text[:start] + kept + new_section + text[end:].lstrip("\n"), encoding="utf-8"
    )


# ── Subcommands ───────────────────────────────────────────────────────────────
def cmd_current(_: argparse.Namespace) -> None:
    print(read_version())


def cmd_bump(args: argparse.Namespace) -> None:
    current = read_version()
    new = next_version(current, args.type, args.prerelease, args.number)
    print(f"{current} -> {new}", file=sys.stderr)
    write_version(new)
    update_changelog(new, args.date or dt.datetime.now(dt.UTC).strftime("%Y-%m-%d"))
    problems = version_problems(new)
    if problems:
        raise SystemExit("error: inconsistent after bump:\n  " + "\n  ".join(problems))
    print(new)


def cmd_check(args: argparse.Namespace) -> None:
    tag = args.tag
    if not TAG_RE.match(tag):
        raise SystemExit(f"error: tag {tag!r} is not vX.Y.Z[a|b|rc N]")
    problems = version_problems(tag[1:])
    if problems:
        raise SystemExit(
            f"error: tag {tag} does not match the tagged tree:\n  " + "\n  ".join(problems)
        )
    print(f"ok: {tag} matches pyproject.toml and CHANGELOG.md")


def _sums(dist: Path) -> list[tuple[str, str]]:
    """(file name, sha256) pairs of ``dist/SHA256SUMS``."""
    rows = []
    for line in (dist / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            rows.append((name.strip().lstrip("*"), digest))
    return rows


def release_notes(version: str, tag: str, dist: Path | None = None) -> str:
    """Markdown body of the GitHub Release: changelog, install hint, SHA-256 sums, compare link.

    With ``dist`` (a directory holding ``SHA256SUMS``) the notes list every artifact with its
    checksum.
    """
    is_pre = parse_version(version)[3] is not None
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    prev = git("describe", "--tags", "--abbrev=0", "--match", "v*", f"{tag}^", check=False)
    parts = [f"## {PROJECT_TITLE} v{version}"]
    if is_pre:
        parts.append("> **Pre-release** — not for use in the lab course.")
    parts.append(changelog_section(version) or "_No changelog entry._")
    if dist is not None:
        sums = _sums(dist)
        wheel = next((n for n, _ in sums if n.endswith(".whl")), None)
        if wheel:
            parts += ["### Install", f"```bash\npip install {wheel}\n```"]
        rows = "\n".join(f"| `{name}` | `{digest}` |" for name, digest in sums)
        parts += ["### Artifacts", f"| File | SHA-256 |\n|---|---|\n{rows}"]
    if prev and repo:
        parts.append(f"**Full diff:** [{prev}...{tag}]({server}/{repo}/compare/{prev}...{tag})")
    return "\n\n".join(parts) + "\n"


def cmd_notes(args: argparse.Namespace) -> None:
    tag = args.tag
    parse_version(tag.removeprefix("v"))
    dist = Path(args.dist) if args.dist else None
    text = release_notes(tag.removeprefix("v"), tag, dist)
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"wrote {args.out}", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("current").set_defaults(fn=cmd_current)

    b = sub.add_parser("bump")
    b.add_argument("--type", required=True, choices=["major", "minor", "patch", "keep", "graduate"])
    b.add_argument("--prerelease", default="none", choices=["none", "a", "b", "rc"])
    b.add_argument("--number", type=int, default=1)
    b.add_argument("--date", help="YYYY-MM-DD (default: today, UTC)")
    b.set_defaults(fn=cmd_bump)

    c = sub.add_parser("check")
    c.add_argument("--tag", required=True)
    c.set_defaults(fn=cmd_check)

    n = sub.add_parser("notes")
    n.add_argument("--tag", required=True)
    n.add_argument("--dist", help="directory containing SHA256SUMS (adds the sums)")
    n.add_argument("--out", required=True)
    n.set_defaults(fn=cmd_notes)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
