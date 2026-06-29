#!/usr/bin/env python3
"""Generate Enma addon import metadata used by validators.

Input defaults to docs/llms-perception-enma.md so CI works offline. Pass a
freshly fetched llms-language.md/addon bundle to refresh from upstream docs.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "docs" / "llms-perception-enma.md"
OUT = REPO_ROOT / "knowledge" / "enma-addon-imports.json"

# Seeded from documented addon pages. The parser below can add symbols from docs,
# but these are the stable module boundaries the validator needs.
MODULES: dict[str, set[str]] = {
    "vec": {"vec2", "vec3", "vec4"},
    "color": {"color"},
    "math3d": {"quat", "mat4"},
    "variant": {"variant", "variant_int", "variant_float", "variant_bool", "variant_str", "variant_box_owned", "variant_null"},
    "regex": {"regex"},
    "hash_set": {"hash_set"},
    "sorted_map": {"sorted_map"},
    "list": {"list"},
}
IMPORT_RE = re.compile(r'import\s+"([A-Za-z0-9_]+)"')
CODE_SYMBOL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:<|\(|=|;)")

def infer_symbols(text: str) -> dict[str, set[str]]:
    modules = {k: set(v) for k, v in MODULES.items()}
    current = ""
    for line in text.splitlines():
        imp = IMPORT_RE.search(line)
        if imp:
            current = imp.group(1) if imp.group(1) in MODULES else ""
        if not current:
            continue
        for symbol in CODE_SYMBOL_RE.findall(line):
            if symbol in {"import", "return", "if", "for", "while", "auto", "int64", "int32", "float64", "float32", "bool", "string"}:
                continue
            if current in MODULES and (symbol.startswith(current) or symbol in MODULES[current]):
                modules[current].add(symbol)
    return modules

def main() -> int:
    ap = argparse.ArgumentParser(description="Build knowledge/enma-addon-imports.json")
    ap.add_argument("source", nargs="?", default=str(DEFAULT_INPUT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    source = Path(args.source)
    text = source.read_text(encoding="utf-8", errors="ignore") if source.exists() else ""
    modules = infer_symbols(text)
    required_types = sorted({s for mod in ("vec", "color", "math3d", "variant", "regex", "hash_set", "sorted_map", "list") for s in modules.get(mod, set()) if not s.startswith(("variant_",))})
    payload = {
        "source": (source.relative_to(REPO_ROOT) if source.is_relative_to(REPO_ROOT) else source).as_posix(),
        "modules": {k: sorted(v) for k, v in sorted(modules.items())},
        "import_required_types": required_types,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != rendered:
            print(f"{OUT.relative_to(REPO_ROOT)} is stale; run tools/build-enma-addon-metadata.py")
            return 1
        return 0
    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO_ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
