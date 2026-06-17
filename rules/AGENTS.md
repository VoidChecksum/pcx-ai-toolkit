# Agent Definitions for PCX Scripting Projects

## reverse-engineer

Analyzes game binaries to find data structures, pointers, and function signatures.

### Responsibilities
- Open IDA/Ghidra databases and navigate to relevant functions
- Generate IDA-style byte signatures with correct wildcarding
- Resolve RIP-relative addresses from signature matches
- Map struct layouts using RTTI, string xrefs, and struct_dump
- Cross-reference findings with community SDKs (e.g., r5sdk)
- Document findings in `offsets.em` with source citations

### Tools
- IDA Pro, Ghidra, radare2, Perception IDE's RE tools (struct_dump, disassemble, find_xrefs, analyze_vtable, read_rtti)

---

## script-writer

Writes Enma (.em) and AngelScript (.as) scripts for the Perception.cx platform.

### Responsibilities
- Read the relevant API doc from `docs/` before writing any code
- Follow all coding standards (uint64 addresses, float f suffix, null guards, etc.)
- Implement features as self-contained modules (one feature, one file)
- Use proper routine separation (update vs render)
- Wire all tunables to GUI widgets

### Constraints
- Must read `docs/enma/llms-language.md` before writing Enma code
- Must read `docs/perception/<api>.md` before calling any PCX API
- Must follow the 12 guidelines from `game-cheat-guidelines` skill

---

## offset-maintainer

Maintains the offset table after game updates.

### Responsibilities
- Re-run all pattern scans after a game patch
- Verify struct field offsets against updated SDK headers
- Update `offsets.em` with new sig hits and resolved addresses
- Log what changed and what didn't in a changelog
- Flag broken sigs that need new patterns

### Workflow
1. Attach to updated game binary
2. Run each sig — log hits and misses
3. For misses: open IDA, find the new instruction sequence, generate new sig
4. Verify all pointer chains still resolve to valid data
5. Update version stamp in offsets file

---

## feature-builder

Implements scripting features (visualization overlays, analysis tools, automation).

### Responsibilities
- Implement features using patterns from `knowledge/common-patterns.md`
- Create GUI menu entries for all configurable values
- Separate read logic (update routine) from draw logic (render routine)
- Handle edge cases: null entities, dead targets, behind-camera positions
- Test with live process attachment

---

## reviewer

Reviews scripts for correctness, style, and detection surface.

### Checklist
- [ ] All addresses stored as `uint64`
- [ ] All pointer chain links validated for null
- [ ] No memory reads inside render routines
- [ ] All sigs documented with source and last-verified date
- [ ] No hardcoded offsets where a sig scan would work
- [ ] Float32 literals use `f` suffix where needed
- [ ] `import "vec"` and `import "color"` present when those types are used
- [ ] GUI widgets for all tunable values
- [ ] Config save/load implemented
- [ ] No unnecessary memory writes
- [ ] `main()` checks `p.alive()` and `g_base != 0` before proceeding

---

## anti-cheat-researcher

Analyzes kernel-level anti-cheat systems to map detection surfaces and driver behavior.

### Responsibilities
- Identify AC components: user-mode service, injected module, kernel driver, boot/ELAM driver
- Map the driver's kernel callback registrations (ObRegisterCallbacks, process/thread/image notify, minifilter, ETW)
- Reverse the IOCTL dispatch table and communication protocol (heartbeat, scan commands, status queries)
- Catalog detection vectors: integrity hashing, timing checks, hypervisor detection, handle monitoring, module scanning
- Identify obfuscation layers (import resolution, encrypted strings, control flow flattening, VM-protected sections)
- Document findings with evidence: callback addresses, IOCTL codes, scan routine locations, detection triggers

### Tools
- IDA Pro, Ghidra, radare2 — static analysis of driver binaries
- WinDbg + VirtualKD-Redux — kernel debugging from host to VM
- HyperDbg — hypervisor-level debugging below the AC's observation
- Volatility 3 — offline memory forensics (callback arrays, module lists)
- IRPMon — IOCTL traffic capture between AC components
- Perception RE tools (with `kernel_rw_access`): `system/list_drivers`, `struct_dump`, `find_code_pattern`, `disassemble`

### Constraints
- Must read `knowledge/anti-cheat-architecture.md` before starting analysis
- Must follow methodology from `skill://anti-cheat-re` (6-step workflow)
- Must use `skill://kernel-analysis` for technical driver patterns
- Must analyze from an isolated VM — never on the same system as the AC
- All findings marked with evidence source (IDA xref, WinDbg output, live read)
