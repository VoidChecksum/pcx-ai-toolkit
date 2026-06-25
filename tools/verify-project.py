#!/usr/bin/env python3
"""Project-wide verifier for Perception Enma/AngelScript projects.

Runs the same checks agents should run before handing code to PCX:
  * Enma linter for .em files
  * AngelScript linter for .as files
  * source-backed symbol-check across the whole project
  * optional placeholder / UNVERIFIED hygiene gate
  * evidence-log-validator when an evidence/ directory exists
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


TOOL_DIR = Path(__file__).resolve().parent


def collect_scripts(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in {".em", ".as"} else []
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in {".em", ".as"})


def run_tool(args: list[str]) -> dict[str, Any]:
    res = subprocess.run(args, capture_output=True, text=True)
    return {
        "command": args,
        "returncode": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "ok": res.returncode == 0,
    }


def scan_hygiene(root: Path, allow_placeholders: bool, allow_unverified: bool) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    patterns: list[tuple[str, re.Pattern[str], str]] = []
    if not allow_placeholders:
        patterns.append(("placeholder", re.compile(r"\b(?:placeholder|TODO|FIXME|HACK|XXX)\b", re.I), "replace placeholder/TODO text before shipping"))
    if not allow_unverified:
        patterns.append(("unverified", re.compile(r"\bUNVERIFIED\b", re.I), "replace or cite UNVERIFIED offsets/signatures before shipping"))
    if not patterns:
        return findings

    for path in collect_scripts(root):
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for kind, pat, fix in patterns:
                if pat.search(line):
                    findings.append({
                        "file": str(path),
                        "line": lineno,
                        "kind": kind,
                        "message": line.strip()[:180],
                        "fix": fix,
                    })
    return findings


def verify_project(root: Path, allow_placeholders: bool, allow_unverified: bool) -> dict[str, Any]:
    target = root.resolve()
    scripts = collect_scripts(target)
    if not scripts:
        return {"ok": False, "error": f"no .em or .as files found at {target}", "steps": []}

    steps: list[dict[str, Any]] = []
    has_em = any(p.suffix.lower() == ".em" for p in scripts)
    has_as = any(p.suffix.lower() == ".as" for p in scripts)

    if has_em:
        steps.append(run_tool([sys.executable, str(TOOL_DIR / "script-linter.py"), "--strict", str(target)]))
    if has_as:
        steps.append(run_tool([sys.executable, str(TOOL_DIR / "as-linter.py"), "--strict", str(target)]))

    steps.append(run_tool([sys.executable, str(TOOL_DIR / "symbol-check.py"), str(target)]))

    evidence_dir = target / "evidence" if target.is_dir() else target.parent / "evidence"
    evidence_files = [p for p in evidence_dir.glob("*.md") if p.name.lower() != "readme.md"] if evidence_dir.is_dir() else []
    if evidence_files and not allow_unverified:
        offset_files = [p for p in scripts if p.name.lower().startswith(("offset", "offsets"))]
        for offset_file in offset_files:
            steps.append(run_tool([
                sys.executable,
                str(REPO_ROOT / "tools" / "evidence-log-validator.py"),
                "--strict",
                "--evidence-dir",
                str(evidence_dir),
                str(offset_file),
            ]))

    hygiene = scan_hygiene(target, allow_placeholders, allow_unverified)
    ok = all(step["ok"] for step in steps) and not hygiene
    return {
        "ok": ok,
        "root": str(target),
        "scripts": [str(p) for p in scripts],
        "steps": steps,
        "hygiene_findings": hygiene,
        "summary": {
            "scripts": len(scripts),
            "tool_failures": sum(1 for step in steps if not step["ok"]),
            "hygiene_findings": len(hygiene),
        },
    }


def print_human(result: dict[str, Any]) -> None:
    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        return
    print(f"Verifying project: {result['root']}")
    for step in result["steps"]:
        label = " ".join(step["command"][-2:]) if len(step["command"]) > 2 else " ".join(step["command"])
        status = "OK" if step["ok"] else "FAIL"
        print(f"[{status}] {label}")
        if step["stdout"].strip():
            print(step["stdout"].rstrip())
        if step["stderr"].strip():
            print(step["stderr"].rstrip(), file=sys.stderr)
    if result["hygiene_findings"]:
        print("Hygiene findings:")
        for finding in result["hygiene_findings"]:
            print(f"  {finding['file']}:{finding['line']}: {finding['kind']}: {finding['message']}")
            print(f"      fix: {finding['fix']}")
    print("clean: project verified" if result["ok"] else "project verification failed")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", help="project directory or script file")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--allow-placeholders", action="store_true", help="do not fail on placeholder/TODO text")
    ap.add_argument("--allow-unverified", action="store_true", help="do not fail on UNVERIFIED markers")
    args = ap.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"ERROR: not found: {target}", file=sys.stderr)
        return 2

    result = verify_project(target, args.allow_placeholders, args.allow_unverified)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)
    if "error" in result:
        return 2
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
