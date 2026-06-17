#!/usr/bin/env python3
"""Map PE module exports and cross-reference which neighbours import them.

Lists the export table of a PE module (ordinal | name | RVA), decodes a short
hint from MSVC/Itanium mangled names, tags forwarded exports, and — in consumer
mode — scans a directory of PE files to answer "which binary actually pulls in
engine.dll!GetEntityListAddress?" without opening N modules in a disassembler.

Usage:
    python3 module-export-mapper.py engine.dll
    python3 module-export-mapper.py engine.dll --consumers /path/to/game/dir/
    python3 module-export-mapper.py engine.dll --filter Entity
    python3 module-export-mapper.py engine.dll --ordinal-only
    python3 module-export-mapper.py engine.dll --filter Entity --json
"""
import sys, struct, os, json, argparse


def read_u16(d, o): return struct.unpack_from('<H', d, o)[0]
def read_u32(d, o): return struct.unpack_from('<I', d, o)[0]
def read_u64(d, o): return struct.unpack_from('<Q', d, o)[0]


def parse_headers(data):
    """Minimal PE parser — sections + export/import data directories."""
    if data[:2] != b'MZ':
        return None
    pe_off = read_u32(data, 0x3C)
    if data[pe_off:pe_off+4] != b'PE\x00\x00':
        return None
    coff = pe_off + 4
    num_sec = read_u16(data, coff + 2)
    opt_size = read_u16(data, coff + 16)
    opt = coff + 20
    is_64 = read_u16(data, opt) == 0x20B
    dd_off = opt + (112 if is_64 else 96)
    sec_off = opt + opt_size
    sections = []
    for i in range(num_sec):
        s = sec_off + i * 40
        if s + 40 > len(data):
            break
        sections.append({
            'vaddr': read_u32(data, s + 12),
            'vsize': read_u32(data, s + 8),
            'raddr': read_u32(data, s + 20),
            'rsize': read_u32(data, s + 16),
        })
    return {
        'is_64': is_64,
        'sections': sections,
        'export_dir': (read_u32(data, dd_off), read_u32(data, dd_off + 4)),
        'import_dir': (read_u32(data, dd_off + 8), read_u32(data, dd_off + 12)),
    }


def rva_to_off(rva, sections):
    """Translate an RVA to a file offset, or None when it lands in no section."""
    for s in sections:
        if s['vaddr'] <= rva < s['vaddr'] + max(s['vsize'], s['rsize']):
            return rva - s['vaddr'] + s['raddr']
    return None


def read_cstr(data, off, maxlen=512):
    if off is None or off >= len(data):
        return ''
    end = data.find(b'\x00', off, off + maxlen)
    if end < 0:
        end = min(off + maxlen, len(data))
    return data[off:end].decode('ascii', errors='replace')


def mangle_hint(name):
    """Pull the readable identifier out of a mangled name — not a full demangle."""
    if name.startswith('?'):                       # MSVC: ?Name@Class@@...
        end = name.find('@', 1)
        return name[1:end] if end > 1 else name[1:]
    if name.startswith('_Z'):                       # Itanium: _ZN6Engine9GetEntityEv
        s = name[2:]
        if s[:1] == 'N':
            s = s[1:]
        parts, i = [], 0
        while i < len(s) and s[i].isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            n = int(s[i:j])
            parts.append(s[j:j + n])
            i = j + n
        return '::'.join(p for p in parts if p) or None
    return None


def parse_exports(data, headers):
    """Return (module_name, [export records]) from the export data directory."""
    exp_rva, exp_size = headers['export_dir']
    sections = headers['sections']
    base_off = rva_to_off(exp_rva, sections)
    if not exp_rva or base_off is None:
        return None, []

    name_rva = read_u32(data, base_off + 12)
    ord_base = read_u32(data, base_off + 16)
    num_func = read_u32(data, base_off + 20)
    num_name = read_u32(data, base_off + 24)
    eat_off = rva_to_off(read_u32(data, base_off + 28), sections)
    name_tbl = rva_to_off(read_u32(data, base_off + 32), sections)
    ord_tbl = rva_to_off(read_u32(data, base_off + 36), sections)
    module = read_cstr(data, rva_to_off(name_rva, sections)) or '?'

    # Build ordinal-index -> exported-name map from the name pointer tables.
    names = {}
    if name_tbl is not None and ord_tbl is not None:
        for i in range(num_name):
            n_off = rva_to_off(read_u32(data, name_tbl + i * 4), sections)
            idx = read_u16(data, ord_tbl + i * 2)
            names[idx] = read_cstr(data, n_off)

    exports = []
    if eat_off is None:
        return module, exports
    for i in range(num_func):
        func_rva = read_u32(data, eat_off + i * 4)
        if func_rva == 0:                           # empty EAT slot
            continue
        forward = None
        if exp_rva <= func_rva < exp_rva + exp_size:  # RVA inside the export dir
            forward = read_cstr(data, rva_to_off(func_rva, sections))
        nm = names.get(i)
        exports.append({
            'ordinal': ord_base + i,
            'name': nm,
            'rva': '0x%X' % func_rva,
            'forward': forward,
            'hint': mangle_hint(nm) if nm else None,
            'consumers': [],
        })
    return module, exports


def imported_from(data, target_names):
    """Names + ordinals this PE imports from the target module (target_names is a
    set of acceptable module names, lowercase — on-disk basename and internal name)."""
    headers = parse_headers(data)
    if not headers:
        return set(), set()
    imp_rva, _ = headers['import_dir']
    sections, is_64 = headers['sections'], headers['is_64']
    off = rva_to_off(imp_rva, sections)
    if not imp_rva or off is None:
        return set(), set()

    step = 8 if is_64 else 4
    high = 0x8000000000000000 if is_64 else 0x80000000
    names, ords = set(), set()
    for _ in range(4096):                           # cap walk on malformed tables
        if off + 20 > len(data):
            break
        oft = read_u32(data, off)
        mod_rva = read_u32(data, off + 12)
        ft = read_u32(data, off + 16)
        if oft == 0 and mod_rva == 0 and ft == 0:
            break
        if read_cstr(data, rva_to_off(mod_rva, sections)).lower() in target_names:
            toff = rva_to_off(oft or ft, sections)
            for _ in range(8192):
                if toff is None or toff + step > len(data):
                    break
                val = read_u64(data, toff) if is_64 else read_u32(data, toff)
                if val == 0:
                    break
                if val & high:
                    ords.add(val & 0xFFFF)
                else:
                    ibn = rva_to_off(val, sections)
                    if ibn is not None:
                        names.add(read_cstr(data, ibn + 2))
                toff += step
        off += 20
    return names, ords


def attach_consumers(target_path, module, consumer_dir, exports):
    """Populate each export's consumer list by scanning sibling PE files."""
    target_names = {os.path.basename(target_path).lower(), module.lower()}
    by_name = {e['name']: e for e in exports if e['name']}
    by_ord = {e['ordinal']: e for e in exports}
    target_abs = os.path.abspath(target_path)
    for entry in sorted(os.listdir(consumer_dir)):
        if not entry.lower().endswith(('.dll', '.exe')):
            continue
        path = os.path.join(consumer_dir, entry)
        if not os.path.isfile(path) or os.path.abspath(path) == target_abs:
            continue
        try:
            with open(path, 'rb') as f:
                names, ords = imported_from(f.read(), target_names)
        except OSError:
            continue
        for nm in names:
            if nm in by_name:
                by_name[nm]['consumers'].append(entry)
        for od in ords:
            if od in by_ord:
                by_ord[od]['consumers'].append(entry)
    for e in exports:
        e['consumers'] = sorted(set(e['consumers']))


def select(exports, flt, ordinal_only):
    out = exports
    if ordinal_only:
        out = [e for e in out if e['name'] is None]
    if flt:
        low = flt.lower()
        out = [e for e in out
               if (e['name'] and low in e['name'].lower())
               or (e['hint'] and low in e['hint'].lower())]
    return out


def print_table(module, exports, with_consumers):
    print(f"MODULE: {module}  ({len(exports)} exports shown)")
    print(f"{'ORD':>6}  {'NAME':<40}  {'RVA':<10}  "
          + ("CONSUMERS" if with_consumers else "HINT"))
    for e in exports:
        name = e['name'] or '<ordinal-only>'
        if e['forward']:
            name = f"{name}  FORWARD -> {e['forward']}"
        if with_consumers:
            cons = e['consumers']
            tail = f"{len(cons)}  {', '.join(cons)}" if cons else "0"
        else:
            tail = e['hint'] or ''
        print(f"{e['ordinal']:>6}  {name:<40}  {e['rva']:<10}  {tail}")


def main():
    ap = argparse.ArgumentParser(description='Map PE module exports and consumers')
    ap.add_argument('binary', help='PE module whose exports to list')
    ap.add_argument('--consumers', metavar='DIR',
                    help='scan DIR of .dll/.exe and cross-reference importers')
    ap.add_argument('--filter', metavar='PATTERN',
                    help='only exports whose name/hint contains PATTERN (icase)')
    ap.add_argument('--ordinal-only', action='store_true',
                    help='only pure-ordinal exports (no name)')
    ap.add_argument('--json', action='store_true', help='machine-readable output')
    args = ap.parse_args()

    if not os.path.isfile(args.binary):
        print(f"Error: {args.binary} not found", file=sys.stderr)
        sys.exit(1)
    with open(args.binary, 'rb') as f:
        data = f.read()
    headers = parse_headers(data)
    if headers is None:
        print(f"Error: {args.binary} is not a valid PE", file=sys.stderr)
        sys.exit(1)

    module, exports = parse_exports(data, headers)
    if not exports:
        # Not an error — most EXEs have no export directory by design.
        out = {'module': args.binary, 'exports': [], 'note': 'no export directory'}
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(f'{args.binary}: no export directory (binary has no exports).')
        sys.exit(0)
    if args.consumers:
        if not os.path.isdir(args.consumers):
            print(f"Error: {args.consumers} is not a directory", file=sys.stderr)
            sys.exit(1)
        attach_consumers(args.binary, module, args.consumers, exports)

    shown = select(exports, args.filter, args.ordinal_only)
    if args.json:
        print(json.dumps({'module': module, 'exports': shown}, indent=2))
    else:
        print_table(module, shown, bool(args.consumers))


if __name__ == '__main__':
    main()
