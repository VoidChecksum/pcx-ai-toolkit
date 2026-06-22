#!/usr/bin/env python3
from __future__ import annotations
"""Analyze VMProtect-protected PE files and recommend tooling/workflows.

Detects VMProtect presence, estimates the version/variant (1/2/3/Ultra),
locates VM entry stubs, flags anti-debug and virtualization artifacts, and
suggests the appropriate open-source tooling (backengineering/vmp2, NoVmp,
x64dbg ScyllaHide plugin, etc.) for authorized research.

Usage:
    python3 analyze-vmprotect.py <binary>
    python3 analyze-vmprotect.py --json <binary>
    python3 analyze-vmprotect.py --run-vmemu --out unpacked.bin <binary>

All analysis is read-only on the disk file unless --run-vmemu is used, in
which case an external vmemu executable is invoked to produce an unpacked
memory dump. You must supply a legitimately obtained vmemu binary and only
run it on software you own or are authorized to test.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.lib.pe_parse import parse_pe, rva_to_off, read_u32

# Section names strongly associated with VMProtect
VMP_SECTIONS = (b'.vmp0', b'.vmp1', b'.vmp2', b'.vmp3', b'.vmp4')

# Byte patterns of interest
PATTERNS = {
    'vmp_entry_call': (b'\x68....\xe8', 'VMP-style entry: PUSH imm32; CALL rel32'),
    'vmp_entry_jmp':  (b'\x68....\xe9', 'VMP-style entry: PUSH imm32; JMP rel32'),
    'rdtsc':          (b'\x0f\x31', 'RDTSC timing check'),
    'int2d':          (b'\xcd\x2d', 'INT 2D SEH debug detection'),
    'peb_debug_x64':  (b'\x64\x48\x8b\x04\x25\x60\x00\x00\x00', 'PEB.BeingDebugged access (x64)'),
    'peb_debug_x86':  (b'\x64\xa1\x30\x00\x00\x00', 'PEB.BeingDebugged access (x86)'),
    'cpuid':          (b'\x0f\xa2', 'CPUID (hypervisor/VM detection)'),
}


def regex_escape_bytes(pat: bytes) -> str:
    """Convert a byte pattern with '.' wildcards to a bytes regex."""
    return b''.join(b'.' if b == 0x2e else re.escape(bytes([b])) for b in pat).decode('latin-1')


def find_pattern_all(data: bytes, pattern: bytes) -> list[int]:
    """Find all occurrences of a byte pattern."""
    hits = []
    start = 0
    while True:
        idx = data.find(pattern, start)
        if idx == -1:
            break
        hits.append(idx)
        start = idx + 1
    return hits


def entropy(data: bytes) -> float:
    """Shannon entropy of a byte chunk (0..8)."""
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    total = len(data)
    ent = 0.0
    for c in counts:
        if c == 0:
            continue
        p = c / total
        ent -= p * math.log2(p)
    return ent


def analyze(filepath: str, run_vmemu: bool = False, vmemu_out: str | None = None) -> dict[str, Any]:
    with open(filepath, 'rb') as f:
        data = f.read()

    pe = parse_pe(data)

    result: dict[str, Any] = {
        'file': os.path.basename(filepath),
        'size': len(data),
        'arch': 'x64' if pe['pe64'] else 'x86',
        'vmprotect_detected': False,
        'version_hint': 'unknown',
        'sections': [],
        'vm_entries': [],
        'indicators': [],
        'recommendations': [],
        'vmemu_result': None,
    }

    vmp_sections = []
    for sec in pe['sections']:
        raw_name = sec['name'].encode('ascii', errors='replace')
        is_vmp = any(s in raw_name for s in VMP_SECTIONS)
        info = {
            'name': sec['name'],
            'virtual_size': sec['vsize'],
            'virtual_addr': sec['vaddr'],
            'raw_size': sec['rsize'],
            'raw_addr': sec['raddr'],
            'exec': sec['exec'],
            'is_vmp': is_vmp,
            'entropy': None,
        }
        if sec['rsize'] > 0:
            chunk = data[sec['raddr']:sec['raddr'] + sec['rsize']]
            info['entropy'] = round(entropy(chunk), 2)
        vmp_sections.append(info)

    result['sections'] = vmp_sections

    if any(s['is_vmp'] for s in vmp_sections):
        result['vmprotect_detected'] = True

    section_names = [s['name'] for s in vmp_sections]
    if '.vmp2' in section_names:
        result['version_hint'] = 'likely VMProtect 2.x (vmp2 tooling applicable)'
    elif '.vmp3' in section_names:
        result['version_hint'] = 'likely VMProtect 3.x (NoVmp / VTIL toolchain recommended)'
    elif '.vmp0' in section_names or '.vmp1' in section_names:
        result['version_hint'] = 'likely VMProtect 1.x or 2.x'
    else:
        result['version_hint'] = 'VMProtect variant unknown (section names absent or non-standard)'

    for sec in pe['sections']:
        if not sec['exec'] or sec['rsize'] == 0:
            continue
        start = sec['raddr']
        end = min(start + sec['rsize'], len(data))
        chunk = data[start:end]

        for pat_name, (pat_bytes, desc) in PATTERNS.items():
            hits = find_pattern_all(chunk, pat_bytes)
            for hit in hits[:5]:
                rva = sec['vaddr'] + hit
                result['indicators'].append({
                    'pattern': pat_name,
                    'description': desc,
                    'section': sec['name'],
                    'file_offset': start + hit,
                    'rva': f"0x{rva:X}",
                })

        entry_hits = []
        for m in re.finditer(regex_escape_bytes(b'\x68....\xe8').encode('latin-1'), chunk):
            entry_hits.append((m.start(), 'call'))
        for m in re.finditer(regex_escape_bytes(b'\x68....\xe9').encode('latin-1'), chunk):
            entry_hits.append((m.start(), 'jmp'))
        for hit, kind in entry_hits[:10]:
            rva = sec['vaddr'] + hit
            result['vm_entries'].append({
                'rva': f"0x{rva:X}",
                'file_offset': start + hit,
                'section': sec['name'],
                'type': f"push_imm32;{kind}",
            })

    import_rva = pe['import_dir'][0]
    if import_rva:
        import_foff = rva_to_off(import_rva, pe['sections'])
        if import_foff is not None:
            off = import_foff
            dlls = []
            while off + 20 <= len(data):
                name_rva = read_u32(data, off + 12)
                if name_rva == 0:
                    break
                name_foff = rva_to_off(name_rva, pe['sections'])
                if name_foff is not None:
                    end = data.find(b'\x00', name_foff, name_foff + 256)
                    dll = data[name_foff:end].decode('ascii', errors='replace') if end > name_foff else ''
                    if dll:
                        dlls.append(dll.lower())
                off += 20
            if any('vmprotect' in d for d in dlls):
                result['indicators'].append({
                    'pattern': 'vmp_dll_name',
                    'description': 'DLL name references VMProtect',
                    'value': [d for d in dlls if 'vmprotect' in d],
                })

    recs = result['recommendations']
    recs.append({
        'tool': 'backengineering/vmp2',
        'use_case': 'VMProtect 2.x unpacking and VM bytecode analysis',
        'note': 'Use vmemu to unpack and produce .vmp2 CFG; vmdevirt recompiles (experimental).',
        'url': 'https://github.com/backengineering/vmp2',
    })
    recs.append({
        'tool': 'x64dbg + ScyllaHide',
        'use_case': 'Anti-debug bypass for live VMProtect debugging',
        'note': 'Enable all ScyllaHide options, set VirtualProtect breakpoint to reach OEP.',
        'url': 'https://github.com/x64dbg/ScyllaHide',
    })
    recs.append({
        'tool': 'NoVmp',
        'use_case': 'VMProtect 3.x static devirtualization',
        'note': 'Lifts VMP bytecode to LLVM IR; requires target RVA.',
        'url': 'https://github.com/can1357/NoVmp',
    })
    recs.append({
        'tool': 'vtil / VTIL-Core',
        'use_case': 'Generic VM lifting and optimization IR',
        'note': 'Alternative to LLVM IR for VM-specific semantics.',
        'url': 'https://github.com/vtil-project/VTIL-Core',
    })

    if run_vmemu and vmemu_out:
        vmemu_path = find_tool('vmemu')
        if vmemu_path:
            try:
                res = subprocess.run(
                    [vmemu_path, '--bin', filepath, '--unpack', '--out', vmemu_out],
                    capture_output=True, text=True, timeout=300,
                )
                result['vmemu_result'] = {
                    'returncode': res.returncode,
                    'stdout': res.stdout,
                    'stderr': res.stderr,
                    'output_file': vmemu_out if os.path.exists(vmemu_out) else None,
                }
            except Exception as e:
                result['vmemu_result'] = {'error': str(e)}
        else:
            result['vmemu_result'] = {
                'error': 'vmemu not found in PATH. Add it to PATH or place next to this script.',
            }

    return result


def find_tool(name: str) -> str | None:
    """Search PATH and the script directory for an executable named `name`."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, name),
        os.path.join(script_dir, name + '.exe'),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    for path in os.environ.get('PATH', '').split(os.pathsep):
        c = os.path.join(path, name)
        if os.path.isfile(c):
            return c
        c = os.path.join(path, name + '.exe')
        if os.path.isfile(c):
            return c
    return None


def print_report(result: dict[str, Any]) -> None:
    print(f"File: {result['file']} ({result['size']:,} bytes, {result['arch']})")
    print(f"VMProtect detected: {'YES' if result['vmprotect_detected'] else 'NO'}")
    print(f"Version hint: {result['version_hint']}")
    print()

    print("Sections:")
    for s in result['sections']:
        flag = '[VMP]' if s['is_vmp'] else '     '
        print(f"  {flag} {s['name']:10s} VS=0x{s['virtual_size']:08X} RS=0x{s['raw_size']:08X} "
              f"entropy={s['entropy']}")

    if result['vm_entries']:
        print(f"\nVM entry stubs found: {len(result['vm_entries'])}")
        for e in result['vm_entries'][:10]:
            print(f"  \u2022 {e['rva']} ({e['type']}) in {e['section']}")
        if len(result['vm_entries']) > 10:
            print(f"  ... and {len(result['vm_entries']) - 10} more")

    if result['indicators']:
        print(f"\nIndicators:")
        for i in result['indicators']:
            print(f"  \u2022 {i['description']} at {i.get('rva', 'N/A')} in {i['section']}")

    print("\nRecommendations:")
    for r in result['recommendations']:
        print(f"  \u2022 {r['tool']} \u2014 {r['use_case']}")
        print(f"    {r['note']}")
        print(f"    {r['url']}")

    if result['vmemu_result']:
        print("\nvmemu result:")
        print(json.dumps(result['vmemu_result'], indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description='Analyze VMProtect-protected PE files')
    parser.add_argument('binary', help='PE binary to analyze')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--run-vmemu', action='store_true',
                        help='Invoke external vmemu to unpack (requires vmemu in PATH)')
    parser.add_argument('--out', dest='vmemu_out', default='unpacked.bin',
                        help='Output file for --run-vmemu')
    args = parser.parse_args()

    if not os.path.isfile(args.binary):
        print(f"Error: {args.binary} not found", file=sys.stderr)
        return 1

    result = analyze(args.binary, run_vmemu=args.run_vmemu, vmemu_out=args.vmemu_out)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)

    return 0


if __name__ == '__main__':
    sys.exit(main())
