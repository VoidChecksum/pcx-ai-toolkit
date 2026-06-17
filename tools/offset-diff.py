#!/usr/bin/env python3
"""Diff named offsets between two PE binary versions (patch-day triage).

Scans both an old and a new binary for a list of named byte signatures,
resolves RIP-relative matches, and reports which offsets moved, stayed put,
disappeared, or appeared. Use after a game update to see at a glance which
sigs survived the patch and how far the rest shifted.

Usage:
    python3 offset-diff.py --old old.exe --new new.exe --sigs sigs.json
    python3 offset-diff.py --old old.exe --new new.exe --sigs sigs.json --json

sigs.json is a list of named signatures:
    [
      {"name": "entity_list", "pattern": "48 8D 0D ?? ?? ?? ??",
       "rip_offset": 3, "insn_len": 7, "kind": "rip"},
      {"name": "local_player", "pattern": "48 8B 05 ?? ?? ?? ??", "kind": "direct"}
    ]

kind="direct" reports the match RVA; kind="rip" resolves the RIP-relative
displacement to its target RVA. Addresses are version-independent RVAs, never
hardcoded offsets.
"""
import sys, struct, os, json, argparse

IMAGE_SCN_MEM_EXECUTE = 0x20000000


def read_u16(d, o): return struct.unpack_from('<H', d, o)[0]
def read_u32(d, o): return struct.unpack_from('<I', d, o)[0]


def get_sections(data):
    """Minimal PE parser — returns list of section dicts, or None if not PE."""
    if data[:2] != b'MZ':
        return None
    pe_off = read_u32(data, 0x3C)
    if data[pe_off:pe_off+4] != b'PE\x00\x00':
        return None
    coff = pe_off + 4
    num = read_u16(data, coff + 2)
    opt_size = read_u16(data, coff + 16)
    sec_off = coff + 20 + opt_size
    sections = []
    for i in range(num):
        s = sec_off + i * 40
        name = data[s:s+8].rstrip(b'\x00').decode('ascii', errors='replace')
        sections.append({
            'name': name,
            'vaddr': read_u32(data, s + 12),       # RVA
            'rsize': read_u32(data, s + 16),       # raw size
            'raddr': read_u32(data, s + 20),       # raw file offset
            'chars': read_u32(data, s + 36),       # +0x24 characteristics
        })
    return sections


def file_off_to_rva(sec, off):
    """Map a raw file offset inside a section to its RVA."""
    return sec['vaddr'] + (off - sec['raddr'])


def compile_pattern(text):
    """Parse '48 8B ?? ?? ??' into a list of ints / None wildcards."""
    out = []
    for tok in text.split():
        out.append(None if tok == '??' else int(tok, 16))
    return out


def find_matches(data, sec, pat):
    """Yield raw file offsets where pat matches within a section's raw bytes."""
    start, end = sec['raddr'], sec['raddr'] + sec['rsize']
    plen = len(pat)
    i = start
    while i <= end - plen:
        for j, b in enumerate(pat):
            if b is not None and data[i + j] != b:
                break
        else:
            yield i
        i += 1


def scan_sig(data, sections, sig):
    """Scan all executable sections for one sig. Returns list of hit dicts."""
    pat = compile_pattern(sig['pattern'])
    hits = []
    for sec in sections:
        if not (sec['chars'] & IMAGE_SCN_MEM_EXECUTE):
            continue
        for off in find_matches(data, sec, pat):
            rva = file_off_to_rva(sec, off)
            hit = {'file_off': off, 'rva': rva, 'resolved': rva}
            if sig.get('kind') == 'rip':
                disp_off = off + sig['rip_offset']
                disp = struct.unpack_from('<i', data, disp_off)[0]
                hit['resolved'] = rva + sig['insn_len'] + disp
            hits.append(hit)
    return hits


def shex(n):
    return f"{'-' if n < 0 else '+'}0x{abs(n):X}"


def addr_str(hit):
    if hit is None:
        return '-'
    if hit['resolved'] != hit['rva']:
        return f"0x{hit['rva']:X}->0x{hit['resolved']:X}"
    return f"0x{hit['rva']:X}"


def classify(old_hits, new_hits):
    """Compare hit lists for one sig and return (status, delta_or_None)."""
    if len(old_hits) > 1:
        return 'MULTIPLE_HITS_OLD', None
    if len(new_hits) > 1:
        return 'MULTIPLE_HITS_NEW', None
    if old_hits and not new_hits:
        return 'LOST_IN_NEW', None
    if new_hits and not old_hits:
        return 'NEW_IN_NEW', None
    if not old_hits and not new_hits:
        return 'LOST_IN_NEW', None
    delta = new_hits[0]['resolved'] - old_hits[0]['resolved']
    return ('UNCHANGED' if delta == 0 else 'MOVED'), delta


def diff(old_data, new_data, old_secs, new_secs, sigs):
    offsets, summary = [], {'moved': 0, 'unchanged': 0, 'lost': 0}
    for sig in sigs:
        old_hits = scan_sig(old_data, old_secs, sig)
        new_hits = scan_sig(new_data, new_secs, sig)
        status, delta = classify(old_hits, new_hits)
        offsets.append({
            'name': sig['name'],
            'kind': sig.get('kind', 'direct'),
            'old': old_hits[0] if len(old_hits) == 1 else None,
            'new': new_hits[0] if len(new_hits) == 1 else None,
            'delta': shex(delta) if delta is not None else None,
            'status': status,
        })
        if status == 'MOVED':
            summary['moved'] += 1
        elif status == 'UNCHANGED':
            summary['unchanged'] += 1
        elif status == 'LOST_IN_NEW':
            summary['lost'] += 1
    return offsets, summary


def print_table(result):
    rows = result['offsets']
    print(f"OLD: {result['old_binary']}")
    print(f"NEW: {result['new_binary']}")
    print()
    hdr = f"{'NAME':<22}{'KIND':<8}{'OLD':<26}{'NEW':<26}{'DELTA':<14}STATUS"
    print(hdr)
    print('-' * len(hdr))
    for r in rows:
        print(f"{r['name']:<22}{r['kind']:<8}"
              f"{addr_str(r['old']):<26}{addr_str(r['new']):<26}"
              f"{(r['delta'] or '-'):<14}{r['status']}")
    s = result['summary']
    print()
    print(f"Summary: {s['moved']} moved, {s['unchanged']} unchanged, {s['lost']} lost")


def load_binary(path):
    with open(path, 'rb') as f:
        data = f.read()
    secs = get_sections(data)
    if secs is None:
        print(f"Error: {path} is not a valid PE file", file=sys.stderr)
        sys.exit(1)
    return data, secs


def main():
    ap = argparse.ArgumentParser(description='Diff named offsets between two PE versions')
    ap.add_argument('--old', required=True, help='old PE binary')
    ap.add_argument('--new', required=True, help='new PE binary')
    ap.add_argument('--sigs', required=True, help='JSON list of named signatures')
    ap.add_argument('--json', action='store_true', help='machine-readable output')
    args = ap.parse_args()

    for p in (args.old, args.new, args.sigs):
        if not os.path.isfile(p):
            print(f"Error: {p} not found", file=sys.stderr)
            sys.exit(1)

    with open(args.sigs) as f:
        sigs = json.load(f)
    if not isinstance(sigs, list) or not sigs:
        print("Error: --sigs must be a non-empty JSON list", file=sys.stderr)
        sys.exit(1)

    old_data, old_secs = load_binary(args.old)
    new_data, new_secs = load_binary(args.new)
    offsets, summary = diff(old_data, new_data, old_secs, new_secs, sigs)
    result = {
        'old_binary': os.path.basename(args.old),
        'new_binary': os.path.basename(args.new),
        'offsets': offsets,
        'summary': summary,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_table(result)


if __name__ == '__main__':
    main()
