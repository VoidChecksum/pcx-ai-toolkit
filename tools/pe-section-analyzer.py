#!/usr/bin/env python3
from __future__ import annotations
"""Analyze PE sections for packing, encryption, and anomalies.

Usage:
    python3 pe-section-analyzer.py <binary>
    python3 pe-section-analyzer.py --entropy <binary>    # show per-section entropy
    python3 pe-section-analyzer.py --json <binary>

Checks: section entropy (high = encrypted/compressed), virtual-vs-raw size ratio
(packed sections), anomalous characteristics, empty sections, overlays.
"""
import sys
import struct
import os
import math
import json
import argparse
import subprocess


def entropy(data: bytes) -> float:
    """Shannon entropy of a byte sequence (0.0 = uniform, 8.0 = random)."""
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    length = len(data)
    ent = 0.0
    for f in freq:
        if f > 0:
            p = f / length
            ent -= p * math.log2(p)
    return ent


# ── PE parser imports ─────────────────────────────────────────────────────────
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.lib.pe_parse import parse_pe

def analyze(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    try:
        pe = parse_pe(data)
    except SystemExit as e:
        return {'error': str(e)}

    sections = []
    for s in pe['sections']:
        sec_data = data[s['raddr']:s['raddr'] + s['rsize']] if s['rsize'] > 0 else b''
        ent = entropy(sec_data)

        chars = s['chars']
        flags = []
        if chars & 0x00000020:
            flags.append('CODE')
        if chars & 0x00000040:
            flags.append('IDATA')
        if chars & 0x00000080:
            flags.append('UDATA')
        if chars & 0x20000000:
            flags.append('EXEC')
        if chars & 0x40000000:
            flags.append('READ')
        if chars & 0x80000000:
            flags.append('WRITE')

        anomalies = []
        if ent > 7.0 and s['rsize'] > 1024:
            anomalies.append('HIGH ENTROPY (encrypted/compressed)')
        if ent < 1.0 and s['rsize'] > 1024:
            anomalies.append('VERY LOW ENTROPY (padding/zeros)')
        if s['rsize'] == 0 and s['vsize'] > 0:
            anomalies.append('EMPTY ON DISK (runtime-unpacked)')
        if s['vsize'] > 0 and s['rsize'] > 0 and s['vsize'] > s['rsize'] * 5:
            anomalies.append(f'PACKED (VS/RS ratio: {s["vsize"]/s["rsize"]:.1f}x)')
        if 'EXEC' in flags and 'WRITE' in flags:
            anomalies.append('WRITABLE+EXECUTABLE (SMC / packer)')
        name = s['name']
        if name.startswith('.') and name[1:].isdigit():
            anomalies.append('NUMERIC SECTION NAME (obfuscator)')

        sections.append({
            'name': name,
            'virtual_addr': s['vaddr'],
            'virtual_size': s['vsize'],
            'raw_addr': s['raddr'],
            'raw_size': s['rsize'],
            'entropy': round(ent, 3),
            'flags': flags,
            'anomalies': anomalies,
        })

    # Overlay
    overlay_size = 0
    if sections:
        last_end = max(s['raw_addr'] + s['raw_size'] for s in sections)
        if last_end < len(data):
            overlay_size = len(data) - last_end

    return {
        'file': os.path.basename(filepath),
        'size': len(data),
        'arch': 'x64' if pe['pe64'] else 'x86',
        'sections': sections,
        'overlay_size': overlay_size,
    }


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = 'pe-section-analyzer.exe' if os.name == 'nt' else 'pe-section-analyzer'
    binary_path = os.path.join(base_dir, 'bin', bin_name)
    if os.path.exists(binary_path):
        try:
            res = subprocess.run([binary_path] + sys.argv[1:])
            sys.exit(res.returncode)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description='PE section analyzer')
    parser.add_argument('binary', help='PE binary to analyze')
    parser.add_argument('--entropy', action='store_true', help='Show entropy bar graph')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    result = analyze(args.binary)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    if 'error' in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"File: {result['file']} ({result['size']:,} bytes, {result['arch']})")
    print()

    hdr = f"{'Name':<12s} {'VAddr':>10s} {'VSize':>10s} {'RSize':>10s} {'Entropy':>8s} {'Flags':<24s} Anomalies"
    print(hdr)
    print('─' * len(hdr))

    for s in result['sections']:
        flags_str = ','.join(s['flags'])
        anom_str = '; '.join(s['anomalies']) if s['anomalies'] else '—'

        ent_str = f"{s['entropy']:.3f}"
        if args.entropy:
            bar_len = int(s['entropy'] * 3)  # 0-24 chars for 0-8.0 entropy
            bar = '█' * bar_len + '░' * (24 - bar_len)
            ent_str = f"{s['entropy']:.3f} {bar}"

        print(f"{s['name']:<12s} 0x{s['virtual_addr']:08X} 0x{s['virtual_size']:08X} "
              f"0x{s['raw_size']:08X} {ent_str:>8s} {flags_str:<24s} {anom_str}")

    if result['overlay_size'] > 0:
        print(f"\nOverlay: {result['overlay_size']:,} bytes after last section")

    # Summary
    anomalous = [s for s in result['sections'] if s['anomalies']]
    if anomalous:
        print(f"\n⚠ {len(anomalous)} section(s) with anomalies detected")


if __name__ == '__main__':
    main()
