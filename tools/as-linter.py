#!/usr/bin/env python3
"""Static lint for Perception AngelScript (.as) scripts.

This is deliberately shallow and PCX-focused.  It catches high-confidence
mistakes that LLMs commonly make when mixing Enma and AngelScript:

  AS-1  ERROR  Enma-only imports/lifecycle/logging in .as code
  AS-2  ERROR  non-uint64 address storage
  AS-3  WARN   OFF_/SIG_ constants without evidence or UNVERIFIED marker
  AS-4  INFO   proc_t@ handle usage without an on_unload cleanup function

Exit: 0 clean, 1 errors (or warnings under --strict), 2 bad usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


RULES = {
    "AS-1": ("ERROR", "wrong language construct"),
    "AS-2": ("ERROR", "uint64 addresses"),
    "AS-3": ("WARN", "offsets cite source"),
    "AS-4": ("INFO", "handle cleanup"),
}

BAD_ADDR_TYPES = {
    "int", "int8", "int16", "int32", "int64",
    "uint", "uint8", "uint16", "uint32",
}
DECL_RE = re.compile(r"^\s*(?:const\s+)?([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*=\s*(.+?);\s*$")
CONST_HEX_RE = re.compile(r"^\s*const\s+([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*=\s*(0x[0-9A-Fa-f]+)\s*;")
ADDR_CALL_RE = re.compile(r"\.ru64\s*\(|\bfind_code_pattern\s*\(|\bbase_address\s*\(|\bref_process\s*\(")
OFFSET_DECL_RE = re.compile(r"^\s*const\s+(?:\w+\s+(OFF(?:SET)?_\w+)|string\s+(SIG_\w+))\b")
CITE_RE = re.compile(r"\bE-\d+\b", re.I)
UNVERIFIED_RE = re.compile(r"\bUNVERIFIED\b", re.I)
WRONG_LANGUAGE_PATTERNS = (
    (re.compile(r'^\s*import\s+"[^"]+"\s*;', re.M), 'Enma module import; AngelScript projects use host/bundler includes, not `import "module";`'),
    (re.compile(r"\bint64\s+main\s*\("), "Enma entrypoint; AngelScript uses `int main()`"),
    (re.compile(r"\bregister_routine\s*\("), "Enma routine registration; AngelScript uses `register_callback(...)`"),
    (re.compile(r"\bprintln\s*\("), "Enma logging; AngelScript uses `log(...)`"),
    (re.compile(r"\bvec[234]\s*\("), "Enma vector constructors; use PCX AngelScript vector types/shapes from the AS docs"),
    (re.compile(r"\bcolor\s*\("), "Enma color constructor; AngelScript render APIs use documented raw RGBA parameters"),
)


def strip_comment(line: str) -> str:
    out: list[str] = []
    i = 0
    in_str = False
    while i < len(line):
        c = line[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif c == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        else:
            out.append(c)
        i += 1
    return "".join(out)


def strip_strings(code: str) -> str:
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', code)


def collect_as_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(path.rglob("*.as"))
    if path.is_file() and path.suffix.lower() == ".as":
        return [path]
    return []


def lint_file(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    code = [strip_comment(line) for line in raw]
    nostr = [strip_strings(line) for line in code]
    text = "\n".join(nostr)
    findings: list[dict[str, Any]] = []

    for pat, message in WRONG_LANGUAGE_PATTERNS:
        for m in pat.finditer(text):
            line = text[: m.start()].count("\n") + 1
            findings.append({
                "line": line,
                "rule": "AS-1",
                "severity": "ERROR",
                "message": message,
                "fix": "use the AngelScript lifecycle/API shape from docs/perception/angelscript/",
            })

    for i, line in enumerate(nostr):
        d = DECL_RE.match(line)
        if d and d.group(1) in BAD_ADDR_TYPES and ADDR_CALL_RE.search(d.group(3)):
            findings.append({
                "line": i + 1,
                "rule": "AS-2",
                "severity": "ERROR",
                "message": f"'{d.group(2)}' holds an address but is typed {d.group(1)}",
                "fix": f"declare it `uint64 {d.group(2)}`",
            })
            continue
        h = CONST_HEX_RE.match(line)
        if h and h.group(1) != "uint64" and int(h.group(3), 16) > 0xFFFFFFFF:
            findings.append({
                "line": i + 1,
                "rule": "AS-2",
                "severity": "ERROR",
                "message": f"64-bit address constant '{h.group(2)}' typed {h.group(1)}",
                "fix": f"declare it `const uint64 {h.group(2)}`",
            })

        off = OFFSET_DECL_RE.match(line)
        if off:
            name = off.group(1) or off.group(2)
            scope = " ".join(raw[max(0, i - 6): i + 1])
            if not CITE_RE.search(scope) and not UNVERIFIED_RE.search(scope):
                findings.append({
                    "line": i + 1,
                    "rule": "AS-3",
                    "severity": "WARN",
                    "message": f"'{name}' has no evidence citation",
                    "fix": "add // E-NNN on this or the line above, or // UNVERIFIED",
                })

    if ("proc_t@" in text or "ref_process(" in text) and "void on_unload(" not in text:
        findings.append({
            "line": 1,
            "rule": "AS-4",
            "severity": "INFO",
            "message": "proc_t@ handle usage has no on_unload() cleanup function in this file",
            "fix": "add on_unload() with unregister_callback(...) and g_proc.deref() in the final bundled script",
        })

    findings.sort(key=lambda f: (int(f["line"]), str(f["rule"])))
    return findings


def summarize(results: list[tuple[str, list[dict[str, Any]]]]) -> dict[str, int]:
    summary = {"error": 0, "warn": 0, "info": 0, "files": 0, "findings": 0}
    for _path, findings in results:
        if findings:
            summary["files"] += 1
        for finding in findings:
            summary[str(finding["severity"]).lower()] += 1
            summary["findings"] += 1
    return summary


def print_text(results: list[tuple[str, list[dict[str, Any]]]]) -> None:
    shown = False
    for path, findings in results:
        for finding in findings:
            shown = True
            line = (
                f"{path}:{finding['line']}: {finding['severity']} "
                f"{finding['rule']}: {finding['message']}"
            )
            if finding.get("fix"):
                line += f"  (--> {finding['fix']})"
            print(line)
    if not shown:
        print("clean: no AngelScript findings")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", help=".as file or directory to scan")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="exit 1 on WARN, not just ERROR")
    ap.add_argument("--severity", default="", help="comma list: error,warn,info (default: all)")
    args = ap.parse_args()

    files = collect_as_files(Path(args.path))
    if not files:
        print(f"error: no .as files at {args.path}", file=sys.stderr)
        return 2

    sev_filter = {s.strip().lower() for s in args.severity.split(",") if s.strip()}
    if sev_filter - {"error", "warn", "info"}:
        print("error: --severity takes error,warn,info", file=sys.stderr)
        return 2

    results: list[tuple[str, list[dict[str, Any]]]] = []
    for path in files:
        findings = lint_file(path)
        if sev_filter:
            findings = [f for f in findings if str(f["severity"]).lower() in sev_filter]
        results.append((str(path), findings))

    summary = summarize(results)
    if args.json:
        print(json.dumps({"files": {p: {"findings": fs} for p, fs in results if fs}, "summary": summary}, indent=2))
    else:
        print_text(results)

    fail = summary["error"] > 0 or (args.strict and summary["warn"] > 0)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
