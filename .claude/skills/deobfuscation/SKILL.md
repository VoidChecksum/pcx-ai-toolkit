# Deobfuscation — Reversing Protected Binaries

Methodology for reversing binaries protected by commercial obfuscators (Themida/WinLicense, VMProtect, Code Virtualizer), compiler-level obfuscation (LLVM-obfuscator, Hikari, OLLVM), and custom protection schemes (anti-cheat VMs, game-specific packers). Covers the full workflow: identification → classification → layer stripping → devirtualization → verification.

**Always active when analyzing obfuscated or packed binaries.** This skill covers *methodology* — how to approach and work through each protection layer. For tool-specific commands and configurations, see `knowledge/deobfuscation-tools.md`. For protector identification patterns, see `signatures/obfuscation/protector-patterns.md`.

**Prerequisite:** Read `knowledge/obfuscation-taxonomy.md` for per-protector architecture details before starting analysis.

## Trigger
Encountering VM-protected code, control flow flattening, opaque predicates, packed/encrypted sections, anti-debug/anti-VM tricks, Themida/WinLicense, VMProtect, Code Virtualizer, LLVM-obfuscated code, or any binary where the disassembler output is nonsensical.

---

## 1. Identify the Protector Before You Reverse a Single Instruction

**Name the protector, its version, and which protection features are active. Different protectors require fundamentally different approaches — guessing wastes weeks.**

A protected binary tells you what it is if you know where to look:

### Quick Identification

| Signal | What It Means |
|--------|---------------|
| Sections named `.themida`, `.winlice` | Themida / WinLicense (Oreans) |
| Sections named `.vmp0`, `.vmp1`, `.vmp2` | VMProtect |
| Section named `.cv` or `.cvirt` | Code Virtualizer (Oreans) |
| Section named `.enigma1`, `.enigma2` | Enigma Protector |
| Import of `VirtualProtect` + large encrypted `.text` | Generic packer — unpack first |
| `CPUID` + `RDTSC` + `int 2d` clusters near entry | Anti-debug layer (most commercial protectors) |
| Massive switch/computed-goto loop with 50+ cases | VM dispatcher (any virtualizer) |
| Flat CFG: one loop, one switch, state variable | Control flow flattening (LLVM-obf / custom) |

```
# radare2 — quick protector triage
r2 -nn binary.exe
iS                                  # list sections — look for .vmp0, .themida, etc.
ii                                  # imports — anti-debug APIs?
iz~VM\|themida\|protect\|license    # strings — protector artifacts
```

```
# DIE (Detect It Easy) — automated protector detection
die binary.exe
# Output: "VMProtect v3.6.0", "Themida v3.1.x", etc.
```

**Why:** Themida's VM is architecturally different from VMProtect's. The devirtualization tools, trace strategies, and known weaknesses are protector-specific. Starting analysis without knowing which protector you're facing is like debugging without knowing the language.

---

## 2. Strip the Outer Layers First — Anti-Debug, Packing, Encryption

**Commercial protectors wrap protection in layers. Strip from the outside in: anti-debug → unpacking → decryption → then tackle the VM.**

Most protectors stack multiple defenses:

```
Layer 0: Anti-debug / anti-VM checks
Layer 1: Packing / compression (UPX-like or custom)
Layer 2: Import obfuscation (IAT encryption/redirection)
Layer 3: Code mutation (instruction substitution, junk insertion)
Layer 4: Control flow obfuscation (flattening, opaque predicates)
Layer 5: Virtualization (VM bytecode — the inner layer)
```

### Defeating Anti-Debug

Anti-debug checks must be neutralized before you can trace or debug:

| Check | How to Bypass |
|-------|---------------|
| `IsDebuggerPresent` | Patch PEB.BeingDebugged to 0 (`eb poi(fs:[30])+2 0` in WinDbg) |
| `NtQueryInformationProcess(ProcessDebugPort)` | Hook or patch the syscall return |
| `CheckRemoteDebuggerPresent` | Same as above — queries debug port |
| `NtSetInformationThread(ThreadHideFromDebugger)` | Prevent the call or hook it |
| `int 2d` / `int 3` (SEH-based detection) | Step over, not into; or patch to `nop` |
| `RDTSC` timing | Use HyperDbg (hypervisor-level, no timing artifacts) or patch the delta check |
| `CPUID` hypervisor bit | Spoof via hypervisor or patch the test |
| `NtQuerySystemInformation(SystemKernelDebuggerInformation)` | Hook the syscall |
| PEB flags: `NtGlobalFlag`, heap flags | Zero them in the PEB at process start |

**Tool:** ScyllaHide (IDA/x64dbg plugin) automates most anti-debug bypasses — enable all options and most commercial protectors stop detecting the debugger.

### Unpacking

If the `.text` section is encrypted or compressed:

1. **Run to OEP (Original Entry Point):** Set a hardware breakpoint on `VirtualProtect` — the protector must decrypt the code before executing it. When `VirtualProtect(addr, size, PAGE_EXECUTE_READ, ...)` is called on a large region, the unpacked code is at `addr`.
2. **Dump:** Once unpacked in memory, dump the process with Scylla (x64dbg plugin) or pe-sieve.
3. **Fix IAT:** The protector often redirects imports through stubs. Use Scylla's IAT reconstruction or manually resolve the import table.

```
# x64dbg — find OEP via VirtualProtect breakpoint
bp VirtualProtect
run
# When hit: check args — large PAGE_EXECUTE_READ on .text = unpacked
# Step until you reach the original code
# Then: Scylla → OEP = current EIP → IAT Autosearch → Dump
```

**Why:** Trying to devirtualize code that's still packed is pointless — the VM bytecode is itself encrypted. Unpack first, devirtualize second.

---

## 3. Classify the Obfuscation Type — Mutation, Flattening, or Virtualization

**Each type has a different counter. Mutation is cosmetic; flattening is structural; virtualization is semantic. Know which you're facing.**

### Code Mutation (Instruction Substitution)

**What:** Replaces simple instructions with equivalent complex sequences. `xor eax, eax` becomes `push 0; pop eax; sub eax, eax; xor eax, eax; and eax, 0`.

**Counter:** IDA's microcode optimization handles most mutations automatically. hrtng plugin provides deeper mutation simplification. Alternatively, Miasm's symbolic execution normalizes mutated sequences to their canonical form.

**Difficulty:** LOW — mutation doesn't change the logic, just the encoding.

### Junk Code Insertion

**What:** Dead code (instructions whose results are never used) inserted between real instructions to inflate the function and confuse pattern matching.

**Counter:** IDA's optimizer removes dead code during decompilation. For stubborn junk, use Miasm or Triton to symbolically execute and identify instructions with no dataflow contribution to the function's outputs.

**Difficulty:** LOW — junk doesn't affect dataflow analysis.

### Opaque Predicates

**What:** Conditional branches where the condition is always true (or always false) but the compiler can't prove it statically. Creates fake control flow paths that never execute.

**Counter:** Symbolic execution (Triton, angr, Miasm) evaluates the predicate and proves it's constant → dead path is removed. D-810 (IDA plugin) has built-in opaque predicate detection patterns.

**Difficulty:** MEDIUM — requires symbolic reasoning, but well-tooled.

### Control Flow Flattening (CFF)

**What:** All basic blocks are pulled into one flat loop with a dispatcher switch. A state variable determines which block executes next. The original control flow is hidden in the state transitions.

```
ORIGINAL:                    FLATTENED:
A → B → C                   while (true) {
A → D (if condition)           switch (state) {
                                 case 0: A(); state = f(cond); break;
                                 case 1: B(); state = 2; break;
                                 case 2: C(); return; break;
                                 case 3: D(); return; break;
                               }
                             }
```

**Counter:**
1. **D-810** (IDA plugin) — automated CFF recovery; identifies the dispatcher, traces state transitions, rebuilds the original CFG.
2. **deflat** (Binary Ninja plugin) — symbolic execution-based CFF recovery.
3. **Manual:** Identify the state variable, log its values at each iteration via tracing, then reconstruct the transition table.

**Difficulty:** MEDIUM — automated tools handle standard LLVM-obf CFF. Custom dispatchers may need manual work.

### Virtualization (VM-based protection)

**What:** Code is compiled to a custom bytecode for a proprietary virtual machine embedded in the binary. The VM interpreter fetches, decodes, and executes these bytecodes at runtime. The original x86 instructions no longer exist.

**Architecture:**
```
┌──────────────────────────────────────────┐
│ VM Entry (vmenter / vm_dispatcher)        │
│ ├── Fetch: read bytecode[vpc++]           │
│ ├── Decode: map opcode → handler index    │
│ ├── Dispatch: jump to handler[index]      │
│ │   ├── handler_add: pop a,b; push a+b   │
│ │   ├── handler_load: push mem[addr]      │
│ │   ├── handler_store: mem[addr] = pop    │
│ │   ├── handler_jcc: if flag, vpc = imm   │
│ │   └── ... (50-200 handlers)             │
│ └── Loop back to Fetch                    │
└──────────────────────────────────────────┘
```

**Counter (see §4 for detail):**
1. **Trace the VM execution** — log every handler invocation with its operands
2. **Lift the trace to an IR** — reconstruct what the handlers actually compute
3. **Optimize the IR** — constant folding, dead code elimination, deduplication
4. **Recompile or match** — convert back to x86 or understand the logic from the IR

**Difficulty:** HIGH — this is the hardest obfuscation class. Automated devirtualizers exist for known VMs (VMProtect, Themida) but custom VMs require manual analysis.

---

## 4. Devirtualize VM-Protected Code

**The VM has a dispatcher, handlers, a virtual stack, and virtual registers. Find each component, trace the execution, and lift.**

### Step 1: Find the VM Dispatcher

The dispatcher is the core loop. It's the largest function in a virtualized binary, typically 2,000–50,000+ instructions with a massive switch or computed-goto table.

```
# IDA — find the dispatcher by size
# Sort function list by size — the dispatcher is usually the largest
# Or look for a function with 50+ switch cases

# radare2 — find large switches
afl | sort -k2 -rn | head -10    # largest functions
afb @@ fcn.* | grep -c case      # count switch cases per function
```

### Step 2: Identify the VM Components

| Component | What to Look For |
|-----------|-----------------|
| **Virtual PC (VPC)** | Register or memory location incremented after each handler; points into the bytecode stream |
| **Virtual stack (VSP)** | Register used as a stack pointer for the VM's operand stack (often RSI, RDI, or RBP repurposed) |
| **Virtual registers** | Memory region (often on the real stack) used to store the VM's register file |
| **Handler table** | Array of function pointers or a computed-goto table indexed by opcode |
| **Bytecode stream** | Encrypted or plain byte array in a dedicated section (.vmp0, .themida) or embedded in .text |

### Step 3: Trace and Lift

**Option A: Dynamic tracing (works for any VM)**

```
# Trace every handler invocation:
# 1. Set a breakpoint at the dispatcher's switch/goto
# 2. Log: handler_index, VPC, VSP, virtual_regs
# 3. Run the target function
# 4. Post-process the trace to extract the semantic operations

# WinDbg — trace handler dispatch
bp <dispatcher_switch>
.logopen trace.log
# At each hit:
r @rcx; r @rdx; r @rsi     # handler index, VPC, VSP (register assignments vary)
g
# After execution: parse trace.log to extract the handler sequence
```

**Option B: Symbolic execution (more precise, slower)**

```python
# Using Triton or Miasm:
# 1. Emulate the VM dispatcher symbolically
# 2. Each handler resolves to a symbolic operation (add, load, store, jcc)
# 3. The sequence of symbolic operations IS the deobfuscated program
# 4. Optimize with constant folding / dead store elimination
```

**Option C: Tool-specific devirtualizers (fastest when available)**

| VM | Tool | How |
|----|------|-----|
| VMProtect | **NoVmp** | Static devirtualizer; lifts VMP bytecode to LLVM IR, optimizes, outputs x86 |
| VMProtect | **VMHunt** | Trace-based; records handler semantics, reconstructs expressions |
| VMProtect | **vtil** (Virtual-machine Translation IL) | VTIL framework + optimizer for VMP lifting |
| Themida | **Themida devirtualizer scripts** | Community IDA scripts; handler identification + trace lifting |
| Themida | **Oreans UnVirtualizer** | Commercial; limited effectiveness on newer versions |
| Generic | **Triton** | Symbolic execution engine; works on any VM but requires setup |
| Generic | **Miasm** | IR-based analysis framework; symbolic execution + IR lifting |
| Generic | **REVEN** (Tetrane) | Full-system trace replay with symbolic analysis |

### Step 4: Verify the Devirtualization

The devirtualized output must match the original program's behavior:

1. **Unit test:** If you know the function's I/O contract (e.g., "it XORs buffer with key"), call the virtualized version and the devirtualized version with the same input — outputs must match.
2. **Trace comparison:** Run both versions and compare the sequence of memory writes and API calls.
3. **Spot check:** For complex functions, verify key branch points and return values rather than exhaustive comparison.

**Why:** Devirtualization is lossy — optimizers may alter control flow, and some VM handlers have no direct x86 equivalent. Always verify before trusting the output.

---

## 5. Handle Protector-Specific Tricks

**Each commercial protector has unique anti-analysis features beyond basic VM/CFF. Know the tricks for the protector you're facing.**

### Themida / WinLicense (Oreans)

- **FISH / TIGER / DOLPHIN / EAGLE / SHARK VMs:** Multiple VM architectures with different opcode sets. FISH is the oldest (weakest), SHARK is the newest (strongest).
- **Code Replacement:** Original instructions are deleted and replaced with VM calls — there is no "unpacked" version of the code.
- **Anti-dump:** Detects and blocks process dumping by monitoring `NtReadVirtualMemory` on its own sections.
- **Macro VM:** Short instruction sequences (3-10 instructions) are individually virtualized — produces many small VM entries rather than one large one.
- **Counter:** Trace at the handler level; each handler corresponds to ~1-3 original instructions. The handler dispatch pattern is a `jmp [reg*8 + table]` computed goto.

### VMProtect

- **Multiple VM architectures per binary:** VMP can use different VM instances for different functions — each with its own handler table and opcode mapping.
- **Handler mutation:** Handlers are code-mutated (instruction substitution) on top of virtualization — double obfuscation.
- **Bytecode encryption:** The bytecode stream is XOR'd or rolling-key encrypted; decrypted at VM entry.
- **Ultra mode:** VMP Ultra adds nested virtualization — a VM inside a VM. The inner VM's handlers are themselves virtualized by the outer VM.
- **Counter:** NoVmp handles most VMP versions; for Ultra mode, trace the outer VM to recover the inner VM's bytecode, then devirtualize the inner VM separately.

### LLVM-Obfuscator (Hikari, OLLVM, Pluto)

- **Compiler-integrated:** Obfuscation happens at compile time via LLVM passes — the resulting binary has no "protector" to strip, the obfuscation IS the code.
- **Passes:** CFF (bogus control flow + flattening), instruction substitution, string encryption, indirect branching, MBA (Mixed Boolean-Arithmetic expressions).
- **Counter:** D-810 handles CFF + opaque predicates from OLLVM. MBA expressions require algebraic simplification (SSPAM, Triton, or manual pattern matching). String encryption needs runtime extraction — break on the decryption function and log the plaintext.

### Custom VMs (Game-Specific)

Anti-cheats and game studios sometimes build bespoke VMs:
- **Simpler architecture** (20-40 handlers vs. VMProtect's 200+)
- **No public devirtualizer** — you must build the handler map manually
- **Advantage:** Custom VMs are typically weaker because they lack years of hardening

**Approach:** Identify the dispatch loop → enumerate handlers → name each by its semantic operation → trace a target function → manually reconstruct the logic. This is tedious but straightforward because custom VMs are simpler.

---

## 6. When Not to Devirtualize

**Sometimes the answer is to work around the VM, not through it.**

Devirtualization is expensive (days to weeks for a single function). Before investing that time, consider:

- **Black-box the function.** If you know the I/O contract (takes a buffer, returns a hash), you don't need to understand the internals — call it and use the result.
- **Hook the boundaries.** Place hooks at the VM entry and exit points. Log inputs and outputs. The VM is a function — you can call it without understanding it.
- **Patch around it.** If the VM protects a license check, you may be able to patch the caller to skip the VM call entirely rather than reversing the VM.
- **Focus on the unprotected parts.** Games protect 5-20% of their code. The other 80% is unprotected and contains the data structures, offsets, and entity logic you actually need.

**Why:** Devirtualizing a 10,000-handler VM to understand a license check is a week of work. Patching `jz` to `jmp` at the caller is 2 bytes. The Karpathy principle applies: do the minimum work that achieves the goal.

---

## Summary

| # | Step | One-liner |
|---|------|-----------|
| 1 | Identify | Name the protector and version before reversing anything |
| 2 | Strip outer layers | Anti-debug → unpack → fix IAT; inside-out |
| 3 | Classify | Mutation (cosmetic), flattening (structural), or VM (semantic) |
| 4 | Devirtualize | Find dispatcher → identify components → trace → lift → verify |
| 5 | Protector tricks | Know Themida's VMs, VMP's mutation+encryption, OLLVM's CFF+MBA |
| 6 | Skip when possible | Black-box the VM, hook boundaries, patch around it |
