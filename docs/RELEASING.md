# Releasing

Releases are cut by GitHub Actions. A release bumps the version in `pyproject.toml`, cuts `CHANGELOG.md`, tags the commit, builds the wheel and the sdist and publishes a GitHub Release with the changelog section and the SHA-256 sums as notes. The lab PCs install the wheel with pip (`pip install gyroscope_ui-<version>-py3-none-any.whl`).

## Workflows

| File                  | Trigger                                                                     | Purpose                                                                                                                                                                       |
| --------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ci.yml`              | push to `main`, `dev`, `feature/**`, `refactor/**`, pull request, manual    | ruff and pytest on Linux (Python 3.11 and 3.14), Windows and macOS, tests of `scripts/release.py`; reused by the release workflows                                            |
| `release-prepare.yml` | **manual** ("Run workflow") or a merged PR labelled `major`/`minor`/`patch` | runs CI on the exact commit, bumps the version, cuts the CHANGELOG, commits `chore: bump version to vX.Y.Z [skip ci]`, tags, calls `release.yml`                              |
| `release.yml`         | called by `release-prepare.yml`; also a pushed `vX.Y.Z` tag                 | verifies the tag (stable releases only: version, changelog, default branch), re-runs CI on it, builds and smoke-tests the wheel, creates the GitHub Release (wheel, sdist, `SHA256SUMS`) |

## One-time repository setup

1. **Default branch = `main`.** `release-prepare.yml` only runs on the default branch and `release.yml` only releases stable tags that are on it (pre-release tags `vX.Y.Z[a|b|rc]N` may be on any branch).
2. **Labels** (for the merge-a-PR trigger): `major`, `minor`, `patch`.
3. **If `main` is protected** (rulesets, required pull requests or status checks), the Actions bot cannot push the version-bump commit. Create a fine-grained personal access token for this repository (Repository permissions → **Contents: Read and write**), store it as the repository secret **`RELEASE_TOKEN`**, and add the token's owner to the ruleset's bypass list. Without branch protection no secret is needed.

## Cutting a release

1. Put the notes you want under `## [Unreleased]` in `CHANGELOG.md`. If it is empty, notes are generated from commit subjects since the last stable tag.
2. **Actions → Release (prepare) → Run workflow** on `main` and choose:

   | Input               | Values                                                                                                                                                      |
   | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | `bump_type`         | `patch` · `minor` · `major` — next version. `keep` — next pre-release of the same `X.Y.Z` (`rc1` → `rc2`). `graduate` — `rc` or `.devN` → final. |
   | `prerelease`        | `none` (stable) · `a` · `b` · `rc`                                                                                                                          |
   | `prerelease_number` | e.g. `1`                                                                                                                                                    |

   Examples: stable minor = `minor / none`; first candidate = `minor / rc / 1`; second candidate = `keep / rc / 2`; ship it = `graduate / none`. **The first release (2.0.0)** starts from `2.0.0.dev0`: use `graduate / none` (or `keep / rc / 1` for a candidate first).

   **Or** merge a PR into `main` that carries a `major`, `minor` or `patch` label (highest wins; `semver:minor`, `release:minor`, `bump:minor` also work). Merged PRs without such a label do not release.

3. The workflow tests, bumps, commits, tags and publishes. Pre-releases are tagged `vX.Y.ZrcN` (PEP 440 spelling, e.g. `v2.0.0rc1`) and marked as pre-release on GitHub.

Never edit the version by hand. `release.yml` rejects a tag whose tree disagrees with `pyproject.toml` or the changelog, and a stable tag that is not on `main`. To release from your own machine instead, run `python3 scripts/release.py bump --type patch`, commit, `git tag -a vX.Y.Z`, push the commit and the tag: `release.yml` takes over from the tag.

## Release assets

| Asset                                  | Content                                                                                           |
| -------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `gyroscope_ui-<version>-py3-none-any.whl` | The application (code, `config.json`, Designer forms). Pure Python, installs on Windows and macOS. |
| `gyroscope_ui-<version>.tar.gz`        | The sdist.                                                                                        |
| `SHA256SUMS`                           | Checksums of both files; the release notes repeat them.                                           |

`release.yml` installs the wheel in a clean venv before publishing and fails unless it imports from there with the tagged version and carries `config.json` and the forms. The firmware (`Arduino-Gyroscope/`) is versioned separately (`SOFTWARE_VERSION`) and is not part of a release.

## What is versioned where

| File           | Notes                                                                                                                              |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `pyproject.toml` | single source of truth (read by `scripts/release.py current`); `gyroscope_ui.__version__` reads the installed package metadata   |
| `CHANGELOG.md` | the `[Unreleased]` section is moved to `## [X.Y.Z] - date` (copied for pre-releases)                                               |

## Rollback / withdrawing a release

Never move or re-use a tag. To go back, install the previous wheel. To withdraw a bad release, delete the GitHub Release in the UI, then release a fixed patch version.
