# VMProtect 2.x Analysis with vmp2

Practical guide for analyzing binaries protected by **VMProtect 2.x** using the
open-source **backengineering/vmp2** toolchain, x64dbg VMProtect/ScyllaHide
plugins, and the `tools/analyze-vmprotect.py` toolkit helper.

> **Scope:** Authorized security research only. Use these tools on binaries you
> own, have explicit permission to test, or are analyzing in a controlled CTF /
> research environment. See `skill://authorized-security-research`.

---

## What is VMProtect 2.x?

VMProtect 2.x virtualizes selected functions by translating x86/x64 machine code
into a custom bytecode executed by a runtime interpreter (the *VM dispatcher*).
Key artifacts:

- **`.vmp0` / `.vmp1` / `.vmp2`** sections containing VM bytecode and metadata.
- **VM entry stubs** at every protected function that push a key/bytecode
  pointer, then `call` or `jmp` into `vmenter`.
- **A dispatch loop** that reads an opcode, decrypts it with a rolling key,
  and jumps through a handler table.
- **Import protection**: each API call is redirected through a small stub that
  resolves at runtime.
- **Anti-debug layer**: `RDTSC`, `INT 2D`, `CPUID`, PEB checks, and
  `NtQueryInformationProcess`/`NtSetInformationThread` tricks.

The `backengineering/vmp2` suite (C++, LLVM/Qt/Unicorn) automates the heavy
lifting:

| Component | Purpose |
|-----------|---------|
| `vmemu` | Unpacks VMP-protected binaries by emulating execution until OEP. |
| `vmdevirt` | Lifts VMP bytecode to a closer-to-native representation (experimental). |
| `vmprofiler` | Profiles and visualizes VM handler coverage. |
| `vmprofiler-cli` | Command-line access to `vmprofiler` analysis. |
| `vmhook` | Hooks VM entry stubs to capture bytecode streams at runtime. |
| `vmassembler` | Assembler/disassembler for VMP bytecode research. |

Source: [github.com/backengineering/vmp2](https://github.com/backengineering/vmp2)

---

## Triage with `tools/analyze-vmprotect.py`

The toolkit ships a stdlib-only Python script that detects VMP artifacts,
suggests a tooling chain, and (optionally) shells out to an external `vmemu`
binary for unpacking.

```bash
# Basic analysis (read-only)
python3 tools/analyze-vmprotect.py target.exe

# JSON output for further automation
python3 tools/analyze-vmprotect.py --json target.exe

# Optional: invoke external vmemu to dump unpacked memory
python3 tools/analyze-vmprotect.py --run-vmemu --out unpacked.bin target.exe
```

The script reports:

- VMP section presence and per-section entropy.
- Estimated VMP version/variant.
- VM entry stubs (`PUSH imm32; CALL/JMP rel32`).
- Anti-debug indicators (`RDTSC`, `INT 2D`, PEB debug checks, `CPUID`).
- Tool recommendations (`vmp2`, `x64dbg+ScyllaHide`, `NoVmp`, `VTIL-Core`).

---

## Workflow: VMP 2.x → Unpacked → Devirtualized

### 1. Identify the Protector

Check sections and strings:

```bash
r2 -nn target.exe
iS
iz~vmp|VMProtect|protect
```

Or use the toolkit script:

```bash
python3 tools/analyze-vmprotect.py --json target.exe | jq '.vmprotect_detected, .version_hint'
```

### 2. Bypass Anti-Debug (Live Debugging)

Use x64dbg with the ScyllaHide plugin:

1. Load target in x64dbg.
2. Plugins → ScyllaHide → Options → check **all** anti-debug bypasses.
3. Set breakpoints on `VirtualProtect` and `NtSetInformationThread`.
4. Run; when `VirtualProtect` hits a large `PAGE_EXECUTE_READ` region on the
   original `.text`, the protector has decrypted/unpacked code.
5. Record the OEP and dump the process with Scylla.

### 3. Unpack with `vmemu`

If you have a legitimately obtained `vmemu` binary:

```bash
vmemu --bin target.exe --unpack --out unpacked.bin
```

This emulates the VMP runtime until the original entry point is reached and
writes a dumped memory image. The toolkit wrapper can do this for you:

```bash
python3 tools/analyze-vmprotect.py --run-vmemu --out unpacked.bin target.exe
```

### 4. Find VM Bytecode Regions and Handlers

After unpacking, locate the `.vmp2` bytecode and the dispatcher:

```bash
r2 -nn unpacked.bin
s section..vmp2
px 256             # inspect first bytes
/V 0f b6 00        # search for dispatcher fetch: movzx eax, byte [rax]
```

Typical dispatcher shape:

```asm
movzx   eax, byte ptr [rcx]      ; fetch next opcode
xor     al, <key_byte>            ; decrypt
and     eax, 0xff
mov     rdx, [handler_table]
jmp     qword ptr [rdx + rax*8]  ; dispatch
```

### 5. Lift / Devirtualize

For VMP 2.x, try `vmdevirt` first:

```bash
vmdevirt --input target.exe --bytecode-rva 0x12345 --output lifted.asm
```

For VMP 3.x, prefer `NoVmp` / `VTIL-Core`:

```bash
novmp --input target.exe --rva 0x12345 --output lifted.ll
opt -O2 lifted.ll -o optimized.ll
```

### 6. Validate the Output

- Compare lifted code against known native implementations of the same logic.
- Re-run in a debugger and ensure function outputs match the original.
- Look for missing side effects (VMP sometimes hides IAT writes or SEH setup).

---

## x64dbg VMProtect Plugin Workflow

Some researchers use a dedicated x64dbg VMProtect plugin to speed up VMP work:

1. **Install** the plugin into `x64dbg\x64\plugins`.
2. **Enable ScyllaHide** to neutralize anti-debug.
3. **Plugins → VMProtect → Trace VM entry** to log every `vmenter` call.
4. **Dump bytecode** to a file for offline analysis with `vmassembler` or
   `vmprofiler-cli`.
5. **Set conditional breakpoints** on handler transitions to capture execution
   traces.

> The plugin interface is tool-specific; refer to its documentation for exact
> menu names. The principle remains: bypass anti-debug → trace VM entries → dump
> bytecode → lift/decode.

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `vmemu` fails immediately | Anti-debug is still active; use ScyllaHide or HyperDbg. |
| Dispatcher not found | VMP version may be 3.x; switch to `NoVmp` / `VTIL-Core`. |
| Lifted output is incomplete | Provide the exact bytecode RVA and ensure the binary is unpacked first. |
| Imports still broken after dump | Reconstruct IAT with Scylla before saving the final executable. |
| Entropy low in `.vmp2` | The section may be uninitialized/padded, or the binary is packed differently. |

---


## 2026 guidance: use vmp2 carefully

The current `backengineering/vmp2` README explicitly warns that identifying
individual VM handlers is brittle and does not scale across VM architecture
changes. Treat vmp2 as valuable VMProtect 2 architecture and workflow knowledge,
not as a dependency to vendor or a guarantee that handler matching alone solves
devirtualization.

For new tooling, prefer the generic strategy in
`knowledge/re-workflows/devirtualization-generic.md`: guided symbolic
evaluation, VM-private constant promotion, constant folding, load/store
propagation, dead-store elimination, branch folding, virtual-IP tracking, and
behavioral validation.
## Tool Matrix

| Goal | Best Tool | Notes |
|------|-----------|-------|
| Detect / triage VMP | `tools/analyze-vmprotect.py` | Stdlib-only, safe, fast. |
| Unpack VMP 2.x | `vmemu` (vmp2) | Requires built `vmp2` suite. |
| Live anti-debug bypass | `x64dbg + ScyllaHide` | Easiest first step. |
| Devirtualize VMP 3.x | `NoVmp` / `VTIL-Core` | Static lifting to LLVM/VTIL IR. |
| VM handler profiling | `vmprofiler` / `vmprofiler-cli` | Coverage and handler statistics. |
| Bytecode disassembly | `vmassembler` | VMP-specific opcodes. |

---

## See Also

- `signatures/obfuscation/protector-patterns.md` — byte patterns for VMP entry, dispatcher, import stubs.
- `knowledge/deobfuscation-tools.md` — broader deobfuscation tool reference.
- `.claude/skills/deobfuscation/SKILL.md` — general deobfuscation methodology.
- `skill://authorized-security-research` — legal/ethical scope.
