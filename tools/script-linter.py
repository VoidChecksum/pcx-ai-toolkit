#!/usr/bin/env python3
"""Static lint for Enma .em scripts against the game-cheat-guidelines.

Light analysis (regex + brace tracking, NOT a full parser) for the rules that
have low false-positive rates. Deliberately conservative: when a construct is
ambiguous it is left alone. A linter that fires on legitimate code gets ignored.

Rules checked:
    2  uint64 addresses    ERROR  address-producing calls / 64-bit const hex
                                  stored in a non-uint64 type
    8  f-suffix float32    WARN   float32-typed target assigned a bare float64
                                  literal (draw_* args are float64 by design and
                                  are NOT flagged — see guideline #8)
    7  construct per frame INFO   color/vec global built at file scope and not
                                  bound to a config widget
    1  offsets cite source WARN   OFF_/OFFSET_/SIG_ const with no // E-NNN and
                                  no // UNVERIFIED on its line or the line above
    11 GUI for tunables    INFO   numeric/bool global with a literal default,
                                  never reassigned, never bound to a widget

Usage:
    python3 script-linter.py <file.em | dir>
    python3 script-linter.py src/ --rules 2,8,7
    python3 script-linter.py esp.em --severity error,warn
    python3 script-linter.py src/ --json
    python3 script-linter.py src/ --strict     # exit 1 on any WARN too

Exit: 0 = clean, 1 = ERROR (or WARN under --strict), 2 = bad usage.
"""
import sys, re, json, argparse
from pathlib import Path


# ── Rule registry ─────────────────────────────────────────────────────────────

# rule number -> (severity, one-liner). Severity is fixed per rule, not per hit.
RULES = {
    1:  ('WARN',  'offsets cite source'),
    2:  ('ERROR', 'uint64 addresses'),
    7:  ('INFO',  'construct per frame'),
    8:  ('WARN',  'f-suffix on float32'),
    11: ('INFO',  'GUI for every tunable'),
}
ALL_RULES = sorted(RULES)
SEVERITIES = ('ERROR', 'WARN', 'INFO')

# Integer types that must never hold an address (uint64 is the only correct one).
BAD_ADDR_TYPES = {
    'int', 'int8', 'int16', 'int32', 'int64',
    'uint8', 'uint16', 'uint32',
}
# Types rule 11 considers a "tunable" when given a literal default.
NUM_BOOL_TYPES = {
    'bool', 'int', 'int8', 'int16', 'int32', 'int64',
    'uint', 'uint8', 'uint16', 'uint32', 'uint64', 'float32', 'float64',
}
# Stack-struct types that rule 7 wants constructed inline, not cached globally.
GFX_TYPES = {'color', 'vec2', 'vec3', 'vec4'}

# ── Shared regexes ────────────────────────────────────────────────────────────

# const? <type> <name> = <rhs>;
DECL_RE = re.compile(r'^\s*(?:const\s+)?([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*=\s*(.+?);\s*$')
# const <type> <name> = 0x...;
CONST_HEX_RE = re.compile(r'^\s*const\s+([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*=\s*(0x[0-9A-Fa-f]+)\s*;')
# any address-producing call on the RHS
ADDR_CALL_RE = re.compile(
    r'\.ru64\s*\(|\bfind_code_pattern\s*\(|\bbase_address\s*\('
    r'|\bget_module_base\s*\(|\bresolve_rip\s*\(')
# OFF_/OFFSET_/SIG_ named const (rule 1)
OFFSET_DECL_RE = re.compile(r'^\s*const\s+(?:\w+\s+(OFF(?:SET)?_\w+)|string\s+(SIG_\w+))\b')
CITE_RE = re.compile(r'\bE-\d+\b', re.I)
UNVERIFIED_RE = re.compile(r'\bUNVERIFIED\b', re.I)
# bare float64 literal: 1.5 but not 1.5f / 1.5F and not part of a longer number
BARE_FLOAT_RE = re.compile(r'(?<![\w.])\d+\.\d+(?![fF\d])')
# RHS that is a plain literal default (rule 11)
LITERAL_RE = re.compile(r'^(?:true|false|-?\d+\.\d+f?|-?\d+|0x[0-9A-Fa-f]+)$')
# config-widget calls whose arguments are "bound" tunables (rules 7 & 11)
WIDGET_RE = re.compile(
    r'section_(?:slider_\w+|checkbox|combo\w*|color_picker|keybind)\s*\(([^)]*)\)')
IDENT_RE = re.compile(r'\b[A-Za-z_]\w*\b')


# ── Source model ──────────────────────────────────────────────────────────────

def strip_comment(line):
    """Drop a trailing // comment, respecting string literals."""
    out = []
    i, instr = 0, False
    while i < len(line):
        c = line[i]
        if instr:
            out.append(c)
            if c == '\\' and i + 1 < len(line):
                out.append(line[i + 1]); i += 2; continue
            if c == '"':
                instr = False
        elif c == '"':
            instr = True; out.append(c)
        elif c == '/' and i + 1 < len(line) and line[i + 1] == '/':
            break
        else:
            out.append(c)
        i += 1
    return ''.join(out)


def strip_strings(code):
    """Blank out string-literal contents so identifiers inside labels don't match."""
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', code)


def build_model(path):
    """Parse one .em file into the small representation the rules consume.

    raw   - original lines (for evidence-comment lookups, rule 1)
    code  - comment-stripped lines (strings intact)
    nostr - comment- and string-stripped lines (brace/identifier scanning)
    depth - brace depth at the START of each line (0 == file scope)
    bound - identifiers passed to any config-widget call anywhere in the file
    """
    raw = Path(path).read_text(encoding='utf-8', errors='replace').splitlines()
    code = [strip_comment(l) for l in raw]
    nostr = [strip_strings(c) for c in code]
    depth, d = [], 0
    for c in nostr:
        depth.append(d)
        d += c.count('{') - c.count('}')
    bound = set()
    for c in nostr:
        for m in WIDGET_RE.finditer(c):
            bound.update(IDENT_RE.findall(m.group(1)))
    return {'raw': raw, 'code': code, 'nostr': nostr, 'depth': depth, 'bound': bound}


def is_reassigned(name, nostr, decl_idx):
    """True if `name` is written anywhere outside its declaration line."""
    pat = re.compile(r'\b' + re.escape(name) + r'\s*(?:\+\+|--|[+\-*/]?=(?!=))')
    for i, c in enumerate(nostr):
        if i != decl_idx and pat.search(c):
            return True
    return False


# ── Rule checks (each returns (line, rule, message, fix) tuples) ───────────────

def check_rule_2(m):
    """uint64 addresses: address producers and 64-bit hex consts in wrong types."""
    out = []
    for i, line in enumerate(m['nostr']):
        d = DECL_RE.match(line)
        if d and d.group(1) in BAD_ADDR_TYPES and ADDR_CALL_RE.search(d.group(3)):
            out.append((i + 1, 2,
                        f"'{d.group(2)}' holds an address but is typed {d.group(1)}",
                        f"declare it 'uint64 {d.group(2)}'"))
            continue
        h = CONST_HEX_RE.match(line)
        if h and h.group(1) != 'uint64' and int(h.group(3), 16) > 0xFFFFFFFF:
            out.append((i + 1, 2,
                        f"64-bit address constant '{h.group(2)}' typed {h.group(1)}",
                        f"declare it 'const uint64 {h.group(2)}'"))
    return out


def check_rule_8(m):
    """f-suffix: a float32-typed target assigned a bare float64 literal."""
    out = []
    for i, line in enumerate(m['nostr']):
        if not re.match(r'^\s*(?:const\s+)?float32\s+\w+\s*=', line):
            continue
        rhs = line.split('=', 1)[1]
        lit = BARE_FLOAT_RE.search(rhs)
        if lit:
            out.append((i + 1, 8,
                        f"float32 assigned float64 literal {lit.group(0)}",
                        f"write {lit.group(0)}f"))
    return out


def check_rule_7(m):
    """construct per frame: color/vec global built at file scope, not a widget."""
    out = []
    for i, line in enumerate(m['nostr']):
        if m['depth'][i] != 0:
            continue
        d = DECL_RE.match(line)
        if not d or d.group(1) not in GFX_TYPES:
            continue
        name = d.group(2)
        if name in m['bound']:            # a config-bound widget value is legitimate
            continue
        out.append((i + 1, 7,
                    f"{d.group(1)} '{name}' constructed at file scope",
                    "build it inline in on_render — color/vec are free stack structs"))
    return out


def check_rule_1(m):
    """offsets cite source: OFF_/OFFSET_/SIG_ const without // E-NNN or // UNVERIFIED."""
    out = []
    for i, line in enumerate(m['nostr']):
        d = OFFSET_DECL_RE.match(line)
        if not d:
            continue
        name = d.group(1) or d.group(2)
        scope = m['raw'][i] + (' ' + m['raw'][i - 1] if i > 0 else '')
        if CITE_RE.search(scope) or UNVERIFIED_RE.search(scope):
            continue
        out.append((i + 1, 1,
                    f"'{name}' has no evidence citation",
                    "add // E-NNN on this or the line above, or // UNVERIFIED"))
    return out


def check_rule_11(m):
    """GUI for every tunable: literal-default numeric/bool global with no widget."""
    out = []
    for i, line in enumerate(m['nostr']):
        if m['depth'][i] != 0:
            continue
        d = DECL_RE.match(line)
        if not d or d.group(1) not in NUM_BOOL_TYPES:
            continue
        name, rhs = d.group(2), d.group(3).strip()
        if not LITERAL_RE.match(rhs):                 # runtime-resolved, not a tunable
            continue
        if name == 'g_resolved' or name.startswith('g_cached_'):
            continue
        if name.endswith(('_addr', '_ptr', '_offset', '_base', '_size')) \
           or name.startswith(('OFF_', 'OFFSET_', 'SIG_', 'BONE_', 'ENT_', 'ENTITY_', 'MAX_')):
            # Offset / sig / array-stride / capacity constants are not user-tunable.
            continue
        if name in m['bound']:                        # already exposed in the GUI
            continue
        if is_reassigned(name, m['nostr'], i):        # mutated state, not a static default
            continue
        out.append((i + 1, 11,
                    f"tunable '{name}' has no GUI widget",
                    "bind it with a section_* widget, or rename to runtime state"))
    return out


RULE_FUNCS = {1: check_rule_1, 2: check_rule_2, 7: check_rule_7,
              8: check_rule_8, 11: check_rule_11}


# ── Driver ────────────────────────────────────────────────────────────────────

def collect_em_files(path):
    """Resolve a file or directory argument to a sorted list of .em paths."""
    p = Path(path)
    if p.is_dir():
        return sorted(p.rglob('*.em'))
    if p.is_file():
        return [p]
    return []


def lint_file(path, rules):
    """Run the enabled rule checks over one file; return finding dicts, line-sorted."""
    m = build_model(path)
    raw = []
    for num in rules:
        raw.extend(RULE_FUNCS[num](m))
    findings = []
    for line, num, message, fix in raw:
        findings.append({'line': line, 'rule': num, 'severity': RULES[num][0],
                         'message': message, 'fix': fix})
    findings.sort(key=lambda f: (f['line'], f['rule']))
    return findings


def print_text(results):
    """Human-readable report: one line per finding, grouped by file."""
    any_shown = False
    for path, findings in results:
        for f in findings:
            any_shown = True
            line = f"{path}:{f['line']}: {f['severity']} rule-{f['rule']}: {f['message']}"
            if f['fix']:
                line += f"  (--> {f['fix']})"
            print(line)
    if not any_shown:
        print("clean: no findings")


def summarize(results):
    s = {'error': 0, 'warn': 0, 'info': 0, 'files': 0, 'findings': 0}
    for _path, findings in results:
        if findings:
            s['files'] += 1
        for f in findings:
            s[f['severity'].lower()] += 1
            s['findings'] += 1
    return s


def main():
    p = argparse.ArgumentParser(description='Static lint for Enma .em scripts')
    p.add_argument('path', help='.em file or directory to scan')
    p.add_argument('--rules', default='', help='comma list of rule numbers (default: all)')
    p.add_argument('--severity', default='', help='comma list: error,warn,info (default: all)')
    p.add_argument('--json', action='store_true', help='machine-readable output')
    p.add_argument('--strict', action='store_true', help='exit 1 on any WARN, not just ERROR')
    args = p.parse_args()

    rules = ALL_RULES
    if args.rules:
        rules = [int(r) for r in args.rules.split(',') if r.strip()]
        bad = [r for r in rules if r not in RULES]
        if bad:
            print(f"error: unknown rule(s): {','.join(map(str, bad))}", file=sys.stderr)
            sys.exit(2)
    sev_filter = {s.strip().lower() for s in args.severity.split(',') if s.strip()}
    if sev_filter - {'error', 'warn', 'info'}:
        print("error: --severity takes error,warn,info", file=sys.stderr); sys.exit(2)

    files = collect_em_files(args.path)
    if not files:
        print(f"error: no .em files at {args.path}", file=sys.stderr); sys.exit(2)

    results = []
    for f in files:
        findings = lint_file(f, rules)
        if sev_filter:
            findings = [x for x in findings if x['severity'].lower() in sev_filter]
        results.append((str(f), findings))

    summary = summarize(results)
    if args.json:
        files_obj = {path: {'findings': fs} for path, fs in results if fs}
        print(json.dumps({'files': files_obj, 'summary': summary}, indent=2))
    else:
        print_text(results)

    fail = summary['error'] > 0 or (args.strict and summary['warn'] > 0)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
