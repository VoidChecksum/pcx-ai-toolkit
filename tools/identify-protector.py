#!/usr/bin/env python3
"""Identify binary protectors by PE section names, imports, and byte signatures.

Usage:
    python3 identify-protector.py <binary>
    python3 identify-protector.py --json <binary>

Detects: VMProtect, Themida/WinLicense, Code Virtualizer, Enigma, Obsidium,
ASPack, UPX, NSPack, Petite, MPRESS, PECompact, .NET obfuscators.
"""
import sys
import struct
import os
import json
import argparse

SECTION_SIGS = {
    b'.vmp0':    'VMProtect',
    b'.vmp1':    'VMProtect',
    b'.vmp2':    'VMProtect',
    b'.themida': 'Themida / WinLicense',
    b'.winlice': 'Themida / WinLicense',
    b'Themida':  'Themida (legacy)',
    b'.cv\x00':  'Code Virtualizer',
    b'.enigma':  'Enigma Protector',
    b'.enigm':   'Enigma Protector',
    b'.obsidiu': 'Obsidium',
    b'.aspack':  'ASPack',
    b'.adata':   'ASPack',
    b'UPX0':     'UPX',
    b'UPX1':     'UPX',
    b'UPX2':     'UPX',
    b'.nsp0':    'NSPack',
    b'.nsp1':    'NSPack',
    b'.petite':  'Petite',
    b'.MPRESS':  'MPRESS',
    b'.perplex': 'Perplex',
    b'PEC2':     'PECompact',
    b'.sforce':  'StarForce',
    b'.denuvo':  'Denuvo',
}

IMPORT_SIGS = {
    'VBoxDispatch': 'VirtualBox API (VM detection target)',
    'VMwareVMControl': 'VMware API (VM detection target)',
}

ANTI_DEBUG_IMPORTS = [
    'IsDebuggerPresent',
    'CheckRemoteDebuggerPresent',
    'NtQueryInformationProcess',
    'NtSetInformationThread',
    'OutputDebugStringA',
    'GetTickCount',
    'QueryPerformanceCounter',
]


def read_u16(data, off):
    return struct.unpack_from('<H', data, off)[0]

def read_u32(data, off):
    return struct.unpack_from('<I', data, off)[0]

def read_u64(data, off):
    return struct.unpack_from('<Q', data, off)[0]


def parse_pe(data):
    """Minimal PE parser — extract sections, imports, entry point info."""
    if data[:2] != b'MZ':
        return None

    pe_off = read_u32(data, 0x3C)
    if data[pe_off:pe_off+4] != b'PE\x00\x00':
        return None

    coff_off = pe_off + 4
    machine = read_u16(data, coff_off)
    num_sections = read_u16(data, coff_off + 2)
    opt_hdr_size = read_u16(data, coff_off + 16)
    opt_off = coff_off + 20

    is_64 = read_u16(data, opt_off) == 0x20B
    entry_rva = read_u32(data, opt_off + 16)

    # Section headers start after optional header
    sec_off = opt_off + opt_hdr_size
    sections = []
    for i in range(num_sections):
        s = sec_off + i * 40
        name = data[s:s+8]
        vsize = read_u32(data, s + 8)
        vaddr = read_u32(data, s + 12)
        rsize = read_u32(data, s + 16)
        raddr = read_u32(data, s + 20)
        chars = read_u32(data, s + 36)
        sections.append({
            'name': name,
            'name_str': name.rstrip(b'\x00').decode('ascii', errors='replace'),
            'virtual_size': vsize,
            'virtual_addr': vaddr,
            'raw_size': rsize,
            'raw_addr': raddr,
            'characteristics': chars,
        })

    # Extract import names (quick scan — look for import directory)
    imports = []
    if is_64:
        import_rva = read_u32(data, opt_off + 120)  # import table RVA
    else:
        import_rva = read_u32(data, opt_off + 104)

    if import_rva:
        # Convert RVA to file offset
        for sec in sections:
            if sec['virtual_addr'] <= import_rva < sec['virtual_addr'] + sec['virtual_size']:
                import_foff = import_rva - sec['virtual_addr'] + sec['raw_addr']
                # Walk import descriptors
                off = import_foff
                while off + 20 <= len(data):
                    name_rva = read_u32(data, off + 12)
                    if name_rva == 0:
                        break
                    # Resolve name RVA
                    for s2 in sections:
                        if s2['virtual_addr'] <= name_rva < s2['virtual_addr'] + s2['virtual_size']:
                            name_foff = name_rva - s2['virtual_addr'] + s2['raw_addr']
                            end = data.find(b'\x00', name_foff, name_foff + 256)
                            if end > name_foff:
                                imports.append(data[name_foff:end].decode('ascii', errors='replace'))
                            break
                    off += 20

    return {
        'is_64': is_64,
        'machine': machine,
        'entry_rva': entry_rva,
        'sections': sections,
        'imports': imports,
    }


def identify(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    pe = parse_pe(data)
    if pe is None:
        return {'error': 'Not a valid PE file', 'file': filepath}

    results = {
        'file': os.path.basename(filepath),
        'size': len(data),
        'arch': 'x64' if pe['is_64'] else 'x86',
        'entry_rva': f"0x{pe['entry_rva']:X}",
        'sections': len(pe['sections']),
        'imports': len(pe['imports']),
        'protectors': [],
        'indicators': [],
        'anti_debug': [],
    }

    # 1. Section name matching
    for sec in pe['sections']:
        raw_name = sec['name']
        for sig, prot in SECTION_SIGS.items():
            if sig in raw_name:
                results['protectors'].append({
                    'name': prot,
                    'evidence': f"section '{sec['name_str']}'",
                })

        # Packed section heuristic: virtual size >> raw size
        if sec['raw_size'] > 0 and sec['virtual_size'] > sec['raw_size'] * 3:
            results['indicators'].append(
                f"section '{sec['name_str']}' is packed (VS=0x{sec['virtual_size']:X} >> RS=0x{sec['raw_size']:X})"
            )

        # Empty raw size with non-zero virtual = runtime-unpacked
        if sec['raw_size'] == 0 and sec['virtual_size'] > 0:
            results['indicators'].append(
                f"section '{sec['name_str']}' has no raw data (unpacked at runtime)"
            )

    # 2. Import analysis
    for imp in pe['imports']:
        if imp in ANTI_DEBUG_IMPORTS:
            results['anti_debug'].append(imp)
        for sig, prot in IMPORT_SIGS.items():
            if sig in imp:
                results['indicators'].append(f"import '{imp}' → {prot}")

    # 3. Byte signature scan (first 4KB of each executable section)
    for sec in pe['sections']:
        if not (sec['characteristics'] & 0x20000000):  # IMAGE_SCN_MEM_EXECUTE
            continue
        start = sec['raw_addr']
        end = min(start + min(sec['raw_size'], 8192), len(data))
        chunk = data[start:end]

        # VMP entry stub: push imm32; call rel32
        idx = 0
        while idx < len(chunk) - 10:
            if chunk[idx] == 0x68 and chunk[idx+5] in (0xE8, 0xE9):
                results['indicators'].append(
                    f"VMP-style VM entry stub at section '{sec['name_str']}'+0x{idx:X}"
                )
                break
            idx += 1

        # RDTSC pair (anti-debug timing)
        if b'\x0F\x31' in chunk:
            count = chunk.count(b'\x0F\x31')
            if count >= 2:
                results['indicators'].append(
                    f"RDTSC timing check ({count} instances in '{sec['name_str']}')"
                )

        # int 2d (SEH debug detection)
        if b'\xCD\x2D' in chunk:
            results['indicators'].append(
                f"INT 2D (SEH debug detection) in '{sec['name_str']}'"
            )

        # PEB.BeingDebugged access (x64): mov rax, gs:[0x60]
        peb_sig = b'\x64\x48\x8B\x04\x25\x60\x00\x00\x00'
        if peb_sig in chunk:
            results['indicators'].append(
                f"PEB.BeingDebugged access in '{sec['name_str']}'"
            )

    # 4. Overlay detection (data after last section)
    if pe['sections']:
        last = max(pe['sections'], key=lambda s: s['raw_addr'] + s['raw_size'])
        overlay_start = last['raw_addr'] + last['raw_size']
        if overlay_start < len(data):
            overlay_size = len(data) - overlay_start
            results['indicators'].append(f"PE overlay: {overlay_size} bytes after last section")

    # Deduplicate protectors
    seen = set()
    unique = []
    for p in results['protectors']:
        key = p['name']
        if key not in seen:
            seen.add(key)
            unique.append(p)
    results['protectors'] = unique

    return results


def main():
    parser = argparse.ArgumentParser(description='Identify binary protectors')
    parser.add_argument('binary', help='PE binary to analyze')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    if not os.path.isfile(args.binary):
        print(f"Error: {args.binary} not found", file=sys.stderr)
        sys.exit(1)

    result = identify(args.binary)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"File: {result['file']} ({result['size']:,} bytes, {result['arch']})")
    print(f"Entry: {result['entry_rva']}")
    print(f"Sections: {result['sections']}  Imports: {result['imports']}")
    print()

    if result.get('protectors'):
        print("PROTECTORS DETECTED:")
        for p in result['protectors']:
            print(f"  ✓ {p['name']} — {p['evidence']}")
    else:
        print("No known protector sections found.")

    if result.get('indicators'):
        print("\nINDICATORS:")
        for i in result['indicators']:
            print(f"  • {i}")

    if result.get('anti_debug'):
        print(f"\nANTI-DEBUG IMPORTS: {', '.join(result['anti_debug'])}")


if __name__ == '__main__':
    main()
