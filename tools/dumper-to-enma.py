#!/usr/bin/env python3
"""Convert community dumper output into a ready-to-paste Enma offsets module.

Auto-detects the input format, normalizes it into a table of named offsets and
signatures, and emits an Enma module of `const uint64` / `const string`
constants grouped by category. Drop the result into your project as
`offsets.em` and `import "offsets";` from your feature scripts.

Supported inputs (auto-detected by file shape, override with --format):
    dumper7     Dumper-7 JSON ({"OffsetsInfo": {"GWorld": "0x..", ...}})
                or its Offsets.hpp output (constexpr int32 GWorld = 0x..;)
    il2cpp      Il2CppDumper il2cpp.h / dump.cs — "// RVA: 0x.. Offset: 0x.."
                annotations above declarations, grouped by enclosing struct
    hazedumper  hazedumper config.json (signatures[] + netvars{})
    source2     Source2Gen / generic flat JSON ({"offset_name": value, ...})
    ce          Cheat Engine .CT table (XML <CheatEntry> blocks)

Usage:
    python3 dumper-to-enma.py <dumper-output-file>
    python3 dumper-to-enma.py --format il2cpp dump.cs
    python3 dumper-to-enma.py --module-name sdk --out offsets.em Offsets.hpp
    python3 dumper-to-enma.py --prefix OFFSET_ dumper7.json
    python3 dumper-to-enma.py --json table.ct          # parsed table as JSON

Output uses 2-space indent, LF line endings, and a final newline (.editorconfig).
Unclassifiable input is rejected to stderr with exit code 2.
"""
import sys
import os
import re
import json
import argparse
import xml.etree.ElementTree as ET

# Internal representation: the parsed table is a list of (category, entries)
# groups. `category` is None when the source has no natural grouping; otherwise
# it becomes a "// -- <category> --" header. Each entry is a dict:
#     {"name": str, "kind": "offset"|"sig", "value": int|str}
# offsets carry an int address, signatures carry an IDA-style pattern string.


def _offset(name, value):
    return {"name": name, "kind": "offset", "value": value}


def _sig(name, value):
    return {"name": name, "kind": "sig", "value": value}


def _to_int(s):
    """Parse an offset from a hex string ('0x1A'), decimal, or JSON number.

    Returns None for anything non-numeric (nested objects, empty strings) so
    callers can filter junk keys out of generic dumps.
    """
    if isinstance(s, bool):
        return None
    if isinstance(s, int):
        return s
    s = str(s).strip().rstrip("Ll")
    if not s:
        return None
    try:
        if re.fullmatch(r"0[xX][0-9a-fA-F]+", s):
            return int(s, 16)
        return int(s)
    except ValueError:
        return None


def _ce_addr(s):
    """Parse a Cheat Engine <Address> value (hex; may be 'module.exe+1A2B')."""
    s = s.strip().strip('"')
    if "+" in s:                       # 'game.exe+1A2B3C' -> trailing offset
        s = s.rsplit("+", 1)[1]
    s = s.strip().rstrip("Ll")
    m = re.fullmatch(r"(?:0[xX])?([0-9a-fA-F]+)", s)
    return int(m.group(1), 16) if m else None


def _const_name(raw, prefix):
    """Turn an arbitrary field/description into an Enma constant identifier."""
    name = re.sub(r"[^0-9A-Za-z]+", "_", raw).strip("_").upper()
    if not name:
        name = "UNNAMED"
    if name[0].isdigit():
        name = "_" + name
    return prefix + name


# ── Parsers (each returns a list of (category, entries) groups) ──

def parse_dumper7(text):
    """Dumper-7: JSON OffsetsInfo block, or Offsets.hpp constexpr lines."""
    entries = []
    try:
        obj = json.loads(text)
        info = obj.get("OffsetsInfo", obj) if isinstance(obj, dict) else {}
        for k, v in info.items():
            iv = _to_int(v)
            if iv is not None:
                entries.append(_offset(k, iv))
    except json.JSONDecodeError:
        for m in re.finditer(
            r"constexpr\s+\w+\s+(\w+)\s*=\s*(0x[0-9a-fA-F]+)", text
        ):
            entries.append(_offset(m.group(1), int(m.group(2), 16)))
    return [(None, entries)]


_RVA_RE = re.compile(r"//\s*RVA:\s*0x[0-9a-fA-F]+\s+Offset:\s*(0x[0-9a-fA-F]+)")
_STRUCT_RE = re.compile(r"\b(?:struct|class)\s+([A-Za-z_]\w*)")
_DECL_NAME_RE = re.compile(r"([A-Za-z_]\w*)\s*[(;=]")


def parse_il2cpp(text):
    """Il2CppDumper: capture the declaration named after each RVA/Offset
    comment, grouped under its enclosing struct/class."""
    groups, order, current, pending = {}, [], "Global", None
    for line in text.splitlines():
        sm = _STRUCT_RE.search(line)
        if sm:
            current = sm.group(1)
        m = _RVA_RE.search(line)
        if m:
            pending = int(m.group(1), 16)   # offset from this annotation
            continue
        if pending is not None:
            nm = _DECL_NAME_RE.search(line)
            if nm:
                cat = current or "Global"
                if cat not in groups:
                    groups[cat] = []
                    order.append(cat)
                groups[cat].append(_offset(nm.group(1), pending))
                pending = None              # consumed; wait for the next RVA
    return [(c, groups[c]) for c in order]


def parse_hazedumper(obj):
    """hazedumper: signatures[] -> string sigs, netvars{} -> uint64 offsets."""
    out = []
    sigs = []
    for s in obj.get("signatures") or []:
        pattern = s.get("sig") or s.get("pattern") or ""
        if pattern:
            sigs.append(_sig(s.get("name", "unnamed"), pattern))
    if sigs:
        out.append(("Signatures", sigs))
    netvars = []
    for k, v in (obj.get("netvars") or {}).items():
        iv = _to_int(v)
        if iv is not None:
            netvars.append(_offset(k, iv))
    if netvars:
        out.append(("Netvars", netvars))
    return out


def parse_generic(obj):
    """Source2Gen / generic flat JSON: {"name": numeric_value, ...}."""
    entries = []
    for k, v in obj.items():
        iv = _to_int(v)
        if iv is not None:
            entries.append(_offset(k, iv))
    return [(None, entries)]


def parse_ce(text):
    """Cheat Engine .CT XML: <CheatEntry><Description>/<Address> -> constants."""
    root = ET.fromstring(text)
    entries = []
    for entry in root.iter("CheatEntry"):
        desc = (entry.findtext("Description") or "").strip().strip('"')
        addr = (entry.findtext("Address") or "").strip()
        if not desc or not addr:
            continue
        val = _ce_addr(addr)
        if val is not None:
            entries.append(_offset(desc, val))
    return [(None, entries)]


def detect(text):
    """Best-effort format detection by file shape. Returns None if unknown."""
    if text.lstrip().startswith("<"):
        return "ce"
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        obj = None
    if isinstance(obj, dict):
        if "OffsetsInfo" in obj:
            return "dumper7"
        if "signatures" in obj or "netvars" in obj:
            return "hazedumper"
        return "source2"
    if re.search(r"//\s*RVA:.*Offset:", text):
        return "il2cpp"
    if re.search(r"constexpr\s+\w+\s+\w+\s*=\s*0x", text):
        return "dumper7"
    return None


def parse(fmt, text):
    if fmt == "dumper7":
        return parse_dumper7(text)
    if fmt == "il2cpp":
        return parse_il2cpp(text)
    if fmt == "hazedumper":
        return parse_hazedumper(json.loads(text))
    if fmt == "source2":
        return parse_generic(json.loads(text))
    if fmt == "ce":
        return parse_ce(text)
    raise ValueError(f"unknown format: {fmt}")


# ── Renderers ──

def render_enma(table, module, src, fmt, prefix):
    """Emit a compilable Enma module. Offset names get `prefix`; signature
    names are always `SIG_`-prefixed. Duplicate identifiers are dropped so the
    module never fails to compile on a redefinition."""
    n_off = sum(1 for _, es in table for e in es if e["kind"] == "offset")
    n_sig = sum(1 for _, es in table for e in es if e["kind"] == "sig")
    lines = [
        f"// {module}.em - generated by dumper-to-enma.py from {src} ({fmt})",
        f"// {n_off} offset(s), {n_sig} signature(s). Regenerate after each "
        f"game update; do not hand-edit.",
        "",
    ]
    seen = set()
    for cat, entries in table:
        body = []
        for e in entries:
            pfx = "SIG_" if e["kind"] == "sig" else prefix
            name = _const_name(e["name"], pfx)
            if name in seen:
                continue
            seen.add(name)
            if e["kind"] == "sig":
                body.append(f'const string {name} = "{e["value"]}";')
            else:
                body.append(f"const uint64 {name} = 0x{e['value']:X};")
        if not body:
            continue
        if cat:
            lines.append(f"// \u2500\u2500 {cat} \u2500\u2500")
        lines.extend(body)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def render_json(table):
    """Emit the normalized table as JSON (offsets as hex strings)."""
    payload = []
    for cat, entries in table:
        if not entries:
            continue
        items = []
        for e in entries:
            value = (f"0x{e['value']:X}" if e["kind"] == "offset"
                     else e["value"])
            items.append({"name": e["name"], "kind": e["kind"], "value": value})
        payload.append({"category": cat, "entries": items})
    return json.dumps(payload, indent=2) + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="Convert community dumper output into an Enma offsets module"
    )
    ap.add_argument("input", help="dumper output file (JSON, .hpp, il2cpp.h, .CT)")
    ap.add_argument(
        "--format", default="auto",
        choices=["auto", "dumper7", "il2cpp", "hazedumper", "source2", "ce"],
        help="input format (default: auto-detect by file shape)",
    )
    ap.add_argument("--module-name", default="offsets",
                    help="Enma module name used in the header (default: offsets)")
    ap.add_argument("--out", help="output file (default: stdout)")
    ap.add_argument("--prefix", default="",
                    help="prefix for offset constant names "
                         "(default: none; signatures always use SIG_)")
    ap.add_argument("--json", action="store_true",
                    help="emit the parsed table as JSON instead of Enma")
    args = ap.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        sys.stderr.write(f"error: cannot read {args.input}: {e}\n")
        sys.exit(2)

    fmt = args.format if args.format != "auto" else detect(text)
    if not fmt:
        sys.stderr.write(
            f"error: cannot classify '{args.input}'; pass --format explicitly\n"
        )
        sys.exit(2)

    try:
        table = parse(fmt, text)
    except (ValueError, json.JSONDecodeError, ET.ParseError) as e:
        sys.stderr.write(f"error: failed to parse {args.input} as {fmt}: {e}\n")
        sys.exit(2)

    if not any(entries for _, entries in table):
        sys.stderr.write(
            f"error: no offsets or signatures found in {args.input} ({fmt})\n"
        )
        sys.exit(2)

    if args.json:
        out = render_json(table)
    else:
        out = render_enma(table, args.module_name,
                          os.path.basename(args.input), fmt, args.prefix)

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        sys.stderr.write(f"wrote {args.out} ({fmt})\n")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
