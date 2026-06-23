"""Source-grounded PCX API lookup and validation helpers.

The API index is generated from the official Perception Enma and AngelScript
docs.  This module keeps all hallucination checks on that generated contract so
CLI tools and MCP tools report the same findings and source URLs.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any

from pcx_parser import (
    extract_calls,
    extract_declarations,
    extract_enma_imports,
    extract_function_defs,
)

SUPPORTED_LANGUAGES = {"enma", "angelscript"}

LANG_ALIASES = {
    "enma": "enma",
    "em": "enma",
    ".em": "enma",
    "angelscript": "angelscript",
    "angel-script": "angelscript",
    "as": "angelscript",
    ".as": "angelscript",
}

FENCE_RE = re.compile(r'^```\s*([A-Za-z_.-]*)[^\n]*\n(.*?)\n```', re.MULTILINE | re.DOTALL)

ENMA_IMPORT_REQUIRED_TYPES = {"vec2", "vec3", "vec4", "color", "quat", "mat4"}
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

LANGUAGE_BUILTIN_CALLS: dict[str, set[str]] = {
    "enma": {"print", "println"},
    "angelscript": {"log"},
}

FORBIDDEN_CALLS_BY_LANGUAGE: dict[str, dict[str, str]] = {
    "enma": {
        "register_callback": "AngelScript lifecycle; use register_routine(cast<int64>(fn), data)",
        "log": "AngelScript logging; use println(...) in Enma",
        "get_view": "AngelScript viewport helper; use get_view_width() and get_view_height()",
        "deref": "AngelScript handle cleanup; Enma proc_t is RAII-managed",
    },
    "angelscript": {
        "register_routine": "Enma lifecycle; use register_callback(fn, interval, data_index)",
        "println": "Enma logging; use log(...) in AngelScript",
        "get_view_width": "Enma viewport helper; use get_view(width, height) out-params",
        "get_view_height": "Enma viewport helper; use get_view(width, height) out-params",
        "vec2": "Enma value type; use AngelScript API shapes from docs/perception/angelscript/",
        "vec3": "Enma value type; use AngelScript API shapes from docs/perception/angelscript/",
        "vec4": "Enma value type; use AngelScript API shapes from docs/perception/angelscript/",
        "color": "Enma value type; AngelScript render calls usually take raw RGBA args",
    },
}

FORBIDDEN_TYPES_BY_LANGUAGE: dict[str, dict[str, str]] = {
    "enma": {
        "dictionary": "AngelScript dictionary; use map<K,V> or imap<V> in Enma",
    },
    "angelscript": {
        "vec2": "Enma value type; use AngelScript Vector2/raw API shapes from docs",
        "vec3": "Enma value type; use AngelScript Vector3/raw API shapes from docs",
        "vec4": "Enma value type; use AngelScript docs for the registered vector type",
        "color": "Enma value type; AngelScript render APIs usually take raw RGBA args",
        "map": "Enma map; use dictionary in AngelScript",
    },
}


def load_api_index(path: Path) -> dict[str, Any]:
    """Load the generated API index and normalize absent sections."""
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("functions", {})
    data.setdefault("methods", {})
    data.setdefault("types", [])
    data.setdefault("modules", [])
    return data


def known_function_names(index: dict[str, Any]) -> set[str]:
    return set(index.get("functions", {}).keys())


def known_method_names(index: dict[str, Any]) -> set[str]:
    return set(index.get("methods", {}).keys())


def known_type_names(index: dict[str, Any]) -> set[str]:
    return set(index.get("types", []))


def all_symbol_names(index: dict[str, Any]) -> set[str]:
    return known_function_names(index) | known_method_names(index) | known_type_names(index)


def signatures_for(index: dict[str, Any], symbol: str, language: str | None = None) -> list[dict[str, Any]]:
    """Return all source-backed signatures for a function/method symbol."""
    sigs: list[dict[str, Any]] = []
    for section in ("functions", "methods"):
        raw = index.get(section, {}).get(symbol, [])
        if isinstance(raw, list):
            sigs.extend(dict(s) for s in raw if not language or s.get("language") == language)
    return sigs


def languages_for_symbol(index: dict[str, Any], symbol: str) -> set[str]:
    return {str(s.get("language")) for s in signatures_for(index, symbol) if s.get("language")}


def signature_text(sig: dict[str, Any]) -> str:
    args = ", ".join(str(a) for a in sig.get("arg_types", []))
    ret = str(sig.get("return_type") or "void")
    parent = sig.get("parent_type")
    name = sig.get("name", "")
    target = f"{parent}.{name}" if parent else name
    return f"{ret} {target}({args})"


def lookup_symbol(index: dict[str, Any], symbol: str, language: str | None = None) -> dict[str, Any]:
    """Return an exact source-backed lookup result with typo suggestions."""
    sigs = signatures_for(index, symbol, language)
    languages = sorted(languages_for_symbol(index, symbol))
    suggestions = difflib.get_close_matches(symbol, sorted(all_symbol_names(index)), n=8, cutoff=0.62)
    type_match = symbol in known_type_names(index)
    return {
        "symbol": symbol,
        "language": language or "",
        "found": bool(sigs or type_match),
        "type": type_match,
        "languages": languages,
        "signatures": [
            {
                "text": signature_text(sig),
                "language": sig.get("language", ""),
                "kind": sig.get("kind", ""),
                "source": sig.get("source", ""),
                "arity": sig.get("arity", 0),
            }
            for sig in sigs
        ],
        "suggestions": suggestions,
    }


def _base_type(t: str) -> str:
    t = t.strip().rstrip("@").replace("&", "").replace("*", "").strip()
    t = re.sub(r'<.*>', "", t)
    t = re.sub(r'\[.*\]', "", t)
    return t.strip()


def _type_first_line(text: str, t: str) -> int:
    m = re.search(r'\b' + re.escape(t) + r'\b', text)
    return text[:m.start()].count("\n") + 1 if m else 1


def _finding(kind: str, line: int, symbol: str, message: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "line": line,
        "symbol": symbol,
        "kind": kind,
        "message": message,
    }
    out.update({k: v for k, v in extra.items() if v not in (None, [], {}, "")})
    return out


def _symbol_context(index: dict[str, Any], symbol: str, language: str) -> dict[str, Any]:
    exact = lookup_symbol(index, symbol, language)
    any_lang = lookup_symbol(index, symbol)
    context: dict[str, Any] = {}
    if exact["signatures"]:
        context["signatures"] = exact["signatures"][:5]
    elif any_lang["signatures"]:
        context["available_languages"] = any_lang["languages"]
        context["signatures"] = any_lang["signatures"][:5]
    if any_lang["suggestions"]:
        context["suggestions"] = any_lang["suggestions"][:5]
    return context


def validate_code_against_index(
    code: str,
    language: str,
    index: dict[str, Any],
    source_path: str = "",
) -> list[dict[str, Any]]:
    """Validate Enma/AngelScript code for unknown or cross-language symbols."""
    if language not in SUPPORTED_LANGUAGES:
        return [_finding("unsupported_language", 0, language,
                         f"unsupported language: {language}; expected enma or angelscript")]

    findings: list[dict[str, Any]] = []
    user_funcs = {name for name, _ in extract_function_defs(code, language)}
    language_builtins = LANGUAGE_BUILTIN_CALLS.get(language, set())
    forbidden_calls = FORBIDDEN_CALLS_BY_LANGUAGE.get(language, {})
    forbidden_types = FORBIDDEN_TYPES_BY_LANGUAGE.get(language, {})
    known_types = known_type_names(index)
    known_functions = known_function_names(index)
    known_methods = known_method_names(index)

    for name, line in extract_calls(code, language):
        if name in forbidden_calls:
            findings.append(_finding(
                "wrong_language_symbol",
                line,
                name,
                f"'{name}' is not valid {language}: {forbidden_calls[name]}",
                **_symbol_context(index, name, language),
            ))
            continue

        lang_sigs = signatures_for(index, name, language)
        any_sigs = signatures_for(index, name)
        if lang_sigs or name in user_funcs or name in known_types or name in language_builtins:
            continue
        if any_sigs:
            findings.append(_finding(
                "wrong_language_symbol",
                line,
                name,
                f"'{name}' exists in {', '.join(sorted(languages_for_symbol(index, name)))} but not in {language}",
                **_symbol_context(index, name, language),
            ))
            continue
        if language == "enma" and name in {"main", "on_render", "on_update", "on_unload"}:
            continue
        if language == "angelscript" and name in {"main", "on_tick", "on_unload", "on_frame"}:
            continue
        if name in known_functions or name in known_methods:
            continue
        findings.append(_finding(
            "unknown_call",
            line,
            name,
            f"'{name}' is not a known Perception Enma or AngelScript function/method",
            **_symbol_context(index, name, language),
        ))

    for type_part, name, line in extract_declarations(code, language):
        base = _base_type(type_part)
        if base in forbidden_types:
            findings.append(_finding(
                "wrong_language_type",
                line,
                base,
                f"'{base}' is not valid {language}: {forbidden_types[base]}",
                suggestions=lookup_symbol(index, base).get("suggestions", [])[:5],
            ))
            continue
        if not base or base in known_types or base in user_funcs:
            continue
        if base[0].isupper():
            continue
        findings.append(_finding(
            "unknown_type",
            line,
            base,
            f"'{base}' is not a known Perception Enma or AngelScript type (in declaration of '{name}')",
            suggestions=lookup_symbol(index, base).get("suggestions", [])[:5],
        ))

    if language == "enma":
        imports = set(extract_enma_imports(code))
        used_types = {t for t in ENMA_IMPORT_REQUIRED_TYPES if re.search(r'\b' + re.escape(t) + r'\b', code)}
        for t in used_types:
            provider_imported = any(t in names and mod in imports for mod, names in ENMA_MODULE_HINTS.items())
            if provider_imported:
                continue
            for mod, names in ENMA_MODULE_HINTS.items():
                if t in names:
                    findings.append(_finding(
                        "missing_import",
                        _type_first_line(code, t),
                        t,
                        f"'{t}' requires `import \"{mod}\";`",
                        fix=f'import "{mod}";',
                    ))
                    break

    if source_path:
        for finding in findings:
            finding["file"] = source_path
    return findings


def extract_code_blocks(markdown: str) -> list[dict[str, object]]:
    """Extract fenced Enma/AngelScript blocks from Markdown-like text."""
    blocks: list[dict[str, object]] = []
    for idx, match in enumerate(FENCE_RE.finditer(markdown), 1):
        hint = match.group(1).strip().lower()
        language = LANG_ALIASES.get(hint)
        if not language:
            continue
        line = markdown[:match.start()].count("\n") + 1
        blocks.append({
            "index": idx,
            "line": line,
            "language": language,
            "code": match.group(2),
        })
    return blocks


def validate_answer_markdown(markdown: str, index: dict[str, Any], source_path: str = "answer") -> dict[str, Any]:
    """Validate all Enma/AngelScript code blocks in a generated answer."""
    blocks = extract_code_blocks(markdown)
    findings: list[dict[str, Any]] = []
    for block in blocks:
        source = f"{source_path}:code-block-{block['index']}"
        block_findings = validate_code_against_index(
            str(block["code"]),
            str(block["language"]),
            index,
            source,
        )
        for finding in block_findings:
            finding["code_block"] = block["index"]
            finding["code_block_line"] = block["line"]
            finding["language"] = block["language"]
            findings.append(finding)
    return {
        "source": source_path,
        "blocks_checked": len(blocks),
        "findings": findings,
        "ok": not findings,
    }
