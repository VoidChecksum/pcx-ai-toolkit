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
PERMISSION_RULES_PATH = data_root() / "knowledge" / "permission-rules.json"
DEPRECATED_SYMBOLS_PATH = data_root() / "knowledge" / "deprecated-symbols.json"
SYMBOL_METADATA_PATH = data_root() / "knowledge" / "perception-symbol-versions.json"

def load_unsupported_symbols() -> dict[str, str]:
    if not UNSUPPORTED_SYMBOLS_PATH.exists():
        return {}
    raw_data: object = json.loads(UNSUPPORTED_SYMBOLS_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        return {}
    data = cast(dict[str, object], raw_data)
    raw_symbols = data.get("symbols", {})
    if not isinstance(raw_symbols, dict):
        return {}
    symbols = cast(dict[object, object], raw_symbols)
    return {str(k): str(v) for k, v in symbols.items()}


def load_permission_rules() -> list[dict[str, Any]]:
    if not PERMISSION_RULES_PATH.exists():
        return []
    raw_data: object = json.loads(PERMISSION_RULES_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        return []
    rules = cast(dict[str, object], raw_data).get("rules", [])
    return cast(list[dict[str, Any]], rules) if isinstance(rules, list) else []


def load_deprecated_symbols() -> dict[str, dict[str, str]]:
    if not DEPRECATED_SYMBOLS_PATH.exists():
        return {}
    raw_data: object = json.loads(DEPRECATED_SYMBOLS_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        return {}
    raw_symbols = cast(dict[str, object], raw_data).get("symbols", {})
    if not isinstance(raw_symbols, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for key, value in cast(dict[object, object], raw_symbols).items():
        if isinstance(value, dict):
            out[str(key)] = {str(k): str(v) for k, v in cast(dict[object, object], value).items()}
        else:
            out[str(key)] = {"replacement": "", "reason": str(value)}
    return out



def load_symbol_metadata() -> dict[str, dict[str, Any]]:
    if not SYMBOL_METADATA_PATH.exists():
        return {}
    raw_data: object = json.loads(SYMBOL_METADATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        return {}
    raw_symbols = cast(dict[str, object], raw_data).get("symbols", [])
    if not isinstance(raw_symbols, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in cast(list[object], raw_symbols):
        if not isinstance(item, dict):
            continue
        row = cast(dict[str, Any], item)
        symbol = row.get("symbol")
        if symbol:
            out[str(symbol)] = row
    return out


def symbol_metadata(symbol: str) -> dict[str, Any]:
    return load_symbol_metadata().get(symbol, {})

def permissions_for_symbol(symbol: str, sig: dict[str, Any] | None = None) -> list[str]:
    source = str((sig or {}).get("source", ""))
    found: list[str] = []
    for rule in load_permission_rules():
        raw_match = rule.get("match", {})
        if not isinstance(raw_match, dict):
            continue
        match = cast(dict[str, Any], raw_match)
        ok = False
        exact = str(match.get("symbol", ""))
        prefix = str(match.get("prefix", ""))
        contains = str(match.get("symbol_contains", ""))
        source_contains = str(match.get("source_contains", ""))
        if exact == symbol:
            ok = True
        if prefix and symbol.startswith(prefix):
            ok = True
        if contains and contains in symbol:
            ok = True
        if source_contains and source_contains in source:
            ok = True
        if ok:
            for perm in rule.get("permissions", []):
                if str(perm) not in found:
                    found.append(str(perm))
    return found

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
    meta = symbol_metadata(symbol)
    citation = ""
    if meta.get("source") and meta.get("line_start") and meta.get("line_end"):
        citation = f"{meta['source']}:{meta['line_start']}-{meta['line_end']}"
    return {
        "symbol": symbol,
        "language": language or "",
        "found": bool(sigs or type_match or meta),
        "type": type_match or meta.get("kind") == "type",
        "languages": languages or ([str(meta.get("language"))] if meta.get("language") else []),
        "source": meta.get("source", ""),
        "source_anchor": meta.get("source_anchor"),
        "line_start": meta.get("line_start"),
        "line_end": meta.get("line_end"),
        "citation": citation,
        "permissions": meta.get("permissions", []),
        "permission_notes": meta.get("permission_notes", ""),
        "failure_modes": meta.get("failure_modes", []),
        "return_sentinel": meta.get("return_sentinel"),
        "requires_context": meta.get("requires_context"),
        "signatures": [
            {
                "text": signature_text(sig),
                "language": sig.get("language", ""),
                "kind": sig.get("kind", ""),
                "source": sig.get("source", ""),
                "arity": sig.get("arity", 0),
                "permissions": meta.get("permissions", permissions_for_symbol(symbol, sig)),
                "source_anchor": meta.get("source_anchor"),
                "line_start": meta.get("line_start"),
                "line_end": meta.get("line_end"),
                "citation": citation,
                "deprecated": load_deprecated_symbols().get(symbol, {}),
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

def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out



def _line_for_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def _without_line_comments(text: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())

def _split_args(args: str) -> list[str]:
    out: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(args):
        if ch in "(<[":
            depth += 1
        elif ch in ")>]":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            out.append(args[start:i].strip())
            start = i + 1
    tail = args[start:].strip()
    if tail:
        out.append(tail)
    return out


def _extract_call_args(code: str) -> list[tuple[str, str, int]]:
    clean = _without_line_comments(code)
    out: list[tuple[str, str, int]] = []
    for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", clean):
        name = match.group(1)
        start = match.end()
        depth = 1
        i = start
        while i < len(clean) and depth:
            if clean[i] == "(":
                depth += 1
            elif clean[i] == ")":
                depth -= 1
            i += 1
        if depth == 0:
            out.append((name, clean[start:i - 1], _line_for_offset(clean, match.start())))
    return out

def _looks_raw_scalar(arg: str) -> bool:
    text = arg.strip()
    if re.fullmatch(r"[-+]?(?:0x[0-9A-Fa-f]+|\d+(?:\.\d+)?)", text):
        return True
    if re.fullmatch(r"[-+]?(?:0x[0-9A-Fa-f]+|\d+(?:\.\d+)?)\s*,", text):
        return True
    return False


def _main_body(clean: str) -> str:
    match = re.search(r"\b(?:int64|int32|int)\s+main\s*\([^)]*\)\s*\{", clean)
    if not match:
        return ""
    start = match.end()
    depth = 1
    i = start
    while i < len(clean) and depth:
        if clean[i] == "{":
            depth += 1
        elif clean[i] == "}":
            depth -= 1
        i += 1
    return clean[start:i - 1] if depth == 0 else clean[start:]




def _validate_enma_lifecycle(code: str) -> list[dict[str, Any]]:
    clean = _without_line_comments(code)
    findings: list[dict[str, Any]] = []
    if re.search(r"\bvoid\s+main\s*\(", clean):
        findings.append(_finding("invalid_entrypoint", _line_for_offset(clean, clean.find("void main")), "main", "Enma entry point must be `int64 main()` and return 1."))
    main_body = _main_body(clean)
    true_offset = clean.find("return true")
    if main_body and re.search(r"\breturn\s+true\s*;", main_body):
        findings.append(_finding("invalid_entrypoint_return", _line_for_offset(clean, true_offset), "return true", "Enma main should return integer sentinel `1`, not boolean `true`."))
    for match in re.finditer(r"\bregister_callback\s*\(", clean):
        findings.append(_finding("wrong_routine_api", _line_for_offset(clean, match.start()), "register_callback", "Use `register_routine(cast<int64>(fn), data)`; Enma has no automatic callback API.", repair="register_routine(cast<int64>(fn), data);"))
    functions = {m.group(2): (m.group(1), _split_args(m.group(3)), _line_for_offset(clean, m.start())) for m in re.finditer(r"\b([A-Za-z_][\w:<>,\\s*&]*)\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*\{", clean)}
    for name, args, line in _extract_call_args(clean):
        if name != "register_routine":
            continue
        parts = _split_args(args)
        if parts and not parts[0].startswith("cast<int64>"):
            findings.append(_finding("routine_missing_cast", line, "register_routine", "First register_routine argument must be `cast<int64>(fn)`.", repair="register_routine(cast<int64>(fn), data);"))
        fn_match = re.search(r"cast\s*<\s*int64\s*>\s*\(\s*(\w+)\s*\)", parts[0] if parts else "")
        if fn_match and fn_match.group(1) in functions:
            _ret, fn_args, fn_line = functions[fn_match.group(1)]
            if len(fn_args) != 1 or "int64" not in fn_args[0]:
                findings.append(_finding("invalid_routine_signature", fn_line, fn_match.group(1), "Routine callback must be `void fn(int64 data)`.", repair=f"void {fn_match.group(1)}(int64 data) {{ ... }}"))
    return findings


def _validate_call_shapes(code: str, index: dict[str, Any], language: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for name, args, line in _extract_call_args(code):
        sigs = signatures_for(index, name, language)
        if not sigs:
            continue
        actual = _split_args(args)
        arities = {int(sig.get("arity", len(sig.get("arg_types", [])))) for sig in sigs}
        if len(actual) not in arities:
            findings.append(_finding("argument_count_mismatch", line, name, f"{name} expects {sorted(arities)} argument(s), got {len(actual)}.", signatures=[{"text": signature_text(sig), "source": sig.get("source", "")} for sig in sigs[:3]]))
            continue
        sig = next((s for s in sigs if int(s.get("arity", len(s.get("arg_types", [])))) == len(actual)), sigs[0])
        expected = [str(t) for t in sig.get("arg_types", [])]
        for i, (arg, typ) in enumerate(zip(actual, expected), start=1):
            base = _base_type(typ)
            if base in {"vec2", "vec3", "vec4", "color"} and _looks_raw_scalar(arg):
                findings.append(_finding("argument_shape_mismatch", line, name, f"Argument {i} of {name} should be {base}; wrap raw values with `{base}(...)`.", repair=f"Use `{base}(...)` for argument {i}."))
    return findings


def _validate_enma_semantics(code: str) -> list[dict[str, Any]]:
    clean = _without_line_comments(code)
    findings: list[dict[str, Any]] = []
    for match in re.finditer(r"\barray\s*<[^>]+>\s*@", clean):
        findings.append(_finding(
            "semantic_trap",
            _line_for_offset(clean, match.start()),
            "@",
            "Enma arrays use `T[]`; AngelScript handle syntax `array<T>@` is not valid here.",
            repair="Use `T[] name;`.",
        ))
    for match in re.finditer(r"\bread_memory\s*<", clean):
        findings.append(_finding(
            "unknown_call",
            _line_for_offset(clean, match.start()),
            "read_memory",
            "C++ template helper `read_memory<T>` is not a Perception Enma API; use documented proc methods.",
        ))
    for match in re.finditer(r"\bawait\s+\w+\s*\(", clean):
        findings.append(_finding(
            "semantic_trap",
            _line_for_offset(clean, match.start()),
            "await",
            "Enma validation does not support JavaScript async/await; check documented net return values.",
        ))
    for match in re.finditer(r"\bauto\s+\w+\s*=", clean):
        findings.append(_finding(
            "unknown_type",
            _line_for_offset(clean, match.start()),
            "auto",
            "C++ `auto` is not valid Enma; write the documented concrete type.",
        ))
    for match in re.finditer(r"\bvector\s*<", clean):
        findings.append(_finding(
            "unknown_type",
            _line_for_offset(clean, match.start()),
            "vector",
            "Use Enma `T[]` arrays, not C++ `vector<T>`.",
        ))
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
    ret_match = re.search(r"\breturn\s*&", clean)
    if ret_match:
        findings.append(_finding(
            "semantic_error",
            _line_for_offset(clean, ret_match.start()),
            "return &",
            "Enma rejects escaping local addresses; return values or store owned state.",
        ))
    pointer_vars = {m.group(1) for m in re.finditer(r"\b\w+(?:\s*<[^>]+>)?\s*\*\s*(\w+)", clean)}
    for match in re.finditer(r"\b(\w+)\s*=\s*\1\s*[+-]\s*\d+", clean):
        if match.group(1) not in pointer_vars:
            continue
        findings.append(_finding(
            "semantic_trap",
            _line_for_offset(clean, match.start()),
            match.group(1),
            "Enma does not support C-style pointer arithmetic; use indexed containers or host-validated offsets.",
        ))
    for match in re.finditer(r"cast\s*<\s*int64\s*>\s*\(\s*(\w+)\s*\)", clean):
        if match.group(1) not in pointer_vars:
            continue
        findings.append(_finding(
            "semantic_trap",
            _line_for_offset(clean, match.start()),
            "cast<int64>(ptr)",
            "Do not cast Enma pointers to int64; keep handles/offsets as documented integer values.",
        ))
    for match in re.finditer(r"\b([A-Z]\w*)\s+\w+\s*=\s*new\s+\1\s*\(", clean):
        findings.append(_finding(
            "semantic_trap",
            _line_for_offset(clean, match.start()),
            match.group(1),
            "Stack/heap mismatch: `T x = new T()` is invalid; use `T* x = new T()` or stack construction.",
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
    runtime_mode: str = "project",
) -> list[dict[str, Any]]:
    """Validate Enma code for unknown symbols."""
    if language not in SUPPORTED_LANGUAGES:
        return [_finding("unsupported_language", 0, language,
                         f"unsupported language: {language}; use enma")]

    findings: list[dict[str, Any]] = []
    if language == "enma":
        findings.extend(_validate_enma_semantics(code))
        findings.extend(_validate_enma_lifecycle(code))
        findings.extend(_validate_call_shapes(code, index, language))
    user_funcs = {name for name, _ in extract_function_defs(code, language)}
    if extra_user_functions:
        user_funcs.update(extra_user_functions)
    language_builtins = LANGUAGE_BUILTIN_CALLS.get(language, set())
    forbidden_calls = FORBIDDEN_CALLS_BY_LANGUAGE.get(language, {})
    forbidden_types = FORBIDDEN_TYPES_BY_LANGUAGE.get(language, {})
    unsupported_symbols = load_unsupported_symbols()
    deprecated_symbols = load_deprecated_symbols()
    known_types = known_type_names(index)
    known_functions = known_function_names(index)
    known_methods = known_method_names(index)

    for name, line in extract_calls(code, language):
        if name in user_funcs:
            continue
        if name in unsupported_symbols and name not in known_functions and name not in known_methods:
            findings.append(_finding(
                "unsupported_symbol",
                line,
                name,
                unsupported_symbols[name],
                suggestions=lookup_symbol(index, name).get("suggestions", [])[:5],
            ))
            continue

        if name in deprecated_symbols:
            meta = deprecated_symbols[name]
            replacement = meta.get("replacement", "")
            message = f"{name} is deprecated" + (f"; use {replacement}" if replacement else "")
            findings.append(_finding("deprecated_symbol", line, name, message, replacement=replacement, reason=meta.get("reason", "")))
            continue

        if runtime_mode == "script_execute" and (name.startswith("gui_") or name in ENMA_MODULE_HINTS.get("thread", set())):
            findings.append(_finding(
                "runtime_mode_unsupported",
                line,
                name,
                "Perception script/execute does not register GUI/thread addons; use a project script instead.",
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
            meta = symbol_metadata(name)
            meta_permissions = list(meta.get("permissions", [])) if isinstance(meta.get("permissions", []), list) else []
            rule_permissions = permissions_for_symbol(name)
            for perm in _dedupe([*rule_permissions, *[str(p) for p in meta_permissions]]):
                if perm not in code:
                    findings.append(_finding(
                        "permission_required",
                        line,
                        name,
                        f"{name} requires {perm}; declare or document that permission before use.",
                        permission=perm,
                    ))
            sentinel = meta.get("return_sentinel")
            has_guard = name.startswith("fs_read") and "fs_file_exists" in code
            if sentinel and not has_guard and re.search(rf"=\s*{name}\s*\(", code):
                findings.append(_finding(
                    "unchecked_failure_sentinel",
                    line,
                    name,
                    f"{name} can signal failure with {sentinel}; check documented failure modes before trusting the value.",
                    sentinel=sentinel,
                ))
            required_context = meta.get("requires_context")
            if required_context and runtime_mode == "script_execute":
                findings.append(_finding(
                    "wrong_context",
                    line,
                    name,
                    f"{name} requires {required_context}; script_execute may not provide that context.",
                    requires_context=required_context,
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
