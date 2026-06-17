#!/usr/bin/env python3
"""High-level change summary between two PE binary versions (patch-day prep).

Answers one question before you commit an afternoon to a game update: *how
much did this binary actually change?* This is not a byte-by-byte diff —
Diaphora and radiff2 already do function-level matching. This tool hashes
fixed-size blocks of each named section and uses multiset comparison to report
the share of content that survived the patch, was replaced, was added, or was
removed. From that it classifies the .text section as a RECOMPILE (sigs likely
survive, offsets shifted), a REFACTOR (some sigs survive), or a MAJOR_CHANGE
(assume full re-RE), and recommends whether the patch-day playbook applies.

Run it first; run tools/offset-diff.py second to confirm the specific sigs.

Usage:
    python3 binary-diff-summary.py --old old.exe --new new.exe
    python3 binary-diff-summary.py --old old.exe --new new.exe --sections .text,.rdata
    python3 binary-diff-summary.py --old old.exe --new new.exe --block-size 4096
    python3 binary-diff-summary.py --old old.exe --new new.exe --json

Block comparison is content-based, not positional: a recompile shifts every
block's file offset but leaves the block bytes intact, so positional diffing
would falsely report 100% changed. Matching by hash reveals the survivors.
"""
import sys, struct, os, json, argparse, hashlib
from collections import Counter

# .text classifier thresholds (block-level identical %, raw-size delta %).
RECOMPILE_MIN_SAME = 70.0
RECOMPILE_MAX_DELTA = 1.0
REFACTOR_MIN_SAME = 30.0
MAJOR_MAX_DELTA = 10.0


def read_u16(d, o): return struct.unpack_from('<H', d, o)[0]
def read_u32(d, o): return struct.unpack_from('<I', d, o)[0]


def get_sections(data):
    """Minimal PE parser — returns list of (name, offset, size) tuples."""
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
        rsize = read_u32(data, s + 16)
        raddr = read_u32(data, s + 20)
        sections.append((name, raddr, rsize))
    return sections


def block_hashes(blob, block_size):
    """Hash non-sliding block_size windows. 8-byte SHA1 prefix = cheap block ID."""
    return Counter(
        hashlib.sha1(blob[i:i + block_size]).digest()[:8]
        for i in range(0, len(blob), block_size)
    )


def pct(n, total):
    return round(100.0 * n / total, 1) if total else 0.0


def diff_section(old_blob, new_blob, block_size):
    """Multiset block comparison for one section. Buckets sum to max(old,new)."""
    old_c = block_hashes(old_blob, block_size)
    new_c = block_hashes(new_blob, block_size)
    old_total = sum(old_c.values())
    new_total = sum(new_c.values())
    identical = sum((old_c & new_c).values())   # min-intersection: surviving content
    new_only = new_total - identical             # blocks present only in new
    removed_only = old_total - identical         # blocks present only in old
    changed = min(new_only, removed_only)        # paired replacements (modified)
    net_new = new_only - changed                 # genuine additions (growth)
    net_removed = removed_only - changed         # genuine deletions (shrink)
    total = max(old_total, new_total)
    return {
        'old_size': len(old_blob),
        'new_size': len(new_blob),
        'size_delta': len(new_blob) - len(old_blob),
        'old_blocks': old_total,
        'new_blocks': new_total,
        'identical': identical,
        'changed': changed,
        'new': net_new,
        'removed': net_removed,
        'pct_identical': pct(identical, total),
        'pct_changed': pct(changed, total),
        'pct_new': pct(net_new, total),
        'pct_removed': pct(net_removed, total),
    }


def size_delta_pct(d):
    """Magnitude of raw-size change as % of old section size."""
    return abs(d['size_delta']) / d['old_size'] * 100.0 if d['old_size'] else 0.0


def classify_text(d):
    """RECOMPILE / REFACTOR / MAJOR_CHANGE from .text block survival + size drift."""
    same = d['pct_identical']
    delta = size_delta_pct(d)
    if same < REFACTOR_MIN_SAME or delta > MAJOR_MAX_DELTA:
        return 'MAJOR_CHANGE'
    if same >= RECOMPILE_MIN_SAME and delta < RECOMPILE_MAX_DELTA:
        return 'RECOMPILE'
    # 30-70% survived, or high survival with 1-10% size drift: sigs partly hold.
    return 'REFACTOR'


ACTIONS = {
    'RECOMPILE': 'Offsets shifted, sigs likely survive. Patch-day re-sig viable; '
                 'see skill://pcx-patch-day-playbook.',
    'REFACTOR': 'Some sigs survive, many will not. Playbook applies but expect '
                'manual re-anchoring; see skill://pcx-patch-day-playbook.',
    'MAJOR_CHANGE': 'Block survival too low for a patch-day pass. Assume full '
                    're-RE; the playbook is insufficient on its own.',
}


def build_report(old_data, old_secs, new_data, new_secs, want, block_size):
    """Diff every requested section common to either binary; classify .text."""
    old_map = {n: (r, s) for n, r, s in old_secs}
    new_map = {n: (r, s) for n, r, s in new_secs}
    names = [n for n, _, _ in new_secs] + [n for n, _, _ in old_secs if n not in new_map]
    if want:
        names = [n for n in names if n in want]
    sections = []
    classification = None
    for name in names:
        o_r, o_s = old_map.get(name, (0, 0))
        n_r, n_s = new_map.get(name, (0, 0))
        d = diff_section(old_data[o_r:o_r + o_s], new_data[n_r:n_r + n_s], block_size)
        d['name'] = name
        if name == '.text':
            classification = classify_text(d)
            d['class'] = classification
        sections.append(d)
    tot = sum(max(s['old_blocks'], s['new_blocks']) for s in sections)
    same = sum(s['identical'] for s in sections)
    if classification is None:
        # No .text in scope — fall back to overall survival for the verdict.
        overall = pct(same, tot)
        classification = ('RECOMPILE' if overall >= RECOMPILE_MIN_SAME
                          else 'REFACTOR' if overall >= REFACTOR_MIN_SAME
                          else 'MAJOR_CHANGE')
    summary = {
        'pct_identical': pct(same, tot),
        'pct_changed': round(100.0 - pct(same, tot), 1),
        'classification': classification,
        'recommended_action': ACTIONS[classification],
    }
    return {'sections': sections, 'summary': summary}


def fmt_delta(d):
    return f"{'+' if d >= 0 else '-'}{abs(d)}"


def print_report(report, old_name, new_name):
    print(f"OLD: {old_name}")
    print(f"NEW: {new_name}")
    print()
    hdr = (f"{'SECTION':<10}{'OLD':>11}{'NEW':>11}{'DELTA':>11}"
           f"{'%SAME':>8}{'%CHG':>8}{'%NEW':>8}{'%DEL':>8}  CLASS")
    print(hdr)
    print('-' * len(hdr))
    for s in report['sections']:
        print(f"{s['name']:<10}{s['old_size']:>11}{s['new_size']:>11}"
              f"{fmt_delta(s['size_delta']):>11}"
              f"{s['pct_identical']:>8}{s['pct_changed']:>8}"
              f"{s['pct_new']:>8}{s['pct_removed']:>8}  {s.get('class', '-')}")
    sm = report['summary']
    print()
    print(f"Overall: {sm['pct_identical']}% identical, {sm['pct_changed']}% changed")
    print(f"Verdict: {sm['classification']}")
    print(f"Action:  {sm['recommended_action']}")


def load_binary(path):
    with open(path, 'rb') as f:
        data = f.read()
    secs = get_sections(data)
    if secs is None:
        print(f"Error: {path} is not a valid PE file", file=sys.stderr)
        sys.exit(1)
    return data, secs


def main():
    ap = argparse.ArgumentParser(description='High-level diff summary between two PE versions')
    ap.add_argument('--old', required=True, help='old PE binary')
    ap.add_argument('--new', required=True, help='new PE binary')
    ap.add_argument('--sections', help='comma-separated section names (default: all)')
    ap.add_argument('--block-size', type=int, default=4096, help='block size in bytes (default 4096)')
    ap.add_argument('--json', action='store_true', help='machine-readable output')
    args = ap.parse_args()

    for p in (args.old, args.new):
        if not os.path.isfile(p):
            print(f"Error: {p} not found", file=sys.stderr)
            sys.exit(1)
    if args.block_size < 1:
        print("Error: --block-size must be >= 1", file=sys.stderr)
        sys.exit(1)

    want = {n.strip() for n in args.sections.split(',')} if args.sections else None
    old_data, old_secs = load_binary(args.old)
    new_data, new_secs = load_binary(args.new)
    report = build_report(old_data, old_secs, new_data, new_secs, want, args.block_size)
    if not report['sections']:
        print("Error: no matching sections to compare", file=sys.stderr)
        sys.exit(1)

    if args.json:
        report['old_binary'] = os.path.basename(args.old)
        report['new_binary'] = os.path.basename(args.new)
        report['block_size'] = args.block_size
        print(json.dumps(report, indent=2))
    else:
        print_report(report, os.path.basename(args.old), os.path.basename(args.new))


if __name__ == '__main__':
    main()
