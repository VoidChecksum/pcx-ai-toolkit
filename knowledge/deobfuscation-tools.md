# Deobfuscation Tools Reference

Tools for defeating binary protection: devirtualizers, unpackers, symbolic execution engines, anti-debug bypass, string extraction, and CFG recovery. Organized by the obfuscation layer they target.

> **Scope:** Authorized security research only. These tools are for analyzing binaries you own, are authorized to test, or are studying in a research/CTF context. See `skill://authorized-security-research`.

---

## Devirtualizers (VM → native/IR)

| Tool | Target VM | Output | Status |
|------|-----------|--------|--------|
| **NoVmp** | VMProtect 3.x | LLVM IR → x86 | Active; best open-source VMP devirtualizer |
| **VMHunt** | VMProtect | Expression trees | Research; trace-based handler semantic extraction |
| **vtil** (Virtual-machine Translation IL) | VMProtect, generic | VTIL IR → optimized | Active; VTIL is a dedicated IR for VM lifting |
| **Oreans UnVirtualizer** | Themida/CV (older) | x86 | Limited on newer versions |
| **Devirtualize** (can1357) | VMProtect 2.x | Lifted IR | Older; VMP 2.x only |
| **VMPAttack** | VMProtect 3.x | Trace analysis | Trace + symbolic; less automated than NoVmp |

### NoVmp — VMProtect Devirtualizer

**What:** Static devirtualizer for VMProtect. Analyzes the VM dispatcher and handler table, identifies the VM architecture, lifts the bytecode to LLVM IR, optimizes it, and optionally recompiles to x86.

**Install:**
```bash
git clone https://github.com/can1357/NoVmp.git
cd NoVmp && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

**Usage:**
```bash
# Lift a VMP-protected function at RVA 0x1234
novmp --input protected.exe --rva 0x1234 --output lifted.ll
# The output is LLVM IR — readable with llvm-dis or optimizable with opt
opt -O2 lifted.ll -o optimized.ll
```

**Source:** [github.com/can1357/NoVmp](https://github.com/can1357/NoVmp)

---

### vtil — VM Translation IL

**What:** A dedicated intermediate language and optimizer for representing VM-lifted code. Designed specifically for the operations VMs perform (push/pop, handler dispatch, virtual register access). More appropriate than LLVM IR for VM analysis because it preserves VM semantics during optimization.

**Source:** [github.com/vtil-project/VTIL-Core](https://github.com/vtil-project/VTIL-Core)

---

## Symbolic Execution Engines

| Tool | Language | Best For |
|------|----------|----------|
| **Triton** | C++ / Python bindings | Precise symbolic execution, constraint solving, taint analysis |
| **Miasm** | Python | IR lifting, symbolic execution, code emulation, CFG recovery |
| **angr** | Python | Full binary analysis framework; symbolic execution + CFG recovery |
| **Unicorn Engine** | C / Python | CPU emulation (not symbolic); trace concrete execution |
| **Qiling** | Python | Higher-level emulation framework built on Unicorn; OS emulation |

### Triton — Dynamic Symbolic Execution

**What:** Pin-based dynamic symbolic execution engine. Hooks instruction execution, builds symbolic expressions for each operation, and can solve constraints (via Z3) to find inputs that reach specific code paths.

**Use for:**
- Evaluating opaque predicates (prove a branch is always-true/always-false)
- Simplifying MBA expressions (`(x ^ y) + 2*(x & y)` → `x + y`)
- Tracing VM handler semantics symbolically
- Deobfuscating control flow by resolving indirect branches

**Install:**
```bash
pip install triton-library
# Or build from source for Pin integration:
git clone https://github.com/JonathanSalwan/Triton.git
```

**Source:** [github.com/JonathanSalwan/Triton](https://github.com/JonathanSalwan/Triton)

---

### Miasm — Reverse Engineering Framework

**What:** Full RE framework with its own IR (Miasm IR), symbolic execution, code emulation, and binary analysis. Particularly strong at lifting x86 to IR and performing transformations (dead code elimination, constant propagation).

**Use for:**
- Lifting x86 instruction traces to a clean IR
- Dead code / junk code elimination via dataflow analysis
- Automated deobfuscation pipelines (script a chain: lift → simplify → emit)
- Handling self-modifying code (emulate the modification, then analyze the result)

**Install:**
```bash
pip install miasm
```

**Source:** [github.com/cea-sec/miasm](https://github.com/cea-sec/miasm)

---

## IDA Pro Plugins

### D-810 — Deobfuscation Plugin

**What:** IDA plugin for deobfuscating code at the microcode level. Handles CFF recovery, opaque predicate removal, MBA simplification, and dead code elimination. Works on IDA's internal microcode representation, so results appear directly in the decompiler output.

**Handles:**
- OLLVM/Hikari control flow flattening
- Opaque predicates (constant-condition branches)
- Instruction substitution patterns
- MBA (Mixed Boolean-Arithmetic) expression simplification
- Dead code paths

**Install:** Copy plugin to IDA plugins directory. Requires IDA 7.4+ with Hex-Rays decompiler.

**Source:** [github.com/joydo/d-810](https://github.com/joydo/d-810)

---

### hrtng — Deobfuscation & Decryption (already installed)

2024 Hex-Rays Plugin Contest winner. Handles string decryption, control flow unflattening, vtable resolution. Already in `re-tools/ida-plugins/hrtng/`.

---

### HashDB — API Hash Resolver

**What:** Resolves API hashes used by malware and protectors for dynamic import resolution. Supports 50+ hash algorithms (ROR13+ADD, CRC32, DJB2, FNV-1a, MurmurHash, etc.). Identifies the algorithm and resolves the hash to the API name.

**Source:** [github.com/OALabs/hashdb-ida](https://github.com/OALabs/hashdb-ida)

---

## Binary Ninja Plugins

### deflat — CFF Recovery

**What:** Symbolic execution-based control flow flattening recovery for Binary Ninja. Identifies the dispatcher, traces state transitions, and rebuilds the original control flow graph.

**Source:** [github.com/cq674350529/deflat](https://github.com/cq674350529/deflat)

---

## Unpacking & Anti-Debug

### ScyllaHide — Anti-Debug Bypass

**What:** Advanced anti-anti-debug plugin for x64dbg, IDA, and OllyDbg. Hooks all known anti-debug APIs and PEB fields to hide the debugger from the target process.

**Bypasses:**
- `IsDebuggerPresent`, `CheckRemoteDebuggerPresent`
- `NtQueryInformationProcess` (ProcessDebugPort, ProcessDebugFlags, ProcessDebugObjectHandle)
- `NtSetInformationThread` (ThreadHideFromDebugger)
- PEB flags: `BeingDebugged`, `NtGlobalFlag`, heap flags
- `NtQuerySystemInformation` (SystemKernelDebuggerInformation)
- Hardware breakpoint detection via `GetThreadContext`
- `OutputDebugString` exception handling
- `int 2d` / `int 3` SEH-based checks
- Timing checks (partial — patches `GetTickCount`/`QueryPerformanceCounter`)

**Install:** x64dbg: download from releases, copy to `plugins/`. IDA: copy to IDA plugins.

**Source:** [github.com/x64dbg/ScyllaHide](https://github.com/x64dbg/ScyllaHide)

---

### Scylla — IAT Reconstruction & Dumping

**What:** Import reconstruction tool. After unpacking a protected binary in memory, Scylla scans for the original import address table, resolves all imports, and produces a clean PE with a valid IAT.

**Use for:** Fixing the import table after dumping a packed/protected binary. The packer redirects imports through stubs — Scylla resolves them back to the real DLL functions.

**Source:** [github.com/NtQuery/Scylla](https://github.com/NtQuery/Scylla)

---

### pe-sieve — Process Hollowing Detector

**What:** Scans a running process for in-memory modifications: hollowed sections, injected code, hooked imports, replaced modules. Dumps the modified regions for analysis.

**Use for:** Detecting what a protector has modified in memory compared to the on-disk PE. Identifies unpacked/decrypted code regions.

**Source:** [github.com/hasherezade/pe-sieve](https://github.com/hasherezade/pe-sieve)

---

## String Extraction

### FLOSS — Obfuscated String Solver

**What:** FireEye Labs Obfuscated String Solver. Extracts strings from binaries even when they're constructed on the stack, XOR-encrypted, or dynamically generated. Uses emulation to execute string-construction routines and capture the cleartext.

**Extracts:**
- Stack strings (character-by-character construction)
- XOR-encrypted strings
- Base64-encoded strings
- Dynamically generated strings (via emulation)

**Install:**
```bash
pip install floss
```

**Source:** [github.com/mandiant/flare-floss](https://github.com/mandiant/flare-floss)

---

## Tracing & Instrumentation

### Intel PIN — Dynamic Instrumentation

**What:** Binary instrumentation framework. Injects analysis code into a running process at the instruction level. Used by Triton for symbolic execution and by custom trace tools.

**Use for:** Building custom VM tracers — instrument the dispatcher to log handler index + operands at every VM cycle.

**Source:** [intel.com/pin](https://www.intel.com/content/www/us/en/developer/articles/tool/pin-a-dynamic-binary-instrumentation-tool.html)

---

### Frida — Dynamic Instrumentation Toolkit

**What:** JavaScript-based dynamic instrumentation. Inject scripts into running processes to hook functions, trace calls, modify behavior. Works on Windows, Linux, macOS, iOS, Android.

**Use for:** Quick API hooking (hook `VirtualProtect` to log unpacking), VM handler tracing (hook the dispatcher), import resolution (hook `GetProcAddress`).

**Install:**
```bash
pip install frida-tools
```

**Source:** [frida.re](https://frida.re/)

---

### DynamoRIO — Dynamic Instrumentation

**What:** Runtime code manipulation framework. Intercepts instruction execution for analysis, profiling, and modification. More performant than PIN for heavy instrumentation.

**Source:** [dynamorio.org](https://dynamorio.org/)

---

## Recommended Workflow by Protector

| Protector | Tool Chain |
|-----------|-----------|
| **VMProtect** | DIE (identify) → ScyllaHide (anti-debug) → NoVmp (devirtualize) → IDA (analyze) |
| **Themida (FISH/TIGER)** | DIE → ScyllaHide → x64dbg trace → handler mapping → manual lift |
| **Themida (EAGLE/SHARK)** | DIE → ScyllaHide → Triton (symbolic trace) → manual analysis |
| **OLLVM CFF** | D-810 (IDA) or deflat (BN) → automatic recovery |
| **OLLVM MBA** | Triton (simplification) or SSPAM → algebraic reduction |
| **Generic packer** | x64dbg → VirtualProtect bp → Scylla dump + IAT fix |
| **API hashing** | HashDB (IDA) → resolve all hashes in one pass |
| **Stack strings** | FLOSS → automated extraction |
| **Custom VM** | x64dbg/HyperDbg trace → Triton/Miasm lift → manual handler mapping |
