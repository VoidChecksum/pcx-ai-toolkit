#!/usr/bin/env python3
"""Symbol-level hallucination checker for Enma, AngelScript, and Lua scripts.

Loads knowledge/pcx-api-index.json (built by tools/build-api-index.py) and
reports unknown function/method calls and unknown declared types. This catches
the most common LLM hallucinations: invented function names, wrong method
names, and missing imports for Enma addon modules.

Usage:
    python tools/symbol-check.py file.em
    python tools/symbol-check.py file.as
    python tools/symbol-check.py file.lua
    python tools/symbol-check.py --json file_or_dir

Exit code: 0 if clean, 1 if any unknown symbol found.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / "knowledge" / "pcx-api-index.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_parser import (  # noqa: E402
    extract_calls,
    extract_declarations,
    extract_enma_imports,
    extract_function_defs,
)


# Types that require an explicit module import in Enma.
ENMA_IMPORT_REQUIRED_TYPES = {
    "vec2", "vec3", "vec4", "color", "quat", "mat4",
}
# Module -> names it provides, for missing-import hints.
ENMA_MODULE_HINTS: dict[str, set[str]] = {
    "vec": {"vec2", "vec3", "vec4"},
    "color": {"color"},
    "math3d": {"quat", "mat4"},
    "math": {"sin", "cos", "sqrt", "pow", "clamp", "lerp", "abs", "floor", "ceil",
             "deg_to_rad", "rad_to_deg", "lerp_angle", "move_toward"},
    "strings": {"format", "to_int", "split", "replace", "substr"},
    "json": {"json_parse", "json_stringify", "json_value"},
    "file": {"read_file", "write_file", "create_directory", "does_file_exist", "query_directory"},
    "bits": {"popcount", "clz", "ctz", "bswap", "rotl", "rotr"},
    "time": {"time_ms", "time_us", "sleep"},
    "array": {"push", "pop", "sort", "contains", "slice", "resize", "length"},
    "map": {"map", "imap", "get", "set", "contains", "remove"},
}


def load_index(path: Path) -> dict[str, set[str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Build it first:\n  python3 tools/build-api-index.py"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "functions": set(data.get("functions", {}).keys()),
        "methods": set(data.get("methods", {}).keys()),
        "types": set(data.get("types", [])),
        "modules": set(data.get("modules", [])),
    }


def detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".em":
        return "enma"
    if ext == ".as":
        return "angelscript"
    if ext == ".lua":
        return "lua"
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if text.startswith("import \"") or "register_routine" in text[:500]:
        return "enma"
    if "register_callback" in text[:500] or "@" in text[:200]:
        return "angelscript"
    return "lua"


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(p for p in target.rglob("*") if p.suffix.lower() in {".em", ".as", ".lua"})


def _base_type(t: str) -> str:
    t = t.strip().rstrip("@").replace("&", "").replace("*", "").strip()
    t = re.sub(r'<.*>', "", t)
    t = re.sub(r'\[.*\]', "", t)
    return t.strip()


def _type_first_line(text: str, t: str) -> int:
    m = re.search(r'\b' + re.escape(t) + r'\b', text)
    return text[:m.start()].count("\n") + 1 if m else 1


def check_file(path: Path, index: dict[str, set[str]], language: str | None = None) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if language is None:
        language = detect_language(path)

    user_funcs = {name for name, _ in extract_function_defs(text, language)}

    # ── Unknown calls ─────────────────────────────────────────────────────────
    known_types = set(index.get("types", []))
    for name, line in extract_calls(text, language):
        if name in index["functions"] or name in index["methods"] or name in user_funcs:
            continue
        if name in known_types:
            continue  # constructor call, e.g. color(...) or vec2(...)
        if language == "enma" and name in {"main", "on_render", "on_update", "on_unload"}:
            continue
        if language == "angelscript" and name in {"main", "on_tick", "on_unload", "on_frame"}:
            continue
        if language == "lua" and name in {"main", "on_frame", "on_unload", "on_tick"}:
            continue
        findings.append({
            "file": str(path),
            "line": line,
            "symbol": name,
            "kind": "unknown_call",
            "message": f"'{name}' is not a known PCX or Enma function/method",
        })

    # ── Unknown declared types (Enma / AngelScript only) ─────────────────────
    if language in {"enma", "angelscript"}:
        for type_part, name, line in extract_declarations(text, language):
            base = _base_type(type_part)
            if not base or base in index["types"] or base in user_funcs:
                continue
            if base[0].isupper():
                continue
            findings.append({
                "file": str(path),
                "line": line,
                "symbol": base,
                "kind": "unknown_type",
                "message": f"'{base}' is not a known type (in declaration of '{name}')",
            })

    # ── Missing Enma imports for value types ─────────────────────────────────
    if language == "enma":
        imports = set(extract_enma_imports(text))
        used_types = {t for t in ENMA_IMPORT_REQUIRED_TYPES if re.search(r'\b' + re.escape(t) + r'\b', text)}
        for t in used_types:
            provider_imported = any(t in names and mod in imports for mod, names in ENMA_MODULE_HINTS.items())
            if provider_imported:
                continue
            for mod, names in ENMA_MODULE_HINTS.items():
                if t in names:
                    findings.append({
                        "file": str(path),
                        "line": _type_first_line(text, t),
                        "symbol": t,
                        "kind": "missing_import",
                        "message": f"'{t}' requires `import \"{mod}\";`",
                    })
                    break

    return findings


def print_findings(findings: list[dict[str, object]], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(findings, indent=2))
        return
    if not findings:
        print("clean: no unknown symbols")
        return
    by_file: dict[str, list[dict[str, object]]] = {}
    for f in findings:
        by_file.setdefault(str(f["file"]), []).append(f)
    for file_path, items in by_file.items():
        print(f"\n{file_path}")
        for it in sorted(items, key=lambda x: int(str(x["line"]))):
            print(f"  {it['line']}: [{it['kind']}] {it['message']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="file or directory to check")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--lang", choices=["enma", "angelscript", "lua"], help="force language detection")
    args = ap.parse_args()

    try:
        index = load_index(INDEX_FILE)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    target = Path(args.target)
    if not target.exists():
        print(f"ERROR: not found: {target}", file=sys.stderr)
        return 2

    all_findings: list[dict[str, object]] = []
    for path in collect_files(target):
        all_findings.extend(check_file(path, index, args.lang))

    print_findings(all_findings, args.json)
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
