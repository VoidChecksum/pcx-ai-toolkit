#!/usr/bin/env python3
from __future__ import annotations
"""Scan a PE binary for anti-debug surfaces and report findings.

Defensive RE tool — flags techniques the binary uses to detect debuggers,
so the analyst knows what to expect or handle before attaching.

Detects: direct-check imports (IsDebuggerPresent / NtQueryInformationProcess
/ CheckRemoteDebuggerPresent), PEB-walk byte patterns (fs:[30h] / gs:[60h]),
NtGlobalFlag heap-flag checks, RDTSC timing loops, INT 2D / INT 3 abuse,
hardware-breakpoint manipulation (Get/SetThreadContext + CONTEXT_DEBUG_REGISTERS),
VEH/SEH chain manipulation, debugger process-name scans, debugger window-class scans.

Usage:
    python3 anti-debug-scanner.py <binary>
    python3 anti-debug-scanner.py <binary> --json
    python3 anti-debug-scanner.py <binary> --category timing,peb
"""
import sys
import struct
import os
import json
import argparse
import re
import subprocess


# ── Detection tables ──────────────────────────────────────────────────────────

DIRECT_CHECK_IMPORTS = {
    'IsDebuggerPresent', 'CheckRemoteDebuggerPresent',
    'NtQueryInformationProcess', 'ZwQueryInformationProcess',
    'NtSetInformationThread', 'ZwSetInformationThread',
    'DbgUiRemoteBreakin', 'DbgBreakPoint', 'DbgUserBreakPoint',
}
TIMING_IMPORTS = {
    'GetTickCount', 'GetTickCount64', 'QueryPerformanceCounter',
    'GetSystemTimeAsFileTime', 'timeGetTime',
}
HANDLER_HIJACK_IMPORTS = {
    'AddVectoredExceptionHandler', 'RemoveVectoredExceptionHandler',
    'SetUnhandledExceptionFilter', 'RaiseException',
}
WINDOW_ENUM_IMPORTS = {
    'FindWindowA', 'FindWindowW', 'FindWindowExA', 'FindWindowExW',
    'EnumWindows', 'GetWindowTextA', 'GetWindowTextW',
}
PROCESS_ENUM_IMPORTS = {
    'CreateToolhelp32Snapshot', 'Process32First', 'Process32FirstW',
    'Process32Next', 'Process32NextW', 'EnumProcesses', 'OpenProcess',
}
THREAD_CTX_IMPORTS = {
    'GetThreadContext', 'SetThreadContext', 'Wow64GetThreadContext',
    'Wow64SetThreadContext',
}
ENV_PROBE_IMPORTS = {
    'OutputDebugStringA', 'OutputDebugStringW',
    'BlockInput', 'SwitchDesktop', 'GetForegroundWindow',
}

# Categories used in --category filtering and severity scoring
CATEGORIES = {
    'imports_direct':      ('Direct debugger-presence checks',  'STRONG'),
    'imports_timing':      ('Timing-based detection imports',   'INFO'),
    'imports_handler':     ('Exception-handler manipulation',   'SUSPICIOUS'),
    'imports_window':      ('Window enumeration imports',       'INFO'),
    'imports_process':     ('Process enumeration imports',      'INFO'),
    'imports_threadctx':   ('Thread-context (HW BP) imports',   'SUSPICIOUS'),
    'imports_env':         ('Debugger-environment probes',      'INFO'),
    'peb':                 ('PEB-relative byte patterns',       'SUSPICIOUS'),
    'ntglobalflag':        ('NtGlobalFlag heap-flag check',     'STRONG'),
    'timing':              ('RDTSC timing-pair patterns',       'SUSPICIOUS'),
    'int2d':               ('INT 2D / INT 3 abuse patterns',    'SUSPICIOUS'),
    'hwbp_context':        ('Debug-register CONTEXT manipulation', 'STRONG'),
    'veh_chain':           ('VEH chain manipulation',           'SUSPICIOUS'),
    'debugger_strings':    ('Known debugger process names',     'STRONG'),
    'window_class_strings':('Known debugger window classes',    'STRONG'),
}

DEBUGGER_PROCESS_STRINGS = [
    'ollydbg.exe', 'x32dbg.exe', 'x64dbg.exe', 'ida.exe', 'ida64.exe',
    'idaq.exe', 'idaq64.exe', 'idaw.exe', 'idaw64.exe', 'windbg.exe',
    'ghidra', 'cheatengine.exe', 'cheatengine-x86_64.exe',
    'processhacker.exe', 'procexp.exe', 'procmon.exe', 'fiddler.exe',
    'httpdebuggerui.exe', 'wireshark.exe', 'apimonitor', 'scylla',
    'pe-sieve', 'lordpe.exe', 'immunitydebugger.exe', 'binaryninja',
]

# Window class names debuggers register. ALL entries must be >= 5 chars to avoid
# substring noise on short tokens like "ID" (which matches everywhere).
DEBUGGER_WINDOW_CLASSES = [
    'OLLYDBG', 'WinDbgFrameClass', 'Zeta Debugger', 'Rock Debugger',
    'ImmunityDebugger', 'IDA View', 'IDA Window',
]

# PEB-walk byte signatures
PEB_PATTERNS = [
    (b'\x64\xa1\x30\x00\x00\x00',                 'fs:[30h]  (32-bit PEB)'),
    (b'\x65\x48\x8b\x04\x25\x60\x00\x00\x00',     'gs:[60h]  (64-bit PEB)'),
    (b'\x65\x48\x8b\x0c\x25\x60\x00\x00\x00',     'gs:[60h]  (64-bit PEB, RCX form)'),
]


# ── PE parser imports ─────────────────────────────────────────────────────────
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.lib.pe_parse import (
    parse_pe as _parse_pe, rva_to_off, read_cstr, read_u16, read_u32, read_u64
)

def parse_pe(data: bytes) -> dict:
    pe = _parse_pe(data)
    pe['import_dir_rva'] = pe['import_dir'][0]
    return pe

def text_sections(pe: dict) -> list[dict]:
    return [s for s in pe['sections'] if s['exec'] and s['rsize']]


# ── Import table walk ────────────────────────────────────────────────────────

def collect_imports(data, pe):
    """Return set of (dll_name_lower, function_name) tuples."""
    out = set()
    rva = pe['import_dir_rva']
    if not rva:
        return out
    off = rva_to_off(rva, pe['sections'])
    if off is None:
        return out
    ptr_sz = 8 if pe['pe64'] else 4
    ord_bit = 0x8000000000000000 if pe['pe64'] else 0x80000000
    fmt = '<Q' if pe['pe64'] else '<I'

    i = 0
    while True:
        desc_off = off + i * 20
        if desc_off + 20 > len(data):
            break
        oft = read_u32(data, desc_off + 0)        # OriginalFirstThunk
        name_rva = read_u32(data, desc_off + 12)
        ft = read_u32(data, desc_off + 16)        # FirstThunk
        if oft == 0 and name_rva == 0 and ft == 0:
            break
        i += 1
        dll_off = rva_to_off(name_rva, pe['sections']) if name_rva else None
        dll = read_cstr(data, dll_off).lower() if dll_off is not None else '?'

        thunk_rva = oft if oft else ft
        thunk_off = rva_to_off(thunk_rva, pe['sections'])
        if thunk_off is None:
            continue
        j = 0
        while True:
            t_off = thunk_off + j * ptr_sz
            if t_off + ptr_sz > len(data):
                break
            t = struct.unpack_from(fmt, data, t_off)[0]
            if t == 0:
                break
            j += 1
            if t & ord_bit:                      # ordinal import — skip names
                continue
            ibn_off = rva_to_off(t & 0xFFFFFFFF, pe['sections'])
            if ibn_off is None:
                continue
            fn = read_cstr(data, ibn_off + 2)
            if fn:
                out.add((dll, fn))
    return out


# ── Detection routines ───────────────────────────────────────────────────────

def detect_imports(imports):
    """Return list of (category, detail, severity) tuples from import names."""
    found = {cat: [] for cat in CATEGORIES if cat.startswith('imports_')}
    by_table = [
        ('imports_direct',    DIRECT_CHECK_IMPORTS),
        ('imports_timing',    TIMING_IMPORTS),
        ('imports_handler',   HANDLER_HIJACK_IMPORTS),
        ('imports_window',    WINDOW_ENUM_IMPORTS),
        ('imports_process',   PROCESS_ENUM_IMPORTS),
        ('imports_threadctx', THREAD_CTX_IMPORTS),
        ('imports_env',       ENV_PROBE_IMPORTS),
    ]
    for cat, table in by_table:
        for dll, fn in imports:
            if fn in table:
                found[cat].append(f'{dll}!{fn}')
    out = []
    for cat, hits in found.items():
        if not hits:
            continue
        _label, sev = CATEGORIES[cat]
        out.append((cat, ', '.join(sorted(set(hits))), sev))
    return out


def detect_peb_patterns(data, pe):
    """Search executable sections for PEB-walk byte signatures."""
    out = []
    peb_hits_off = []
    for s in text_sections(pe):
        blob = data[s['raddr']:s['raddr'] + s['rsize']]
        for pat, label in PEB_PATTERNS:
            idx = 0
            while True:
                idx = blob.find(pat, idx)
                if idx == -1:
                    break
                rva = s['vaddr'] + idx
                peb_hits_off.append((s, idx, blob, label))
                out.append(('peb',
                            f'{label} at {s["name"]}+0x{idx:X} (rva 0x{rva:X})',
                            CATEGORIES['peb'][1]))
                idx += 1
    # NtGlobalFlag follow-up check: look for CMP imm8/imm32 with 0x70 within 64B
    for s, idx, blob, label in peb_hits_off:
        window = blob[idx:idx + 64]
        if b'\x83' in window and b'\x70' in window:
            # rough heuristic: CMP r/m32, imm8 (0x83 /7) followed by 0x70
            if re.search(rb'\x83[\xf8-\xff]\x70', window):
                out.append(('ntglobalflag',
                            f'PEB+NtGlobalFlag(0x70) check near {s["name"]}+0x{idx:X}',
                            CATEGORIES['ntglobalflag'][1]))
    return out


def detect_rdtsc_pairs(data, pe):
    """Two RDTSC (0F 31) instructions within 256 bytes = classic timing measure."""
    out = []
    for s in text_sections(pe):
        blob = data[s['raddr']:s['raddr'] + s['rsize']]
        hits = [i for i in range(len(blob) - 1) if blob[i] == 0x0F and blob[i+1] == 0x31]
        for a, b in zip(hits, hits[1:]):
            if 0 < (b - a) <= 256:
                out.append(('timing',
                            f'RDTSC pair at {s["name"]}+0x{a:X} -> +0x{b:X} (gap {b-a}B)',
                            CATEGORIES['timing'][1]))
    return out


def detect_int_abuse(data, pe):
    """INT 2D (CD 2D) and standalone INT 3 (CC) outside likely prologues."""
    out = []
    for s in text_sections(pe):
        blob = data[s['raddr']:s['raddr'] + s['rsize']]
        # INT 2D — almost always anti-debug
        idx = 0
        while True:
            idx = blob.find(b'\xCD\x2D', idx)
            if idx == -1:
                break
            out.append(('int2d',
                        f'INT 2D at {s["name"]}+0x{idx:X}',
                        CATEGORIES['int2d'][1]))
            idx += 1
        # CC alignment padding is legitimate (MSVC pads function gaps with INT 3).
        # Only flag when a RET is followed by a LONG run of CC — 12+ bytes is
        # well beyond any normal alignment and suggests deliberate fill or
        # an anti-debug stunt. Severity stays INFO.
        for m in re.finditer(rb'(?:\xC3|\xC2..)\xCC{12,}', blob):
            out.append(('int2d',
                        f'long INT 3 fill after RET at {s["name"]}+0x{m.start()+1:X}',
                        'INFO'))
    return out


def detect_hwbp_context(data, pe, imports):
    """Get/SetThreadContext + CONTEXT_DEBUG_REGISTERS (0x10010) literal in .text."""
    imp_names = {fn for _dll, fn in imports}
    has_ctx_imports = bool(imp_names & THREAD_CTX_IMPORTS)
    if not has_ctx_imports:
        return []
    # CONTEXT_DEBUG_REGISTERS = CONTEXT_AMD64 (0x100000) | 0x10 = 0x100010
    # For x86: CONTEXT_DEBUG_REGISTERS = 0x10010
    out = []
    needles = [
        (b'\x10\x00\x01\x00', 'CONTEXT_DEBUG_REGISTERS (x86)'),
        (b'\x10\x00\x10\x00', 'CONTEXT_DEBUG_REGISTERS (x64)'),
    ]
    for s in text_sections(pe):
        blob = data[s['raddr']:s['raddr'] + s['rsize']]
        for pat, label in needles:
            idx = blob.find(pat)
            if idx != -1:
                out.append(('hwbp_context',
                            f'{label} literal at {s["name"]}+0x{idx:X}; paired with thread-context import',
                            CATEGORIES['hwbp_context'][1]))
    return out


def detect_veh_chain(imports):
    imp_names = {fn for _dll, fn in imports}
    if {'AddVectoredExceptionHandler', 'RemoveVectoredExceptionHandler'} <= imp_names:
        return [('veh_chain',
                 'AddVectoredExceptionHandler + RemoveVectoredExceptionHandler '
                 '(handler-shuffle pattern)',
                 CATEGORIES['veh_chain'][1])]
    return []


def detect_debugger_strings(data):
    """Scan raw data for debugger process/window-class strings (ASCII + UTF-16LE)."""
    out = []
    lower = data.lower()
    for name in DEBUGGER_PROCESS_STRINGS:
        if name.encode('ascii') in lower:
            out.append(('debugger_strings',
                        f'string ref: "{name}"', CATEGORIES['debugger_strings'][1]))
        # UTF-16LE (interleaved zero bytes), lowercased
        wide = b''.join(c.encode('ascii') + b'\x00' for c in name)
        if wide in lower:
            out.append(('debugger_strings',
                        f'wstring ref: "{name}"', CATEGORIES['debugger_strings'][1]))
    for cls in DEBUGGER_WINDOW_CLASSES:
        if cls.encode('ascii') in data:
            out.append(('window_class_strings',
                        f'window class: "{cls}"',
                        CATEGORIES['window_class_strings'][1]))
        wide = b''.join(c.encode('ascii') + b'\x00' for c in cls)
        if wide in data:
            out.append(('window_class_strings',
                        f'window class (wide): "{cls}"',
                        CATEGORIES['window_class_strings'][1]))
    return out


# ── Orchestration ────────────────────────────────────────────────────────────

def scan(path, want_categories=None):
    with open(path, 'rb') as f:
        data = f.read()
    pe = parse_pe(data)
    imports = collect_imports(data, pe)

    findings = []
    findings += detect_imports(imports)
    findings += detect_peb_patterns(data, pe)
    findings += detect_rdtsc_pairs(data, pe)
    findings += detect_int_abuse(data, pe)
    findings += detect_hwbp_context(data, pe, imports)
    findings += detect_veh_chain(imports)
    findings += detect_debugger_strings(data)

    if want_categories:
        findings = [f for f in findings if f[0] in want_categories]

    summary = {sev: 0 for sev in ('STRONG', 'SUSPICIOUS', 'INFO')}
    for _cat, _detail, sev in findings:
        summary[sev] += 1
    return {
        'binary': path, 'pe64': pe['pe64'],
        'findings': [{'category': c, 'detail': d, 'severity': s}
                     for c, d, s in findings],
        'summary': summary,
    }


def print_report(result):
    print(f'File: {result["binary"]}  ({"x64" if result["pe64"] else "x86"})')
    by_cat = {}
    for f in result['findings']:
        by_cat.setdefault(f['category'], []).append(f)
    if not by_cat:
        print('\nNo anti-debug surfaces detected.')
        return
    for cat, items in by_cat.items():
        label, _default_sev = CATEGORIES.get(cat, (cat, 'INFO'))
        print(f'\n[{cat}]  {label}  ({len(items)} finding{"s" if len(items) != 1 else ""})')
        for it in items:
            print(f'  {it["severity"]:<10}  {it["detail"]}')
    s = result['summary']
    print(f'\nSummary: {s["STRONG"]} STRONG, {s["SUSPICIOUS"]} SUSPICIOUS, {s["INFO"]} INFO')


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_name = 'anti-debug-scanner.exe' if os.name == 'nt' else 'anti-debug-scanner'
    binary_path = os.path.join(base_dir, 'bin', bin_name)
    if os.path.exists(binary_path):
        try:
            res = subprocess.run([binary_path] + sys.argv[1:])
            sys.exit(res.returncode)
        except Exception:
            pass

    p = argparse.ArgumentParser(description='Scan a PE for anti-debug surfaces')
    p.add_argument('binary', help='path to PE file')
    p.add_argument('--json', action='store_true', help='emit JSON instead of text')
    p.add_argument('--category', default='',
                   help='comma-separated category filter (e.g. timing,peb,ntglobalflag)')
    args = p.parse_args()
    cats = set(c.strip() for c in args.category.split(',') if c.strip()) or None
    if not os.path.isfile(args.binary):
        print(f'error: not a file: {args.binary}', file=sys.stderr)
        sys.exit(2)
    result = scan(args.binary, want_categories=cats)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)


if __name__ == '__main__':
    main()
