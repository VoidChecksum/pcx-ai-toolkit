#!/usr/bin/env python3
"""Generate docs/COVERAGE.md and docs/COVERAGE.json from committed knowledge."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "docs" / "COVERAGE.json"
OUT_MD = ROOT / "docs" / "COVERAGE.md"

CORE_PAGES = {
    "cpu-api.md",
    "filesystem-api.md",
    "gui-api.md",
    "input-api.md",
    "lifecycle-and-routines.md",
    "mcp-api.md",
    "net-api.md",
    "proc-api.md",
    "render-api.md",
    "sound-api.md",
    "unicorn-api.md",
    "win-api.md",
    "zydis-api.md",
}
PLATFORM_PAGES = {"ide.md", "extensions-api.md", "analyzer.md", "custom-draw-api.md", "sdk-status.md"}
METADATA_PAGES = {"changelogs.md", "versioning-and-migration.md"}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def rows(symbol_versions: dict[str, Any]) -> list[dict[str, Any]]:
    value = symbol_versions.get("symbols", [])
    return value if isinstance(value, list) else []


def api_families(index: dict[str, Any]) -> set[str]:
    families: set[str] = set()
    for group in ("functions", "methods"):
        for signatures in index.get(group, {}).values():
            for sig in signatures:
                source = str(sig.get("source", ""))
                name = Path(source).name.removesuffix(".md")
                if name.endswith("-api"):
                    families.add(name[:-4])
                elif name == "lifecycle-and-routines":
                    families.add("lifecycle")
    return families


def symbol_count(index: dict[str, Any]) -> int:
    return len(index.get("functions", {})) + len(index.get("methods", {})) + len(index.get("types", []))


def has_explicit(row: dict[str, Any], key: str) -> bool:
    return key in row and row.get(key) is not None


def has_nonempty(row: dict[str, Any], key: str) -> bool:
    return row.get(key) not in (None, [], "")


def page_counts() -> dict[str, Any]:
    available = {p.name for p in (ROOT / "docs" / "perception").glob("*.md")}
    def section(names: set[str]) -> dict[str, Any]:
        missing = sorted(names - available)
        return {"current": len(names) - len(missing), "target": len(names), "missing": missing}
    core = section(CORE_PAGES)
    platform = section(PLATFORM_PAGES)
    metadata = section(METADATA_PAGES)
    total_target = len(CORE_PAGES | PLATFORM_PAGES | METADATA_PAGES)
    total_current = core["current"] + platform["current"] + metadata["current"]
    return {"core": core, "platform": platform, "metadata": metadata, "total_current": total_current, "total_target": total_target}


def per_family(symbols: list[dict[str, Any]], cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in symbols:
        by_family[str(row.get("api_family", "unknown"))].append(row)
    eval_text = "\n".join(str(case.get("name", "")) + " " + str(case.get("input", "")) for case in cases).lower()
    out = []
    for family, items in sorted(by_family.items()):
        out.append({
            "family": family,
            "symbols": len(items),
            "signatures": sum(1 for row in items if row.get("signature") or row.get("type_shape") or row.get("callback_shape") or row.get("constant_value")),
            "permissions": sum(1 for row in items if has_explicit(row, "permissions")),
            "failures": sum(1 for row in items if has_explicit(row, "failure_modes")),
            "eval_cases": eval_text.count(family.lower()),
        })
    return out


def build() -> dict[str, Any]:
    index = load_json(ROOT / "knowledge" / "pcx-api-index.json", {})
    symbol_versions = load_json(ROOT / "knowledge" / "perception-symbol-versions.json", {"symbols": []})
    unsupported = load_json(ROOT / "knowledge" / "unsupported-symbols.json", {"symbols": {}})
    deprecated = load_json(ROOT / "knowledge" / "deprecated-symbols.json", {"symbols": {}})
    permissions = load_json(ROOT / "knowledge" / "permission-rules.json", {"rules": []})
    provenance = load_json(ROOT / "docs" / "PROVENANCE.json", {})
    evals = load_json(ROOT / "evals" / "hallucination-regression.json", {"cases": []})
    symbols = rows(symbol_versions)
    cases = evals.get("cases", [])
    pages = page_counts()
    callable_symbols = [row for row in symbols if row.get("kind") in {"function", "method", "callback"}]
    noncallable_symbols = [row for row in symbols if row not in callable_symbols]
    missing_permission = [row["symbol"] for row in symbols if not has_explicit(row, "permissions")]
    missing_failure = [row["symbol"] for row in symbols if not has_explicit(row, "failure_modes")]
    missing_signature = [row["symbol"] for row in callable_symbols if not row.get("signature") and not row.get("callback_shape")]
    missing_shape = [row["symbol"] for row in noncallable_symbols if not (row.get("type_shape") or row.get("constant_value") or row.get("callback_shape") or row.get("signature"))]
    return {
        "schema": "pcx-anti-hallucination-coverage-v2",
        "api": {
            "families_indexed": len(api_families(index)),
            "family_names": sorted(api_families(index)),
            "pages": pages,
            "perception_api_pages_indexed": pages["total_current"],
            "symbols_indexed": len(symbols) or symbol_count(index),
            "symbols_with_explicit_permission_metadata": sum(1 for row in symbols if has_explicit(row, "permissions")),
            "symbols_requiring_permissions": sum(1 for row in symbols if has_nonempty(row, "permissions")),
            "callable_symbols": len(callable_symbols),
            "callable_symbols_with_signatures": sum(1 for row in callable_symbols if row.get("signature") or row.get("callback_shape")),
            "noncallable_symbols": len(noncallable_symbols),
            "noncallable_symbols_with_shape": sum(1 for row in noncallable_symbols if row.get("type_shape") or row.get("constant_value") or row.get("callback_shape") or row.get("signature")),
            "symbols_with_failure_metadata": sum(1 for row in symbols if has_explicit(row, "failure_modes")),
        },
        "missing": {
            "permission_metadata": missing_permission,
            "failure_metadata": missing_failure,
            "callable_signatures": missing_signature,
            "noncallable_shapes": missing_shape,
        },
        "families": per_family(symbols, cases),
        "permissions": {"rules": len(permissions.get("rules", []))},
        "deprecated": {"symbols": len(deprecated.get("symbols", {}))},
        "hallucinations": {
            "known_symbols": len(unsupported.get("symbols", {})),
            "eval_cases": len(cases),
            "eval_cases_with_expected_findings": sum(1 for case in cases if case.get("expected_findings")),
        },
        "provenance": {
            "sources": int(provenance.get("count", 0)),
            "drift_checkable": int(provenance.get("drift_checkable", 0)),
        },
    }


def status(current: int, target: int) -> str:
    return "pass" if current >= target else "fail"


def bullet_list(items: list[str]) -> str:
    return "- none" if not items else "\n".join(f"- `{item}`" for item in items)


def render_md(data: dict[str, Any]) -> str:
    api = data["api"]
    pages = api["pages"]
    families = "\n".join(f"- `{name}`" for name in api["family_names"])
    family_rows = "\n".join(
        f"| {row['family']} | {row['symbols']} | {row['signatures']} | {row['permissions']} | {row['failures']} | {row['eval_cases']} |"
        for row in data["families"]
    )
    return f"""# PCX Anti-Hallucination Coverage

> Generated by `tools/build-coverage-dashboard.py`; do not edit manually.

## Summary

- Perception API pages indexed: {pages['total_current']}
- Total Perception pages indexed: {pages['total_current']}/{pages['total_target']}
- Core Enma API pages indexed: {pages['core']['current']}/{pages['core']['target']}
- Platform/tooling pages indexed: {pages['platform']['current']}/{pages['platform']['target']}
- Metadata/status pages indexed: {pages['metadata']['current']}/{pages['metadata']['target']}
- API families indexed: {api['families_indexed']}
- Symbols indexed: {api['symbols_indexed']}
- Symbols with explicit permission metadata: {api['symbols_with_explicit_permission_metadata']}
- Symbols requiring non-empty permissions: {api['symbols_requiring_permissions']}
- Callable symbols with signatures: {api['callable_symbols_with_signatures']}/{api['callable_symbols']}
- Non-callable symbols with shape metadata: {api['noncallable_symbols_with_shape']}/{api['noncallable_symbols']}
- Symbols with failure metadata: {api['symbols_with_failure_metadata']}
- Permission rules: {data['permissions']['rules']}
- Deprecated or removed symbols tracked: {data['deprecated']['symbols']}
- Known hallucinations covered: {data['hallucinations']['known_symbols']}
- Hallucination eval cases: {data['hallucinations']['eval_cases']}
- Generated bundle sources: {data['provenance']['sources']}
- Drift-checkable sources: {data['provenance']['drift_checkable']}

## Targets

| Metric | Current | Target | Status |
|---|---:|---:|---|
| Symbols indexed | {api['symbols_indexed']} | 216 | {status(api['symbols_indexed'], 216)} |
| Symbols with explicit permission metadata | {api['symbols_with_explicit_permission_metadata']} | 216 | {status(api['symbols_with_explicit_permission_metadata'], 216)} |
| Callable symbols with signatures | {api['callable_symbols_with_signatures']} | {api['callable_symbols']} | {status(api['callable_symbols_with_signatures'], api['callable_symbols'])} |
| Non-callable symbols with shape metadata | {api['noncallable_symbols_with_shape']} | {api['noncallable_symbols']} | {status(api['noncallable_symbols_with_shape'], api['noncallable_symbols'])} |
| Symbols with failure metadata | {api['symbols_with_failure_metadata']} | 216 | {status(api['symbols_with_failure_metadata'], 216)} |
| Known hallucinations covered | {data['hallucinations']['known_symbols']} | 100 | {status(data['hallucinations']['known_symbols'], 100)} |
| Eval cases | {data['hallucinations']['eval_cases']} | 150 | {status(data['hallucinations']['eval_cases'], 150)} |
| Eval cases with expected findings | {data['hallucinations']['eval_cases_with_expected_findings']} | 100 | {status(data['hallucinations']['eval_cases_with_expected_findings'], 100)} |
| Total Perception pages indexed | {pages['total_current']} | {pages['total_target']} | {status(pages['total_current'], pages['total_target'])} |

## Perception Page Classes

| Class | Current | Target | Missing |
|---|---:|---:|---|
| Core Enma API pages | {pages['core']['current']} | {pages['core']['target']} | {', '.join(pages['core']['missing']) or 'none'} |
| Platform/tooling pages | {pages['platform']['current']} | {pages['platform']['target']} | {', '.join(pages['platform']['missing']) or 'none'} |
| Metadata/status pages | {pages['metadata']['current']} | {pages['metadata']['target']} | {', '.join(pages['metadata']['missing']) or 'none'} |

## Per-Family Coverage

| Family | Symbols | Signatures/shapes | Permissions | Failures | Eval mentions |
|---|---:|---:|---:|---:|---:|
{family_rows}

## Missing Permission Metadata

{bullet_list(data['missing']['permission_metadata'])}

## Missing Failure Metadata

{bullet_list(data['missing']['failure_metadata'])}

## Missing Callable Signatures

{bullet_list(data['missing']['callable_signatures'])}

## Missing Non-Callable Shape Metadata

{bullet_list(data['missing']['noncallable_shapes'])}

## Indexed API Families

{families}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if generated files differ")
    args = ap.parse_args()
    data = build()
    rendered_json = json.dumps(data, indent=2, sort_keys=True) + "\n"
    rendered_md = render_md(data)
    if args.check:
        stale = []
        if not OUT_JSON.exists() or OUT_JSON.read_text(encoding="utf-8") != rendered_json:
            stale.append(str(OUT_JSON.relative_to(ROOT)))
        if not OUT_MD.exists() or OUT_MD.read_text(encoding="utf-8") != rendered_md:
            stale.append(str(OUT_MD.relative_to(ROOT)))
        if stale:
            print("coverage dashboard drift: " + ", ".join(stale), file=sys.stderr)
            return 1
        return 0
    OUT_JSON.write_text(rendered_json, encoding="utf-8")
    OUT_MD.write_text(rendered_md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
