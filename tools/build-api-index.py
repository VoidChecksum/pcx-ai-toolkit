#!/usr/bin/env python3
"""Build knowledge/pcx-api-index.json from the two upstream PCX API docs.

Authoritative roots:
  1. https://docs.perception.cx/perception/enma/overview  (Enma API surface)
  2. https://docs.perception.cx/perception/angel-script/overview  (AngelScript API surface)

This tool scans the local drift-checked mirrors of those trees under
docs/perception/ (plus the Enma addon docs the Enma API references) and
builds a JSON index of global functions, methods, types, and importable
modules. The index is consumed by tools/symbol-check.py and by the
mcp/pcx-knowledge-mcp server's validate_code tool to catch hallucinated API
names before they reach the compiler.

Usage:
    python tools/build-api-index.py          # regenerate knowledge/pcx-api-index.json
    python tools/build-api-index.py --check # exit 1 if the JSON drifts from tree

Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_PERCEPTION = REPO_ROOT / "docs" / "perception"
DOCS_ENMA = REPO_ROOT / "docs" / "enma"
KNOWLEDGE = REPO_ROOT / "knowledge"
OUT_FILE = KNOWLEDGE / "pcx-api-index.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "lib"))
from pcx_parser import (  # noqa: E402
    _base_type,
    extract_api_signatures,
    extract_calls,
    extract_enma_imports,
)


# ── Hard-wired addon maps from docs/enma/addon-*.md ──────────────────────────
ENMA_MODULE_TYPES: dict[str, set[str]] = {
    "vec": {"vec2", "vec3", "vec4"},
    "color": {"color"},
    "math3d": {"quat", "mat4"},
    "math": {"sin", "cos", "atan2", "atan", "sqrt", "clamp", "lerp", "random",
             "min", "max", "abs", "floor", "ceil", "round", "pow", "log", "exp",
             "fmod", "deg_to_rad", "rad_to_deg", "lerp_angle", "move_toward",
             "ease_in", "ease_out", "ease_in_out", "approx_eq"},
    "strings": {"format", "to_int", "split", "replace", "substr", "find", "length",
                "wstring_from_str", "wstring_to_str", "wstring_from_wchar_ptr", "wstring_from_utf8_ptr"},
    "json": {"json_parse", "json_stringify", "json_value", "json_object", "json_array"},
    "array": {"push", "pop", "sort", "contains", "slice", "resize", "length", "empty"},
    "map": {"map", "imap", "get", "set", "contains", "remove", "keys", "values"},
    "file": {"read_file", "write_file", "read_file_text", "write_file_text",
             "create_directory", "does_file_exist", "query_directory"},
    "thread": {"mutex", "lock_guard", "condition_variable"},
    "bits": {"popcount", "clz", "ctz", "bswap", "rotl", "rotr"},
    "time": {"time_ms", "time_us", "sleep"},
    "atomic": {"aint32", "aint64"},
}

ENMA_BUILTIN_TYPES = {
    "bool", "char", "wchar", "wchar_t", "int8", "int16", "int32", "int64",
    "uint8", "uint16", "uint32", "uint64", "aint8", "aint16", "aint32", "aint64",
    "float32", "float64", "double", "string", "wstring", "void", "null", "auto",
    "proc_t", "array", "hash_set", "sorted_map", "list", "map", "variant",
    "json_value",
}

AS_BUILTIN_TYPES = {
    "bool", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
    "float", "double", "string", "void", "any", "array", "dictionary", "grid",
    "proc_t", "mutex_t", "ws_t", "subtab_t", "panel_t", "checkbox_t",
    "slider_double_t", "slider_int_t", "input_t", "multi_select_t",
    "single_select_t", "keybind_t", "button_t", "color_picker_t",
    "vector2", "vector3", "vector4", "matrix4x4", "quaternion",
    "funcdef",
}

ENMA_GUI_FUNCTIONS = {
    "create_section", "create_sidebar_section", "create_sidebar_separator",
    "section_checkbox", "section_slider_float", "section_slider_int",
    "section_button", "section_text_input", "section_keybind",
    "section_color_picker", "section_dropdown", "section_label",
    "section_separator", "section_combo", "section_combo_box",
    "print_console", "show_toast", "gui_active",
}

ENMA_PROC_METHODS = [
    ("proc", "ru8", ["uint64"]),
    ("proc", "ru16", ["uint64"]),
    ("proc", "ru32", ["uint64"]),
    ("proc", "ru64", ["uint64"]),
    ("proc", "r8", ["uint64"]),
    ("proc", "r16", ["uint64"]),
    ("proc", "r32", ["uint64"]),
    ("proc", "r64", ["uint64"]),
    ("proc", "rf32", ["uint64"]),
    ("proc", "rf64", ["uint64"]),
    ("proc", "rs", ["uint64", "int32"]),
    ("proc", "rws", ["uint64", "int32"]),
    ("proc", "wu8", ["uint64", "uint8"]),
    ("proc", "wu16", ["uint64", "uint16"]),
    ("proc", "wu32", ["uint64", "uint32"]),
    ("proc", "wu64", ["uint64", "uint64"]),
    ("proc", "w8", ["uint64", "int8"]),
    ("proc", "w16", ["uint64", "int16"]),
    ("proc", "w32", ["uint64", "int32"]),
    ("proc", "w64", ["uint64", "int64"]),
    ("proc", "wf32", ["uint64", "float32"]),
    ("proc", "wf64", ["uint64", "float64"]),
    ("proc", "ws", ["uint64", "string"]),
    ("proc", "wws", ["uint64", "string"]),
    ("proc", "rvm", ["uint64", "uint64"]),
    ("proc", "wvm", ["uint64", "array"]),
    ("proc", "read_vec2_fl32", ["uint64"]),
    ("proc", "read_vec2_fl64", ["uint64"]),
    ("proc", "read_vec3_fl32", ["uint64"]),
    ("proc", "read_vec3_fl64", ["uint64"]),
    ("proc", "read_vec4_fl32", ["uint64"]),
    ("proc", "read_vec4_fl64", ["uint64"]),
    ("proc", "read_quat_fl32", ["uint64"]),
    ("proc", "read_quat_fl64", ["uint64"]),
    ("proc", "read_mat4_fl32", ["uint64"]),
    ("proc", "read_mat4_fl64", ["uint64"]),
    ("proc", "write_vec2_fl32", ["uint64", "vec2"]),
    ("proc", "write_vec2_fl64", ["uint64", "vec2"]),
    ("proc", "write_vec3_fl32", ["uint64", "vec3"]),
    ("proc", "write_vec3_fl64", ["uint64", "vec3"]),
    ("proc", "write_vec4_fl32", ["uint64", "vec4"]),
    ("proc", "write_vec4_fl64", ["uint64", "vec4"]),
    ("proc", "write_quat_fl32", ["uint64", "quat"]),
    ("proc", "write_quat_fl64", ["uint64", "quat"]),
    ("proc", "write_mat4_fl32", ["uint64", "mat4"]),
    ("proc", "write_mat4_fl64", ["uint64", "mat4"]),
    ("proc", "r128", ["uint64"]),
    ("proc", "r256", ["uint64"]),
    ("proc", "r512", ["uint64"]),
    ("proc", "w128", ["uint64", "array"]),
    ("proc", "w256", ["uint64", "array"]),
    ("proc", "w512", ["uint64", "array"]),
]

ENMA_VALUE_METHODS = {
    "add", "sub", "scale", "neg", "negate", "dot", "length", "length_sq",
    "distance", "normalize", "lerp", "rotate", "cross", "reflect", "project",
    "angle", "rotate_around", "conjugate", "inverse", "mul", "slerp", "to_euler",
    "get", "set", "transpose", "determinant", "transform_point", "transform_vec3",
    "transform_vec4",
}

LUA_BUILTIN_NAMES = {"main", "on_frame", "on_unload", "on_tick"}


def _find_markdown_code_blocks(text: str) -> list[tuple[str, str]]:
    """Return list of (language_hint, body) for fenced code blocks."""
    out: list[tuple[str, str]] = []
    for m in re.finditer(r'^```\s*(\w*)\s*\n(.*?)\n```', text, re.MULTILINE | re.DOTALL):
        out.append((m.group(1).lower(), m.group(2)))
    return out


def _language_from_path(path: Path) -> str:
    rel = path.relative_to(DOCS_PERCEPTION).as_posix()
    if rel.startswith("angelscript/"):
        return "angelscript"
    if rel.startswith("lua/"):
        return "lua"
    return "enma"


def _collect_docs() -> list[Path]:
    if not DOCS_PERCEPTION.exists():
        return []
    docs: list[Path] = []
    for p in sorted(DOCS_PERCEPTION.rglob("*.md")):
        if p.name in {"changelogs.md", "readme.md"}:
            continue
        docs.append(p)
    return docs


def _collect_enma_addon_docs() -> list[Path]:
    if not DOCS_ENMA.exists():
        return []
    return sorted(DOCS_ENMA.glob("addon-*.md"))


def _extract_import_examples(text: str) -> set[str]:
    """Grab module names from `import "foo";` examples in docs."""
    return set(extract_enma_imports(text))


def _enrich_enma_modules(modules: dict[str, set[str]]) -> None:
    for mod, names in ENMA_MODULE_TYPES.items():
        modules.setdefault(mod, set()).update(names)


def _seed_proc_methods(methods: dict[str, list[dict]]) -> None:
    for parent, name, arg_types in ENMA_PROC_METHODS:
        methods.setdefault(name, []).append({
            "name": name,
            "language": "enma",
            "source": "docs/perception/proc-api.md",
            "kind": "method",
            "parent_type": parent,
            "arity": len(arg_types),
            "arg_types": arg_types,
            "return_type": "",
        })


def _seed_enma_gui_functions(functions: dict[str, list[dict]]) -> None:
    for name in ENMA_GUI_FUNCTIONS:
        functions.setdefault(name, []).append({
            "name": name,
            "language": "enma",
            "source": "docs/perception/gui-api.md",
            "kind": "global",
            "parent_type": None,
            "arity": -1,
            "arg_types": [],
            "return_type": "int64" if name.startswith("create") else "void",
        })


def build_index() -> dict:
    functions: dict[str, list[dict]] = {}
    methods: dict[str, list[dict]] = {}
    types: set[str] = set()
    modules: dict[str, set[str]] = {}

    types.update(ENMA_BUILTIN_TYPES)
    types.update(AS_BUILTIN_TYPES)

    docs = _collect_docs()
    for doc in docs:
        language = _language_from_path(doc)
        text = doc.read_text(encoding="utf-8", errors="ignore")

        if language == "enma":
            for mod in _extract_import_examples(text):
                modules.setdefault(mod, set())

        for lang_hint, body in _find_markdown_code_blocks(text):
            block_language = lang_hint if lang_hint in {"enma", "angelscript", "lua"} else language
            sigs = extract_api_signatures(body, block_language, doc.as_posix())
            for sig in sigs:
                name = sig["name"]
                types.add(_base_type(sig.get("return_type") or ""))
                for at in sig.get("arg_types", []):
                    types.add(_base_type(at))

                if sig["kind"] == "method":
                    methods.setdefault(name, []).append(sig)
                else:
                    functions.setdefault(name, []).append(sig)

    # Scan Enma addon docs for example method calls (vec2.length, quat.normalize, ...)
    for addon_doc in _collect_enma_addon_docs():
        text = addon_doc.read_text(encoding="utf-8", errors="ignore")
        for _lang_hint, body in _find_markdown_code_blocks(text):
            for name, _ in extract_calls(body, "enma"):
                if name in ENMA_VALUE_METHODS:
                    methods.setdefault(name, []).append({
                        "name": name,
                        "language": "enma",
                        "source": addon_doc.as_posix(),
                        "kind": "method",
                        "parent_type": "vec/quat/mat4",
                        "arity": -1,
                        "arg_types": [],
                        "return_type": "",
                    })
                elif name in ENMA_MODULE_TYPES.get("math", set()) or name in ENMA_MODULE_TYPES.get("strings", set()):
                    functions.setdefault(name, []).append({
                        "name": name,
                        "language": "enma",
                        "source": addon_doc.as_posix(),
                        "kind": "global",
                        "parent_type": None,
                        "arity": -1,
                        "arg_types": [],
                        "return_type": "",
                    })

    _enrich_enma_modules(modules)
    _seed_proc_methods(methods)
    _seed_enma_gui_functions(functions)

    for mod, names in modules.items():
        for name in names:
            if name[0].isupper() or name in ENMA_BUILTIN_TYPES:
                types.add(name)
            else:
                if name not in functions:
                    functions[name] = [{
                        "name": name,
                        "language": "enma",
                        "source": f"module:{mod}",
                        "kind": "global",
                        "parent_type": None,
                        "arity": -1,
                        "arg_types": [],
                        "return_type": "",
                    }]

    if (DOCS_ENMA / "lang-basics.md").exists():
        basics = (DOCS_ENMA / "lang-basics.md").read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'`([A-Za-z_][A-Za-z0-9_]*)`', basics):
            types.add(m.group(1))

    module_names = set(modules.keys())

    for name in LUA_BUILTIN_NAMES:
        functions.setdefault(name, []).append({
            "name": name,
            "language": "lua",
            "source": "lua-lifecycle",
            "kind": "global",
            "parent_type": None,
            "arity": -1,
            "arg_types": [],
            "return_type": "",
        })

    types = {t for t in types if t and not t[0].isdigit() and t not in {
        "if", "else", "for", "while", "return", "true", "false", "null", "nil",
        "const", "constexpr", "auto", "void", "null",
    }}

    def sig_list_to_json(d: dict[str, list[dict]]) -> dict[str, list[dict]]:
        return {k: [{kk: vv for kk, vv in s.items() if kk != "line"} for s in v] for k, v in sorted(d.items())}

    return {
        "version": 1,
        "generated_by": "tools/build-api-index.py",
        "functions": sig_list_to_json(functions),
        "methods": sig_list_to_json(methods),
        "types": sorted(types),
        "modules": sorted(module_names),
        "doc_count": len(docs),
    }


def write_index(index: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if JSON drifts from source docs")
    args = ap.parse_args()

    index = build_index()

    if args.check:
        if not OUT_FILE.exists():
            print(f"ERROR: {OUT_FILE} missing; run without --check to generate.", file=sys.stderr)
            return 1
        current = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        if current != index:
            print(f"ERROR: {OUT_FILE} is out of sync with docs. Regenerate with:", file=sys.stderr)
            print(f"    python3 tools/build-api-index.py", file=sys.stderr)
            return 1
        print(f"OK: {OUT_FILE} is up to date ({index['doc_count']} docs, "
              f"{len(index['functions'])} functions, {len(index['methods'])} methods).")
        return 0

    write_index(index, OUT_FILE)
    print(f"Wrote {OUT_FILE}")
    print(f"  docs:        {index['doc_count']}")
    print(f"  functions:   {len(index['functions'])}")
    print(f"  methods:     {len(index['methods'])}")
    print(f"  types:       {len(index['types'])}")
    print(f"  modules:     {len(index['modules'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
