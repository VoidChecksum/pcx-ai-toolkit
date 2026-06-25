#!/usr/bin/env python3
"""Bump versions from Conventional Commits and emit release metadata."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def run(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def current_version() -> tuple[int, int, int]:
    text = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    match = VERSION_RE.match(text)
    if not match:
        raise SystemExit(f"invalid VERSION: {text}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def latest_tag() -> str:
    try:
        return run(["git", "describe", "--tags", "--match", "v[0-9]*", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return ""


def commits_since(tag: str) -> list[str]:
    rev = f"{tag}..HEAD" if tag else "HEAD"
    text = run(["git", "log", "--format=%s%n%b%x00", rev])
    return [chunk.strip() for chunk in text.split("\0") if chunk.strip()]


def bump_kind(commits: list[str]) -> str | None:
    kind: str | None = None
    for msg in commits:
        first = msg.splitlines()[0]
        if first.startswith("chore(release):"):
            continue
        if "BREAKING CHANGE" in msg or re.match(r"^[a-z]+(?:\([^)]*\))?!:", first):
            return "major"
        if first.startswith("feat"):
            kind = "minor" if kind != "major" else kind
        elif first.startswith("fix") and kind is None:
            kind = "patch"
    return kind


def bump(version: tuple[int, int, int], kind: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if kind == "major":
        return major + 1, 0, 0
    if kind == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def set_json_version(path: Path, version: str) -> None:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def set_pyproject_version(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'(?m)^version = "[^"]+"$', f'version = "{version}"', text, count=1)
    path.write_text(text, encoding="utf-8")


def update_changelog(version: str, commits: list[str]) -> None:
    path = ROOT / "CHANGELOG.md"
    old = path.read_text(encoding="utf-8") if path.exists() else "# Changelog\n"
    entries = []
    for msg in commits:
        first = msg.splitlines()[0]
        if first.startswith("chore(release):"):
            continue
        entries.append(f"- {first}")
    section = f"\n## v{version} - {datetime.now(UTC).date()}\n\n" + "\n".join(entries or ["- maintenance release"]) + "\n"
    if old.startswith("# Changelog\n"):
        new = "# Changelog\n" + section + old[len("# Changelog\n"):]
    else:
        new = "# Changelog\n" + section + "\n" + old
    path.write_text(new, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write VERSION/package/pyproject/changelog")
    ap.add_argument("--json", action="store_true", help="print machine-readable result")
    args = ap.parse_args()

    tag = latest_tag()
    commits = commits_since(tag)
    kind = bump_kind(commits)
    if kind is None:
        result = {"released": False, "reason": "no releasable commits", "last_tag": tag}
    else:
        version = ".".join(str(part) for part in bump(current_version(), kind))
        result = {"released": True, "kind": kind, "version": version, "tag": f"v{version}", "last_tag": tag}
        if args.apply:
            (ROOT / "VERSION").write_text(version + "\n", encoding="utf-8")
            set_json_version(ROOT / "package.json", version)
            set_pyproject_version(ROOT / "pyproject.toml", version)
            update_changelog(version, commits)

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
