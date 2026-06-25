"""Source-grounded PCX API lookup and validation helpers.

The API index is generated from the official Perception Enma docs.  This module keeps all hallucination checks on that generated contract so
CLI tools and MCP tools report the same findings and source URLs.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any, cast

from pcx_parser import (
    extract_calls,
    extract_declarations,
    extract_enma_imports,
    extract_function_defs,
)
from pcx_paths import data_root


SUPPORTED_LANGUAGES = {"enma"}

LANG_ALIASES = {
    "enma": "enma",
    "em": "enma",
    ".em": "enma",
}

UNSUPPORTED_SYMBOLS_PATH = data_root() / "knowledge" / "unsupported-symbols.json"

def load_unsupported_symbols() -> dict[str, str]:
    if not UNSUPPORTED_SYMBOLS_PATH.exists():
        return {}
    data = json.loads(UNSUPPORTED_SYMBOLS_PATH.read_text(encoding="utf-8"))
    symbols = data.get("symbols", {}) if isinstance(data, dict) else {}
    return {str(k): str(v) for k, v in symbols.items()}

FENCE_RE = re.compile(r'^```\s*([A-Za-z_.-]*)[^\n]*\n(.*?)\n```', re.MULTILINE | re.DOTALL)

ENMA_IMPORT_REQUIRED_TYPES = {"vec2", "vec3", "vec4", "color", "quat", "mat4"}
ENMA_MODULE_HINTS: dict[str, set[str]] = {
    "vec": {"vec2", "vec3", "vec4"},
    "color": {"color"},
    "math3d": {"quat", "mat4"},
    "math": {
        "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
        "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
        "sqrt", "cbrt", "pow", "hypot", "log", "log2", "log10", "log_base", "exp",
        "floor", "ceil", "round", "round_up", "round_down",
        "fabs", "fmod", "fmin", "fmax", "fclamp",
        "iabs", "imin", "imax", "iclamp",
        "abs", "min", "max", "clamp",
        "pi", "euler", "seed", "rand", "rand_int", "random_bool", "random_gaussian",
        "lerp", "inverse_lerp", "remap", "smoothstep", "step", "saturate",
        "is_nan", "is_inf", "is_finite", "sign", "fract", "wrap",
        "copysign", "nextafter", "f32_to_u32", "u32_to_f32", "f64_to_u64", "u64_to_f64",
        "deg_to_rad", "rad_to_deg", "lerp_angle", "move_toward",
        "ease_in", "ease_out", "ease_in_out", "approx_eq",
    },
    "strings": {
        "format", "to_string", "char_to_str", "ord", "chr", "from_chars",
        "hex_encode", "hex_decode", "hex_to_int", "base64_encode", "base64_decode",
        "url_encode", "url_decode", "to_int", "to_float", "split", "replace", "substr",
    },
    "json": {
        "json_parse", "json_stringify", "json_value", "json_object", "json_array",
        "is_valid", "is_null", "is_bool", "is_num", "is_str", "is_array", "is_obj",
        "kind", "as_bool", "as_num", "as_int", "as_str", "size", "has_key", "keys",
        "get_key", "get_at", "set_key", "remove_key", "push_value", "stringify", "pretty",
    },
    "file": {
        "read_file", "write_file", "create_directory", "does_file_exist", "query_directory",
        "file_exists", "file_remove", "file_rename", "file_copy", "file_size", "file_mtime",
        "file_read", "file_write", "file_read_bytes", "file_write_bytes",
        "dir_exists", "dir_create", "dir_list", "dir_walk",
    },
    "bits": {
        "popcount", "popcount_i32", "clz", "clz_i32", "ctz", "ctz_i32",
        "bswap", "bswap_i32", "rotl", "rotl_i32", "rotr", "rotr_i32",
        "parity", "bit_reverse", "bit_reverse_i32", "set_bit", "clear_bit",
        "toggle_bit", "test_bit", "extract_bits", "insert_bits", "is_pow2",
        "next_pow2", "prev_pow2", "align_up", "align_down",
    },
    "time": {
        "now_us", "now_ms", "now_ns", "unix_seconds", "mono_us", "sleep_ms",
        "from_ymd", "from_ymdhms", "year", "month", "day", "hour", "minute",
        "second", "day_of_week", "day_of_year", "is_leap", "days_in_month",
        "iso_format", "iso_parse", "add_seconds", "add_days", "diff_us", "diff_ms", "diff_s",
    },
    "atomic": {"memory_barrier", "read_barrier", "write_barrier"},
    "simd": {
        "simd_add_f64", "simd_sub_f64", "simd_mul_f64", "simd_div_f64", "simd_min_f64",
        "simd_max_f64", "simd_abs_f64", "simd_sqrt_f64", "simd_fma_f64", "simd_scale_f64",
        "simd_dot_f64", "simd_sum_f64", "simd_min_reduce_f64", "simd_max_reduce_f64",
        "simd_cmp_eq_f64", "simd_cmp_lt_f64", "simd_add_f32", "simd_sub_f32",
        "simd_mul_f32", "simd_div_f32", "simd_sqrt_f32", "simd_abs_f32",
        "simd_min_f32", "simd_max_f32", "simd_dot_f32", "simd_sum_f32",
        "simd_add_i64", "simd_sub_i64", "simd_mul_i64", "simd_sum_i64",
        "simd_add_i32", "simd_sub_i32", "simd_mul_i32", "simd_add_i16",
        "simd_sub_i16", "simd_mul_i16", "simd_add_i8", "simd_sub_i8",
        "simd_cmp_eq_i8", "simd_movemask_i8", "simd_shuffle_i8",
        "simd_and", "simd_or", "simd_xor", "simd_memset", "simd_memcpy",
    },
    "thread": {"sleep_us", "yield_cpu", "hardware_threads"},
    "array": {"push", "pop", "sort", "contains", "slice", "resize", "length"},
    "map": {"map", "imap", "get", "set", "contains", "remove"},
}

LANGUAGE_BUILTIN_CALLS: dict[str, set[str]] = {
    "enma": {
        "print", "println", "time_ms", "assert", "heap_collect", "heap_count",
        "set_budget", "set_memory_budget", "register_event", "fire_event", "clear_events",
    },
}

FORBIDDEN_CALLS_BY_LANGUAGE: dict[str, dict[str, str]] = {
    "enma": {
        "register_callback": "AngelScript lifecycle; use register_routine(cast<int64>(fn), data)",
        "log": "AngelScript logging; use println(...) in Enma",
        "get_view": "AngelScript viewport helper; use get_view_width() and get_view_height()",
        "deref": "AngelScript handle cleanup; Enma proc_t is RAII-managed",
    },
}

FORBIDDEN_TYPES_BY_LANGUAGE: dict[str, dict[str, str]] = {
    "enma": {
        "dictionary": "AngelScript dictionary; use map<K,V> or imap<V> in Enma",
    },
}


def load_api_index(path: Path) -> dict[str, Any]:
    """Load the generated API index and normalize absent sections."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"API index root must be an object: {path}")
    data = cast(dict[str, Any], raw)
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
        section_obj = index.get(section, {})
        section_map = cast(dict[str, object], section_obj) if isinstance(section_obj, dict) else {}
        raw_obj: object = section_map.get(symbol, [])
        if isinstance(raw_obj, list):
            for item in cast(list[object], raw_obj):
                if not isinstance(item, dict):
                    continue
                sig = cast(dict[str, Any], item)
                if not language or sig.get("language") == language:
                    sigs.append(dict(sig))
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


def _line_for_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def _without_line_comments(text: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


def _validate_enma_semantics(code: str) -> list[dict[str, Any]]:
    clean = _without_line_comments(code)
    findings: list[dict[str, Any]] = []
    for match in re.finditer(r"\bmap\s*<\s*([^,>]+)", clean):
        key = match.group(1).strip()
        if key != "string":
            symbol = f"map<{key}"
            findings.append(_finding(
                "semantic_error",
                _line_for_offset(clean, match.start()),
                symbol,
                "Enma map<K,V> uses string keys; use imap<V> for integer keys.",
            ))
    for match in re.finditer(r"\buint(?:8|16|32|64)\s+\w+\s*=\s*-(?!\s*cast\s*<)", clean):
        findings.append(_finding(
            "semantic_error",
            _line_for_offset(clean, match.start()),
            "cast<uint",
            "Enma rejects signed-to-unsigned narrowing without an explicit cast<uint...>(...).",
        ))
    match = re.search(r"\breturn\s*&", clean)
    if match:
        findings.append(_finding(
            "semantic_error",
            _line_for_offset(clean, match.start()),
            "return &",
            "Enma rejects escaping local addresses; return values or store owned state.",
        ))
    return findings


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
    extra_user_functions: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Validate Enma code for unknown symbols."""
    if language not in SUPPORTED_LANGUAGES:
        return [_finding("unsupported_language", 0, language,
                         f"unsupported language: {language}; use enma")]

    findings: list[dict[str, Any]] = []
    if language == "enma":
        findings.extend(_validate_enma_semantics(code))
    user_funcs = {name for name, _ in extract_function_defs(code, language)}
    if extra_user_functions:
        user_funcs.update(extra_user_functions)
    language_builtins = LANGUAGE_BUILTIN_CALLS.get(language, set())
    forbidden_calls = FORBIDDEN_CALLS_BY_LANGUAGE.get(language, {})
    forbidden_types = FORBIDDEN_TYPES_BY_LANGUAGE.get(language, {})
    unsupported_symbols = load_unsupported_symbols()
    known_types = known_type_names(index)
    known_functions = known_function_names(index)
    known_methods = known_method_names(index)

    for name, line in extract_calls(code, language):
        if name in unsupported_symbols:
            findings.append(_finding(
                "unsupported_symbol",
                line,
                name,
                unsupported_symbols[name],
                suggestions=lookup_symbol(index, name).get("suggestions", [])[:5],
            ))
            continue

        if name in forbidden_calls:
            findings.append(_finding(
                "wrong_language_symbol",
                line,
                name,
                f"'{name}' is not valid {language}: {forbidden_calls[name]}",
                **_symbol_context(index, name, language),
            ))
            continue

        if language == "enma":
            provider = next((mod for mod, names in ENMA_MODULE_HINTS.items() if name in names), "")
            if provider:
                imports = set(extract_enma_imports(code))
                if provider in imports or provider in {"array", "map"}:
                    continue
                findings.append(_finding(
                    "missing_import",
                    line,
                    name,
                    f"'{name}' requires `import \"{provider}\";`",
                    fix=f'import "{provider}";',
                ))
                continue
            if name.startswith("fs_") and "PERM_FILE" not in code:
                findings.append(_finding(
                    "missing_permission",
                    line,
                    "PERM_FILE",
                    f"{name} requires PERM_FILE in the script permission set",
                ))

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
        if name in known_functions or name in known_methods:
            continue
        findings.append(_finding(
            "unknown_call",
            line,
            name,
            f"'{name}' is not a known Perception Enma function/method",
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
            f"'{base}' is not a known Perception Enma type (in declaration of '{name}')",
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
    """Validate all Enma code blocks in a generated answer."""
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
