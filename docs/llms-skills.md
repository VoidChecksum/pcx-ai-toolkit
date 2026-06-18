# pcx-ai-toolkit — Skills Bundle

> Every AI skill in the pcx-ai-toolkit concatenated into one file. Drop into tools that load a single context document, or @-reference from Cursor / Aider / Continue when you want the full behavioral discipline surface available.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 22**

---

## Source: `.claude/skills/ai-pair-programming/SKILL.md`

---
name: ai-pair-programming
description: >
  Techniques for driving AI coding tools (Claude Code, Cursor, Cline, Aider,
  Copilot) effectively on PCX projects. Covers context loading, prompt
  discipline, and steering the AI to read docs before writing API calls.
  Always active when working with an AI on a PCX scripting project.
license: MIT
---

# AI Pair Programming — Driving Claude / Cursor / Cline / Aider Well on PCX Projects

The other skills cover *what* to write; this one covers *how* to drive the AI to write it well. The user-recurring frustration with AI on PCX projects is uniform: "the AI keeps inventing API names" / "it gave me a script that doesn't compile" / "it skipped the discipline rules." The 35,000-line documentation corpus, the 14 skills, and the rules drop-ins are not magic — they only work if you drive the AI to use them. This skill names the techniques that close the gap.

**Always active when working with an AI on a PCX scripting project.** These techniques apply across Claude Code, Cursor, Cline, Aider, GitHub Copilot, and any other AI coding tool that reads files and writes code.

**Prerequisite:** `rules/CLAUDE.md` / `rules/CURSOR.md` / `rules/CLINE.md` / `rules/COPILOT.md` for the per-tool drop-in; this skill is the workflow that wraps them and makes them stick.

---

## Trigger

Starting a new PCX feature with AI assistance, asking the AI to implement something across multiple files, debugging "this script doesn't compile" / "the AI hallucinated a function name", code-reviewing AI output, deciding which tool to use for which task, frustrated with the rate at which the AI produces broken code.

---

## 1. Always Make the AI Read the Doc BEFORE Writing the Code

**The single best technique in this skill. One sentence changes the failure rate from ~40% (hallucinated APIs) to ~5%.**

The pattern is universal across tools: an AI asked to write code from prior knowledge will confidently produce code that looks right and doesn't compile, because Perception.cx's APIs aren't in any model's pretraining corpus. The fix is to put the read in the prompt:

```
WRONG  — "Write me an ESP overlay."
RESULT — Invented draw_esp(), used int for addresses, forgot null checks.
         Doesn't compile, wrong types.

RIGHT  — "Read docs/perception/render-api.md and docs/perception/proc-api.md,
         then write me an ESP overlay using the actual APIs you find there.
         Follow the 12 game-cheat-guidelines."
RESULT — Uses draw_rect + draw_text from the actual API, uint64 addresses,
         null checks after every ru64. Compiles. Runs.
```

The mechanism: the AI's context window now contains the *actual* API surface before any code generation happens. Hallucination drops because it's pattern-matching against documents in context, not against fuzzy pretraining recall.

The cost: 1-2 extra tool calls per task (file reads), maybe 5-30 seconds. The win: not having to fix every other line by hand.

When working iteratively (multi-turn): keep the same docs in context for the whole session. Reading them once and asking three follow-up questions is much cheaper than re-reading them three times.

**Why:** Every tool reaches for pretraining first if you let it. Pretraining for Perception.cx is empty. Front-load the doc read; the rest of the session pays for it many times over.

---

## 2. Use the Cheatsheet for Breadth, the Per-API Doc for Depth

**`knowledge/pcx-api-cheatsheet.md` (15 KB) is the right first read for "what's available?" Per-API docs are the second read for "how does this specific call work?" Loading the entire `docs/perception/` (multiple MB) wastes context for almost every task.**

A typical decision-tree for "what should the AI read?":

```
The task is...
  Discovery ("does PCX have a way to...?")
    → cheatsheet first, then the specific API doc the cheatsheet points to.

  Implementation ("write me a draw_text call")
    → docs/perception/render-api.md (the specific surface).

  Multi-API integration ("attach + scan + walk entity list")
    → docs/perception/proc-api.md (primary), plus brief skim of cheatsheet
      for cross-reference to the entity-iteration patterns.

  Debugging an API error
    → docs/perception/<area>-api.md for the API that errored, AND
      knowledge/common-patterns.md for any worked example using it.

  Cross-language work (Enma <-> AngelScript <-> Lua)
    → knowledge/pcx-cross-language-bridge.md first (decide language),
      then the per-language API doc.
```

The discipline is per-task, not per-session. A 30-minute session might read 4 different docs — that's fine. Re-loading the cheatsheet at the start of each tool session is also fine; it's small and grounds the AI's API surface.

**Why:** Context is the AI's working memory. Filling it with 35,000 lines of documentation leaves no room for your code, your conversation, or its own reasoning. The cheatsheet was made for this — use it.

---

## 3. Plan Before Code, Especially for Multi-File Work

**Two-step workflow: (a) ask the AI to *plan* the change, (b) approve the plan, (c) implement. Skipping the plan step produces ~3x more rework on multi-file changes.**

A plan from the AI is a one-shot list of:
- Which files will change (paths + intent)
- Which sigs / offsets need to be resolved or added
- Which APIs each file will call
- Which routines (`on_update` / `on_render`) the work goes into
- What the end-state behavior is

This is cheap to produce, cheap to review, expensive to skip. Reviewing a 200-word plan and saying "yes but put the sig resolution in `main()` not in `on_update`" catches in 30 seconds what would otherwise be 10 minutes of edit-and-retry.

```
ASK:    "Plan the change to add a 'find closest enemy' feature.
         Don't write any code yet — just list the files, sigs, APIs,
         and routines you'd touch. Tell me what existing code you'd
         reuse and what's net-new."

REVIEW: [the plan]
        Push back: "The team check belongs in update, not render."
        "Use the existing entity_cache from globals.em instead of
        re-walking the list."

APPROVE: "Yes, implement that. Honor the 12 guidelines."

IMPLEMENT: [the AI writes code; you diff-review the result]
```

This works in Claude Code as `/plan` (or just asking), in Cline as the explicit Plan/Act mode, in Cursor as the Composer "Edit" mode preview, in Aider as `/architect`. Different surface, same workflow.

For single-file changes that are well-scoped, you can skip the plan step. The trigger to *not* skip: any change touching 3+ files, any change that adds a new sig, any change that touches `main.em`.

**Why:** Implementation is the expensive step. Plan-before-implement front-loads the cheap correction. Pure-implementation mode lets the AI dig itself into a hole across 5 files before you see the first diff.

---

## 4. Verify Offsets and Sigs with the MCP, Not by Asking the AI to Guess

**The AI does not have your binary loaded. When it confidently writes a sig, that sig is a hallucination unless it came from `mcp:find_pattern` or `mcp:generate_signature` on your actual binary.**

The wrong workflow:

```
ASK:    "Write me an ESP for game.exe v1.42.3."
RESULT: AI invents:
          const string SIG_ENTITY_LIST = "48 8B 0D ?? ?? ?? ?? 48 85 C9 74";
        That sig might be plausible-shaped but is not actually in your binary.
        Script runs, sig hits nothing, script does nothing, you debug for
        an hour wondering why.
```

The right workflow:

```
1. ASK the MCP (Perception IDE / Cursor with MCP / Cline with MCP):
   "Find a unique sig for the entity-list global in game.exe."
   The MCP runs find_pattern + generate_signature against the live binary.

2. CONFIRM the sig:
   python3 tools/sig-uniqueness-checker.py game.exe --sig "<the sig>"
   Verdict: UNIQUE margin=5. Ship it.

3. THEN ask the AI to write the script around the confirmed sig.
   Paste the sig in the prompt: "Use this sig: <sig>. Resolve as
   RIP-relative (disp@+3, insn_len=7). Read the resulting address as a
   uint64 pointer."
```

The discipline: **never let the AI generate sigs from prior knowledge**. Sigs are physical facts about a specific binary; they cannot be "guessed correctly." Same applies to specific RVAs, struct field offsets, and any other binary-specific number.

When using a tool without MCP (Copilot, Aider without an MCP setup): use the MCP-aware tool for discovery, paste the results into the non-MCP tool's session. Cross-tool handoff is fine; trying to make the non-MCP tool guess is not.

**Why:** Hallucinated sigs are silent failures. The script compiles, runs, draws nothing, and burns an hour of debugging that the 30-second MCP query would have prevented. Always.

---

## 5. Insist on the 12 Guidelines in the Prompt, Not Just in the Rules Drop-In

**Even with `rules/CLAUDE.md` (or CURSOR.md or CLINE.md or COPILOT.md) loaded, an AI mid-flow forgets. End every code-writing prompt with "honor the 12 guidelines." Cheap. Works.**

The rules drop-ins establish baseline behavior; the in-prompt reminder is the per-task checkpoint:

```
ASK:    "Add the smoothing slider. Honor the 12 guidelines — especially
         #11 (GUI for every tunable) and #8 (f suffix on float32 literals)."

RESULT: The slider is added as a section_slider_float with bounds, the
        smoothing value is float32 with proper f suffix in arithmetic,
        nothing hardcoded.
```

The framing works because the AI has the guidelines in its context (from the rules drop-in) and now has them at the top of its working attention (from the explicit mention). When the implementation produces a violation, your follow-up is short: "Rule 8 — the 0.5 in line 23 should be 0.5f."

You can also name specific rules to enforce more strictly. For RE-heavy work:

```
"Honor especially #1 (cite sigs with E-NNN), #5 (sigs over hardcodes),
 #12 (mark UNVERIFIED until you've checked the binary)."
```

For render-path work:

```
"Honor especially #4 (no reads in render), #7 (construct primitives per
 frame), #10 (W2S with w > 0.001 check)."
```

This is also where you bring in the other skills explicitly: "Follow `skill://pcx-perf-budget` for the timing discipline; budget render to 1.5 ms at 144 Hz."

**Why:** Without the in-prompt reminder, the AI honors guidelines for the first few lines and drifts. The mention is the per-task gravity well that keeps it on track for the whole completion.

---

## 6. Diff-Review Every Multi-File Change Before Applying

**This is where the AI's mistakes are catchable cheaply. Cursor, Cline, Aider, Claude Code with a permission gate — all show diffs. Read them.**

The high-value pattern matches to scan for in any AI-produced diff:

| Pattern | Rule violated | Fix |
|---|---|---|
| `int64 g_X` or `int32 g_X` near "addr" / "offset" / "base" / "ptr" | #2 | Change to `uint64` |
| Bare float literal (`8.0`, not `8.0f`) inside a `draw_*` call | #8 | Add `f` suffix |
| `ru64(...)` followed by code that uses the result without checking `!= 0` | #3 | Add null check |
| `color(...)` / `vec2(...)` / `vec3(...)` constructed at file scope (not inside a routine) | #7 | Move construction inside `on_render` |
| Hardcoded address (`0x12345678`) without a `// E-NNN` or `// UNVERIFIED` comment | #1, #12 | Add citation or marker |
| Hotkey hardcoded (`if (is_key_down(VK_F2))`) — no `section_keybind` widget | #11 | Add widget, bind to global |
| `find_code_pattern` call in `on_update` or `on_render` | (cost) | Move to `main()`, cache the result in a global |
| `read_memory` for 4-8 bytes where `read_typed_value` would do | (cost) | Use the typed variant |

A 5-minute diff review catches roughly 90% of guideline violations. The remaining 10% — subtle correctness bugs, off-by-one in struct offsets, wrong RIP arithmetic — are the ones worth a closer second pass.

Do not blanket-approve a multi-file change. Even when the AI gets it right, the review *also* serves as your own context-build: you're learning the change you're approving. Bypassing the review means you've shipped code you don't understand.

**Why:** The AI's review is its own output; your review is the independent check. Without it, you're shipping the AI's confidence. With it, you're shipping verified correctness. Five minutes is cheap.

---

## 7. When the AI Gets Stuck, Change the Question

**The AI loops on "this still doesn't work"; the right move is to re-frame to a more specific question that forces a different action.**

Common stuck-loop patterns:

| Stuck pattern | Re-framing |
|---|---|
| "the script crashes" → AI re-reads the same code | "What does the disassembly at `g_entity_list` look like? Use mcp:disassemble on the address we resolved." |
| "the sig doesn't match" → AI suggests a longer sig | "What's the actual byte sequence at the address we expected the sig to hit? Use mcp:read_memory to dump 32 bytes there." |
| "the field is wrong" → AI guesses different offsets | "Use mcp:struct_dump on three entity pointers and show me which offsets contain the values we expect for health (range 0-100) and team (small int)." |
| "the read returns 0" → AI suggests defensive null checks | "Walk the pointer chain step by step: print each intermediate pointer value. Where does the chain become 0?" |
| "the W2S draws at (0,0)" → AI suggests different matrix math | "Print the view matrix bytes; print the world position bytes. Are they non-zero and plausible? Check the matrix layout in `knowledge/aimbot-math.md`." |
| "the AI keeps suggesting the same fix that doesn't work" | "Stop. Tell me what you don't know yet. What's the next question we should answer?" |

The unstuck question is always more specific than "what's wrong." It names a tool call or a fact-finding step the AI can take next, instead of asking it to brainstorm fixes blindly.

This is the highest-skill move in AI pair programming — recognizing when "more of the same" won't work and stepping out to a different angle. It saves more time than any other single technique.

**Why:** Loops happen because the AI has the same information you do and can only re-shuffle it. Adding new information (a disassembly read, a struct dump, a memory peek) breaks the loop. The fastest path forward is rarely "try harder" — it's "look somewhere else."

---

## Per-Tool Quick Recipes

### Claude Code

- Use `/plan` or ask "plan the change" to trigger the plan-before-implement workflow.
- Skills auto-activate when their keywords appear (`patch day` → `pcx-patch-day-playbook`, `aimbot math` → `knowledge/aimbot-math.md` via skill keyword detection).
- Use `@file:docs/perception/render-api.md` (or whatever Claude Code's reference syntax is in your version) to force a specific doc into context.
- The `task` tool spawns subagents for parallel work; use the `cyber-repo-coverage-fanout` managed skill for multi-file PRs to this kind of repo.

### Cursor

- Use Composer mode for multi-file work; Chat mode for single-file or discussion.
- `@docs/perception/render-api.md` adds a file to the conversation context.
- `@codebase` for a project-wide grep; expensive context-wise but useful for "find every place that does X."
- The `.cursorrules` file (or `rules/CURSOR.md` copied to project root) applies project-wide.

### Cline

- Use Plan mode for any change touching 3+ files. The plan output is its own checkpoint.
- Auto-approve read-only MCP tools (`read_memory`, `find_pattern`, `disassemble`); keep write/execute tools gated.
- `@`-reference specific docs to keep them in context.
- Checkpoints before any `memory_write` or `execute_script` — the rollback path is your safety net.

### Aider

- `/read` adds a file to the always-in-context set; persists across the session.
- `/architect` mode for planning without code edits — the analog of Claude Code's `/plan`.
- `/commit` to commit Aider's changes; review the diff in `git log -p HEAD~1..HEAD` immediately after.
- `CONVENTIONS.md` (copy `rules/CLAUDE.md` content) is auto-loaded on every session.

### GitHub Copilot

- Inline completions for typing; Chat for explanation and review.
- `// from: docs/perception/render-api.md` comment above the cursor steers the next completion's API choice.
- Pair with an MCP-aware tool (the Perception IDE or Cursor with MCP) for binary discovery; bring resolved sigs back to Copilot for the typing-out.
- Accept 5-15 line completions, not 60-line ones.

---

## Summary

| # | Technique | One-liner |
|---|---|---|
| 1 | Read doc before writing code | "Read `docs/perception/X.md` then write…" — cuts hallucination from 40% → 5% |
| 2 | Cheatsheet for breadth, per-API for depth | `knowledge/pcx-api-cheatsheet.md` first, specific doc second |
| 3 | Plan before code on multi-file work | Two-step workflow; 30 seconds of plan review saves 10 minutes of rework |
| 4 | Verify sigs with MCP, not AI memory | Sigs are physical facts about your binary; AI cannot guess them |
| 5 | Honor the 12 guidelines per prompt | In-prompt mention beats rules-drop-in alone; cite specific rules per task |
| 6 | Diff-review every multi-file change | Five-minute scan for the 8 high-value pattern matches catches ~90% of violations |
| 7 | When stuck, change the question | Specific tool-call asks beat "try harder"; the unstuck question is more concrete |

**Cross-references:** `rules/CLAUDE.md`, `rules/CURSOR.md`, `rules/CLINE.md`, `rules/COPILOT.md` (the per-tool drop-ins this skill wraps); `skill://mcp-tool-routing` (which of the 37 Perception MCP tools for which task — the technique-4 backbone); `skill://game-cheat-guidelines` (the 12 rules technique #5 enforces); `skill://pcx-patch-day-playbook` (the workflow when the script breaks after a game update — applies techniques 4, 5, 7); `knowledge/pcx-cross-language-bridge.md` (when to use Enma vs AS vs Lua — the question technique #3 plans against).

---

## Source: `.claude/skills/anti-cheat-re/SKILL.md`

---
name: anti-cheat-re
description: >
  Methodology for reverse engineering kernel-level anti-cheat systems: EAC,
  BattlEye, Vanguard, GameGuard, XIGNCODE3. Covers component enumeration,
  detection-vector cataloging, and verified understanding of the AC
  observation surface. Always active when analyzing anti-cheat systems.
license: MIT
---

# Anti-Cheat Reverse Engineering — Kernel-Level Game Protection Analysis

Methodology for reverse engineering kernel-level anti-cheat systems: EAC (Easy Anti-Cheat), BattlEye, Vanguard, GameGuard, XIGNCODE3, and similar kernel drivers that protect game processes. Covers the full workflow from component enumeration through detection-vector cataloging to verified understanding of the AC's observation surface.

**Always active when analyzing anti-cheat systems.** This is the *methodology* layer — how to approach and work through kernel AC analysis. The `kernel-analysis` skill covers the *technical patterns* (IOCTL dispatch, callback structures, WDM/KMDF internals). Load both.

**Prerequisite:** Read `knowledge/anti-cheat-architecture.md` for per-AC component names, detection matrices, and architecture diagrams before starting analysis. Read `knowledge/kernel-re-tools.md` for the tool reference.

## Trigger
Reversing an anti-cheat driver, analyzing kernel callbacks, mapping IOCTL protocols, understanding detection vectors, researching handle stripping, studying kernel-level game protection, or any mention of EAC, BattlEye, Vanguard, GameGuard, or kernel anti-cheat.

---

## 1. Map the AC's Full Component Stack Before Touching the Driver

**Enumerate every component — user-mode service, injected module, kernel driver, boot driver — and identify how they communicate. Start with user-mode, not kernel.**

A kernel anti-cheat is never just a driver. It's a stack:

- **User-mode service** — `EasyAntiCheat.exe`, `BEService.exe`, `vgc.exe`. Runs as a system service or high-privilege process. Manages the driver lifecycle, communicates with backend servers, relays scan results.
- **Game-injected module** — `EasyAntiCheat_EOS.dll`, `BEClient.dll`. Loaded into the game process. Performs user-mode integrity checks, reports to the service.
- **Kernel driver** — `EasyAntiCheat.sys`, `BEDaisy.sys`, `vgk.sys`. Registers kernel callbacks, strips handles, monitors system state.
- **Boot/ELAM driver** (Vanguard) — loads before third-party drivers at boot time.
- **Backend servers** — BattlEye streams shellcode to `BEClient.dll` at runtime. EAC pushes cloud detection rules. These are out of scope for local RE but explain why static analysis of detection logic is incomplete.

**Start with the user-mode service, not the driver.** The service is unobfuscated (or lightly obfuscated) and reveals:
- The IPC protocol to the driver (IOCTL codes, shared memory layout)
- The heartbeat/keepalive mechanism
- What data it sends to backend servers
- How it launches and communicates with the game-injected module

```
Workflow:
1. Identify components:
   - Process list → find AC processes (service, tray, game-injected)
   - Driver list → find AC kernel module
   - r2 -AA EasyAntiCheat.exe → map imports, find DeviceIoControl calls

2. Map communication:
   - User-mode → driver: DeviceIoControl (IOCTL codes)
   - Service → game module: shared memory / named pipe / RPC
   - Service → backend: HTTPS / custom protocol

3. THEN analyze the driver with the IPC protocol already understood.
```

**Why:** Jumping straight into the driver binary is like reading a server without knowing the protocol. The user-mode component *tells you* what the driver expects — IOCTL codes, buffer structures, heartbeat cadence. Reverse the client first, the server second.

---

## 2. Catalog Every Kernel Callback the Driver Registers

**The driver's `DriverEntry` registers callbacks that ARE the detection surface. Find every one — a missed callback is a missed detection vector.**

The kernel driver's power comes from OS notification callbacks. These are the standard ones, in order of importance for AC analysis:

| Callback Registration | What It Monitors | AC Use |
|---|---|---|
| `ObRegisterCallbacks` | Process/thread handle operations | **Handle stripping** — removes `PROCESS_VM_READ`/`PROCESS_VM_WRITE` from external handles to the game. This is the #1 reason external memory tools fail. |
| `PsSetCreateProcessNotifyRoutineEx` | Process creation/exit | Monitors for known cheat tools launching. Logs process names, paths, hashes. |
| `PsSetCreateThreadNotifyRoutineEx` | Thread creation | Detects remote thread injection (`CreateRemoteThread` into game process). |
| `PsSetLoadImageNotifyRoutine` | DLL/driver loading | Detects foreign modules loaded into game process or unsigned drivers loading into kernel. |
| `CmRegisterCallbackEx` | Registry access | Monitors for cheat-related registry keys (tool configs, driver service entries). |
| `FltRegisterFilter` | File system operations | Minifilter watching for cheat binaries on disk, log files, config files. |
| `EtwRegister` (TI provider) | Syscall-level telemetry | ETW Threat Intelligence provider captures `NtReadVirtualMemory`, `NtWriteVirtualMemory`, `NtAllocateVirtualMemory` across processes. |

**How to find them:** In IDA/r2, open the driver's import table and search for these function names. Each import is a registration call — xref it to find the callback function being registered.

```
# radare2 — find callback registrations in a driver
r2 -AA driver.sys
afl~ObRegister                    # find ObRegisterCallbacks
afl~PsSetCreate                   # find process/thread notify
afl~PsSetLoadImage                # find image load notify
afl~CmRegister                    # find registry callbacks
afl~FltRegister                   # find minifilter registration
afl~EtwRegister                   # find ETW providers

# For each hit, disassemble the caller to find the callback function:
pdf @ sym.imp.ObRegisterCallbacks  # see who calls it
axt @ sym.imp.ObRegisterCallbacks  # xrefs to the import
```

```
// WinDbg — enumerate live callback arrays in kernel
!callback                                    // all registered callbacks
dt nt!_OBJECT_TYPE poi(nt!ObTypeIndexTable+0x38) // process object type callbacks
!object \ObjectTypes\Process                  // OB callbacks on process objects
```

**Why:** If you miss a callback, you miss a detection vector. An AC with an `ObRegisterCallbacks` handler will strip your handles silently — your `OpenProcess` succeeds but returns a handle with no VM access, and your reads return STATUS_ACCESS_DENIED without you understanding why. Map them all.

---

## 3. Trace the Driver ↔ User-Mode Communication Channel

**The driver and user-mode service talk constantly. Find the protocol: IOCTLs, shared memory, events. The heartbeat is the first thing to understand.**

Every kernel AC has a communication channel between its driver and user-mode components. This channel carries:
- **Heartbeat/keepalive** — periodic "I'm alive and unmodified" messages. If the heartbeat stops (driver unloaded, communication interrupted), the AC kills the game.
- **Scan requests** — the service asks the driver to scan specific memory regions, verify integrity, or enumerate handles.
- **Results** — the driver reports detected anomalies back to the service, which relays them to backend servers.

**Finding the channel:**

1. **IOCTLs:** Reverse the driver's `IRP_MJ_DEVICE_CONTROL` handler. This is a switch/jump table on IOCTL codes. Each code has an input and output buffer structure. See `skill://kernel-analysis` §2 for the technical pattern.

2. **Shared memory:** Look for `ZwMapViewOfSection` or `MmMapLockedPagesSpecifyCache` in the driver — these map a kernel buffer into user-mode address space for zero-copy communication.

3. **Events:** `IoCreateNotificationEvent` / `KeSetEvent` / `KeWaitForSingleObject` — the driver and service signal each other through named kernel events.

**The heartbeat pattern:**
```
Service                          Driver
   │                               │
   ├─── IOCTL_HEARTBEAT ──────────►│  (periodic, e.g. every 5-15 seconds)
   │    {timestamp, token, hash}   │
   │                               │── verify token + timing
   │◄── IOCTL_HEARTBEAT_ACK ──────┤
   │    {next_token, scan_cmd}     │
   │                               │
   │  (if no heartbeat for N sec)  │
   │                               │── KeSetEvent(game_kill_event)
   │                               │── or: ZwTerminateProcess(game)
```

**Why:** The heartbeat is the AC's self-integrity check. If you understand its cadence and token scheme, you understand what happens when the driver is absent, modified, or interrupted. Every bypass vector starts from knowing this protocol.

---

## 4. Identify What the AC Actually Scans For

**Don't guess at detection vectors — find the scan routines in the driver and catalog exactly what they check.**

Detection is not magic. It's code that reads specific locations and compares them to expected values. Common scan categories:

### Memory Integrity
- **Code section hashing:** The AC hashes the game's `.text` section periodically and compares against a known-good value. A modified instruction (NOP sled, hook, patch) fails the hash check.
- **Import table validation:** Verifies the game's IAT hasn't been hooked (function pointers still point into the expected module).
- **Stack walking:** Walks the call stack from a game function; an anomalous return address (pointing outside any loaded module) indicates injected code.

### System State
- **Hypervisor detection:** `CPUID` with `EAX=1` checks the VMX bit (ECX bit 31). `CPUID` with `EAX=0x40000000` returns a hypervisor brand string. Timing checks (`RDTSC` pairs) detect VM exit latency.
- **Debug register checks:** Reads `DR0`–`DR3` and `DR7` — hardware breakpoints on game memory are a strong cheat indicator.
- **DMA detection:** Queries IOMMU/VT-d status via `NtQuerySystemInformation`. If DMA remapping is disabled, a DMA device could be reading game memory externally.
- **Unsigned driver detection:** Walks `PsLoadedModuleList` and cross-references with `PiDDBCacheTable` / `MmUnloadedDrivers` to find manually mapped or unsigned kernel modules.

### Process/Handle Monitoring
- **Handle table walks:** Enumerates handles to the game process across all processes. Any external handle with VM read/write access is suspicious.
- **Module injection detection:** `PsSetLoadImageNotifyRoutine` flags DLLs loaded into the game that aren't on an allowlist.
- **Window enumeration:** Scans for windows with known cheat tool class names or titles (user-mode, but often triggered by the driver's scan commands).

```
# How to find scan routines in the driver:

# 1. Look for hash computation — scan for loops with XOR/rotate/add patterns
#    or calls to known hash functions (SHA256, CRC32, xxHash)

# 2. Look for NtQuerySystemInformation imports — these are system state queries
r2 -AA driver.sys
axt @ sym.imp.NtQuerySystemInformation    # who calls it?
# check the SystemInformationClass argument:
#   0x4D = SystemModuleInformation (driver list)
#   0x42 = SystemBigPoolInformation (pool allocations)
#   0x40 = SystemExtendedHandleInformation (handle table)

# 3. Look for MmGetSystemRoutineAddress — dynamic import resolution
#    AC drivers resolve NTAPI functions at runtime to avoid static import analysis
axt @ sym.imp.MmGetSystemRoutineAddress
```

**Why:** You can't avoid detection you don't understand. Each scan is a specific check with specific failure conditions. Catalog them, and you know exactly what's off-limits and what isn't monitored.

---

## 5. Analyze from Below the AC's Observation Layer

**Never run analysis tools on the same system as the AC. Use a VM, hardware debugger, or hypervisor-level tools.**

The AC monitors the system it runs on. If you run IDA, r2, Ghidra, Process Monitor, or even `tasklist` on the same box, the AC may detect and flag it. Analysis must happen from a layer the AC cannot observe.

### Environment Setup

| Layer | Tool | Visibility to AC |
|---|---|---|
| **Hardware debugger** | JTAG / Intel DCI | Invisible — hardware-level, no software artifacts |
| **Hypervisor debugger** | HyperDbg | Below the AC's hypervisor checks (if done right) |
| **Host → VM kernel debug** | WinDbg + VirtualKD-Redux | The AC sees a debugger-enabled boot (`KdDebuggerEnabled`), but can't prevent it from a hardware/pipe debugger |
| **Offline memory dump** | WinPmem → Volatility 3 | No live interaction — analyze a snapshot |
| **DMA acquisition** | PCILeech + MemProcFS | Physical memory access — invisible to software ACs |
| **Same-system tools** | Process Monitor, API Monitor | **Visible** — AC may detect and flag |

### Best Practice

```
1. VM with snapshot:
   - Take snapshot BEFORE installing the AC
   - Install game + AC → analyze → revert to clean snapshot
   - The AC's boot-time checks (Vanguard ELAM) require a fresh boot in the VM

2. Kernel debug from host:
   - bcdedit /debug on (in VM)
   - WinDbg on host: File → Kernel Debug → Net (or pipe via VirtualKD)
   - Set breakpoints in the AC driver: bp EasyAntiCheat!DriverEntry

3. Static analysis on host:
   - Copy the driver binary OUT of the VM before the AC loads
   - Analyze the .sys file in IDA/Ghidra on the host
   - No interaction with the live AC system
```

**Why:** Analyzing an AC from the same system it protects is like auditing a security camera while standing in front of it. The VM boundary is the minimum isolation; offline analysis of extracted binaries is the safest.

---

## 6. Verify Your Understanding Against Live Behavior

**A reversed IOCTL table or callback list is a hypothesis until you confirm it against the running AC. Diff after updates — the AC evolves silently.**

Anti-cheat drivers update without notice. EAC pushes cloud rules. BattlEye streams shellcode. Vanguard updates `vgk.sys` with game patches. Your understanding from last week may be wrong today.

### Verification loop:
1. **Confirm callbacks are active:** In WinDbg, walk the callback arrays (`PspCreateProcessNotifyRoutine`, `PspCreateThreadNotifyRoutine`, `PspLoadImageNotifyRoutine`) and verify the AC driver's functions are in the list.
2. **Confirm IOCTL handling:** Send a known IOCTL from a test user-mode program (or log it via IRPMon) and verify the driver dispatches it as expected.
3. **Confirm detection triggers:** In a test VM, trigger a known detection vector (e.g., `OpenProcess` with `PROCESS_VM_READ` on the game) and observe whether the AC strips the handle, logs the event, or takes action.
4. **Diff after updates:** Extract the driver binary before and after a game update. Binary diff in IDA (`BinDiff`) or r2 (`radiff2`) to see what changed.

```
# radare2 — diff two driver versions
radiff2 -C EasyAntiCheat_old.sys EasyAntiCheat_new.sys

# WinDbg — check process notify callbacks
kd> dd nt!PspCreateProcessNotifyRoutine L10
# each non-zero entry is a callback — resolve to module:
kd> ln <address_from_above>

# WinDbg — verify ObRegisterCallbacks on process objects
kd> !object \ObjectTypes\Process
kd> dt nt!_OBJECT_TYPE poi(<process_type_addr>) .CallbackList
```

**Why:** The AC is a moving target. A callback you reversed last month may have been replaced, reordered, or supplemented. A verified understanding is current; everything else is stale. Treat every analysis session as potentially outdated and re-confirm the critical paths.

---

## Summary

| # | Step | One-liner |
|---|------|-----------|
| 1 | Map the stack | Enumerate all components and communication channels; start with user-mode |
| 2 | Catalog callbacks | Find every kernel callback registration — each one is a detection vector |
| 3 | Trace communication | Reverse the IOCTL protocol and heartbeat mechanism |
| 4 | Identify scans | Find what the AC checks: code integrity, system state, handles, modules |
| 5 | Analyze from below | VM + host debugger + offline analysis; never from the same OS instance |
| 6 | Verify live | Confirm against the running AC; diff after every update |

---

## Source: `.claude/skills/deobfuscation/SKILL.md`

---
name: deobfuscation
description: >
  Methodology for reversing binaries protected by commercial obfuscators
  (Themida, VMProtect), compiler-level obfuscation (OLLVM, Hikari), and
  custom protection schemes. Covers identification, classification, layer
  stripping, devirtualization, and verification. Active when analyzing
  obfuscated or packed binaries.
license: MIT
---

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

---

## Source: `.claude/skills/game-cheat-guidelines/SKILL.md`

---
name: game-cheat-guidelines
description: >
  Behavioral rules for writing game cheats in Enma, AngelScript, and C++ on
  Perception.cx. Derived from Karpathy principles, rewritten for cheat
  development: memory hacking, ESP, aimbot, hooking, overlay rendering, and
  RE workflows. Always active — these rules apply every time you write or
  edit cheat code.
license: MIT
---

# Game Cheat Development Guidelines

Behavioral rules for writing game cheats in Enma, AngelScript, and C++. Derived from the Karpathy principles but rewritten for the domain: memory hacking, ESP, aimbot, hooking, overlay rendering, and reverse engineering workflows on the Perception.cx platform.

**Always active.** These rules apply every time you write or edit cheat code. They are not suggestions.

**Prerequisite:** The `game-hacking-pcx` skill MUST be loaded alongside this one. It contains the full doc index (33,580 lines across 99 files) for Enma, AngelScript, and all Perception.cx APIs. **Read the relevant doc before writing any API call** — see `skill://game-hacking-pcx` for the complete file-by-file index.

---

## 1. Know the Target Before You Touch Memory

**Never read or write a single byte until you know what you're reading.**

Before implementing any feature:
- State the game, engine, and binary you're targeting. Name the module.
- Identify whether offsets come from a sig scan, a hardcoded offset table, or the r5sdk/community SDK. Say which.
- If an offset is hardcoded, flag it: hardcoded offsets break on game updates. Prefer pattern scans.
- If the struct layout comes from a reversed SDK, cite the header file. If you guessed it, say "UNVERIFIED" and mark the offset.
- If you don't know the field size, read it as `ru64` and inspect — never assume `int32` vs `float32` without evidence.

```
Before: "Read player health at base+0x43E0"
After:  "r5sdk/src/game/server/player.h defines m_iHealth at 0x43E0 (int32).
         Sig for entity list: 48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 81
         Last verified: Season 21 patch 1.98"
```

**Why:** A wrong offset doesn't crash your script — it reads garbage silently. You'll spend an hour debugging ESP that draws at (0, 0) because the position field moved 8 bytes. Ground every offset.

---

## 2. Addresses Are `uint64`, Always

**One type for addresses. No exceptions. No `int64` addresses.**

- Every variable holding a memory address is `uint64`. Period.
- `proc.base_address()` returns `uint64`. Module bases are `uint64`. Pointer chain intermediates are `uint64`.
- If you must pass an address to a function taking `int64`, use `cast<int64>(addr)` at the call site, not at storage.
- Pattern scan results are `uint64`. Entity list pointers are `uint64`. VTable slots are `uint64`.

```cpp
// WRONG
int64 base = p.base_address();
int64 entity = p.r64(base + 0x1234);  // sign-extends high addresses, subtle corruption

// RIGHT
uint64 base = p.base_address();
uint64 entity = p.ru64(base + 0x1234);
```

**Why:** `int64` and `uint64` are implicitly convertible in Enma but sign-extend differently in pointer arithmetic. Kernel addresses and high-usermode addresses (Windows `0x7FF...`) turn negative in `int64`, breaking comparisons and offset math. One type, zero bugs.

---

## 3. Validate Before You Chain

**Every pointer in a chain can be null. Check it or crash.**

- After every `ru64` that produces a pointer, check for 0 before dereferencing.
- After `ref_process()`, check `.alive()` immediately.
- After `find_code_pattern()`, check for 0 — a missed sig means the offset table is stale.
- After `get_module_base()`, check for 0 — the module might not be loaded yet.
- `is_valid_address()` exists. Use it when chasing unknown pointer chains.

```cpp
// WRONG — entity_list could be 0 after a patch
uint64 entity_list = p.ru64(base + ENTITY_LIST_OFFSET);
uint64 entity = p.ru64(entity_list + i * 0x8);  // reads from address 0x0 + i*8 = garbage

// RIGHT
uint64 entity_list = p.ru64(base + ENTITY_LIST_OFFSET);
if (entity_list == 0) return;
uint64 entity = p.ru64(entity_list + i * 0x8);
if (entity == 0) continue;
```

**Why:** Failed reads return 0 silently in Perception. A null pointer in a chain doesn't crash — it reads from address `0 + offset`, which returns more zeros or garbage. Your ESP draws nothing or draws at (0,0) and you don't know why. Validate every link.

---

## 4. Separate Scan from Render

**Pattern scans and heavy reads happen once or on interval. Rendering happens every frame.**

Structure every script as:
1. **`main()`** — setup: process attach, pattern scans, resolve base addresses. Run once.
2. **Update routine** — read entity data, build display list. Runs on interval or every frame, but does NO drawing.
3. **Render routine** — draws from the cached display list. Runs every frame. Does NO memory reads.

```cpp
// Global state
proc_t g_proc;
uint64 g_entity_list;
vec3[] g_positions;

void on_update(int64 data) {
    // Read game state — separated from render
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 0x8);
        if (ent == 0) continue;
        g_positions[i] = g_proc.read_vec3_fl32(ent + POS_OFFSET);
    }
}

void on_render(int64 data) {
    // Draw from cache — no proc reads here
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        draw_circle(world_to_screen(g_positions[i]), 5.0, g_color_enemy, 1.0, true);
    }
}
```

**Why:** Mixing reads and draws makes every frame dependent on read latency. If the target process lags or a page is swapped out, your overlay stutters. Separating them means the render path is pure compute — smooth even when reads are slow. It also makes the code testable: you can verify reads independently from draw correctness.

---

## 5. Pattern Scans Over Hardcoded Offsets

**Sigs survive patches. Hardcoded offsets don't.**

- For any address that isn't a direct struct field offset from a known base, use `find_code_pattern`.
- The sig should be wide enough to be unique but not so wide it spans an instruction that changes per-build.
- Wildcard (`??`) the bytes that contain relocatable values: RIP-relative displacements, jump targets, immediate addresses.
- Store the sig as a named constant, not inline. Document what it finds.

```cpp
// Sig for CEntityList global pointer — LEA RCX, [rip+????]
// Wildcards on the 4-byte RIP displacement
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";

uint64 resolve_entity_list(proc_t& p, uint64 base, uint64 size) {
    uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0) return 0;
    // Resolve RIP-relative: read 4-byte displacement at hit+3, add to hit+7
    int32 disp = p.r32(hit + 3);
    return hit + 7 + cast<uint64>(disp);
}
```

**Why:** Every game update shuffles code and data. A hardcoded offset `0x25AB3F0` is dead on the next patch. A sig for the instruction that loads that pointer survives unless the compiler changes the instruction pattern — which is rare. Name your sigs, document what instruction they match, and resolve RIP-relative displacements correctly (4 bytes, signed, added to the *end* of the instruction).

---

## 6. One Feature, One File

**Each cheat feature lives in its own file. No god scripts.**

- ESP in `esp.em`. Aimbot in `aim.em`. Radar in `radar.em`. Config/GUI in `menu.em`.
- Shared state (process handle, entity cache, config values) goes in a `globals.em` module and is imported.
- If two features need the same data, extract it into a shared update routine — don't duplicate reads.

```
project/
├── globals.em      # proc_t, entity cache, config state
├── offsets.em      # all sigs and resolved addresses
├── esp.em          # render routine for boxes/names/health
├── aim.em          # aimbot logic + smoothing
├── menu.em         # GUI sidebar widgets
└── main.em         # main() — setup, register routines
```

**Why:** A 2000-line monolith means every edit risks breaking unrelated features. Separate files let you reload one feature without touching others (Perception supports hot reload). It also makes it trivial to disable a feature: just don't register its routine.

---

## 7. Construct Every Frame, Cache Nothing Graphical

**Colors, vec2 positions, and font handles from `get_font*()` are cheap. Construct them fresh.**

- `color(r, g, b, a)` is a 4-byte stack struct. Creating it costs nothing.
- `vec2(x, y)` is two floats. Creating it costs nothing.
- `get_font20()` returns a cached handle — calling it every frame is fine.
- Never cache a `color` or `vec2` in a global to "avoid allocation" — there is no allocation. Enma drops them at scope exit.

```cpp
// WRONG — premature "optimization" that adds global state for nothing
color g_white;
color g_red;
int64 g_font;

int64 main() {
    g_white = color(255, 255, 255, 255);
    g_red = color(255, 0, 0, 255);
    g_font = get_font20();
    // ...
}

// RIGHT — construct in the render function, zero overhead
void on_render(int64 data) {
    color white = color(255, 255, 255, 255);
    color red = color(255, 0, 0, 255);
    draw_text("ESP", vec2(10.0, 10.0), white, get_font20(), 0, color(0,0,0,0), 0.0);
}
```

**Why:** Enma's `[[packed]]` structs are stack-allocated value types. A `color` is 4 bytes on the stack — cheaper than a global load. Caching render primitives adds mutable global state that makes reasoning about the render path harder, for literally zero performance gain.

---

## 8. Float Literals Need the `f` Suffix

**`0.2` is `float64`. `0.2f` is `float32`. The GPU and the game don't agree on which you meant.**

- All `vec2`/`vec3`/`vec4` constructors that feed vertex buffers need `float32` — use `f` suffix.
- Screen coordinates from `get_view_width()`/`get_view_height()` return `float64` — that's fine for draw calls.
- `read_vec3_fl32` returns `float64` fields (promoted) — arithmetic is `float64`, no suffix needed.
- When writing back to game memory with `wf32()`, the value is narrowed — make sure your math didn't accumulate `float64` precision you'll silently lose.

```cpp
// Custom vertex buffer data — must be float32
float32 x = 10.0f;
float32 y = 20.0f;

// Draw calls accept float64 — no suffix needed
draw_line(vec2(10.0, 20.0), vec2(100.0, 200.0), white, 1.0);
```

---

## 9. Don't Write Memory Unless You Must

**Read-only cheats are invisible. Writes leave forensic traces.**

- ESP, radar, entity highlighting, distance display — all read-only. Prefer these.
- If you must write (aimbot smoothing via angle writes, no-recoil via value patches, speed hacks), write the minimum bytes needed.
- Never `wvm` a large buffer when `wu32` or `wf32` on a single field suffices.
- After writing, verify the write took effect with a read-back if the field is contested (anti-cheat may revert it).
- Gate all writes behind `write_memory` permission checks — Perception enforces this, respect it in your design too.

```cpp
// WRONG — nop-patching 16 bytes of recoil code
array<uint8> nops = {0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90};
p.wvm(recoil_addr, nops);

// RIGHT — write the float that controls recoil spread, minimal footprint
p.wf32(recoil_spread_addr, 0.0f);
```

**Why:** Every memory write is a detection surface. Anti-cheats integrity-check code sections (`.text`), monitor write patterns on game state, and log anomalous page faults. A single float write to a gameplay variable is orders of magnitude harder to detect than a 16-byte NOP sled in executable memory.

---

## 10. World-to-Screen Is Math, Not Magic

**Implement W2S correctly once. Never approximate it.**

The formula depends on the engine's view matrix layout. For Source Engine (Apex, CS2, TF2):

```cpp
// Source Engine uses a 4x3 view matrix (3 rows of 4 floats = 48 bytes)
// Row 0: right.x, right.y, right.z, right.w
// Row 1: up.x,    up.y,    up.z,    up.w
// Row 2: fwd.x,   fwd.y,   fwd.z,   fwd.w

bool world_to_screen(vec3 world, out vec2 screen, float64 matrix_addr) {
    // Read 12 floats from the view matrix
    float64 w = m[3]*world.x + m[7]*world.y + m[11]*world.z + m[15]; // not present in 4x3 — check engine
    if (w < 0.001) return false;  // behind camera

    float64 inv_w = 1.0 / w;
    float64 nx = (m[0]*world.x + m[4]*world.y + m[8]*world.z + m[12]) * inv_w;
    float64 ny = (m[1]*world.x + m[5]*world.y + m[9]*world.z + m[13]) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2(
        (vw * 0.5) + (nx * vw * 0.5),
        (vh * 0.5) - (ny * vh * 0.5)
    );
    return true;
}
```

**Rules:**
- Always check `w > 0` (or a small epsilon) — behind-camera points produce mirrored coordinates.
- Read the matrix from the game's actual view matrix address, not a reconstructed one.
- Match the matrix layout to the engine. Source uses column-major 4x4, Unreal uses row-major, Unity uses column-major with flipped Z.
- Implement it once in a shared module. Every feature imports it.

---

## 11. GUI State Is Config, Not Code

**Every tunable goes through the GUI API. No magic constants buried in logic.**

- Bind every threshold, color, toggle, and hotkey to a GUI widget in a sidebar section.
- Use `section_checkbox` for feature toggles, `section_slider_float` for distances/smoothing, `section_keybind` for hotkeys.
- Read widget state at the top of each routine, then branch on it. Don't mix widget reads deep inside nested loops.
- Persist config to a file via the filesystem API. Load it in `main()`.

```cpp
bool g_esp_enabled;
float64 g_esp_distance;
color g_esp_color;

void setup_gui() {
    int64 sec = create_section("ESP");
    section_checkbox(sec, "Enable ESP", g_esp_enabled);
    section_slider_float(sec, "Max Distance", g_esp_distance, 0.0, 5000.0);
    // color picker, keybind, etc.
}
```

**Why:** Hardcoded thresholds mean recompiling to tweak. The overlay is your debugger — every value you might change during a session should be adjustable live. This also means someone else can use your script without reading the source.

---

## 12. Verify With the Binary, Not With Your Memory

**The IDB, the sig, and the live read must agree. If they don't, trust the live read.**

When something doesn't work:
1. Check the sig still hits in the current binary: `find_code_pattern` returns 0? Offset table is stale.
2. `struct_dump` the entity at the base you have — verify the field layout visually.
3. Cross-reference against the r5sdk headers or IDA's type info, but remember the SDK may be from an older season.
4. If the live read shows a valid-looking float where you expected an int, the struct changed. Update your types.
5. Never assume your cached offset table is correct after a game update. Re-scan everything.

```
Debugging checklist:
1. Is the process alive?           → p.alive()
2. Is the module loaded?           → get_module_base() != 0
3. Does the sig still hit?         → find_code_pattern() != 0
4. Is the pointer chain valid?     → check every link for 0
5. Does the field contain what     → struct_dump() or read + print
   you expect?
```

---

## Summary

| # | Rule | One-liner |
|---|------|-----------|
| 1 | Know the target | Ground every offset in evidence |
| 2 | `uint64` addresses | One type, zero sign bugs |
| 3 | Validate chains | Every pointer can be null |
| 4 | Separate scan/render | Reads and draws don't mix |
| 5 | Sigs over hardcodes | Survive patches |
| 6 | One feature, one file | No god scripts |
| 7 | Construct every frame | Colors and vecs are free |
| 8 | `f` suffix for float32 | The GPU cares |
| 9 | Minimize writes | Reads are invisible |
| 10 | W2S once, correctly | Math, not magic |
| 11 | GUI for all tunables | No magic constants |
| 12 | Verify with the binary | Trust live reads over memory |

---

## Source: `.claude/skills/game-hacking-pcx/SKILL.md`

---
name: game-hacking-pcx
description: >
  Mandatory doc router for all PCX scripting sessions. Triggers on any game
  hacking, Enma, AngelScript, or Perception.cx work. Provides the full doc
  index (34,000+ lines across 110 files) and enforces reading the relevant
  documentation before writing any API call. Load alongside
  game-cheat-guidelines on every PCX session.
license: MIT
---

# Game Hacking & Scripting — Perception.cx / Enma / AngelScript / C++

## Trigger
Game hacking, game cheats, memory reading/writing, ESP, aimbot, pattern scanning, vtable hooking,
process manipulation, Enma scripting, AngelScript scripting, Perception.cx, PCX, render overlays,
any `.em` or `.as` game script work, or any mention of the Perception platform.

## MANDATORY: Read Before Writing Code

**You MUST read the relevant docs from `docs/` before writing ANY Enma, AngelScript,
or PCX API code.** Do not write from memory. The docs are the source of truth.

### When writing Enma (.em) code — read these:

**Language (always read `llms-language.md` first — it's the complete single-page reference):**
| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Complete language ref** | `docs/enma/llms-language.md` | 2861 | Every type, operator, control flow, struct, class, template, coroutine, exception, heap, FFI, annotation, module, addon |
| Complete SDK ref | `docs/enma/llms-sdk.md` | 832 | Embedding API, type registration, native functions, hot reload |

**Language guide (granular pages if you need detail beyond the single-page ref):**
| Doc | Path | Lines |
|-----|------|-------|
| Basics (types, vars, operators, control flow) | `docs/enma/lang-basics.md` | 267 |
| Functions (params, defaults, refs, out, variadic, lambdas) | `docs/enma/lang-functions.md` | 247 |
| Pointers (heap, address-of, member access, null) | `docs/enma/lang-pointers.md` | 357 |
| Structs & Classes (value/ref types, inheritance, vtable, interfaces, mixins) | `docs/enma/lang-structs-and-classes.md` | 912 |
| Templates (generics, monomorphization) | `docs/enma/lang-templates.md` | 173 |
| Advanced (delegates, namespaces, coroutines, exceptions, smart ptrs, FFI) | `docs/enma/lang-advanced.md` | 562 |
| Annotations (packed, align, reflect, serialize, export, dll, custom) | `docs/enma/lang-annotations.md` | 209 |
| Modules (import, .emb, multi-module linking) | `docs/enma/lang-modules.md` | 100 |
| Preprocessor (#define, #ifdef, #include, #pragma) | `docs/enma/lang-pre-processor.md` | 77 |
| Semantics & Limits (guarantees, compile-time rejects, what doesn't exist) | `docs/enma/lang-semantics-and-limits.md` | 181 |

**Addons (standard library — read the addon doc before using its types):**
| Addon | Path | Lines | Key types/functions |
|-------|------|-------|---------------------|
| Core | `docs/enma/addon-core.md` | 42 | `println`, `print` |
| Strings | `docs/enma/addon-strings.md` | 165 | `format`, `to_int`, `split`, `replace`, `substr` |
| Arrays | `docs/enma/addon-arrays.md` | 119 | `push`, `pop`, `sort`, `contains`, `slice`, `for-each` |
| Maps | `docs/enma/addon-maps.md` | 200 | `map<K,V>`, `get`, `set`, `contains`, `imap<V>` |
| Math | `docs/enma/addon-math.md` | 137 | `sin`, `cos`, `atan2`, `sqrt`, `clamp`, `lerp`, `random` |
| SIMD | `docs/enma/addon-simd.md` | 128 | SSE2 `f32x4`, `i32x4` vector ops |
| Vectors | `docs/enma/addon-vec.md` | 135 | `vec2`, `vec3`, `vec4` math types |
| 3D Math | `docs/enma/addon-math3d.md` | 182 | `quat`, `mat4` rotation/transform |
| Variant | `docs/enma/addon-variant.md` | 130 | Type-erased value container |
| Atomic | `docs/enma/addon-atomic.md` | 94 | `aint32`, `aint64` atomic ops |
| Bits | `docs/enma/addon-bits.md` | 117 | `popcount`, `clz`, `ctz`, `bswap`, `rotl` |
| Time | `docs/enma/addon-time.md` | 95 | `time_ms()`, `time_us()`, ISO 8601, `sleep` |
| Regex | `docs/enma/addon-regex.md` | 61 | `match`, `find`, `replace`, `split`, capture groups |
| File | `docs/enma/addon-file.md` | 125 | Sandboxed file I/O (permission-gated) |
| Thread | `docs/enma/addon-thread.md` | 120 | `mutex`, `lock_guard`, `condition_variable` |
| Hash Set | `docs/enma/addon-hash_set.md` | 89 | `hash_set<T>` |
| Sorted Map | `docs/enma/addon-sorted_map.md` | 89 | `sorted_map<K,V>` ordered iteration |
| List | `docs/enma/addon-list.md` | 192 | Double-ended O(1) push/pop |
| JSON | `docs/enma/addon-json.md` | 108 | `json_parse`, `json_stringify`, `json_value` navigation |

**SDK (C++ embedding — read when building host-side or custom addons):**
| Doc | Path | Lines |
|-----|------|-------|
| Quick Start | `docs/enma/sdk-quick-start.md` | 126 |
| Engine Lifecycle | `docs/enma/sdk-engine-lifecycle.md` | 166 |
| Compilation | `docs/enma/sdk-compilation.md` | 65 |
| Execution | `docs/enma/sdk-execution.md` | 103 |
| Calling Functions | `docs/enma/sdk-calling-functions.md` | 82 |
| Globals | `docs/enma/sdk-globals.md` | 79 |
| Type Registration | `docs/enma/sdk-type-registration.md` | 862 |
| Native Functions | `docs/enma/sdk-native-functions.md` | 446 |
| Hot Reload | `docs/enma/sdk-hot-reload.md` | 64 |
| Serialization & Linking | `docs/enma/sdk-serialization-and-linking.md` | 97 |
| Introspection | `docs/enma/sdk-introspection.md` | 317 |
| Lifecycle & RAII | `docs/enma/sdk-lifecycle.md` | 227 |
| Debug & Heap | `docs/enma/sdk-debug-and-gc.md` | 202 |
| Error Handling | `docs/enma/sdk-error-handling.md` | 116 |
| Safety | `docs/enma/sdk-safety.md` | 121 |
| Custom Addons | `docs/enma/sdk-custom-addons.md` | 576 |
| API Reference | `docs/enma/sdk-api-reference.md` | 411 |

### When writing PCX Enma API code — read the relevant API doc:

| API | Path | Lines | Use for |
|-----|------|-------|---------|
| **Proc API** | `docs/perception/proc-api.md` | 294 | Memory read/write, modules, pattern scan, VAD, pointer arrays, vec/quat/mat reads |
| **Render API** | `docs/perception/render-api.md` | 264 | 2D drawing (text, lines, circles, rects), fonts, shaders, vertex/index buffers, compute |
| **GUI API** | `docs/perception/gui-api.md` | 455 | Sidebar sections, checkboxes, sliders, buttons, text inputs, color pickers, keybinds |
| **Input API** | `docs/perception/input-api.md` | 126 | Mouse + keyboard state polling |
| **CPU API** | `docs/perception/cpu-api.md` | 92 | CPU ID, timing, datetime, bitcasts, thread priority |
| **Zydis API** | `docs/perception/zydis-api.md` | 133 | x86-64 assembler/disassembler |
| **Unicorn API** | `docs/perception/unicorn-api.md` | 151 | x86-64 CPU emulation |
| **Net API** | `docs/perception/net-api.md` | 200 | HTTP, WebSocket, raw UDP |
| **Win API** | `docs/perception/win-api.md` | 120 | Window enum, clipboard, keyboard/mouse send |
| **Filesystem API** | `docs/perception/filesystem-api.md` | 162 | Sandboxed file I/O |
| **Sound API** | `docs/perception/sound-api.md` | 90 | WAV/OGG playback |
| **Lifecycle** | `docs/perception/lifecycle-and-routines.md` | 134 | main(), routines, unload, exceptions |
| **MCP API** | `docs/perception/mcp-api.md` | 268 | AI agent JSON-RPC surface |

### When writing PCX AngelScript (.as) code — read these:

| API | Path | Lines |
|-----|------|-------|
| Overview | `docs/perception/angelscript/overview.md` | 68 |
| Life Cycle | `docs/perception/angelscript/life-cycle.md` | 128 |
| Engine | `docs/perception/angelscript/engine.md` | 178 |
| Atomic Types | `docs/perception/angelscript/atomic-types.md` | 185 |
| Proc API | `docs/perception/angelscript/proc-api.md` | 1156 |
| Render API | `docs/perception/angelscript/render-api.md` | 1829 |
| GUI API | `docs/perception/angelscript/gui-api.md` | 718 |
| Input API | `docs/perception/angelscript/input-api.md` | 226 |
| System/CPU/Disasm | `docs/perception/angelscript/system-api-cpu-and-disassembly.md` | 304 |
| Net API | `docs/perception/angelscript/net-api.md` | 379 |
| File System | `docs/perception/angelscript/file-system.md` | 298 |
| Extended Math | `docs/perception/angelscript/extended-math-api.md` | 580 |
| Win API | `docs/perception/angelscript/win-api.md` | 594 |
| JSON API | `docs/perception/angelscript/json-api.md` | 479 |
| Unicorn | `docs/perception/angelscript/unicorn.md` | 702 |
| Zydis Encoder | `docs/perception/angelscript/zydis-encoder.md` | 703 |
| Intrinsics | `docs/perception/angelscript/intrinsics.md` | 661 |
| Mutex API | `docs/perception/angelscript/mutex-api.md` | 248 |
| Utilities | `docs/perception/angelscript/utilities.md` | 607 |
| Sound API | `docs/perception/angelscript/sound-api.md` | 250 |
| Bit Reinterpret | `docs/perception/angelscript/bit-reinterpret-helpers.md` | 167 |
| Engine Specific | `docs/perception/angelscript/engine-specific-api.md` | 195 |
| CS2 Extended | `docs/perception/angelscript/cs2-extended-api.md` | 165 |

### PCX IDE & Extensions:

| Doc | Path | Lines |
|-----|------|-------|
| Perception IDE | `docs/perception/ide.md` | 585 |
| Extensions API | `docs/perception/extensions-api.md` | 371 |
| Analyzer | `docs/perception/analyzer.md` | 370 |

### PCX Lua (.lua) scripting:

| API | Path | Lines |
|-----|------|-------|
| Overview | `docs/perception/lua/overview.md` | 59 |
| All APIs | `docs/perception/lua/*.md` | 5779 total |

## How To Use These Docs

1. **Before writing Enma code**: `read docs/enma/llms-language.md` (the single-page complete ref)
2. **Before calling a PCX API**: `read docs/perception/<api-name>.md`
3. **Before writing AngelScript**: `read docs/perception/angelscript/<api-name>.md`
4. **If unsure about a type, function, or parameter**: read the doc, don't guess
5. **If the doc says a function is "gated"**: it requires a permission flag — mention this to the user

## Critical Enma Rules (from the docs)

- **Addresses are `uint64`**, never `int64` — sign-extension breaks high addresses
- **`float32` literals need `f` suffix**: `0.2f` not `0.2`
- **Implicit conversion: `int→float` OK, `float→int` COMPILE ERROR** — use `cast<int32>(f)`
- **`signed↔unsigned` is COMPILE ERROR** — use `cast<uint64>(signed_val)`
- **`color` and `vec2` are value types** — 4-byte and 8-byte stack structs, construct every frame
- **Handles from `create_*`/`load_*` are encrypted `int64`** — pass back, don't inspect
- **`main()` returns `> 0` to stay loaded, `<= 0` to unload**
- **Routines registered via `register_routine(cast<int64>(fn), data)`**
- **`proc_t` released on scope exit** (RAII) — no leak if you use stack variables
- **Failed reads return 0**, not exceptions — validate pointers
- **Pattern sigs**: hex bytes, `??` wildcard, e.g. `"48 8B 05 ?? ?? ?? ?? 48 85 C0"`
- **`import "vec"; import "color";`** — modules must be imported to use their types
- **`string` interpolation**: `f"value={x}"` — use `format()` for hex: `format("0x{x}", addr)`
- **No garbage collector** — deterministic RAII, destructors run at scope exit

## LSP Servers (built, ready to use)

- **Enma LSP**: `lsp/enma-lsp/server/dist/server.js`
- **AngelScript+PCX LSP**: `lsp/angel-lsp-pcx/server/out/server.js`

## RE Tools & Knowledge

- **Plugins & FLIRT sigs**: `knowledge/re-plugins-and-tools.md` — 6 IDA plugins, 4 Ghidra extensions, 51 FLIRT sigs, diffing, ret-sync
- **Anti-cheat architecture**: `knowledge/anti-cheat-architecture.md` — EAC/BE/Vanguard/GG detection matrix
- **Kernel RE tools**: `knowledge/kernel-re-tools.md` — WinDbg, HyperDbg, Volatility, PCILeech, IRPMon
- **AC driver patterns**: `signatures/anti-cheat/common-ac-patterns.md` — driver ID, callback sigs, integrity check patterns
- **Deobfuscation**: `skill://deobfuscation` — VM/CFF/packer reversal methodology (Themida, VMProtect, OLLVM)
- **Obfuscation taxonomy**: `knowledge/obfuscation-taxonomy.md` — protector architecture and weaknesses
- **Deobfuscation tools**: `knowledge/deobfuscation-tools.md` — NoVmp, Triton, Miasm, D-810, ScyllaHide, FLOSS
- **Protector patterns**: `signatures/obfuscation/protector-patterns.md` — VMP/Themida/OLLVM section names, dispatcher patterns, anti-debug
- r5sdk: `sdks/r5sdk/` (2438 reversed headers for Apex Legends)
- IDA IDB: `idb/r5apex_dx12_dump.i64` (28936 functions, FLIRT+types)
- Ghidra: `ghidra-projects/r5apex/`
- radare2, Ghidra, semgrep MCP servers all available

---

## Source: `.claude/skills/kernel-analysis/SKILL.md`

---
name: kernel-analysis
description: >
  Technical patterns for reversing Windows kernel drivers: WDM/KMDF
  structure identification, IOCTL dispatch tables, kernel callback
  enumeration, integrity checks, obfuscation layers, and driver
  communication protocols. Focused on anti-cheat driver analysis. Always
  active when analyzing kernel driver binaries.
license: MIT
---

# Kernel Driver Analysis — Technical Patterns for AC Driver Reversing

Technical patterns for reversing Windows kernel drivers: WDM/KMDF structure identification, IOCTL dispatch table extraction, kernel callback enumeration, integrity check routines, obfuscation layers, and driver communication protocols. Focused on anti-cheat driver analysis but applicable to any Windows kernel module.

**Always active when analyzing kernel driver binaries.** This is the *technical patterns* layer — structures, commands, and code patterns. The `anti-cheat-re` skill covers the *methodology* (what order to work in and why). Load both.

**Prerequisite:** Read `knowledge/kernel-re-tools.md` for the tool reference.

## Trigger
Analyzing a `.sys` driver binary, reversing IOCTL handlers, mapping kernel callbacks, understanding WDM/KMDF dispatch tables, deobfuscating driver code, reconstructing shared memory communication, or working with kernel structures in IDA/Ghidra/radare2/WinDbg.

---

## 1. Identify the Driver Model Before Reading Instructions

**WDM, KMDF, or legacy — the model determines where the dispatch table lives and how IOCTLs are handled.**

Every Windows kernel driver has a `DriverEntry` function — the entry point. What it calls in the first few instructions tells you the model:

| Pattern in DriverEntry | Driver Model | Dispatch Location |
|---|---|---|
| `IoCreateDevice` + manual `MajorFunction[]` assignment | **WDM (legacy)** | `DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL]` |
| `WdfDriverCreate` + `WdfDeviceCreate` | **KMDF (modern)** | `WdfIoQueueCreate` with `EvtIoDeviceControl` callback |
| `GsDriverEntry` wrapper → real entry | **GS-protected** | Unwrap — the real `DriverEntry` is the first call inside |

Most anti-cheat drivers use **WDM** for direct control over IRP handling. KMDF adds a framework layer that ACs typically avoid.

```
# radare2 — find DriverEntry and identify model
r2 -AA driver.sys
afl~DriverEntry                              # find entry point
pdf @ entry0                                 # disassemble — look for first calls

# IDA — DriverEntry is the entry point
# Look for: IoCreateDevice (WDM) or WdfDriverCreate (KMDF)
# The second argument to IoCreateDevice is the device name

# WinDbg — inspect a loaded driver
!drvobj \Driver\EasyAntiCheat 7              # dump driver object + all MajorFunction handlers
dt nt!_DRIVER_OBJECT <addr>                  # raw driver object structure
```

**Finding the entry point:** In a PE driver, the entry point is `DriverEntry` (or `GsDriverEntry` which calls the real one). IDA labels it automatically with PDB or FLIRT. In r2, it's `entry0`. The function signature is:

```c
NTSTATUS DriverEntry(
    PDRIVER_OBJECT  DriverObject,   // rcx — the driver's identity
    PUNICODE_STRING RegistryPath    // rdx — HKLM\SYSTEM\...\Services\<name>
);
```

**Why:** Jumping into the instruction stream without knowing WDM vs. KMDF means you don't know where the IOCTL handler is. WDM drivers set `DriverObject->MajorFunction[14]` (IRP_MJ_DEVICE_CONTROL = 0x0E) directly in DriverEntry. KMDF drivers register it through `WdfIoQueueCreate`. Wrong model = you look in the wrong place.

---

## 2. Extract the IOCTL Dispatch Table

**The `IRP_MJ_DEVICE_CONTROL` handler contains the switch/jump table on IOCTL codes. Each code maps to a detection or communication function.**

In a WDM driver, the IOCTL handler is assigned in DriverEntry:

```c
DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = IoctlDispatch;
```

The `IoctlDispatch` function extracts the IOCTL code from the IRP stack location and switches on it:

```c
NTSTATUS IoctlDispatch(PDEVICE_OBJECT DeviceObject, PIRP Irp) {
    PIO_STACK_LOCATION stack = IoGetCurrentIrpStackLocation(Irp);
    ULONG code = stack->Parameters.DeviceIoControl.IoControlCode;

    switch (code) {
        case IOCTL_HEARTBEAT:       return HandleHeartbeat(Irp);
        case IOCTL_SCAN_REQUEST:    return HandleScanRequest(Irp);
        case IOCTL_QUERY_STATUS:    return HandleQueryStatus(Irp);
        // ...
    }
}
```

**Decoding IOCTL codes:** The `CTL_CODE` macro packs four fields into a 32-bit value:

```
Bits 31-16: DeviceType    (e.g., 0x22 = FILE_DEVICE_UNKNOWN)
Bits 15-14: Access        (0=ANY, 1=READ, 2=WRITE, 3=READ|WRITE)
Bits 13-2:  Function      (0x800+ = user-defined)
Bits 1-0:   Method        (0=BUFFERED, 1=IN_DIRECT, 2=OUT_DIRECT, 3=NEITHER)

CTL_CODE(DeviceType, Function, Method, Access)
  = (DeviceType << 16) | (Access << 14) | (Function << 2) | Method
```

```python
# Python — decode an IOCTL code
def decode_ioctl(code):
    device_type = (code >> 16) & 0xFFFF
    access      = (code >> 14) & 0x3
    function    = (code >> 2)  & 0xFFF
    method      = code & 0x3
    methods = {0: "BUFFERED", 1: "IN_DIRECT", 2: "OUT_DIRECT", 3: "NEITHER"}
    print(f"DeviceType=0x{device_type:X} Function=0x{function:X} "
          f"Method={methods[method]} Access={access}")

# Example: decode_ioctl(0x22E004) → DeviceType=0x22 Function=0x801 Method=BUFFERED Access=0
```

```
# radare2 — find the IOCTL dispatch
r2 -AA driver.sys
axt @ sym.imp.IoGetCurrentIrpStackLocation   # who calls it?
# navigate to the caller — the switch/cmp chain on the IOCTL code follows

# IDA — find MajorFunction[14] assignment in DriverEntry
# The function pointer stored at offset 0x70 + 14*8 = 0xE0 in the DRIVER_OBJECT
# is the IOCTL dispatch handler
```

**Why:** The IOCTL table is the driver's API surface. Each code corresponds to a specific operation — heartbeat, scan command, status query, configuration. Mapping these codes and their buffer structures gives you the complete protocol between user-mode and kernel.

---

## 3. Enumerate Registered Kernel Callbacks

**Each callback type has a specific structure and a global array in ntoskrnl. Find them in the driver binary (registration calls) and in live memory (the arrays).**

### ObRegisterCallbacks — Handle Filtering

The most important callback for anti-cheat: intercepts `ObOpenObjectByPointer` / `NtOpenProcess` and can modify the granted access mask.

```c
// Registration structure
typedef struct _OB_CALLBACK_REGISTRATION {
    USHORT                    Version;          // OB_FLT_REGISTRATION_VERSION
    USHORT                    OperationRegistrationCount;
    UNICODE_STRING            Altitude;         // e.g., L"321000"
    PVOID                     RegistrationContext;
    OB_OPERATION_REGISTRATION *OperationRegistration;
} OB_CALLBACK_REGISTRATION;

typedef struct _OB_OPERATION_REGISTRATION {
    POBJECT_TYPE              *ObjectType;      // PsProcessType or PsThreadType
    OB_OPERATION              Operations;       // OB_OPERATION_HANDLE_CREATE | _DUPLICATE
    POB_PRE_OPERATION_CALLBACK  PreOperation;   // ← THIS is the stripping function
    POB_POST_OPERATION_CALLBACK PostOperation;
} OB_OPERATION_REGISTRATION;
```

The `PreOperation` callback receives `OB_PRE_OPERATION_INFORMATION` and modifies `DesiredAccess` to strip flags like `PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION`.

```
# WinDbg — find ObCallbacks for process objects
dt nt!_OBJECT_TYPE poi(nt!ObTypeIndexTable + 0x38)
# follow .CallbackList → linked list of OB_CALLBACK_REGISTRATION entries
```

### Process/Thread/Image Notification Callbacks

```
# WinDbg — dump the global callback arrays
# Process creation:
dps nt!PspCreateProcessNotifyRoutine L40

# Thread creation:
dps nt!PspCreateThreadNotifyRoutine L40

# Image (DLL/driver) load:
dps nt!PspLoadImageNotifyRoutine L40

# Each non-zero entry is a pointer (with low bits as flags).
# Clear the low 4 bits and resolve:
ln (<entry_value> & ~0xF)
```

### Registry Callbacks

```c
// CmRegisterCallbackEx registers a callback for all registry operations.
// The callback receives REG_NOTIFY_CLASS (enum) + operation-specific data.
// AC uses this to detect: reading/writing cheat config keys, enumerating
// driver service keys for known cheat tools.
```

### Minifilter (File System)

```c
// FltRegisterFilter uses FLT_REGISTRATION → FLT_OPERATION_REGISTRATION[]
// Each entry specifies: MajorFunction (IRP_MJ_CREATE, IRP_MJ_WRITE, etc.),
//   PreOperation callback, PostOperation callback.
// AC uses this to: detect cheat files on disk, monitor log file access,
//   prevent deletion of AC components.
```

```
# WinDbg — list minifilter instances
!fltkd.filters              # all registered minifilters
!fltkd.filter <filter_addr> # detail on one filter — shows operation callbacks
```

### ETW Threat Intelligence

```c
// The ETW TI provider (Microsoft-Windows-Threat-Intelligence) captures:
//   NtReadVirtualMemory, NtWriteVirtualMemory, NtAllocateVirtualMemory,
//   NtProtectVirtualMemory, NtMapViewOfSection — cross-process.
// AC registers as a consumer of this provider via EtwRegister.
// The provider GUID: {F4E1897C-BB5D-5668-F1D8-040F4D8DD344}
```

**Why:** Each callback is a sensor. Missing one means you don't know the AC is watching that specific operation. A cheat that calls `NtOpenProcess` without knowing about `ObRegisterCallbacks` will silently get a crippled handle and not understand why reads fail.

---

## 4. Analyze Integrity Check Routines

**Integrity checks are loops that hash, compare, or time-measure. Find them by their structure, not their name — they're rarely labeled.**

### Code Section Hashing

Pattern: a loop that reads pages from the game's `.text` section and feeds them to a hash function. Look for:
- `MmCopyVirtualMemory` or `KeStackAttachProcess` + direct read — the driver reads the game's code pages
- A hash accumulator loop (XOR / rotate / add, or a call to `RtlComputeCrc32` / a custom SHA variant)
- A comparison against a stored expected hash — mismatch = detection

```
# In IDA/r2 — find code-hashing routines:
# Look for references to PE section headers (.text base + size)
# followed by a read loop with XOR/rotate/add operations.
# The stored "good" hash is often in the driver's .data section
# or received via IOCTL from the service.
```

### Timing Checks

Pattern: `RDTSC` (or `KeQueryPerformanceCounter`) called twice around a block, delta compared against a threshold. VM exits and single-stepping inflate the delta.

```asm
; Typical RDTSC anti-debug/anti-VM check
rdtsc                    ; read timestamp counter → EDX:EAX
mov esi, eax             ; save low 32 bits
; ... sensitive operation ...
rdtsc
sub eax, esi             ; delta = current - saved
cmp eax, 0x1000          ; threshold — if delta > 0x1000, VM/debugger suspected
ja  detected
```

### Hypervisor Detection

```asm
; CPUID leaf 1 — check VMX bit
mov eax, 1
cpuid
bt  ecx, 31              ; bit 31 = hypervisor present
jc  hypervisor_detected

; CPUID leaf 0x40000000 — hypervisor brand string
mov eax, 0x40000000
cpuid
; EBX:ECX:EDX = brand string: "VMwareVMware", "Microsoft Hv", "KVMKVMKVM", etc.
```

### Manual-Mapped Driver Detection

The AC walks kernel data structures to find drivers loaded outside the normal `IoLoadDriver` path:

- `PsLoadedModuleList` — official module list; manually mapped drivers aren't in it
- `MmUnloadedDrivers` — recently unloaded drivers; some mappers leave traces here
- `PiDDBCacheTable` — driver database cache; SCM-loaded drivers appear here even after unload
- `BigPoolTable` / `MmAllocateIndependentPages` — large kernel allocations that could be mapped driver images

```
# WinDbg — walk loaded module list
lm                                    # all loaded modules
!pool <addr> -t                       # check if an address is in a known pool allocation
dt nt!_KLDR_DATA_TABLE_ENTRY <addr>   # module list entry structure
```

**Why:** Integrity checks are the AC's runtime assertions. Each one is a specific, findable code pattern. Reversing them tells you exactly what invariants the AC enforces — and by exclusion, what it doesn't check.

---

## 5. Decode Obfuscation Layers

**AC drivers obfuscate to slow analysis. Identify the obfuscation type, then defeat it systematically — not by reading obfuscated instructions.**

### Import Obfuscation

Instead of importing `ObRegisterCallbacks` directly (which would appear in the import table), AC drivers resolve functions at runtime:

```c
// Common pattern — hash-based dynamic import
typedef NTSTATUS (*fn_ObRegisterCallbacks)(POB_CALLBACK_REGISTRATION, PVOID*);
fn_ObRegisterCallbacks pObRegister;

// In DriverEntry:
UNICODE_STRING name = RTL_CONSTANT_STRING(L"ObRegisterCallbacks");
pObRegister = (fn_ObRegisterCallbacks)MmGetSystemRoutineAddress(&name);
// Or: hash-based resolution — hash each export in ntoskrnl and compare
```

**Finding dynamically resolved imports:**
```
# radare2 — find MmGetSystemRoutineAddress calls
axt @ sym.imp.MmGetSystemRoutineAddress
# for each call site, the argument (rcx) points to a UNICODE_STRING
# with the function name being resolved
```

### Encrypted Strings

AC drivers encrypt configuration strings, device names, and error messages. Common schemes: XOR with a static key, RC4, AES-128 with a key derived from system state (build number, KUSER_SHARED_DATA timestamp).

**Strategy:** Find the decryption stub (called before each string use), extract the key, and apply it to all encrypted blobs. Or: hook the decryption function in WinDbg and log cleartext outputs.

### Control Flow Flattening

The compiler (or a post-processing tool like LLVM-obfuscator) replaces normal control flow with a state machine: a loop with a switch on a state variable. Each basic block sets the next state and jumps back to the switch.

**Strategy:** Trace the state transitions to recover the original control flow graph. Tools: D-810 (IDA plugin for deobfuscation), or manual state-machine tracing in the debugger.

### Virtualized Code (Themida / VMProtect)

Critical sections may be virtualized — converted to bytecode for a custom VM interpreter embedded in the driver. The VM dispatcher is a loop that fetches, decodes, and executes bytecodes.

**Strategy:** Identify the VM dispatcher (large switch or computed-goto loop), then either:
- Trace the bytecode execution in WinDbg and log the effective operations
- Use devirtualization tools (VMHunt, NoVmp for VMProtect) if available
- Focus on inputs/outputs of the virtualized block rather than reversing the VM itself

**Why:** Obfuscation is meant to waste your time. Identify the *type* of obfuscation, apply the standard counter for that type, and move on. Don't read obfuscated code instruction by instruction — that's what the obfuscation wants you to do.

---

## 6. Reconstruct Driver Communication Structures

**Beyond IOCTLs, drivers use shared memory, events, and direct kernel object manipulation to communicate. Find the shared region and map its layout.**

### Shared Memory

The driver creates a section object and maps it into both kernel and user-mode address space:

```c
// Kernel side (in DriverEntry or IOCTL handler):
ZwCreateSection(&hSection, SECTION_ALL_ACCESS, &oa, &maxSize,
                PAGE_READWRITE, SEC_COMMIT, NULL);
ZwMapViewOfSection(hSection, ZwCurrentProcess(), &kernelAddr, ...);

// User-mode side (in the service):
// The service opens the section by name or receives a handle via IOCTL,
// then calls NtMapViewOfSection to map the same pages.
```

**Finding shared memory in the driver:**
```
# Look for section-creation APIs:
axt @ sym.imp.ZwCreateSection
axt @ sym.imp.MmMapLockedPagesSpecifyCache
axt @ sym.imp.MmAllocateContiguousMemory

# The buffer structure is defined by the driver — you must reverse it from
# how both sides read/write the mapped region.
```

### Kernel Events

```c
// Named event for signaling:
IoCreateNotificationEvent(&eventName, &eventHandle);
// Driver sets: KeSetEvent(event, 0, FALSE);
// Service waits: WaitForSingleObject(eventHandle, INFINITE);
```

### Direct Process Memory

Some ACs write scan results directly into the game process memory (via `KeStackAttachProcess` + `RtlCopyMemory`) to avoid IOCTL round-trips.

**Why:** Not all driver communication goes through IOCTLs. Missing the shared memory region means missing an entire communication channel — heartbeat data, scan results, or configuration that never touches the IOCTL handler.

---

## Summary

| # | Pattern | One-liner |
|---|---------|-----------|
| 1 | Driver model | WDM vs KMDF determines where the dispatch table lives |
| 2 | IOCTL dispatch | Extract codes, decode `CTL_CODE`, reverse buffer structures |
| 3 | Kernel callbacks | Every registration is a detection vector — find them all |
| 4 | Integrity checks | Hash loops, RDTSC pairs, CPUID checks, module walks — find by structure |
| 5 | Obfuscation | Identify the type (import/string/CFG/VM), apply the standard counter |
| 6 | Communication | Shared memory, events, direct writes — not everything is an IOCTL |

---

## Source: `.claude/skills/mcp-tool-routing/SKILL.md`

---
name: mcp-tool-routing
description: >
  Routing guide for the 42+ Perception MCP tools — which to pick for memory
  reads, scans, disassembly, and analysis to avoid slower or redundant calls.
  Always active when calling Perception MCP tools. Answers "which tool for
  this task" so the AI picks the cheapest tool with the required precision.
license: MIT
---

# Perception MCP Tool Routing — The Decision Guide

37 tools across memory / analysis / scanning / process / files. This skill answers "which one for this task" so the AI doesn't reach for the wrong tool. The Perception MCP server (`mcp/perception-mcp-config.json`) exposes a wide surface where several tools overlap in capability but differ wildly in cost or precision — using `read_memory` for what `read_typed_value` does costs you a parse step; using `find_pattern` for what `scan_string` does is an order of magnitude slower; using `analyze_function` for what `disassemble` does costs an unnecessary IDA-style pass. Routing matters.

**Always active when calling Perception MCP tools.** Before every MCP call, the question is: am I picking the cheapest tool that gives me the precision I need? This skill makes that decision tree explicit.

**Prerequisite:** `mcp/perception-mcp-config.json` is the authoritative tool list and signatures. `mcp/claude-code-setup.md` covers the wiring. `mcp/cursor-setup.md` covers the Cursor variant. This skill is the *routing* layer that sits above all of those.

---

## Trigger

About to call a Perception MCP tool, deciding between `read_memory` vs `read_typed_value` vs `struct_dump`, choosing between `find_pattern` vs `scan_string` vs `find_string_refs`, deciding when `analyze_function` is worth its cost over `disassemble`, deciding whether to call a tool per-frame or cache the result, composing multiple tools into a workflow.

---

## 1. "I Need to Read N Bytes at Address X"

**Decision tree, cheapest precise option first:**

```
Is it a typed scalar (one int / float / pointer)?
  └── yes → read_typed_value(addr, type)
            cheapest; parses for you; one round trip

Is it a known struct (you have a declaration)?
  └── yes → struct_dump(addr, struct_name)
            one read of the whole struct, parsed by name

Is it a pointer chain (deref → +offset → deref → ...)?
  └── yes → read_pointer_chain(start, [offsets...])
            saves N round trips; the server does the chase

Is it a null-terminated string?
  └── yes → read_string(addr, max_len, charset?)
            chooses null termination over fixed length

Otherwise — a raw byte buffer:
  └── read_memory(addr, length)
            no parsing, returns bytes
```

The cost gradient (cheapest left, most expensive right):

```
read_typed_value < read_string < struct_dump < read_pointer_chain < read_memory(large N)
```

`read_memory` for a 4-byte field where `read_typed_value` would do it costs you a manual struct-unpack on the client side and one extra parse round trip. `read_memory` for a 12-byte vec3 where `read_typed_value` for each component would also work depends — if you call `read_typed_value` three times, that's three round trips vs one `read_memory` for 12 bytes. Use `read_memory` when N ≥ 8 *and* you need the raw bytes, or use `read_typed_value` when you need one specific component cheaply.

`struct_dump` requires that the server side knows the struct. When it does, it's the right answer almost always. When it doesn't, fall back to `read_memory(addr, sizeof_struct)` + client-side parsing — but consider whether to define the struct so future calls are clean.

`read_pointer_chain` is the killer feature for entity-list walks. Instead of `read_typed_value` × 3 (deref base, deref +offset, deref +offset), one call does all three.

**Why:** Most "slow MCP" complaints reduce to picking `read_memory` when a typed variant would be faster, or picking three calls when `read_pointer_chain` would do it in one. The cost of a wrong choice is per-frame latency; the cost of the right choice is reading the doc once.

---

## 2. "I Need to Find Something in Memory"

**Different "find" tools for different inputs.** Picking the wrong one is the most common search-related mistake.

```
What are you looking for?
  ASCII / UTF-8 string?  → scan_string(needle, [section?])
  UTF-16LE string?       → scan_wstring(needle, [section?])
  Specific numeric value (4/8 bytes)?  → scan_value(value, size)
  A pointer to a known address?         → scan_pointer_to(target_addr)
  A specific instruction pattern (bytes + wildcards)?  → find_pattern(bytes, mask)
  References to a function in code?     → find_xrefs(func_addr)
  References to a known string?         → find_string_refs(string_addr OR string_literal)
  What changed since I last looked?     → scan_changed() then diff_memory(then, now)
```

The cost gradient (cheapest first):

```
scan_string ~ scan_wstring ~ scan_value < scan_pointer_to < find_pattern < find_xrefs < find_string_refs < scan_changed
```

Special-case observations:

- **`find_pattern` is for *code* sigs**, not random data — it's faster on `.text` than `.data` because the search is bounded to executable sections by default. If you're searching `.data`, a `scan_value` for the discriminating field is usually faster.
- **`scan_pointer_to` is the right tool for "find every variable that points to this object"** — pointer scans for tracing object ownership / entity-list discovery. Faster than `find_pattern` for an 8-byte address because the search knows the alignment and excludes obvious-noise patterns.
- **`find_string_refs` does the cross-reference walk for you**: pass a string literal, get back the addresses of every instruction that loads it via `LEA`/`MOV [rip+...]`. The combo `find a UI label → find_string_refs → analyze_function` is the canonical "find the function that owns this UI element" workflow.
- **`scan_changed` + `diff_memory` is the cheat-engine workflow**: snapshot the process state, do an in-game action, snapshot again, diff. The output is a list of changed addresses + before/after values. Use sparingly — it scans the whole process and is expensive.

**Why:** `find_pattern` is the tool every new user reaches for because it sounds the most general. It's actually the most *specialized* — it scans `.text` for code patterns. For data search (string, value, pointer), the dedicated scan tools are 5-10× faster because they know the type they're hunting for.

---

## 3. "I Need to Understand This Function"

**Cost-tiered: just see the asm vs full IDA-style analysis. Pick the depth you actually need.**

```
Just want the disassembly of a few instructions?
  → disassemble(addr, num_insns)
    cheap; one call; bytes → asm

Need start/end of the function containing addr?
  → find_function_bounds(addr)
    cheap; returns [start, end]

Need what the function calls + complexity hints?
  → analyze_function(addr)
    medium; recursive into prologue/epilogue, calls table

Need the full call graph rooted at addr?
  → build_call_graph(addr, depth)
    expensive; can be slow on deep / wide call graphs — cap depth

Need to know what value RCX/RDX/etc. holds at a specific instruction?
  → trace_register(addr, register, direction)
    medium; useful for "what's the first argument to this call site"
```

The standard composition:

```
find_pattern(sig)              → addr
find_function_bounds(addr)     → [start, end]
disassemble(start, end-start)  → asm
trace_register(call_addr, RCX) → what gets passed
```

This is the four-step "what does this code path do?" workflow that replaces an IDA session for most questions.

Avoid `build_call_graph` unless you actually need the graph as a graph. For "what does this function call," `analyze_function` returns the immediate call list, which is usually what you wanted.

**Why:** `analyze_function` and `build_call_graph` are the most expensive tools in the routing table. Calling them when `disassemble` would do is multi-second latency vs millisecond latency. The cost isn't visible until you wire one into a per-frame path.

---

## 4. "I Need to Understand This Class / VTable"

**Two tools, often used together:**

```
Want the vtable function-pointer layout?
  → analyze_vtable(vtable_addr)
    returns ordered list of [offset, function_addr] entries

Want the RTTI class name + parent chain?
  → read_rtti(object_addr)
    returns class name string + inheritance hierarchy
```

The combo gives you a full picture of "what is this object?" — start with `read_rtti` to know the class, then `analyze_vtable` to get the methods. Together they replace a Class Informer / Class Explorer pass in IDA.

Caveat: RTTI is only present in binaries compiled with `/GR` (MSVC) or `-frtti` (GCC/Clang). Stripped binaries return nothing useful from `read_rtti`. In that case, the vtable layout is your only handle on the class identity — name your "VTable_<addr>" yourself.

**Why:** Class identification is half the battle in any C++ game RE. `read_rtti` answers "what is this?" in one call when it works; falling back to vtable layout matching is the alternative. Routing here is binary: try RTTI first, fall back to vtable analysis.

---

## 5. "I Need a Sig for This Address"

**`generate_signature(addr, length_hint)` produces a sig from the instruction at `addr`, with sensible wildcarding of relocatable bytes (RIP-relative displacements, call targets).**

Pair immediately with `tools/sig-uniqueness-checker.py` (added in this branch) to validate:

```
1. generate_signature(addr, 16)         → "48 8D 0D ?? ?? ?? ?? E8"
2. write to a temp file, then:
3. python3 tools/sig-uniqueness-checker.py game.exe --sig "..."
4. read the verdict:
   - UNIQUE margin=5    → ship it
   - AMBIGUOUS, N hits  → regenerate with longer length
   - STALE              → the sig doesn't match at the expected address (very rare; investigate)
   - BRITTLE margin=0   → regenerate longer
```

The `length_hint` is a starting point; you can iterate with `generate_signature(addr, 24)` if the 16-byte version is ambiguous. Each generation is cheap; the validation step is also cheap. Iterate until UNIQUE with `margin ≥ 2` and add the sig to your `offsets.em` with an `// E-NNN` evidence reference (per `skill://re-evidence-log`).

**Why:** The MCP can generate sigs but cannot validate them; the local Python tool can validate sigs but cannot generate them from a live address. The combination is the workflow.

---

## 6. "I Need to Know About the Process / Modules"

**Process and module enumeration tools.** All cheap; safe to call at script start.

```
What processes are running?                → list_processes()
Info on one process (pid, threads, modules)? → get_process_info(pid OR name)
What does this module export?              → get_module_exports(module_name)
What does this module import?              → get_module_imports(module_name)
```

For deeper cross-module analysis (which other modules import a specific export from this one), pair with `tools/module-export-mapper.py --consumers <dir>` (added in this branch). The MCP gives you exports + imports per module; the Python tool joins them into "this DLL is consumed by ..." map.

`get_process_info` is the right call when attaching: it returns the module list including base addresses + sizes, which is what you need for `find_pattern` calls bounded to a specific module. Don't iterate `list_processes` + `get_module_exports` per module yourself — `get_process_info` returns the full picture in one call.

**Why:** These tools are cheap and idempotent; the routing is mostly "use them rather than guessing." The only mistake is overusing `list_processes` in a loop — it scans the system every call. Call it once; cache the result.

---

## 7. "I Need to Work with Files / Scripts"

**File and script lifecycle tools.** Mostly self-explanatory but the validate/check/execute trio is worth mapping out.

```
Read a file:        read_file(path)
Write a file:       write_file(path, contents)
Patch a file:       edit_file(path, [{search, replace}, ...])

Grep across files:  search_text(pattern, [scope?])
Find references:    find_references(symbol, [scope?])

Compile-only:       check_script(path)   ← syntax + types, no run
Semantic check:     validate_script(path) ← deeper passes (unused decls, etc.)
Run it:             execute_script(path)  ← actually loads + runs

What APIs are available? get_script_api()  ← runtime API surface for the active scripting language
```

The check/validate/execute progression:

- `check_script` first — compile-only, catches syntax + type errors. Cheap; safe to run on every save.
- `validate_script` when you're about to ship — deeper checks: unused decls, unreachable code, suspicious patterns. Slower; run before release.
- `execute_script` only when you actually want to run it — actively loads into the engine and starts callbacks. Has side effects (attaches to processes, allocates GPU resources).

`get_script_api()` is the version-introspection tool — returns the currently-available API surface, useful for runtime checks and for documenting what your script depends on. Pair with `knowledge/pcx-version-matrix.md` for the historical timeline.

**Why:** Mixing up `check_script` and `execute_script` is the new-user mistake — running the script when you only wanted to check syntax. The progression cheap → medium → side-effecting is the right ladder; climb only as far as the question demands.

---

## 8. Cost Tiers — What's Expensive, What's Cheap

**Internalize these tiers. Cheap tools are fine in tight loops; expensive ones must be cached or called outside hot paths.**

| Tier | Tools | Latency feel |
|---|---|---|
| **Cheap** (<1 ms typical) | `list_processes`, `get_process_info`, `get_module_exports`, `get_module_imports`, `read_typed_value`, `read_memory` (small), `read_string`, `disassemble` (1-2 insns), `find_function_bounds`, `read_rtti` | Safe per-call when you need them |
| **Medium** (1-100 ms) | `find_pattern`, `scan_string`, `scan_wstring`, `scan_value`, `scan_pointer_to`, `struct_dump`, `read_pointer_chain`, `read_memory` (large), `analyze_function` (small), `analyze_vtable`, `find_xrefs`, `find_string_refs`, `trace_register`, `generate_signature` | Cache results; never call per-frame |
| **Expensive** (100 ms-10 s) | `build_call_graph` (deep), `analyze_function` (with deep recursion), `scan_changed` (whole-process), `diff_memory` (large region), `search_text` (large codebase), `find_references` (large codebase), `validate_script` (large project), `web_search` | Manual workflow tools; never automated into hot paths |
| **Side-effecting** | `memory_write`, `write_file`, `edit_file`, `execute_script` | Permission-gated; ask before doing |

The pattern in PCX scripts: call medium-tier tools in `main()` (one-shot setup), cache results into globals, then in `on_update` / `on_render` only call cheap tools. The 12-rule discipline (`game-cheat-guidelines` rule #4: separate update from render; `skill://pcx-perf-budget` Step 5: cache expensive, recompute cheap) is the same principle applied to MCP calls.

**Why:** The MCP latency budget is shared with the rest of your frame. A 5 ms `find_pattern` in `on_render` at 144 Hz eats 72% of the frame. Tier awareness is what keeps the script smooth.

---

## 9. Composition Patterns — Tools That Compose Well

**The standard combos. Each is a four-to-five-call workflow that's reused across most RE sessions.**

| Goal | Composition |
|---|---|
| "Find the function that handles a UI label" | `scan_string(label)` → `find_string_refs(addr)` → `analyze_function(call_addr)` |
| "Find a global pointer behind a LEA" | `find_pattern(sig)` → `read_typed_value(hit+3, "int32")` (the disp) → resolve RIP manually → `read_typed_value(resolved, "uint64")` |
| "What are the args passed to this call?" | `disassemble(call_site, 1)` (confirm it's a CALL) → `trace_register(call_site, "rcx", "backward")` → repeat for `rdx`, `r8`, `r9` |
| "Map an entity struct" | `read_pointer_chain([entity_list_base, 0, 0])` → `read_rtti(entity_ptr)` → `analyze_vtable(vtable_ptr)` → `struct_dump(entity_ptr, "CEntity")` |
| "Snapshot, perform action, diff" | `scan_changed()` (snapshot 1) → user does in-game action → `scan_changed()` (snapshot 2) → `diff_memory()` |
| "Sig + validate" | `generate_signature(addr, 16)` → save → `python3 tools/sig-uniqueness-checker.py game.exe --sig "..."` → if margin < 2, regenerate longer |
| "Per-binary diff after patch" | `read_file(old_offsets_json)` → `python3 tools/offset-diff.py --old V1 --new V2 --sigs old_offsets_json` → for each LOST: `find_pattern` against V2 with broadened sig → record new sig |

These compose without ceremony — each call's output is the next call's input. The AI should *reach for the composition* rather than asking "should I call N more tools?" — the workflow is the unit, not the individual call.

**Why:** Naming the compositions makes them habits. Without a name, every new user re-derives the workflow from scratch and asks each tool call as a separate question. Named compositions become muscle memory after a handful of uses.

---

## Summary — Goal → Tool Map

| Goal | Right tool | Wrong tool (common mistake) |
|---|---|---|
| Read one int/float at address | `read_typed_value` | `read_memory` + manual unpack |
| Read whole struct | `struct_dump` | N × `read_typed_value` |
| Follow pointer chain | `read_pointer_chain` | N × `read_typed_value` |
| Find string in memory | `scan_string` / `scan_wstring` | `find_pattern` |
| Find numeric value | `scan_value` | `find_pattern` |
| Find pointer to X | `scan_pointer_to` | `find_pattern` |
| Find code pattern | `find_pattern` | `search_text` (search_text is for files, not memory) |
| Find xrefs to function | `find_xrefs` | `disassemble` + manual scan |
| Find xrefs to string | `find_string_refs` | `find_pattern` on the string bytes |
| See some asm | `disassemble` | `analyze_function` |
| Get function start/end | `find_function_bounds` | `disassemble` + walk |
| Get class name | `read_rtti` | `analyze_vtable` (use both — RTTI first) |
| Get vtable layout | `analyze_vtable` | `read_memory` + manual deref |
| Generate a sig | `generate_signature` + `tools/sig-uniqueness-checker.py` | hand-crafting bytes |
| Find diff after action | `scan_changed` + `diff_memory` | `find_pattern` on guesses |

**Cross-references:** `mcp/perception-mcp-config.json` (authoritative tool list), `mcp/claude-code-setup.md` / `mcp/cursor-setup.md` / `mcp/aider-setup.md` (per-IDE wiring), `tools/sig-uniqueness-checker.py` / `tools/offset-diff.py` / `tools/dumper-to-enma.py` / `tools/module-export-mapper.py` (local CLI tools that pair with MCP calls), `skill://pcx-perf-budget` (call-cost discipline that applies to MCP calls), `skill://re-evidence-log` (E-NNN cross-references record which MCP calls produced each offset).

---

## Source: `.claude/skills/multi-binary-targeting/SKILL.md`

---
name: multi-binary-targeting
description: >
  Pattern for supporting multiple game binaries (versions, architectures,
  storefronts, beta channels) from one Enma codebase without forking.
  Triggers when the user mentions multiple game versions, cross-build support,
  32-bit vs 64-bit, multi-store builds, or maintaining stable and
  experimental branches in parallel.
license: MIT
---

# Multi-Binary Targeting — One Script, N Game Versions

The pattern for supporting multiple binaries (game versions, architectures, storefront builds, beta channels) from one Enma codebase. A well-organized script can target v1.42.3 and v1.42.4, 32-bit and 64-bit, Steam and Epic, release and beta — without forking. The mechanics are simple but get reinvented in every project; this skill names them.

**Trigger when:** the user mentions multiple game versions, cross-build support, 32-bit vs 64-bit, multi-store builds (Steam / Epic / GOG / Microsoft Store), the script breaking on the demo / beta channel / PTU, supporting both an old and a new version simultaneously, or maintaining a "stable" and an "experimental" branch in parallel.

**Prerequisite:** `knowledge/script-organization-patterns.md` for the per-binary offset file layout this skill builds on; `.claude/skills/pcx-patch-day-playbook` for the per-patch maintenance workflow this skill scales up; `.claude/skills/re-evidence-log` for the per-binary evidence tracking that prevents claims from cross-contaminating.

---

## Trigger

`Game.exe` exists at multiple hashes the user wants to support; the user maintains a shared script for both the live and beta channels of a game; cross-architecture work (`game32.exe` and `game64.exe`); Steam and Epic builds of the same game ship with different DRM wrappers; a port from one binary to another that "should be similar" but isn't quite.

---

## 1. Identify the Binary at Runtime

**Hash the `.text` section (or its first N MB) at attach time; look up which offset set to use.**

Without runtime identification, the script has no way to pick offsets — it either hardcodes one binary's values (broken on the others) or relies on the user to manually swap offset files (error-prone, defeats the multi-binary point). The hash gives the script a stable handle for "which build am I attached to."

```cpp
import "vec";

const string TARGET_MODULE = "game.exe";

// Map from `.text` hash to the offset-set identifier (a label your code
// uses internally to pick the right OFFSET_* values per binary).
struct binary_id {
    string  hash_prefix;   // first 8-16 hex chars of the .text hash
    string  label;         // "v1.42.3", "v1.42.4_steam", "v1.42.4_epic"
    string  arch;          // "x64", "x86"
}

const binary_id KNOWN_BINARIES[] = {
    binary_id("7a3f4d1c", "v1.42.3",       "x64"),
    binary_id("9b2e8a07", "v1.42.4_steam", "x64"),
    binary_id("c4f12d83", "v1.42.4_epic",  "x64"),
};

string g_active_label = "unknown";

// Identify by hashing a small range from .text — first 4 MB is usually
// enough to discriminate between builds without being slow at attach.
string identify_binary(proc_t p) {
    uint64 base = p.base_address();
    if (base == 0) return "unknown";

    // (a real implementation reads the .text section bounds via the PE
    //  parser; this sketch uses a fixed window for clarity)
    const uint64 SAMPLE_BYTES = 0x400000;   // 4 MB
    array<uint8> buf;
    buf.resize(SAMPLE_BYTES);
    if (!p.read_memory(base + 0x1000, buf, SAMPLE_BYTES)) return "unknown";

    // Hash via a stable function — md5/sha is fine; even a CRC32 is
    // enough since you only need disambiguation, not cryptographic safety.
    string hash_prefix = format("{x}", crc32_buffer(buf, SAMPLE_BYTES));
    // (crc32_buffer is documented in docs/perception/cpu-api.md; or
    //  compute inline if you prefer)

    for (uint32 i = 0; i < KNOWN_BINARIES.length; i++) {
        if (hash_prefix.starts_with(KNOWN_BINARIES[i].hash_prefix)) {
            return KNOWN_BINARIES[i].label;
        }
    }
    return "unknown";
}
```

Notes on the hash choice:

- **`.text` only**, not the whole binary. `.data` / `.rdata` change with every patch (string updates, asset references); `.text` is stable across content-only updates.
- **Sample the first N MB**, not the whole `.text`. Reading 50 MB at attach to compute a hash is slow; the first 4 MB is enough to discriminate between distinct builds.
- **CRC32 is enough**. You're not checking cryptographic integrity, just disambiguating ~5-50 known builds. CRC32 is cheap and stdlib-trivial.
- **Skip headers and relocations** in the sample window — they change cosmetically across rebuilds without changing code. Start the sample at `.text + 0x1000` (past the prologue padding).

**Why:** Without runtime identification, the script either guesses or asks the user. Guessing breaks; asking-the-user adds a manual step that defeats the multi-binary goal. The hash is the cheap, robust handle.

---

## 2. One `offsets-<label>.em` per Binary, One Common `main.em`

**The canonical layout: a `dispatch` module identifies the binary at attach, then re-exports the right per-binary constants under a common name. Every feature module imports the dispatched constants, not the per-binary ones.**

The project tree:

```
project/
├── globals.em                # proc handle, base, cached state — binary-agnostic
├── offsets-v1.42.3.em        # const uint64 OFF_ENTITY_LIST_V1_42_3 = 0x...;
├── offsets-v1.42.4_steam.em  # const uint64 OFF_ENTITY_LIST_V1_42_4_STEAM = 0x...;
├── offsets-v1.42.4_epic.em   # const uint64 OFF_ENTITY_LIST_V1_42_4_EPIC = 0x...;
├── dispatch.em               # identifies binary, selects offset set
├── esp.em                    # imports from dispatch, never from offsets-*.em
├── aim.em                    # same
├── menu.em
└── main.em
```

The `dispatch.em` module is the trick. It identifies the binary, then exposes a *common* set of names every feature uses:

```cpp
// dispatch.em
import "offsets-v1.42.3";
import "offsets-v1.42.4_steam";
import "offsets-v1.42.4_epic";

// The names every other file imports.
uint64 g_off_entity_list = 0;
uint64 g_off_local_player_slot = 0;
uint64 g_off_view_matrix = 0;
string g_sig_entity_list = "";
// ... (one per offset/sig the project uses)

bool dispatch_select(string label) {
    if (label == "v1.42.3") {
        g_off_entity_list      = OFF_ENTITY_LIST_V1_42_3;
        g_off_local_player_slot = OFF_LOCAL_PLAYER_SLOT_V1_42_3;
        g_off_view_matrix      = OFF_VIEW_MATRIX_V1_42_3;
        g_sig_entity_list      = SIG_ENTITY_LIST_V1_42_3;
        return true;
    } else if (label == "v1.42.4_steam") {
        g_off_entity_list      = OFF_ENTITY_LIST_V1_42_4_STEAM;
        // ... etc
        return true;
    } else if (label == "v1.42.4_epic") {
        // ...
        return true;
    }
    return false;
}
```

And `main.em` wires it up:

```cpp
import "dispatch";
import "globals";
import "esp";
import "aim";
import "menu";

int64 main() {
    g_proc = ref_process(TARGET_MODULE);
    if (!g_proc.alive()) { println("not attached"); return 0; }

    g_active_label = identify_binary(g_proc);
    if (!dispatch_select(g_active_label)) {
        println(format("unknown binary: {s}; no offsets available", g_active_label));
        return 0;
    }
    println(format("loaded offsets for {s}", g_active_label));

    setup_gui();
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
```

Feature modules never know which binary is active:

```cpp
// esp.em
import "dispatch";  // for g_off_entity_list

void update_entities() {
    uint64 list_ptr = g_proc.ru64(g_off_entity_list);
    if (list_ptr == 0) return;
    // ... feature logic ...
}
```

This isolates per-binary churn to `offsets-*.em` and `dispatch.em`. Adding a new build means:

1. Add `offsets-<new>.em` with the per-build constants.
2. Add a row to `KNOWN_BINARIES[]` in `dispatch.em`.
3. Add an `else if (label == "<new>")` branch in `dispatch_select`.
4. Done. Every feature module works against the new build automatically.

**Why:** Without the dispatch indirection, every feature module has to know about every supported binary, and a build-add becomes an N-file change. With it, the per-build delta is localized.

---

## 3. Sig Sets vs Hardcoded Resolved Addresses

**Prefer sigs; they survive minor patches. Fall back to per-build hardcoded RVAs only when sigs are ambiguous, or when the binary varies in a way sigs can't bridge.**

Three modes, in order of preference:

- **Same sig across all builds** (best). The sig matches in every build, RIP-resolves to the right address per build. Only the resolved address differs; the sig string in `offsets-*.em` is identical across files. Verify by running `tools/sig-uniqueness-checker.py` against each binary.
- **Per-build sig variants**. The sig had to drift because the instruction sequence changed in one of the builds. Each `offsets-<label>.em` carries its own sig string; the resolution code is shared.
- **Per-build hardcoded RVAs** (last resort). The sig can't be made to work across builds (instruction layout too different, or the function was inlined in one build); fall back to RVA constants per build. Brittle — the next patch invalidates the RVA — but works when nothing else does.

A unified sig set with per-build RIP-offset overrides covers the middle case:

```cpp
// dispatch.em — when the sig is shared but the RIP arithmetic differs
// (e.g. one build uses LEA r64, [rip+disp32] (7B), another uses
//  LEA r64, [rip+disp8] (4B) — same sig prefix, different insn_len)
struct rip_resolver {
    string sig;
    uint64 disp_at;     // byte offset within the matched instruction
    uint64 insn_len;    // total instruction length
}

rip_resolver g_resolve_entity_list;

void configure_resolvers(string label) {
    if (label == "v1.42.3" || label == "v1.42.4_steam") {
        g_resolve_entity_list = rip_resolver(SIG_ENTITY_LIST, 3, 7);   // standard LEA
    } else if (label == "v1.42.4_epic") {
        g_resolve_entity_list = rip_resolver(SIG_ENTITY_LIST, 3, 4);   // short-disp LEA
    }
}

uint64 resolve_entity_list_addr() {
    uint64 base = g_proc.base_address();
    uint64 size = g_proc.get_module_size(TARGET_MODULE);
    uint64 hit = g_proc.find_code_pattern(base, size, g_resolve_entity_list.sig);
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + g_resolve_entity_list.disp_at);
    return hit + g_resolve_entity_list.insn_len + cast<uint64>(disp);
}
```

Decision tree per offset, per supported build:

```
1. Does the same sig hit uniquely in every supported build? YES → shared sig.
2. Does a per-build sig variant hit uniquely? YES → per-build sig string.
3. Is the resolved RVA stable across at least one rebuild family? YES → hardcoded RVA.
4. None of the above? → re-RE from a closer xref; the current anchor is too unstable.
```

Cross-reference `tools/offset-diff.py` and `tools/sig-uniqueness-checker.py` for the validation workflow per build.

**Why:** Hardcoded RVAs are the multi-binary worst case — they invalidate at every patch and must be re-derived per build. Sigs let you ship one offset string that works on N versions, dropping the maintenance per-version to near zero. The choice between "shared sig + per-build RIP" and "per-build sig" is a 5-second `offset-diff.py` check; reach for it before committing.

---

## 4. Architecture Differences (x86 vs x64)

**Pointer size, calling convention, instruction-length, and sometimes struct layout all change between x86 and x64 builds. The script needs branches per architecture; isolate them in `offsets-<label>.em` and a thin abstraction in `dispatch.em`.**

What changes between a 32-bit and 64-bit build of the same game:

| Property | x86 | x64 |
|---|---|---|
| Pointer size | 4 bytes | 8 bytes |
| Pointer read API | `proc.r32(addr)` | `proc.ru64(addr)` |
| Struct field offsets | Often differ — alignment and pointer fields shift | Typically the canonical layout |
| Calling convention | `__stdcall` / `__cdecl` / `__fastcall` (variable) | MS x64 ABI (Windows) / SysV (Linux) |
| Instruction prefixes in sigs | No REX prefix (`48 ...`) | REX prefix common (`48 8B`, `48 8D`) |
| RIP-relative addressing | Not available (x86 uses absolute disp32) | The norm (most globals are RIP-resolved) |
| Branch/jump encoding | Same form, narrower range | Same form, often the same bytes |

The implication: x86 and x64 builds of the same engine require *largely separate* offset sets, not minor patches. Treat them as different binaries for multi-binary purposes:

```
offsets-v1.42.3_x64.em
offsets-v1.42.3_x86.em
```

Inside `dispatch.em`, the per-arch difference is usually a different *helper* per offset (pointer reads, struct walks) rather than a different *constant*:

```cpp
// Wrapper that reads the right width per active architecture
uint64 ptr_read(uint64 addr) {
    if (g_active_arch == "x64") return g_proc.ru64(addr);
    if (g_active_arch == "x86") return cast<uint64>(g_proc.r32(addr));
    return 0;
}
```

Feature code uses `ptr_read` instead of `ru64` directly, and the script works against either architecture.

When the offset set differs *significantly* in struct layout (because the engine's structs have different field shapes per architecture, not just per build), it's often cleaner to maintain genuinely separate feature implementations per architecture, joined only by the shared `globals.em` and `main.em`. The 30%-divergence heuristic in section 7 below applies.

**Why:** A pointer that's 4 bytes on x86 and 8 bytes on x64 is the single most common silent-failure source in cross-arch scripts. The abstraction is two lines; the bug-class it eliminates is broad.

---

## 5. Storefront Variation (Steam / Epic / GOG / Microsoft Store)

**Same game content, different DRM wrapper. The wrapper changes the entry point and may move `.text`; sigs based on internal engine anchors usually survive, sigs near the original entry point usually don't.**

Storefronts ship the same engine binary wrapped in DRM specific to their platform:

- **Steam** — `steam_api.dll` / `steam_api64.dll` linked; sometimes Steamworks DRM stub at the entry point; Steamworks call sites scattered through code.
- **Epic** — `EOSSDK-Win64-Shipping.dll`; Epic Online Services init shim; usually less invasive than Steamworks.
- **GOG** — Galaxy SDK shim; sometimes plus an Arxan or VMProtect wrapper for DRM.
- **Microsoft Store** — UWP packaging; binary may be inside a `WindowsApps` container with restricted access.
- **Standalone / itch.io** — usually no wrapper at all; closest to the developer's own build.

What this means for offsets:

- Sigs targeting *engine* code (entity list, view matrix, player struct) almost always work across storefronts unchanged.
- Sigs targeting *runtime initialization* (early-attach hooks, DRM-wrapped functions) often need per-store variants.
- The DRM wrapper sometimes alters the module name — `game.exe` vs `game-Win64-Shipping.exe` vs `game_steam.exe`. Identify both the module name AND the binary hash per storefront in your `KNOWN_BINARIES` table.

The detection pattern: a small per-storefront probe runs after attach, looking for the DRM-DLL fingerprint:

```cpp
string detect_storefront(proc_t p) {
    if (p.get_module_base("steam_api64.dll") != 0 ||
        p.get_module_base("steam_api.dll")   != 0) return "steam";
    if (p.get_module_base("EOSSDK-Win64-Shipping.dll") != 0) return "epic";
    if (p.get_module_base("Galaxy64.dll") != 0)             return "gog";
    return "standalone";
}
```

Combine with the hash-based identification — `label = "{version}_{storefront}"` gives you the dispatch key you need.

**Why:** Many users have the same game across multiple stores; the script's user-perceived support breadth is the cross-product of versions × storefronts. Catching the DRM-DLL fingerprint is a 5-line check that doubles or triples how many users your script "just works" for.

---

## 6. Channel Variation (Release / Beta / PTU / Demo)

**Same engine, different content packs, sometimes different telemetry. Engine-code sigs survive across channels; content-script sigs (UI strings, level-specific behaviors) may not.**

Games ship multiple channels for testing and engagement:

- **Release** — the public, stable build.
- **Beta** — early access to upcoming features, semi-public.
- **PTU / PTR** (Public Test Universe / Realm) — pre-release testing channel, semi-public.
- **Demo / Free Trial** — limited content, public.
- **Internal / staff** — not user-facing; if you have access to one, the engine layout may match release but the content does not.

What this means for offsets:

- Engine code is usually identical or near-identical across channels (same binary build pipeline, same engine version) — engine-targeted sigs survive.
- Content-driven offsets (level-specific entity slots, UI panel addresses tied to specific menus) often differ — content-targeted sigs may not.
- Telemetry sometimes differs — the beta channel may have additional anti-cheat instrumentation the release doesn't, or vice versa; the additional code shifts addresses.

The pattern: dispatch on `version_channel` (e.g. `v1.42.3_release`, `v1.42.3_beta`, `v1.42.3_ptu`), treat each as a distinct binary in `KNOWN_BINARIES`. If you find that 95% of offsets are identical between two channels, you can collapse them into a shared dispatch entry — but be explicit about it (a comment in `dispatch.em` saying "v1.42.3 release and beta share all sigs; PTU does not").

**Why:** Users on beta / PTU channels are usually the most engaged users; supporting them well matters disproportionately to the script's reception. The channel-detection layer is the same hash check — adding channel coverage is free if the hash table already exists.

---

## 7. Graceful Degradation When No Offset Set Matches

**The script should not crash on an unknown binary; it should print a clear message and skip its features. Features that don't depend on the missing offsets should still work.**

The failure-handling pattern:

```cpp
int64 main() {
    g_proc = ref_process(TARGET_MODULE);
    if (!g_proc.alive()) {
        println(format("[{s}] target process not attached", SCRIPT_NAME));
        return 0;
    }

    g_active_label = identify_binary(g_proc);
    if (g_active_label == "unknown") {
        uint64 base = g_proc.base_address();
        uint64 size = g_proc.get_module_size(TARGET_MODULE);
        println(format("[{s}] unknown binary build at base 0x{x} (size 0x{x})",
                       SCRIPT_NAME, base, size));
        println(format("[{s}] hash: {s} — add to KNOWN_BINARIES to enable support",
                       SCRIPT_NAME, current_hash));
        // Still register routines — the GUI loads, the user sees the status,
        // but features that need offsets are gracefully no-op.
        setup_gui();
        register_routine(cast<int64>(on_update_unknown), 0);
        register_routine(cast<int64>(on_render_unknown), 0);
        return 1;
    }

    if (!dispatch_select(g_active_label)) {
        println(format("[{s}] dispatch failed for label {s}",
                       SCRIPT_NAME, g_active_label));
        return 0;
    }

    println(format("[{s}] loaded offsets for {s}", SCRIPT_NAME, g_active_label));
    setup_gui();
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

void on_render_unknown(int64 data) {
    // Minimal render — show the user the script is loaded but offsets missing.
    draw_text(format("[{s}] unknown binary — see console", SCRIPT_NAME),
              vec2(10.0, 10.0), color(255, 200, 80, 255),
              get_font20(), 1, color(0, 0, 0, 200), 1.0);
}
```

The principles:

- **Never silently no-op.** A script that loads but does nothing visible is indistinguishable from a broken install. The on-screen text tells the user what happened.
- **Print the hash to the console** so the user can report it ("got hash 8e4f2a... on the new build"); you can add it to `KNOWN_BINARIES` in the next release.
- **Keep the GUI alive.** Even with no offsets, the user can interact with the menu, knows the script is loaded, and gets feedback when they re-attach to a supported build.
- **Cross-reference the patch-day skill.** When users report an unknown hash on a new build, the playbook in `skill://pcx-patch-day-playbook` is the workflow for adding support.

**Why:** Graceful degradation turns "the script is broken on the new build" reports into "the script noticed it doesn't have offsets for the new build" reports. Same problem, much better signal-to-noise for triage.

---

## When NOT to Multi-Target

**The pattern has a maintenance ceiling. When the binary changes structurally between versions, N offset sets become unsustainable; fork the script instead.**

Heuristics for when to fork:

| Signal | Reaction |
|---|---|
| >30% of sigs need per-version overrides | Engine rebuild or major refactor — fork |
| Struct layouts vary materially per version | Rewrite features per version, share only `main.em` |
| IL2CPP regeneration (Unity titles) between versions | Each regen invalidates the offset metadata; multi-target is fragile, fork is cleaner |
| The dispatched offsets file grows past ~500 lines per binary | The complexity is in the per-binary differences, not in shared logic — fork |
| Two versions are being maintained on different release cadences | Effort to keep them merged exceeds effort to maintain separately |

Forking pattern: separate branches (`main-v1.42.x`, `main-v1.43.x`) with selective cherry-picking of feature work between them. Heavier ops-wise, lighter cognition-wise — each branch's `offsets.em` is for one binary.

The threshold is subjective; the rough rule is "if the dispatch table is more complex than the feature code, you're past the ceiling."

**Why:** Multi-binary targeting is a power tool with a sweet spot. Below the sweet spot (2-5 builds, mostly shared code), it's strictly better than forking. Above it (10+ builds, mostly divergent code), it becomes a maintenance trap. Know when to switch.

---

## Summary

| # | Topic | One-liner |
|---|---|---|
| 1 | Identify the binary at runtime | Hash `.text` first N MB → look up in `KNOWN_BINARIES` |
| 2 | Per-binary offsets, common dispatch | `offsets-<label>.em` files; `dispatch.em` re-exports under shared names |
| 3 | Sigs over hardcoded RVAs | Shared sig > per-build sig > per-build RVA, in that preference order |
| 4 | Architecture (x86 vs x64) abstraction | `ptr_read` helper handles 4-vs-8-byte pointers; separate offset sets |
| 5 | Storefront detection | DRM-DLL fingerprint adds `_steam` / `_epic` / `_gog` to the label |
| 6 | Channel detection | Treat release / beta / PTU as distinct hashes; collapse only when verified identical |
| 7 | Graceful degradation | Unknown binary → print hash, keep GUI alive, no-op features |

**When NOT to multi-target:** >30% of sigs need per-version overrides → fork instead of patching.

**Cross-references:** `knowledge/script-organization-patterns.md` (the layered file structure this skill scales up); `.claude/skills/pcx-patch-day-playbook` (per-patch workflow — the multi-binary case is N patch days run in parallel); `.claude/skills/re-evidence-log` (per-binary evidence files keep claims isolated); `tools/offset-diff.py` (per-build sig validation), `tools/sig-uniqueness-checker.py` (per-build sig verdicts), `tools/dumper-to-enma.py` (regenerate per-build offset modules from updated dumper output).

---

## Source: `.claude/skills/pcx-angelscript-discipline/SKILL.md`

---
name: pcx-angelscript-discipline
description: >
  Behavioral and syntactic rules for writing .as scripts on Perception.cx.
  Prevents Enma-reflex errors in the AngelScript API surface — method names,
  parameter shapes, and constants differ between the two languages. Always
  active when editing .as files.
license: MIT
---

# AngelScript Discipline for Perception.cx

Behavioral and syntactic rules for writing `.as` scripts on Perception.cx. The companion skill to `game-cheat-guidelines` (which is Enma-flavored): same domain, different language, different gotchas. AngelScript on PCX has its own type system, lifecycle conventions, and API surface; the AI defaults to Enma idioms when editing `.as` files and produces code that does not compile.

**Always active when editing `.as` files.** These rules apply every time you write or edit a Perception.cx AngelScript script.

**Prerequisite:** `game-hacking-pcx` skill for the full doc index. **Read the relevant `docs/perception/angelscript/<file>.md` before writing any API call** — the AngelScript surface is not the Enma surface, and method names, parameter shapes, and constants differ.

---

## Trigger

`.as` file open, AngelScript syntax visible (`&in` references, `@` handles, `register_callback`, `on_tick`), user mentions AngelScript / `proc_t` / PCX scripting in AS context, any code referencing `docs/perception/angelscript/`.

---

## 1. AngelScript Is Not Enma — Don't Paste Enma APIs

**The PCX AngelScript API has different function names, different parameter shapes, and different idioms than the Enma API. They look similar; they are not interchangeable.**

The most common bug in AI-written `.as` scripts is pasting Enma API calls verbatim. The script doesn't compile, or worse, compiles to something that looks right and behaves wrong because AngelScript happens to have a same-named function with a different signature.

| Enma | AngelScript |
|---|---|
| `register_routine(cast<int64>(on_render), 0)` | `register_callback(on_tick, 16, 0)` |
| `int64 main()` | `int main()` |
| `void on_render(int64 data)` | `void on_tick(int id, int data_index)` |
| `println(...)` | `log(...)` |
| `color(r,g,b,a)` then `draw_rect(pos, size, color, ...)` | `draw_rect_filled(x, y, w, h, r, g, b, a, rounding, corner_flags)` |
| `get_view_width()` / `get_view_height()` | `get_view(vw, vh)` — out-param into two floats |
| `create_section("X")` returning `int64` | `create_section("X")` — same name, but check the AS gui-api doc for return type |

```cpp
// WRONG — Enma idioms in an .as file
int64 main() {
    color c = color(255, 0, 0, 255);
    draw_rect(vec2(10, 10), vec2(100, 100), c, 1.0, 4.0, 15);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

// RIGHT — AngelScript syntax, AS API, AS lifecycle
int main() {
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_tick(int id, int data_index) {
    draw_rect_filled(10.0f, 10.0f, 100.0f, 100.0f,
                     255, 0, 0, 255, 4.0f, RR_ALL);
}
```

**Why:** AngelScript is a separately registered host language with its own bindings. The Enma and AS APIs cover overlapping domains but the function signatures, type registrations, and constants are independent. Always confirm the call in `docs/perception/angelscript/<area>-api.md` before writing it.

---

## 2. Handles vs Values — Know Which You're Holding

**AngelScript distinguishes reference handles (`Type@`) from value types. PCX types use both, and the rule for each is in the doc.**

A handle is `Type@` — a reference-counted pointer. Assignment with `=` copies the handle; assignment with `@=` rebinds it. Method calls on a null handle throw. Value types use `=` for deep copy; you cannot have a "null" value.

```cpp
// Handle syntax — explicit @, null-checkable, ref-counted
proc_t@ p = ref_process("game.exe");      // ref_process returns a handle
if (p is null) { log("process not found"); return 0; }
if (!p.alive()) { p.deref(); return 0; }   // also deref when alive returns false

// Value syntax — vec3, color tuples, math types are typically values
Vector3 pos(1.0f, 2.0f, 3.0f);             // direct construction, no @
Vector3 copy = pos;                         // deep copy
```

The PCX docs are explicit about which types are handle-only, value-only, or both — *check the API page for each type you instantiate*. `proc_t` is documented as a handle; never declare it without `@` and never skip `is null` after `ref_process`.

```cpp
// WRONG — proc_t without handle syntax; may compile depending on registration
//         but ref_process returns a handle, and you lose the null-check pattern
proc_t p = ref_process("game.exe");
uint64 base = p.base_address();   // throws if process didn't open

// RIGHT
proc_t@ p = ref_process("game.exe");
if (p is null || !p.alive()) { return 0; }
uint64 base = p.base_address();
```

**Why:** A null handle dereference is a runtime exception that kills your script. Value-vs-handle confusion is the #1 source of `.as` crashes on PCX. The doc for each type tells you which one it is; check it once, write the right syntax forever.

---

## 3. Always `deref()` When You're Done — Even on Failure

**`proc_t` is reference-counted. You MUST call `deref()` to release it. The docs are explicit: even if `alive()` returns false, deref the handle.**

This is unique to AngelScript on PCX. The Enma equivalent (`ref_process` returning a `proc_t` value) is RAII-managed; the AngelScript version is not. A script that leaks `proc_t` handles will accumulate them across reloads.

```cpp
// WRONG — early return without deref leaks the handle
int main() {
    proc_t@ p = ref_process("game.exe");
    if (p is null) return 0;
    if (!p.alive()) return 0;            // LEAK — never derefed
    // ... do work ...
    p.deref();
    return 0;
}

// RIGHT — single exit path, or deref on every exit
int main() {
    proc_t@ p = ref_process("game.exe");
    if (p is null) return 0;
    if (!p.alive()) { p.deref(); return 0; }
    // ... do work ...
    p.deref();
    return 0;
}

// BETTER — for persistent scripts, store the handle globally and deref in on_unload
proc_t@ g_proc = null;

int main() {
    @g_proc = ref_process("game.exe");
    if (g_proc is null || !g_proc.alive()) { return 0; }
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload() {
    if (g_proc !is null) {
        g_proc.deref();
        @g_proc = null;
    }
}
```

Note the `@=` operator for rebinding handle assignments (`@g_proc = ...`); plain `=` between handles invokes the value-copy path on most PCX types and will not compile.

**Why:** Leaked handles keep the underlying process reference alive past script unload. Across many script reloads in an editing session, this accumulates resource pressure and can prevent re-attach to the target. The deref pattern is cheap; making it a habit costs you nothing and saves a class of bug.

---

## 4. `float` Is `float32` — Use `f` Suffixes; `double` Promotes Silently

**AngelScript uses `float` for 32-bit and `double` for 64-bit. Literal `1.5` is `double`. Render APIs and vertex math expect `float`. Use `1.5f` literals.**

This mirrors C/C++. The AS compiler will silently promote `float` to `double` when mixed in arithmetic, then narrow the result back at the call boundary — a path that can lose precision in tight render loops. Be explicit.

```cpp
// WRONG — double literals everywhere
float vw, vh; get_view(vw, vh);
float cx = vw * 0.5;                      // promotes vw to double, narrows result
draw_rect_filled(cx - 100, cy - 50, 200, 100,
                 40, 40, 40, 255, 8.0, RR_ALL);  // 8.0 is double → 8.0f conversion

// RIGHT — f suffix on every float literal that feeds a float API
float vw, vh; get_view(vw, vh);
float cx = vw * 0.5f;
draw_rect_filled(cx - 100.0f, cy - 50.0f, 200.0f, 100.0f,
                 40, 40, 40, 255, 8.0f, RR_ALL);
```

Color components are integers (0-255) in the PCX AS draw API — no `f` suffix on those. Rounding, dimensions, positions are floats — `f` suffix.

**Why:** AS's implicit promotion does the right thing for correctness but pays in a constant stream of `cvtss2sd` / `cvtsd2ss` around every literal. In a render path hit at 144 Hz, that's measurable. The `f` suffix is also a clarity signal — when you read the code later, you can tell what's a pixel coordinate (`100.0f`) and what's a count or flag (`100`).

---

## 5. Out Parameters Use `&out` — Not `out`, Not Pointers

**AngelScript out parameters are reference parameters declared `&out` (write-only) or `&inout` (read-write). `&in` is read-only by reference. These are *part of the declaration*, not call-site syntax.**

```cpp
// Declaring an out-param function
void get_view(float &out width, float &out height);
bool world_to_screen(const Vector3 &in world, Vector2 &out screen);

// Calling it — just pass the variables, no `&` at call site
float vw, vh;
get_view(vw, vh);                          // AS handles the reference

Vector2 screen;
if (world_to_screen(player_pos, screen)) {
    draw_circle_filled(screen.x, screen.y, 4.0f, 255, 0, 0, 255);
}
```

Three common mistakes:

- Declaring `out` without `&` — compile error, AS requires the reference qualifier
- Trying to write to `&in` — read-only, compile error
- Using `&inout` when you only write — silently legal but confusing; prefer `&out` when you mean "I will write this"

```cpp
// WRONG — bare `out` is C# syntax, not AS
void get_view(out float width, out float height);

// WRONG — & at call site is C++ syntax
get_view(&vw, &vh);

// RIGHT — & at declaration, plain variable at call
void get_view(float &out width, float &out height);
get_view(vw, vh);
```

**Why:** AS's reference syntax is its own — neither C++ nor C#. Mixing them gives confusing errors. Pin the rule once: `&in` / `&out` / `&inout` go on the parameter declaration; the call site is plain.

---

## 6. `array<T>` Is the Container, Not `T[]`

**AngelScript's standard array is `array<T>`, registered as part of the array add-on (per `docs/perception/angelscript/overview.md`). Do not use `T[]` — that is Enma syntax.**

```cpp
// WRONG — Enma syntax
uint64[] entities;
entities.push(0x12345);

// RIGHT — AngelScript syntax
array<uint64> entities;
entities.insertLast(0x12345);              // not push — check array docs for full API
uint count = entities.length();             // length() returns uint
for (uint i = 0; i < count; i++) {
    log("ent " + i + " = 0x" + formatInt(entities[i], "X", 16));
}
```

The AS array methods are `insertLast`, `removeLast`, `insertAt`, `removeAt`, `length`, `resize`, `sortAsc`, `sortDesc`, `find` — not the Enma `push`/`pop`/`contains`/`slice` set. The signatures and return types come from the AS standard library and are documented in the AngelScript reference (search "array" in the AS docs); read it once when you need a method you haven't used.

**Why:** `T[]` is a compile error in PCX AS. Even if you remember `array<T>`, defaulting to Enma method names (`push`, `pop`) will fail. The script-helper exception messages are clear, but the time wasted on a 30-second lookup adds up across an editing session.

---

## 7. Use `dictionary` for Maps, Not `map<K,V>`

**`dictionary` is AS's string-keyed map. There is no generic `map<K,V>` in the registered surface (per `docs/perception/angelscript/overview.md`).**

```cpp
// WRONG — Enma map syntax
map<string, int32> counts;
counts.set("a", 1);
int32 v = counts.get("a");

// RIGHT — AS dictionary
dictionary counts;
counts["a"] = 1;
int v;
if (counts.get("a", v)) {                  // get returns bool; out-param the value
    log("a = " + v);
}
```

Dictionary keys are always `string`. Values are `any`-typed (stored as `?` boxed values); reading them requires the typed `get(key, out_value)` form to unbox correctly. If you need a non-string key, encode it as a string (`formatInt(addr, "X")` for addresses) or use parallel arrays.

**Why:** AS's type system doesn't carry through generic K/V parameters in the same way Enma's does. The boxed-`any` pattern via `dictionary` is the idiomatic substitute. Mis-typing the `get` form is the common error — always use the two-arg form with a typed output variable.

---

## 8. Render API Takes Raw RGBA Ints, Not `color` Structs

**The PCX AS render API is positional-args-style: pass red, green, blue, alpha as separate `uint8`-range integers (0-255). There is no `color` value type to wrap them in the way Enma does.**

```cpp
// WRONG — Enma-style color struct
color c(255, 100, 50, 200);
draw_rect_filled(10, 10, 100, 100, c, 4.0f, RR_ALL);

// RIGHT — raw rgba ints inline
draw_rect_filled(10.0f, 10.0f, 100.0f, 100.0f,
                 255, 100, 50, 200, 4.0f, RR_ALL);

// For text — same pattern with optional shadow color
uint64 font = get_font20();
draw_text("HUD", 10.0f, 10.0f,
          255, 255, 255, 255,                // fg rgba
          font, TE_SHADOW,
          0, 0, 0, 180,                       // shadow rgba
          1.0f, true);                        // shadow dist, centered
```

This means colors don't carry through assignments cleanly. If you need named colors, define them as four constants each:

```cpp
const uint8 FG_R = 255, FG_G = 200, FG_B = 50, FG_A = 255;
const uint8 BG_R =   0, BG_G =   0, BG_B =  0, BG_A = 180;

void on_tick(int id, int data_index) {
    draw_rect_filled(10.0f, 10.0f, 200.0f, 50.0f, BG_R, BG_G, BG_B, BG_A, 4.0f, RR_ALL);
    draw_text("HUD", 20.0f, 25.0f, FG_R, FG_G, FG_B, FG_A,
              get_font20(), TE_NONE, 0,0,0,0, 0.0f, false);
}
```

**Why:** The AS render API is wide-call-shaped intentionally — the marshaling cost to host C++ for a `color` struct would dominate the call. Accepting integers directly maps to a single C function call with stack arguments. Embrace the verbosity; it pays in performance and clarity.

---

## 9. `register_callback` — Two-Argument Callback Signature, Interval in Milliseconds

**Callbacks registered with `register_callback(fn, interval_ms, data_index)` are invoked with `void on_X(int id, int data_index)`. The id is the callback id from `register_callback`; data_index is the third arg you passed at registration, so one function can serve many registrations.**

```cpp
// Two callbacks, same function, different data_index — common pattern for
// running the same logic against multiple targets
int g_cb_fast = 0;
int g_cb_slow = 0;

int main() {
    g_cb_fast = register_callback(on_tick, 8,   0);  // ~120 Hz, data 0
    g_cb_slow = register_callback(on_tick, 100, 1);  // 10 Hz,   data 1
    return 1;
}

void on_tick(int id, int data_index) {
    if (data_index == 0) {
        // hot path — runs every 8 ms
        render_overlay();
    } else if (data_index == 1) {
        // cold path — runs every 100 ms
        refresh_entity_cache();
    }
}

void on_unload() {
    unregister_callback(g_cb_fast);
    unregister_callback(g_cb_slow);
}
```

The interval is in milliseconds and is a *minimum gap*, not a deadline — if your callback runs 12 ms and you asked for 8 ms, the next call is in 12 ms, not -4 ms backed up. Use `100`–`200` for cold-path entity refresh, `8`–`16` for render-frequency updates.

**Why:** Mis-binding the callback signature is a silent failure — the engine looks up the function by name+arity, and if your signature is wrong it either fails to register or registers a different function. `unregister_callback` in `on_unload` is mandatory for clean reloads; an un-unregistered callback survives the script unload and fires against a freed context, which crashes.

---

## 10. Hot Reload Boundaries — Globals Reset, Game State Doesn't

**AS scripts on PCX reload by tearing down the whole script context — globals reset, callbacks are released, the dictionary heap is rebuilt. The game process is untouched. Design your data flow around this.**

What survives a reload:
- The game process and its memory (you re-attach via `ref_process`)
- File-system state (if you persisted config to disk)
- The PCX engine and its GUI state

What does NOT survive a reload:
- Global variables (reset to declaration default)
- Registered callbacks (cleared; you must `register_callback` again in `main`)
- Cached pattern-scan results (re-resolve in `main` or first callback)
- Dictionary entries holding values (rebuilt from disk if you persist them)
- GUI section state (per-section configuration; the GUI API will re-create sections, but their widget states are reinitialized to your defaults)

```cpp
// Typical hot-reload-safe persistent script structure:
proc_t@ g_proc = null;
uint64  g_entity_list = 0;
int     g_cb = 0;

int main() {
    // Re-attach on every load
    @g_proc = ref_process("game.exe");
    if (g_proc is null || !g_proc.alive()) { return 0; }

    // Re-resolve sigs on every load (cheap relative to runtime cost of running)
    uint64 base = g_proc.base_address();
    uint64 size = g_proc.module_size("game.exe");
    uint64 hit  = g_proc.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0) { g_proc.deref(); return 0; }
    g_entity_list = resolve_rip(g_proc, hit, 3, 7);

    // Load config from disk if you persist it
    load_config();

    g_cb = register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload() {
    unregister_callback(g_cb);
    save_config();
    if (g_proc !is null) { g_proc.deref(); @g_proc = null; }
}
```

**Why:** A script that assumes globals survive a reload will read stale or zero data on its first callback after reload — your overlay draws nothing, or worse, against a freed process handle. Treat `main()` as the authoritative initializer that runs from scratch every time.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | AS is not Enma | Look up every API in `docs/perception/angelscript/` before pasting |
| 2 | Handles vs values | `proc_t@` not `proc_t`; null-check with `is null` |
| 3 | Always deref | Even when alive() is false; in `on_unload` for persistent scripts |
| 4 | `float` literals get `f` | `8.0f` not `8.0` — render APIs are float-typed |
| 5 | `&out` at declaration | Call site is plain variable, no `&` |
| 6 | `array<T>` not `T[]` | Methods are `insertLast` / `removeLast` / `length` |
| 7 | `dictionary` for maps | String keys only; `get(key, out_var)` two-arg form |
| 8 | Raw RGBA ints | No `color` struct; pass `r, g, b, a` separately |
| 9 | `register_callback` | Signature `void on_X(int id, int data_index)`; deregister in `on_unload` |
| 10 | Hot-reload safety | Re-attach, re-resolve, re-register every `main()` |

**The 12 game-cheat-guidelines rules still apply** — this skill is the *AngelScript-flavored* version of those discipline rules. Address types are `uint64`, null-check every read, separate update from render, sigs over hardcodes, one feature per file, minimize writes, validate against the live binary. Read `skill://game-cheat-guidelines` for the full discipline.

**Cross-references:** `skill://game-cheat-guidelines` (the 12 rules; Enma-flavored examples but principles apply), `skill://game-hacking-pcx` (doc router), `docs/perception/angelscript/overview.md` (registered modules and addons), `docs/perception/angelscript/proc-api.md`, `docs/perception/angelscript/render-api.md`, `docs/perception/angelscript/life-cycle.md`, `docs/perception/angelscript/gui-api.md`.

---

## Source: `.claude/skills/pcx-bloat-audit/SKILL.md`

---
name: pcx-bloat-audit
description: >
  Whole-project audit for over-engineering in PCX scripts. Scans every .em and
  .as file for wrappers, dead abstractions, duplicate entity walks, unused
  offsets, and config systems that outweigh their settings. Ranked by lines
  recoverable. Use when the user says "audit for bloat", "what can I delete",
  "find over-engineering", "slim this project", or invokes /pcx-bloat-audit.
  One-shot report, does not apply fixes.
license: MIT
---

pcx-bloat-review, project-wide. Scan every `.em` and `.as` file. Rank
findings by lines recoverable, biggest first.

## Tags

Same as pcx-bloat-review:

- `delete:` dead code, unused feature path, speculative abstraction.
- `pcx-api:` hand-rolled thing the PCX API ships. Name the function + doc.
- `inline:` wrapper/class/helper with one caller.
- `yagni:` abstraction with one implementation, config for nothing.
- `shrink:` same logic, fewer lines.
- `merge:` two routines/walks that should be one.

## Hunt List

Scan for these in priority order:

1. **Dead offsets** — sig constants or hardcodes nothing reads. Post-patch debris.
2. **Single-caller wrappers** — functions that wrap one `p.ru64()` / `p.wu64()` call.
3. **Class hierarchies for one feature** — `IFeature`, `BaseEntity`, `AbstractRenderer` with one concrete child.
4. **Config systems vs setting count** — if the config loader is longer than the settings it loads, flag it.
5. **Duplicate entity walks** — two routines independently iterating the same list.
6. **Files exporting one symbol** — `utils.em` with one function, `types.em` with one typedef.
7. **Unused imports** — `import` statements for modules nothing in the file calls.
8. **Commented-out code blocks** — not `// defer:` or `// UNVERIFIED`, just dead code behind `//`.

## Output

One line per finding, ranked by lines recoverable:

```
<tag> <what to cut>. <replacement or "nothing">. [<file>:<lines>] (-<N> lines)
```

End with:

```
net: -<N> lines, -<M> files possible across <P> findings.
```

Nothing to cut: `Lean already. Ship.`

## Boundaries

Complexity only. Does not flag correctness, security, or performance issues.
Does not touch `// defer:` or `// UNVERIFIED` markers — those are
deliberate/tracked. Does not apply fixes.

---

## Source: `.claude/skills/pcx-bloat-review/SKILL.md`

---
name: pcx-bloat-review
description: >
  Code review focused on over-engineering in PCX scripts. Finds what to delete:
  proc_t wrappers, entity managers for three entities, config systems for two
  settings, class hierarchies for one feature. One line per finding. Use when
  the user says "review for bloat", "is this over-engineered", "what can I
  delete", or invokes /pcx-bloat-review. Complements correctness review — this
  one only hunts unnecessary complexity in Enma/AngelScript scripts.
license: MIT
---

Review PCX script diffs for unnecessary complexity. One line per finding.
The diff's best outcome is getting shorter.

## Format

`L<line>: <tag> <what>. <replacement>.`, or `<file>:L<line>: ...` for
multi-file diffs.

## Tags

- `delete:` dead code, unused feature path, speculative abstraction. Replacement: nothing.
- `pcx-api:` hand-rolled thing the PCX API already ships. Name the function + doc page.
- `inline:` wrapper/class/helper with one caller. Inline it.
- `yagni:` abstraction with one implementation, config nobody sets, manager for one thing.
- `shrink:` same logic, fewer lines. Show the shorter form.
- `merge:` two routines/walks that should be one. Name the merge.

## PCX-Specific Hunts

- **proc_t wrappers** — `ReadMemory()` / `ReadEntity()` functions that just call `p.ru64()` with no added validation. The proc API *is* the interface.
- **Entity managers / registries** — `EntityManager`, `FeatureRegistry`, `IFeature` interface for ≤3 features. Three routines registered in `main()` is the framework.
- **Config systems for few settings** — JSON/file config loader for 2-5 `bool` toggles. A `bool g_esp = true;` + sidebar checkbox is the config system.
- **Color/theme abstractions** — `ThemeManager`, `ColorScheme` classes when `color(r,g,b,a)` constructed per-frame costs nothing.
- **Over-split files** — `utils.em` exporting one function, `types.em` defining one typedef. Inline into the caller.
- **Duplicate entity walks** — two `on_update` routines walking the same entity list independently. One walk, two consumers.
- **Dead offset blocks** — sig constants or hardcoded offsets that nothing reads anymore. Post-patch leftover.

## Examples

✅ `esp.em:L12-38: inline: ReadEntity() wraps p.ru64() once with no guard. Inline the call, save 26 lines.`

✅ `main.em:L5-44: yagni: FeatureRegistry class for 2 features. register_routine() twice in main(), done.`

✅ `menu.em:L80-130: yagni: JSON config loader for 3 bools. bool globals + sidebar checkbox, 6 lines.`

✅ `globals.em:L22: delete: g_old_entity_list — nothing reads it since the sig update.`

✅ `esp.em:L60, radar.em:L40: merge: both walk entity_list independently. One walk in on_update, both draw in on_render.`

✅ `utils.em:L1-8: inline: exports only clamp(). Move to the one file that calls it, delete utils.em.`

## Scoring

End with: `net: -<N> lines, -<M> files possible.`

Nothing to cut: `Lean already. Ship.`

## Boundaries

Complexity only. Correctness bugs (wrong offsets, missing null guards, sign
extension), security (detection surface), and performance (read frequency)
belong to a normal review pass.

Does not touch `// defer:` comments — those are tracked deliberately.
Does not apply fixes, only lists them.

---

## Source: `.claude/skills/pcx-coding-discipline/SKILL.md`

---
name: pcx-coding-discipline
description: >
  Workflow discipline for developing Enma (.em) and AngelScript (.as) scripts
  on Perception.cx. Derived from Karpathy principles — think before coding,
  simplicity first, surgical changes, goal-driven execution — rewritten for
  cheat development realities: stale offsets, silent failed reads, detection
  surface. Always active when writing or editing PCX scripts.
license: MIT
---

# PCX Coding Discipline — How to Write Scripts, Not What They Look Like

Workflow discipline for developing Enma (`.em`) and AngelScript (`.as`) scripts on Perception.cx. Derived from the four Karpathy principles — *think before coding, simplicity first, surgical changes, goal-driven execution* — and rewritten for the realities of cheat development: stale offsets, silent failed reads, detection surface, and overlays you debug by looking at them.

**Always active when writing or editing PCX scripts.** This is the *process* layer. The `game-cheat-guidelines` skill is the *code-shape* layer (uint64 addresses, null guards, render separation). Load both: this one tells you how to work, that one tells you what the code must look like.

**Prerequisite:** Read the relevant doc before writing any API call — see `skill://game-hacking-pcx` for the file-by-file index.

## Trigger
Writing or editing any `.em` / `.as` script, adding a cheat feature, refactoring a script, fixing a broken overlay, deciding how much to build, or judging whether a script is "done."

---

## 1. Think Before You Touch the Editor

**Name the target, the source of every offset, and the tradeoff you're making — out loud — before you write a line.**

The single most expensive habit in cheat development is writing code against assumptions. A wrong offset doesn't throw; it reads garbage and your ESP draws at (0, 0). Before implementing:

- **State the target.** Game, engine, module. "Apex / Source (r5) / `r5apex.exe`."
- **State where each offset comes from.** Sig scan, SDK header, or hardcode — and say which. If you're guessing a struct field, write `// UNVERIFIED` next to it.
- **Surface the tradeoff the user didn't ask about.** Read-only ESP is invisible; a memory write for aimbot is a detection surface. Per-frame reads are simple but couple render to read latency. Say which you're choosing and why.
- **If the doc is ambiguous or the API is permission-gated, stop and read it.** Do not invent `draw_esp()` or assume `draw_circle` takes a fill flag. Open `docs/perception/render-api.md`.

```
Before: "I'll write an ESP overlay."
        *invents function names, assumes int32 offsets, no W2S behind-camera check*

After:  "Target: Apex / Source (r5). Entity list via sig (UNVERIFIED layout, r5sdk season 21).
         Read-only ESP, per-frame W2S — accepting read/render coupling for v1 simplicity.
         Reading render-api.md + lifecycle-and-routines.md before writing."
```

**Why:** Confusion hidden behind plausible code costs hours. Confusion stated up front costs one sentence and gets corrected before it compiles into a silent bug.

---

## 2. The Simplest Cheat That Works

**Build the minimum feature that satisfies the ask. Nothing speculative.**

Cheat scripts rot into 2000-line monoliths because every feature arrives with prediction, smoothing, themes, and a config framework nobody requested. Climb down the ladder:

- **"Highlight enemies" is a box, not a skeleton-ESP-with-bones-and-LOD.** Ship the box. Add bones when asked.
- **An aimbot the user described as "snap to head" doesn't need velocity prediction.** Don't add it.
- **No config system for a value that never changes.** A fixed enemy color is `color(255,0,0,255)`, not a JSON-loaded theme engine.
- **No abstraction over the proc API.** `p.ru64(...)` is the interface. Wrapping it in a `MemoryManager` class buys nothing.
- **No "feature manager" framework for three features.** Three registered routines is the framework.

```cpp
// WRONG — entity-component scaffolding for "draw boxes on enemies"
class IFeature { void update(); void render(); }
class FeatureRegistry { array<IFeature@> features; ... }
class EspFeature : IFeature { /* 200 lines */ }

// RIGHT — two routines, done
void on_update(int64 data) { /* read positions into g_positions */ }
void on_render(int64 data) { /* draw boxes from g_positions */ }
```

**Why:** Every speculative line is a line someone debugs at 3am after a patch. The lazy version ships today and is trivially extended when a real second requirement shows up — which is the only honest signal that the abstraction was needed.

---

## 3. Surgical Edits — One Feature, One Diff

**When changing a script, touch only the feature you're changing. Clean up only the mess your change makes.**

Perception scripts are built for hot reload precisely so you can change one file without disturbing the rest. Honor that:

- **Editing ESP color? Edit `esp.em`.** Do not reformat `menu.em`, rename globals in `globals.em`, or "tidy" `main.em` while you're in there.
- **Match the module's existing style** — naming, the per-feature file split, the order of routine registration. A second convention beside the first is worse than the style you'd have picked.
- **If your change orphans a global or import, remove it.** If you spot pre-existing dead code unrelated to your change, mention it — don't delete it.
- **Don't churn working offsets.** A sig that still hits and resolves to valid data is not your problem today.

```
Task: "the enemy boxes are the wrong color"

WRONG diff:  esp.em (color)  +  globals.em (renamed g_col → g_enemyColor)
             +  menu.em (reordered widgets)  +  main.em (reformatted)

RIGHT diff:  esp.em (color)
```

**Why:** Every file you touch is a file that can break and a file the next reader has to diff. A four-file diff to change one color hides the actual change and risks the three features you didn't mean to touch.

---

## 4. Done Means It Works on the Target

**Define success as something you can *see* on the live game, then loop until you see it. Compiling is not done.**

A script that compiles has proven nothing about whether the offsets are right, the W2S matches the engine, or the overlay aligns. Set a concrete bar and verify against it:

- **Write the success criteria before coding**, as observable facts: "boxes track enemies at any distance, nothing draws behind the camera, count matches the scoreboard."
- **The overlay is your debugger.** When something's off, draw the raw W2S coordinates and `print` the entity count — don't guess.
- **Loop:** compile → load → look at the screen → compare to the criteria → fix → reload. Repeat until every criterion holds.
- **When the IDB, the SDK, and the live read disagree, trust the live read** (see `game-cheat-guidelines` #12). The SDK may be from an older season.

```
Success criteria for "enemy ESP":
[ ] A box appears on every enemy entity (count == live enemy count)
[ ] Boxes track movement smoothly, no stutter
[ ] No box renders when the entity is behind the camera (W2S w > 0)
[ ] No box at (0,0) — that means a null read slipped a guard
[ ] Boxes scale with distance (far enemies = smaller boxes)
```

**Why:** "It compiles" and "it works" are different claims, and only the second one is the deliverable. A success checklist turns a vague "make ESP" into a loop you can run yourself without asking the user whether it's right.

---

## 5. Deletion Before Addition

**Try removing code before writing new code. The shortest script that works is the one with the fewest lines to break after a patch.**

When a feature request arrives, check what already exists first:

- **Can you delete a workaround instead of adding a second one?** Two workarounds for the same stale offset is a sign one should die.
- **Can you inline a wrapper?** A `ReadEntity()` function that calls `p.ru64()` once with no validation adds a name, not value. Inline it.
- **Can you merge two features into one routine?** If `on_update_esp` and `on_update_radar` both walk the same entity list, one walk and two draw calls in `on_render` is fewer lines and fewer reads.
- **Before adding a class, count its callers.** One caller = inline. Two = maybe. Three = extract, not before.

```cpp
// WRONG — utility wrapper around a one-liner
uint64 ReadEntityBase(proc_t@ p, uint64 list, int idx) {
    return p.ru64(list + idx * 0x20);
}
// ... called exactly once

// RIGHT — inline it, the proc_t API is already the interface
uint64 ent = p.ru64(entity_list + i * 0x20);
```

**Why:** Every line in a cheat script is a line you re-validate after a game patch. 80 lines is 80 potential breakpoints. 40 lines is half the post-patch work.

---

## 6. Question the Requirement

**Ship the minimum, then challenge the rest — in the same response, not a separate conversation.**

When the ask is vague or ambitious ("make a full ESP with health bars, distance, snaplines, team colors, and a config panel"):

1. **Build the core** — boxes on enemies, W2S, null guards.
2. **Ship it working.**
3. **In the same response:** "Done: box ESP with W2S + null guards. Health bars and snaplines are 10 lines each when you want them. Team colors need a second read per entity — add when the base ESP is confirmed working. Config panel is overhead for 3 settings — `bool` globals + a sidebar checkbox cover it."

Never stall on an answer you can default. Never build five features to avoid the conversation about whether three of them matter.

```
Pattern:  [working code] → skipped: [X]. add when [Y].
```

---

## 7. Mark Deliberate Shortcuts

**Every deliberate simplification gets a `// defer:` comment naming its ceiling and the trigger to revisit.**

`// UNVERIFIED` marks offset confidence. `// defer:` marks *design* shortcuts — places where you chose the simple path and know the ceiling.

```cpp
// defer: single entity array walk, separate walks per feature if >200 entities tank FPS
void on_update(int64 data) { ... }

// defer: hardcoded team color, config panel if user asks for customization
color enemy_col = color(255, 0, 0, 255);

// defer: global proc_t handle, per-feature handles if multi-process support needed
proc_t@ g_proc;
```

Format: `// defer: <what was simplified>, <when to revisit>`

A `// defer:` with no trigger is a shortcut that rots silently. Always name the trigger.

**Not deferred:** pointer validation, `w > 0` checks, `uint64` for addresses, `f` suffix on floats. Those are the floor, not shortcuts.

---

## 8. One Self-Check Per Non-Trivial Feature

**You can't unit test against a live game, but non-trivial logic leaves one sanity print behind.**

Cheat scripts run against a live target — no mock framework, no test harness. But logic bugs (wrong struct offset math, bad matrix indexing, off-by-one in entity iteration) can be caught with a visible sanity check:

- **Entity count print:** `print("entities: " + g_positions.length());` in `on_update`. If it reads 0 or 9999, something's wrong before you even look at the overlay.
- **Address range check:** `if (addr < 0x10000 || addr > 0x7FFFFFFFFFFF) print("suspect addr: " + addr);` — catches sign-extension and null-deref-adjacent reads.
- **W2S validation:** draw the raw screen coords as text before drawing boxes. If they cluster at (0,0), a null read slipped.
- **One `print()` per feature, gated behind a debug flag.** Not a logging framework — one line.

```cpp
// Self-check: remove or gate behind g_debug when stable
if (g_debug) print("[esp] ents=" + ents.length() + " visible=" + drawn);
```

**Why:** The laziest debugger that catches real bugs. One print per feature is near-zero overhead. A logging framework for three features is debt you don't need.

---

## Summary

| # | Principle | In PCX terms |
|---|-----------|--------------|
| 1 | Think Before Coding | Name target, offset source, and tradeoff before the first line |
| 2 | Simplicity First | Ship the box, not the framework — no speculative features |
| 3 | Surgical Changes | One feature, one diff; clean only your own orphans |
| 4 | Goal-Driven Execution | Done = visible success criteria met on the live target, not "compiles" |
| 5 | Deletion Before Addition | Try removing/inlining before writing new code |
| 6 | Question the Requirement | Ship the minimum, challenge the rest in the same response |
| 7 | Mark Deliberate Shortcuts | `// defer: <ceiling>, <trigger>` for design shortcuts |
| 8 | One Self-Check Per Feature | One `print()` per non-trivial feature, gated behind `g_debug` |

---

## Source: `.claude/skills/pcx-debug-overlay/SKILL.md`

---
name: pcx-debug-overlay
description: >
  Pattern for shipping diagnostic and profiler output as a separate, gated
  overlay rather than mixing it into the production rendering. Triggers when
  debugging a script, building a support-mode panel, profiling a slow path,
  or creating a diagnostic vs release build of the same code.
license: MIT
---

# Debug Overlay — Diagnostic Surfaces Separate from the Production Overlay

The pattern for shipping diagnostic / profiler / address-dump information as a separate, gated overlay rather than mixed into the production rendering. Companion to `pcx-perf-budget` (which gives the timing primitives) and `gui-design-patterns` (which says "no debug section by default"). This skill names the structure that lets you ship a script that's diagnosable when you need it and clean when you don't.

**Trigger when:** the user is debugging a script that "isn't working," wants to ship a script with a built-in support-mode panel, profiling a feature to find a slow path, building a diagnostic build vs a release build of the same code, debugging "the AI says it resolved the sig but the script does nothing."

**Prerequisite:** `skill://pcx-perf-budget` for the `mono_us()`-based profiler recipe this skill consumes; `knowledge/gui-design-patterns.md` section "Don't ship a debug panel by default" for the layout discipline this skill extends.

---

## Trigger

Debugging a non-working script, building a support-mode panel for end users, profiling a script's per-routine costs, tracing why an offset resolution succeeded but a read returns 0, designing a script that needs to be diagnosable in the field without the user having to grep logs.

---

## 1. Two Overlays: Production and Diagnostic — Always Separate

**Production overlay shows what the user wants to see (ESP boxes, HUD, target indicators). Diagnostic overlay shows what the script knows about itself (sigs resolved, addresses, profiler timings, error counts). Never mix.**

When you mix them, the user permanently sees diagnostic noise during normal play, and you can't ship a diagnostic-rich build to a tester without also shipping the noise to everyone else. The separation is the only way to have both.

```cpp
// WRONG — diagnostic info in the production render path
void on_render(int64 data) {
    // ... ESP drawing ...

    // Inline diagnostic — every user sees this, every match
    draw_text(format("entity_list=0x{x} count={d}", g_entity_list, g_ent_count),
              vec2(10.0, 10.0), color(255, 255, 0, 255),
              get_font20(), 1, color(0, 0, 0, 200), 1.0);
}

// RIGHT — diagnostic overlay is its own routine, its own render path
void on_render(int64 data) {
    // ... ESP drawing only ...
}

void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // ... diagnostic drawing, separately registered, separately controlled ...
}

int64 main() {
    // Both registered; the diagnostic one no-ops when g_diag_enabled is false
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    return 1;
}
```

The separation is also a CPU-budget thing: when `g_diag_enabled` is false, the diagnostic routine no-ops on the first line and costs nothing. When it's true, it draws every frame. Letting users (or you, in development) toggle that with a single global is the discipline.

**Why:** Mixed render paths are impossible to ship to two audiences. Separated render paths let you ship one binary that's clean by default and rich-on-demand. Cost is one extra global, one extra routine registration; benefit is permanent.

---

## 2. The Diagnostic Overlay Has Five Standard Sections

**Diagnostic overlays converge on the same shape across projects. Pin it once; reuse it.**

The five sections, in display order:

1. **Process & module status** — `g_proc.alive()` result, base address, module size, whether base resolution succeeded.
2. **Sig resolution status** — per-named-sig: hit address (or 0), resolved address (after RIP), uniqueness margin (if you ran the checker at build time).
3. **Runtime data sanity** — first few entity-list entries, local-player address, view-matrix sample value, whether the values look plausible (in range, non-zero, etc.).
4. **Profiler readouts** — per-routine `avg / max / count` from the `pcx-perf-budget` profiler recipe.
5. **Error counters** — counts of failed reads, null pointer cases caught, sig-resolution fallbacks, exception catches. (Use atomic counters per `addon-atomic` if features can write to them concurrently.)

```cpp
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;

    float64 x = 10.0;
    float64 y = 200.0;
    float64 line_h = 16.0;
    uint64 font = get_font20();
    color fg = color(220, 220, 220, 255);
    color hdr = color(255, 200, 80, 255);
    color shadow = color(0, 0, 0, 180);

    // Section 1: Process & module
    draw_text("[ Process ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  alive: {s}  base: 0x{x}  size: 0x{x}",
                     g_proc.alive() ? "yes" : "no", g_module_base, g_module_size),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 2: Sig resolution
    draw_text("[ Sigs ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  entity_list: hit=0x{x} resolved=0x{x}",
                     g_sig_entity_list_hit, g_off_entity_list),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  view_matrix: hit=0x{x} resolved=0x{x}",
                     g_sig_view_matrix_hit, g_off_view_matrix),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 3: Runtime sanity
    draw_text("[ Runtime ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  ent count: {d}  first ent: 0x{x}",
                     g_ent_count, g_first_ent_ptr),
              vec2(x, y), fg, font, 1, shadow, 1.0);
    y += line_h + 4.0;

    // Section 4: Profiler (read from pcx-perf-budget bucket accumulators)
    draw_text("[ Profile ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    for (int32 i = 0; i < NUM_BUCKETS; i++) {
        if (g_bucket_count[i] == 0) continue;
        int64 avg = g_bucket_total_us[i] / g_bucket_count[i];
        draw_text(format("  {s}: avg {d}us  max {d}us",
                         g_bucket_name[i], avg, g_bucket_max_us[i]),
                  vec2(x, y), fg, font, 1, shadow, 1.0);
        y += line_h;
    }
    y += 4.0;

    // Section 5: Error counters
    draw_text("[ Errors ]", vec2(x, y), hdr, font, 1, shadow, 1.0);
    y += line_h;
    draw_text(format("  null reads: {d}  sig fallbacks: {d}",
                     g_err_null_reads, g_err_sig_fallbacks),
              vec2(x, y), fg, font, 1, shadow, 1.0);
}
```

The five-section structure is enough to diagnose ~90% of script issues without further instrumentation. When a user reports "the script isn't working," the screenshot of this panel answers the question.

**Why:** Ad-hoc diagnostics in different scripts use different shapes; you waste mental energy each time figuring out which info is shown where. The five-section structure is a contract — once your team agrees on it, every script's diagnostic surface is interchangeable.

---

## 3. Gate the Toggle Behind a Hotkey, Not a GUI Widget Default

**The diagnostic overlay should default to OFF and be toggleable via a hotkey. A GUI checkbox is fine *as well*, but the hotkey is the primary control.**

End users won't navigate to a GUI section just to enable diagnostics — they'll Discord-message the author asking "why doesn't this work?" A hotkey they can hit gives them (and you, helping them) a 1-second path to the diagnostic info.

```cpp
bool   g_diag_enabled = false;
int32  g_diag_hotkey  = 0x77;   // VK_F8 by default

int64 main() {
    // ... process attach ...

    int64 sec = create_section("Debug");
    section_checkbox(sec, "Show diagnostic overlay", g_diag_enabled);
    section_keybind(sec, "Toggle diagnostic hotkey", g_diag_hotkey);
    section_separator(sec);
    section_label(sec, "Hotkey toggles section 1-5 readout.");

    register_routine(cast<int64>(on_update),            0);
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    return 1;
}

void on_update(int64 data) {
    if (is_key_pressed(g_diag_hotkey)) {
        g_diag_enabled = !g_diag_enabled;
    }
    // ... feature update logic ...
}
```

When the user reports a problem, the support cycle is:

```
You:    "Hit F8 in-game, screenshot the panel, paste it to me."
User:   [screenshot]
You:    "entity_list resolved=0 — your binary doesn't match the supported version.
        See README requirements."
```

The diagnostic panel + hotkey reduces a 20-message back-and-forth to a 2-message exchange.

**Why:** Hotkeys are the universal "I need diagnostic info now" gesture. GUI checkboxes are good for opt-in features the user explicitly knows they want; diagnostic toggles need to be reachable when the user is *confused*, which is when they're not navigating GUI panels.

---

## 4. Diagnostic Routines Are Read-Only — Never Modify Game State

**The diagnostic overlay reads everything it shows. It never writes, never patches, never calls into game functions, never modifies the script's own behavior.**

This is the rule that lets you leave the diagnostic surface enabled in production builds for support purposes — it cannot break anything by being on. If the diagnostic does any of these:

- Calls `memory_write` to patch a value
- Calls a game function via a hook
- Modifies any other feature's globals (e.g. forcing `g_aim_target_id = X` "to test")
- Reads in a way that has side effects (rare, but some MMIO regions do)

...then the diagnostic itself is now a feature, with its own correctness concerns. It needs its own evidence entries (`skill://re-evidence-log`), its own validation, its own bug surface. Conflating "diagnostic" and "active feature" produces neither well.

The cost of pure-read diagnostics: occasionally you want to verify a write path. Don't put that in the diagnostic overlay; put it in a *separate* "lab" feature in `Misc` with its own master toggle, its own warnings, its own GUI gating. The lab feature is opt-in destructive; the diagnostic overlay is opt-in observational.

```cpp
// RIGHT — pure read diagnostic
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // reads only — g_proc.ru64, g_proc.read_memory, accumulator dereferences
}

// WRONG — diagnostic that also writes
void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    if (is_key_pressed(VK_F9)) {
        g_proc.write_u32(g_off_health, 100);   // "just testing health write"
    }
    // ... drawing ...
}

// RIGHT — separate lab feature, GUI-gated, distinct toggle
bool g_lab_enabled = false;
void on_update_lab(int64 data) {
    if (!g_lab_enabled) return;
    if (is_key_pressed(VK_F9)) {
        g_proc.write_u32(g_off_health, 100);   // intentional, opted-in
    }
}
```

**Why:** A read-only diagnostic can stay enabled during gameplay without consequence; an active diagnostic can't. The discipline preserves the diagnostic overlay's "safe to leave on" property, which is what makes it useful for support.

---

## 5. Atomic Counters for Cross-Routine State

**When multiple routines (update + render + features) increment error counters or sample profile buckets, use atomic types (`addon-atomic`) — not plain integers.**

PCX scripts can have multiple routines firing on different scheduler cadences; if both `on_update` and `on_render` write to `g_err_null_reads`, the increments can interleave and lose counts on plain integers. `aint32` / `aint64` (per `docs/enma/addon-atomic.md`) handle this correctly without locks.

```cpp
import "atomic";

aint32 g_err_null_reads;
aint32 g_err_sig_fallbacks;
aint64 g_total_reads;

void on_update(int64 data) {
    uint64 entity = g_proc.ru64(g_off_entity_list);
    g_total_reads.add(1);                  // atomic increment
    if (entity == 0) {
        g_err_null_reads.add(1);
        return;
    }
    // ...
}

void on_render_diagnostic(int64 data) {
    if (!g_diag_enabled) return;
    // load() reads the current atomic value
    int32 nulls = g_err_null_reads.load();
    int64 total = g_total_reads.load();
    draw_text(format("  null reads: {d} / {d} total", nulls, total),
              vec2(x, y), fg, font, 1, shadow, 1.0);
}
```

For single-writer counters (only `on_update` increments, only `on_render_diagnostic` reads), plain integers are fine — atomic is overkill. The atomic discipline applies when multiple writers exist.

**Why:** Lost counts in error counters silently hide bugs (you report "10 null reads" when the actual was 47 because 37 increments interleaved and overwrote each other). Atomics are cheap; the bug they prevent is invisible.

---

## 6. Ship a Diagnostic-Only Build for Power Users

**Some users want the diagnostic build by default — the streamer doing tech-content, the long-tail debugger, the script's contributor. Ship two `.emb` artifacts: production (`script.emb`) and diagnostic (`script-debug.emb`).**

The split:

| Build | `g_diag_enabled` default | `g_diag_hotkey` works | Extra debug features |
|---|---|---|---|
| `script.emb` (production) | `false` | yes | none |
| `script-debug.emb` (diagnostic) | `true` | yes | profiler dumps to file, extra logging |

The implementation: a single `#define` (per `docs/enma/lang-pre-processor.md`) controls the build flavor:

```cpp
// At the top of main.em
#define BUILD_FLAVOR_DEBUG     // comment out for production

#ifdef BUILD_FLAVOR_DEBUG
    bool g_diag_enabled_default = true;
#else
    bool g_diag_enabled_default = false;
#endif

bool g_diag_enabled = g_diag_enabled_default;

#ifdef BUILD_FLAVOR_DEBUG
    // Extra debug-only routines
    void on_update_log_to_file(int64 data) {
        // periodic snapshot of profiler buckets to disk for offline analysis
    }
#endif

int64 main() {
    // ... process attach ...
    register_routine(cast<int64>(on_render),            0);
    register_routine(cast<int64>(on_render_diagnostic), 0);
    #ifdef BUILD_FLAVOR_DEBUG
        register_routine(cast<int64>(on_update_log_to_file), 0);
    #endif
    return 1;
}
```

Build both flavors as part of your release process (see `skill://script-bundler`). Ship the production one as the headline download; ship the debug one as a "for support / contributors" link in the README.

**Why:** Two builds from one source is cheap (one `#define` swap, two compilations); the value to users who need diagnostics-by-default (streamers, contributors, support) is real. The alternative is shipping one build and asking users to enable diagnostics manually each time — fine for most, friction for the power users you want engaged.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | Two overlays, always separate | Production renders user-visible features; diagnostic renders script-internal state |
| 2 | Five standard sections | Process / Sigs / Runtime / Profile / Errors — covers ~90% of "script isn't working" reports |
| 3 | Hotkey-gated, off by default | Default off, F8 toggles on — reachable when the user is confused, invisible otherwise |
| 4 | Read-only diagnostics | No writes, no hooks; lab/test features are separate, opt-in destructive features |
| 5 | Atomic counters for cross-routine state | `aint32` / `aint64` for multi-writer counters; plain ints for single-writer |
| 6 | Two builds: production + diagnostic | `#define BUILD_FLAVOR_DEBUG` switch; both shipped, production headline |

**Cross-references:** `skill://pcx-perf-budget` (the `mono_us()` profiler recipe section 4 consumes); `knowledge/gui-design-patterns.md` (the "no debug panel by default" rule this skill extends); `skill://script-bundler` (the two-build process); `skill://re-evidence-log` (the lab features' citation discipline); `docs/enma/addon-atomic.md` (the atomic types section 5 uses); `docs/enma/lang-pre-processor.md` (the `#ifdef` mechanism section 6 uses).

---

## Source: `.claude/skills/pcx-defer-ledger/SKILL.md`

---
name: pcx-defer-ledger
description: >
  Harvest every `// defer:` comment in the PCX project into a debt ledger.
  Tracks deliberate shortcuts (global handles, hardcoded colors, single-walk
  assumptions) so deferrals don't rot into permanent hacks. Use when the user
  says "defer ledger", "what did we defer", "list shortcuts", "show debt", or
  invokes /pcx-defer-ledger. One-shot report, changes nothing.
license: MIT
---

Every deliberate shortcut is marked `// defer: <ceiling>, <trigger>`. This
collects them into one ledger so a deferral can't quietly become permanent.

## Scan

Search `.em` and `.as` files for `// defer:` markers, skipping build output:

```
grep -rnE '// ?defer:' --include='*.em' --include='*.as' .
```

Also scan for `// UNVERIFIED` — those are offset-confidence markers, tracked
separately but surfaced in the same report.

## Output

### Defer markers

One row per marker, grouped by file:

```
<file>:<line> — <what was simplified>. ceiling: <limit>. trigger: <when to revisit>.
```

Pull ceiling and trigger from the comment. The convention is
`// defer: <ceiling>, <trigger>`.

### Rot risk

Flag `no-trigger` on any `// defer:` that names no upgrade condition — those
rot silently.

### Unverified offsets

Separate section:

```
<file>:<line> — <offset/field>. source: UNVERIFIED.
```

These aren't shortcuts, they're confidence gaps. Surface them so they can be
resolved against the live target.

### Summary

```
<N> defer markers (<M> with no trigger)
<P> UNVERIFIED offsets
```

Nothing found: `No deferred debt. Clean ledger.`

## Boundaries

Reads and reports only, changes nothing. To persist: ask, and it writes the
ledger to `DEFER-LEDGER.md` at the project root. One-shot.

---

## Source: `.claude/skills/pcx-knowledge-index/SKILL.md`

---
name: pcx-knowledge-index
description: >
  Guide to the three surfaces (llms.txt static index, bundle files, MCP
  server) through which AI tools reach the toolkit corpus, and which to pick
  under which integration model. Always active when working with the
  pcx-ai-toolkit knowledge base from any AI tool (Claude Code, Cursor, Cline,
  Aider, Copilot, Continue, Zed).
license: MIT
---

# PCX Knowledge Index — The Three Ways AI Tools Reach the Toolkit's Corpus

The toolkit publishes its docs / skills / knowledge / templates / tools via three complementary surfaces, each optimized for a different AI-tool integration model. This skill names which surface to reach for under which circumstances, so a session doesn't waste tokens preloading a 4 MB bundle when MCP search would do, and doesn't fail mid-task because the tool only supports `@`-file references and you reached for a search call instead.

**Always active when working with the pcx-ai-toolkit corpus from an AI tool.** Applies to Claude Code, Claude Desktop, Cursor, Cline, Aider, Copilot, Continue, Zed, and any other AI tool that consumes external knowledge.

**Prerequisite:** `tools/build-llms-index.py` (the generator for the static surface), `mcp/pcx-knowledge-mcp/` (the dynamic surface), the per-IDE drop-ins (`rules/CLAUDE.md`, `rules/CURSOR.md`, etc.) for how each tool wires in its preferred surface.

---

## Trigger

About to load the toolkit's docs into AI context, the user asked which doc to use, the AI is preloading too much / too little context, deciding whether to ship the toolkit content as bundles vs MCP server vs both, debugging "the AI doesn't know about the PCX X API," configuring a new AI tool to consume the toolkit.

---

## The Three Surfaces

### 1. `llms.txt` — the Auto-Fetch Convention

Located at `docs/llms.txt` (also `docs/llms-full.txt` for the full bundle).

**What it is.** A structured plain-text index of the entire toolkit, following the Anthropic / Mintlify `llms.txt` convention. ~45 KB; lists every doc, skill, knowledge file, IDE drop-in, template, signature guide, and tool with its title, URL, and one-line description grouped by category.

**Who uses it.** Tools that auto-fetch this convention from a project's root:
- Claude (when given a repo URL, often auto-fetches `<repo>/llms.txt`)
- Cursor (configurable)
- Cline (via project context)
- Several others, growing

**When to reach for it.** First-touch with a new tool, or any time you want the tool to discover the toolkit's surface area without manually `@`-referencing every file.

**Cost.** ~45 KB of context (the index, not the full content). Tiny relative to the value.

### 2. Concatenated Context Packs — the Bundle Surface

Located at `docs/llms-full.txt`, `docs/llms-perception-{enma,angelscript,lua}.md`, `docs/llms-skills.md`, `docs/llms-knowledge.md`.

**What it is.** Per-language and per-category single-file concatenations of the relevant subset of the toolkit. Each file carries every member document inline with stable separators and the original source path preserved.

| Bundle | Scope | Size |
|---|---|---:|
| `llms-full.txt` | Everything (docs / skills / knowledge / rules / templates / signatures) | ~2 MB |
| `llms-perception-enma.md` | Enma language + APIs + Enma-discipline skills + cheatsheet | ~950 KB |
| `llms-perception-angelscript.md` | AngelScript APIs + AS discipline + cheatsheet | ~400 KB |
| `llms-perception-lua.md` | Lua APIs + Lua discipline + cheatsheet | ~215 KB |
| `llms-skills.md` | All 17 skills concatenated | ~300 KB |
| `llms-knowledge.md` | All 20 knowledge references concatenated | ~350 KB |

**Who uses it.** Any tool that accepts a single file as context:
- Aider (`/read docs/llms-perception-enma.md`)
- Copilot (paste-into custom instructions, or `@file` reference)
- Cursor (`@docs/llms-perception-enma.md`)
- Continue (`@files`)
- Any AI editor that has a "load file as context" surface

**When to reach for it.** Tools without MCP support, sessions where you know upfront which language you'll work in (load the matching pack), or anywhere the AI client is stateless across calls and you want a known-fixed context surface.

**Cost.** The chosen bundle's full byte cost loaded into context. The per-language bundles are much smaller than `llms-full.txt`; default to the per-language pack unless you're working across all three.

### 3. The Knowledge MCP Server — the Dynamic Surface

Located at `mcp/pcx-knowledge-mcp/` (Python package).

**What it is.** An MCP server exposing four tools (`search`, `get_file`, `list_files`, `overview`) and every file as a `file://<repo-path>` resource. Search is keyword-based with light TF-IDF scoring, runs in-process, no embeddings model, no external service. Returns ranked `{path, score, snippet}` results.

**Who uses it.** Any MCP-aware tool:
- Claude Desktop
- Cline
- Cursor (MCP support varies by version)
- Continue
- Zed
- Custom MCP clients

**When to reach for it.** Long sessions where you'll touch many files unpredictably, sessions where you don't know upfront which docs you need, or any time you want lazy loading instead of preload-everything. The AI calls `search("entity list walk")` first, then `get_file(top_hit)` — only the relevant slice ends up in context.

**Cost.** One running Python process. Per-query latency <50ms cold, <5ms warm. Memory: ~5-10 MB resident.

---

## The Decision Tree

```
Which surface should I use right now?

  ┌─ Is the AI tool MCP-aware AND will the session span many files?
  │
  ├── YES → MCP server (mcp/pcx-knowledge-mcp/)
  │        Configure once per client; the AI searches lazily.
  │        Examples: Claude Desktop, Cline, Continue.
  │
  └── NO  → continue
            │
            ├─ Will the session work primarily in ONE language (Enma / AS / Lua)?
            │
            ├── YES → the matching per-language bundle (docs/llms-perception-<lang>.md)
            │        Smallest preload that covers the typical session.
            │        Examples: Aider /read, Cursor @file, Continue @files.
            │
            └── NO  → continue
                      │
                      ├─ Does the tool auto-fetch llms.txt conventions?
                      │
                      ├── YES → let it; no manual setup needed.
                      │        Examples: Claude when given the repo URL.
                      │
                      └── NO  → load docs/llms-full.txt (~2 MB) or
                                a category-specific bundle (llms-skills.md / llms-knowledge.md).
```

The choices are not exclusive — combining the MCP server with a small upfront bundle (e.g. `llms-perception-enma.md` for "you work in Enma" baseline + MCP for "and you can search the rest") is the recommended setup for long, complex sessions.

---

## Recipe per AI Tool

### Claude Code (this tool)

- Primary: skills auto-load; this skill IS one of them.
- For specific docs: `@`-reference by path, or use the perception MCP (the runtime one in `mcp/perception-mcp-config.json` — not the knowledge one). The knowledge MCP is more useful for Claude Desktop than Claude Code.

### Claude Desktop

- **Wire the knowledge MCP** (see `mcp/pcx-knowledge-mcp/README.md` for the JSON config).
- Optionally also drop `docs/llms-perception-enma.md` content into Claude Desktop's "Files" feature for persistent context.

### Cursor

- **First choice**: `@docs/llms-perception-<lang>.md` per session, scoped to the language.
- **For wider exploration**: configure the knowledge MCP via `.cursor/mcp.json`.
- The `.cursorrules` file (`rules/CURSOR.md`) handles project-rule baseline.

### Cline

- **Wire the knowledge MCP** via `cline_mcp_settings.json` (see `rules/CLINE.md`).
- Use Plan mode + the MCP's `search` tool to explore before any edits.
- Auto-approve read-only MCP tools (search, get_file, list_files, overview) — they're safe.

### Aider

- **Per-session**: `/read docs/llms-perception-enma.md` (or matching language pack).
- For broader work: `/read docs/llms-full.txt` (large; only when you'll truly use the breadth).
- Pair with `CONVENTIONS.md` carrying `rules/CLAUDE.md` content.
- The knowledge MCP works but Aider's MCP support is newer/less mature than Continue's or Cline's.

### Copilot

- **Wire `.github/copilot-instructions.md`** with `rules/COPILOT.md` content.
- For session context: paste `docs/llms-perception-<lang>.md` excerpts into the chat (Copilot Chat) when working on a specific area.
- Copilot doesn't speak MCP, so the static bundles are the only surface.

### Continue

- **Wire the knowledge MCP** via `.continue/config.yaml` `mcpServers` block.
- Pin `knowledge/pcx-api-cheatsheet.md` as always-loaded context via Continue's per-project config.

### Zed

- **Wire the knowledge MCP** via `~/.config/zed/settings.json` `context_servers`.
- For agent panel: `@`-reference docs as needed; the MCP search handles the discovery half.

---

## When the Bundles Drift

The static bundles (`docs/llms*.{txt,md}`) are generated by `tools/build-llms-index.py`. If you commit changes to docs / skills / knowledge / etc. *without* regenerating the bundles, they go stale. The fix:

```bash
python3 tools/build-llms-index.py          # regenerate
git add docs/llms*
git commit
```

CI runs `python3 tools/build-llms-index.py --check`; the build fails on drift. This is the same discipline as committing a generated lockfile or compiled-protobuf — if you change the source, regenerate the artifact.

---

## When You Don't Need the Index at All

For one-off lookups of a specific known doc, just read the file directly. The whole indexing apparatus is for the case where the AI doesn't know what's there to read; if you (the human) know the path, just `read docs/perception/render-api.md` and skip the index entirely.

The index also doesn't help with content the toolkit doesn't have — if you're working on a different PCX runtime version with different APIs, the toolkit's docs are the wrong source regardless of which surface you reach them through. See `knowledge/pcx-version-matrix.md` for the version dimension.

---

## Summary

| # | Surface | When to use | Cost |
|---|---|---|---|
| 1 | `docs/llms.txt` | First-touch with a new tool; auto-fetch convention | ~45 KB context |
| 2 | `docs/llms-perception-<lang>.md` | One-language session in a non-MCP tool | ~215-950 KB context |
| 3 | `docs/llms-full.txt` | All-language session in a non-MCP tool | ~2 MB context |
| 4 | `docs/llms-skills.md` / `llms-knowledge.md` | Skills- or knowledge-focused session | ~300-350 KB context |
| 5 | `mcp/pcx-knowledge-mcp/` server | MCP-aware tool, long session, lazy loading | One running process |

**Combine #2 + #5** for the best of both: small upfront context for your primary language + searchable depth for everything else. Recommended for long sessions.

**Cross-references:** `tools/build-llms-index.py` (generates the static bundles), `mcp/pcx-knowledge-mcp/` (the server + install guide), `.claude/skills/mcp-tool-routing/SKILL.md` (which Perception runtime MCP tool for which task — different MCP, different purpose), `.claude/skills/ai-pair-programming/SKILL.md` (the meta-workflow this skill slots into at the "load context" step).

---

## Source: `.claude/skills/pcx-lua-discipline/SKILL.md`

---
name: pcx-lua-discipline
description: >
  Lua-specific rules for writing Perception.cx scripts in Lua 5.4.6.
  Prevents Enma-reflex errors (typed addresses, C truthiness, struct value
  types, register_routine) in the Lua scripting surface. Always active when
  editing .lua PCX scripts — applies on top of game-cheat-guidelines.
license: MIT
---

# PCX Lua Discipline — Lua Idioms for Perception.cx Scripts

Lua-specific rules for writing Perception.cx scripts in **Lua 5.4.6** (confirmed in `docs/perception/lua/render-api.md`). PCX exposes a third scripting surface alongside Enma and AngelScript; the host APIs are nearly identical in shape but the *language* underneath is Lua, and the failure modes are different. Default to Lua semantics here, not Enma idioms — Enma reflexes (typed addresses, C truthiness, struct value types, `register_routine`) produce code that silently misreads memory or never runs.

**Always active when writing or editing `.lua` PCX scripts.** These rules apply on top of `game-cheat-guidelines`, not instead of it.

**Prerequisite:** `game-cheat-guidelines` MUST be loaded alongside this skill — its 12 rules (ground offsets, validate chains, separate scan from render, sigs over hardcodes, minimize writes) still govern *what* you do to memory. This skill governs *how Lua expresses it*. **Read the relevant page in `docs/perception/lua/` before writing any host API call.**

## Trigger

Activate when: the script file is `.lua`; the user asks for a Lua overlay/ESP/aimbot/dumper; you are porting an Enma or AngelScript script to Lua; you see `ref_process`, `on_frame`, `ui.create_subtab`, `proc:ru64`, or `string.format("0x%016X", ...)`; or you catch yourself writing `uint64 x =`, `register_routine`, `cast<>`, or `color(...)` in a file that is supposed to be Lua.

---

## 1. Addresses Are 64-bit Integers — Keep Them Integer-Typed

**Lua 5.4 has one number value with two subtypes: integer and float. Addresses are integers. The moment a float touches address math, anything past 2^53 is silently wrong.**

PCX is built on Lua 5.4.6, which has a true 64-bit integer subtype — so `proc:base_address()` returns a full-width integer, not a lossy double (`docs/perception/lua/proc-api.md` documents every read as `--> number (uint64)`, and `engine-specific-api.md` calls returned pointers "integer addresses"). This is *unlike* LuaJIT/5.1, where every number is a double and high addresses are already broken. The danger in 5.4 is the silent promotion: `/`, `^`, and mixing a float literal into the expression turn an exact integer into a float, and `0x7FF6_1234_5678` cannot be represented exactly as a double.

```lua
-- WRONG — float division and a float literal poison the address
local base = proc:base_address()
local slot = base + (i / 2)          -- '/' always yields a float in 5.4
local ent  = base + index * 8.0      -- 8.0 is a float; whole expr promotes
-- ent is now a float; past 2^53 it rounds to the wrong byte, read returns garbage

-- RIGHT — stay in integer land
local base = proc:base_address()
local slot = base + (i // 2)         -- floor division keeps the integer subtype
local ent  = base + index * 8        -- integer literal, integer result
```

**Why:** A float-contaminated address does not error — `proc:ru64` happily reads from the rounded address and returns more plausible-looking garbage. You get ESP at (0,0) and no stack trace. Use `//` (floor division) not `/`, use integer literals (`8` not `8.0`), and when you must check, `math.type(addr) == "integer"` tells you the subtype. Format with `%X`/`%d`, never `%f`.

---

## 2. `0` Is Truthy in Lua — Nil-Check and Zero-Check Are Different Tests

**`if x then` is true for `0`. PCX host functions split into two failure conventions, and using the wrong test lets failures through.**

This is the single biggest Enma-to-Lua porting bug. In C/Enma, `0` is false; in Lua, only `nil` and `false` are falsy — `0`, `0.0`, and `""` are all truthy. PCX host functions fail in two different ways (`docs/perception/lua/proc-api.md`):

- Return **`nil`** on failure: `ref_process`, `proc:get_module` → `if not x then` is correct.
- Return **`0`** on failure: `proc:find_code_pattern`, `proc:get_proc_address`, and every scalar read → you MUST compare `== 0` explicitly, because `if addr then` is **true** when `addr == 0`.

```lua
-- WRONG — a missed sig returns 0, and 0 is truthy, so this branch runs anyway
local hit = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
if hit then                          -- TRUE even when hit == 0
    local list = proc:ru64(hit + 3)  -- reads from 0x3, returns garbage
end

-- RIGHT — match the test to the convention
local proc = ref_process("game.exe")
if not proc then return 0 end                 -- nil convention
local base, size = proc:get_module("game.exe")
if not base then return 0 end                 -- nil convention

local hit = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
if hit == 0 then return 0 end                 -- ZERO convention — explicit
local list = proc:ru64(base + ENTITY_LIST_OFF)
if list == 0 then return 0 end                -- reads fail to 0, check it
```

**Why:** `if addr then` reads as a null check to anyone with a C background, but in Lua it only catches `nil`. A stale sig returns `0`, the truthy check passes, and you dereference address `0`. Memorize the split: handles are `nil`-checked, addresses and reads are `== 0`-checked.

---

## 3. A Table Is an Array or a Map — Never Both in One Variable

**Pick one shape per table. Mixing 1-based integer keys with string keys breaks `#`, `ipairs`, and every reader after you.**

Lua has one container type. PCX leans on both faces of it: `proc:read_struct_array` returns a **1-based array** (`docs/perception/lua/proc-api.md`), while struct descriptors and the view tables from `unreal_engine.read_minimal_view_info` are **string-keyed maps** (`docs/perception/lua/engine-specific-api.md`). The `#` operator and `ipairs` only work on a *sequence* (contiguous integer keys `1..n`); the instant you stash a string key on an array, `#t` becomes unreliable and `ipairs` stops early.

```lua
-- WRONG — array with a bolted-on string field
local ents = {}
ents[1] = ptr_a
ents[2] = ptr_b
ents.count = 2                       -- now #ents and ipairs are unreliable
for i = 1, #ents do ... end          -- may or may not see everything

-- RIGHT — array stays a pure sequence; metadata lives elsewhere
local ents = proc:read_struct_array(list_base, MAX_ENTS, ENT_SIZE, ENT_DESC)
for i, e in ipairs(ents) do          -- ipairs for sequences
    if e.health > 0 then draw_enemy(e) end
end

-- RIGHT — a descriptor is a map; iterate with pairs, never #
local ENT_DESC = {
    health = { offset = HEALTH_OFF, type = "i32" },
    pos_x  = { offset = POS_OFF,    type = "f32" },
}
for name, field in pairs(ENT_DESC) do ... end
```

**Why:** `#t` on a mixed table returns *any* border, not the count you meant — a documented Lua quirk, not a bug you can patch around. Use `ipairs`/`#` for sequences you built contiguously, `pairs` for maps, and keep the two roles in separate variables.

---

## 4. PCX Userdata Carries a Host Metatable — Don't Replace It

**`process`, `ui_*`, and `net_ws` handles are userdata with host-owned metatables. `setmetatable` on them breaks method dispatch. Wrap, don't reparent.**

Every PCX handle is userdata whose methods (`proc:ru64`, `cb:get`, `ws:send_text`) resolve through a metatable the host installed — `docs/perception/lua/net-api.md` names the WebSocket metatable `"net_ws"` outright. If you `setmetatable` one of these to add a helper, you detach `__index` and the built-in methods vanish. The Lua-correct move when you want helpers is to wrap the handle in a *plain table* you own and forward to it.

```lua
-- WRONG — clobbers the host metatable; proc:ru64 now errors
setmetatable(proc, { __index = { read_ptr = function(self, a) ... end } })

-- RIGHT — your own wrapper table delegates to the real handle
local Mem = {}
Mem.__index = Mem
function Mem.new(proc) return setmetatable({ p = proc }, Mem) end
function Mem:chain(base, ...)        -- helper that null-checks each hop
    local addr = base
    for _, off in ipairs({...}) do
        addr = self.p:ru64(addr + off)
        if addr == 0 then return 0 end
    end
    return addr
end

local mem = Mem.new(proc)
local weapon = mem:chain(base, OFF_LOCAL, OFF_WEAPON)
```

**Why:** Host userdata is opaque on purpose. Replacing its metatable is how you get `attempt to call a nil value (method 'ru64')` three frames later. Extend behavior by composition — a table that holds the handle and adds methods — and leave the host's metatable untouched.

---

## 5. Pass Function *Values* to Callbacks; Lifecycle Hooks Are Looked Up by Global Name

**There is no `register_routine` in Lua. Button callbacks take a function value. Lifecycle hooks must exist as global functions with exact names.**

PCX Lua wires logic two ways (`docs/perception/lua/life-cycle.md`, `gui-api.md`):

- **Lifecycle** — the engine calls the *globals* `main`, `on_frame`, and `on_unload` by name. They must be global (`function main()`, not `local function main()`) and spelled exactly. There is no registration call.
- **GUI callbacks** — `panel:add_button(name, fn)` takes a **function value** (a closure or a reference), not a string name.

```lua
-- WRONG — Enma reflexes: there is no register_routine, and a name string is not a callback
register_routine(on_frame, 0)                 -- nil global -> error
pnl:add_button("Reload", "do_reload")         -- string is not callable

-- WRONG — lifecycle hook hidden behind a local; engine never finds it
local function on_frame() ... end             -- not global -> never runs

-- RIGHT — globals for lifecycle, a function value for the callback
function main()
    local st  = ui.create_subtab(0, "ESP")
    local pnl = st:add_panel("Main", false)
    pnl:add_button("Reload Offsets", function() resolve_offsets() end)
    return 1                                   -- >0 AND on_frame defined => persistent
end

function on_frame() ... end                    -- engine calls this by name every frame
function on_unload() deref_process(g_proc) end -- cleanup hook
```

**Why:** `main()` returning `> 0` only keeps the script alive *if `on_frame` exists* (`life-cycle.md`); a `local function on_frame` is invisible to the engine and your overlay silently unloads. And a callback passed as `"do_reload"` is just a string — the button does nothing. Globals for hooks, function values for callbacks.

---

## 6. Closures Capture Upvalues by Reference — The Bite Is Shared Mutable State, Not the Loop Variable

**Lua's numeric `for` gives each iteration a fresh variable, so closing over the loop counter is safe. What bites is a closure or coroutine that captures an outer mutable local and runs *later*.**

The JS `var`-in-loop trap does not exist here: in Lua 5.4 the `for i = ...` control variable is a fresh local per iteration, so buttons created in a loop capture distinct `i` values correctly. The real PCX bug is deferred execution over a *shared upvalue* — a callback or `on_frame`-resumed coroutine that reads a variable mutated after the closure was created.

```lua
-- SAFE — each iteration's `i` is a fresh local; every button prints its own index
for i = 1, 3 do
    pnl:add_button("Slot " .. i, function() print("slot", i) end)
end

-- WRONG — all closures share the single upvalue `cur`, read at click time
local cur
for _, ent in ipairs(entities) do
    cur = ent                                  -- mutated every iteration
    pnl:add_button("Lock " .. ent.name, function() lock(cur) end)
end                                            -- every button locks the LAST entity

-- RIGHT — capture a fresh per-iteration local
for _, ent in ipairs(entities) do
    local target = ent                         -- new local each iteration
    pnl:add_button("Lock " .. ent.name, function() lock(target) end)
end
```

**Why:** Closures grab the *variable*, not its value-at-creation. A loop-local declared inside the body is fresh each pass and captures cleanly; a single local declared outside the loop is one shared box that every closure sees mutate. This matters most for GUI callbacks and coroutines (rule 9) that fire long after the loop finished.

---

## 7. Wrap Genuinely-Throwing Calls in `pcall` — One Bad Pointer Must Not Kill the Frame

**Scalar reads fail soft (return `0`/`""`), so don't `pcall` them. A handful of helpers raise Lua errors — those you wrap, or an uncaught error aborts `on_frame`.**

PCX reads are designed to fail quietly: `proc:ru64` on a bad address returns `0`, `proc:rs` returns `""` (`docs/perception/lua/proc-api.md`). Wrapping those in `pcall` is noise. But some helpers *raise*: `unreal_engine.world_to_screen` "raises a Lua error" on invalid input (`docs/perception/lua/engine-specific-api.md`), and JSON/net parsing can throw. An uncaught error propagates out of `on_frame`, and returning nothing (or erroring) unloads the script mid-session.

```lua
-- WRONG — reads already fail soft; this pcall is pure overhead
local ok, hp = pcall(function() return proc:r32(ent + HEALTH_OFF) end)

-- WRONG — w2s can raise; an uncaught error here kills the whole overlay this frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local s = unreal_engine.world_to_screen(e.pos, g_view)  -- may error
        draw_box(s.x, s.y)
    end
end

-- RIGHT — pcall only the call that actually throws; degrade one entity, not the frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local ok, s = pcall(unreal_engine.world_to_screen, e.pos, g_view)
        if ok and s and s.visible then         -- w2s also returns nil behind camera
            draw_box(s.x, s.y)
        end
    end
end
```

**Why:** Reads returning `0` are handled by rule 2's zero-checks, not by `pcall` — wrapping them buys nothing and hides the real check. Reserve `pcall` for the documented throwers, and scope it to the smallest call so a single malformed entity skips a draw instead of blanking the overlay and unloading the script.

---

## 8. Build Hot-Path Strings with `table.concat`, Never `..` in `on_frame`

**Lua strings are immutable. Each `..` allocates and interns a new string; chaining them in a per-frame loop is O(n²) garbage churn. Format once, cache, or use `table.concat`.**

Every `..` produces a fresh immutable string (the engine's own example uses `table.concat` for exactly this reason — `docs/perception/lua/proc-api.md` line ~279). In `on_frame`, which runs every frame, repeated concatenation allocates per frame and thrashes the GC, dropping FPS. Best is to not build strings in render at all: compute display text in the update pass and cache it; `draw_text` takes the cached string directly.

```lua
-- WRONG — N concatenations per entity, every frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local label = "[" .. e.name .. "] " .. e.hp .. "hp " .. e.dist .. "m"
        draw_text(label, e.sx, e.sy, 255,255,255,255, g_font, TE_SHADOW, 0,0,0,180, 1.0)
    end
end

-- RIGHT — format in the update pass, cache the string, draw the cache
function update_labels()                       -- runs on interval, not every frame
    for _, e in ipairs(g_ents) do
        e.label = string.format("[%s] %dhp %dm", e.name, e.hp, e.dist)
    end
end

function on_frame()
    for _, e in ipairs(g_ents) do
        draw_text(e.label, e.sx, e.sy, 255,255,255,255, g_font, TE_SHADOW, 0,0,0,180, 1.0)
    end
end

-- When you must assemble many pieces, collect and join once
local parts = {}
for i, e in ipairs(g_ents) do parts[i] = e.name end
local csv = table.concat(parts, ", ")          -- one allocation
```

**Why:** `a .. b .. c` builds two intermediate strings and a final one, all interned; do that for 64 entities at 240 FPS and the allocator is your bottleneck. `string.format` in a cached field (rule from `game-cheat-guidelines` #4: separate scan from render) keeps the render path allocation-free, and `table.concat` collapses a join to a single allocation.

---

## 9. Use Coroutines to Spread Heavy Work Across Frames

**The `coroutine` add-on is enabled. A scan that stalls one frame should `yield` periodically and be resumed a slice at a time from `on_frame` — never loop until done inside a single frame.**

`docs/perception/lua/overview.md` lists `coroutine` as a registered add-on, and `life-cycle.md` is explicit: "No infinite loops — frame updates are handled by the engine." A full-module pattern scan or a deep entity walk done synchronously in one `on_frame` freezes the overlay. Model it as a coroutine that does a bounded chunk, `coroutine.yield`s, and is resumed each frame until `coroutine.status` is `"dead"`.

```lua
-- WRONG — scans the whole module in one frame; overlay hitches
function on_frame()
    g_list = proc:find_code_pattern(base, size, SIG)   -- blocks the frame if huge
end

-- RIGHT — a coroutine that scans in slices, resumed once per frame
local scanner
function main()
    g_proc = ref_process("game.exe")
    if not g_proc then return 0 end
    scanner = coroutine.create(function()
        local base, size = g_proc:get_module("game.exe")
        if not base then return end
        local CHUNK = 0x100000                          -- 1 MiB per frame
        local off = 0
        while off < size do
            local hit = g_proc:find_code_pattern(base + off, math.min(CHUNK, size - off), SIG)
            if hit ~= 0 then g_entity_list = hit; return end
            off = off + CHUNK
            coroutine.yield()                           -- give the frame back
        end
    end)
    return 1
end

function on_frame()
    if scanner and coroutine.status(scanner) ~= "dead" then
        local ok = coroutine.resume(scanner)            -- resume returns ok, err
        if not ok then scanner = nil end                -- coroutine errored; stop
    end
    -- render from whatever state is ready
end
```

**Why:** A coroutine turns a one-frame freeze into a smooth multi-frame task without threads or callbacks. `coroutine.resume` returns `false` plus the error message if the body throws — check it (same spirit as rule 7) so a failed scan stops cleanly instead of resuming a dead coroutine. `ponytail:` only reach for coroutines when the work genuinely overruns a frame; a fast scan in `main()` needs none of this.

---

## 10. `require` for File-Per-Feature Modules — Return a Table, Don't Leak Globals

**The `package` add-on gives you `require()`. Keep one feature per file, share state through a returned module table, and reserve globals for the lifecycle hooks the engine calls by name.**

`docs/perception/lua/overview.md` registers `package` with "`require()` and module loading", so the standard Lua module pattern applies and `game-cheat-guidelines` rule #6 (one feature, one file) carries over directly. `require` runs a module once and caches the result — return a table of that feature's API instead of scattering globals. The exception is the lifecycle trio (`main`/`on_frame`/`on_unload`, rule 5): those must be globals in the entry script.

```lua
-- offsets.lua — resolves and exposes addresses
local M = {}
function M.resolve(proc)
    local base, size = proc:get_module("game.exe")
    if not base then return false end
    M.entity_list = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
    if M.entity_list == 0 then return false end          -- rule 2: zero-check
    return true
end
return M

-- esp.lua — pure render, imports shared state
local offsets = require("offsets")
local M = {}
function M.draw(proc) ... end
return M

-- main.lua — entry script; globals only for lifecycle
local offsets = require("offsets")
local esp     = require("esp")
g_proc = nil

function main()
    g_proc = ref_process("game.exe")
    if not g_proc then return 0 end
    if not offsets.resolve(g_proc) then return 0 end
    return 1
end

function on_frame() esp.draw(g_proc) end
function on_unload() deref_process(g_proc) end           -- always release the handle
```

**Why:** `require` caching means a module's top-level code runs exactly once — perfect for resolving offsets, wrong for per-frame work. Returning a table keeps each feature's surface explicit and reloadable; dumping everything into globals reintroduces the god-script you split the files to avoid. And every `ref_process` needs its matching `deref_process` in `on_unload` (`docs/perception/lua/proc-api.md`) — a leaked handle outlives the script.

---

## Summary

| # | Rule | One-liner |
|---|------|-----------|
| 1 | Integer addresses | `//` not `/`; no float literals in address math (2^53 cliff) |
| 2 | `0` is truthy | `nil`-handles use `not x`; `0`-returns need `== 0` |
| 3 | One table shape | Array or map per variable; `ipairs`/`#` vs `pairs` |
| 4 | Don't reparent userdata | Wrap host handles, never `setmetatable` them |
| 5 | Values & global hooks | Callbacks take functions; lifecycle hooks are named globals |
| 6 | Capture loop-locals | Fresh local per iteration; shared upvalues bite later |
| 7 | `pcall` only throwers | Reads fail soft; wrap w2s/json so one error ≠ dead frame |
| 8 | `table.concat` in hot paths | `..` per frame is O(n²) garbage; cache formatted strings |
| 9 | Coroutines for big work | Yield slices across frames; no in-frame loops |
| 10 | `require` per feature | Return a module table; globals only for lifecycle |

---

## Source: `.claude/skills/pcx-patch-day-playbook/SKILL.md`

---
name: pcx-patch-day-playbook
description: >
  Ordered triage workflow for recovering a PCX script after a game update.
  Triggers when sigs return 0, reads return garbage after a patch, or the
  user says "broken", "updated", "patch day", "hotfix", "season drop", or
  "DLC dropped". Keeps diagnosis short and fixes targeted.
license: MIT
---

# Patch Day Playbook — Recovering After a Game Update

The ordered triage workflow for when a game update lands and your Perception.cx script stops working. This is the single most painful recurring scenario in scripting work; the cost is dominated by *not knowing what changed*, not by the re-RE itself. This playbook keeps the diagnosis short and the fix targeted.

**Trigger when:** the target game updated, sigs return 0, the script throws on first run after a patch, `ref_process().alive()` is fine but reads return garbage, or the user says any of: "broken", "updated", "patch day", "hotfix", "season drop", "DLC dropped".

**Prerequisite:** `knowledge/offset-methodology.md` for sig resolution mechanics, `tools/offset-diff.py` for batch sig diffing between binary versions, `tools/sig-uniqueness-checker.py` for re-sig validation. Also requires that you saved the previous-version binary and the working `offsets.em` *before* the update landed (see Step 1).

---

## Trigger

`.em` script suddenly throws on launch after a game update, overlay draws at (0,0), ESP renders no entities, sigs return 0, RIP-resolved addresses point outside the module, the user updates the game and runs the script and nothing works.

---

## 1. Snapshot the Broken State Before You Touch Anything

**Patch day is destructive. Save the old binary and old offsets before you do anything else. Diffing is impossible if you've already overwritten history.**

The single most common amateur mistake is "let me just update the offsets and see." Two hours later you can't remember what worked yesterday because everything is overwritten and the game's auto-updater wiped the old binary.

```
# Before any debugging — make a snapshot directory:
mkdir patch-2026-06-17

# 1. Copy the new game binary out (it's already on disk after the patch)
cp "C:/Games/MyGame/MyGame.exe" patch-2026-06-17/MyGame-new.exe

# 2. The OLD binary should already be in your previous snapshot dir.
#    If you don't have one, the lesson is: make one TODAY before the next patch.
#    The toolkit's `tools/offset-diff.py` needs both binaries to diff.

# 3. Save the last-known-good offsets:
cp scripts/offsets.em patch-2026-06-17/offsets-old.em

# 4. Save the broken script output for reference:
#    (in the IDE, copy the error trace; or run `check_script` and capture output)
```

**Why:** Without a snapshot, you're guessing what changed. With one, `offset-diff.py` and `radiff2` will tell you exactly which sigs moved, which are still valid, and which are gone. The 30 seconds of snapshotting saves the 2 hours of guesswork.

---

## 2. Run `tools/offset-diff.py` Before Editing Anything

**Most sigs survive a patch. You want to find the few that didn't — not re-do every one.**

The natural reflex is to open IDA on the new binary and start re-deriving offsets from scratch. Don't. The diff tool tells you in 30 seconds which sigs are intact, which moved (delta only — still resolvable), and which are gone (need re-sig).

```bash
# Build a JSON of named sigs once (reuse forever):
cat > sigs.json <<EOF
[
  {"name": "entity_list", "pattern": "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8", "kind": "rip", "rip_offset": 3, "insn_len": 7},
  {"name": "local_player", "pattern": "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 81", "kind": "rip", "rip_offset": 3, "insn_len": 7},
  {"name": "view_matrix",  "pattern": "48 8D 15 ?? ?? ?? ?? 48 8D 4C 24 ?? E8", "kind": "rip", "rip_offset": 3, "insn_len": 7}
]
EOF

# Diff:
python3 tools/offset-diff.py --old patch-old/MyGame.exe \
                              --new patch-new/MyGame.exe \
                              --sigs sigs.json
```

Read the output table top to bottom:

| Status | What it means | What to do |
|---|---|---|
| `UNCHANGED` | sig hits same address in both binaries | Nothing. Keep the offset. |
| `MOVED` | sig hits, but the resolved address differs (recompile shifted code) | Update the resolved address; sig itself is still good. |
| `LOST_IN_NEW` | sig hit old, doesn't hit new | Re-sig needed; instruction sequence changed. Go to Step 4. |
| `NEW_IN_NEW` | sig hit new but not old | Probably a typo in the old sig; ignore unless suspicious. |
| `MULTIPLE_HITS_OLD` / `MULTIPLE_HITS_NEW` | sig is ambiguous | Sig is too broad; tighten before trusting either result. Go to Step 4. |

**Why:** Triage before surgery. A patch typically moves 5-15% of sigs and breaks 1-3% outright. The diff tells you which 1-3% to spend the next hour on, instead of re-checking the 95% that survived.

---

## 3. Bisect the Cascade: Find the Earliest Failure, Not the Loudest

**A broken script after a patch shows ten errors. Nine of them are downstream of one bad pointer. Find the first one.**

Failure cascades trick you into chasing the wrong fix. The script log says "no entities drawn"; the actual cause is `g_entity_list = 0` because the *base address resolution* failed because the module name in the script changed (rare, but happens with engine version bumps). Fixing the entity-list sig won't help.

Bisect in dependency order:

```
1. Process attach   → ref_process("game.exe").alive() == true?
                      If false: process name changed? Anti-cheat blocking attach?
2. Base resolve     → get_module_base("game.exe") returns non-zero?
                      If 0: module renamed (e.g. CSGO → CS2 binary swap).
3. Module size      → get_module_size("game.exe") plausible (hundreds of MB)?
                      If wildly different: you're looking at the wrong binary.
4. First sig hit    → find_code_pattern returns non-zero for the FIRST sig you try?
                      If 0: the .text section may have moved (rare) or the binary
                      is encrypted/packed at runtime (e.g. Denuvo VM re-emergence).
5. RIP resolve      → resolved_addr is in [base, base+size]?
                      If outside: RIP math is wrong (Step 5).
6. Field reads      → ru64() on the resolved address returns non-zero?
                      If 0: pointer chain broken, struct layout changed.
```

Stop at the first failing step. Fix that. Re-run. Most of the cascade evaporates.

```cpp
// Tiny diagnostic harness — drop into main() temporarily:
int64 main() {
    proc_t p = ref_process("game.exe");
    if (!p.alive())                  { println("STEP 1 FAIL: process not attached"); return 0; }
    uint64 base = p.base_address();
    if (base == 0)                   { println("STEP 2 FAIL: no module base"); return 0; }
    uint64 size = p.get_module_size("game.exe");
    println(format("base={x} size={x}", base, size));

    uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0)                    { println("STEP 4 FAIL: entity_list sig stale"); return 0; }
    uint64 entity_list = resolve_rip(p, hit, 3, 7);
    if (entity_list < base || entity_list > base + size) {
        println(format("STEP 5 FAIL: rip resolve out of range: {x}", entity_list));
        return 0;
    }
    uint64 first = p.ru64(entity_list);
    println(format("first entity={x}", first));
    return 1;
}
```

**Why:** Without bisection you fix symptoms. You'll spend 30 minutes re-deriving an entity-list sig that was fine the whole time because the *real* failure was the module name. Bisection points the spotlight.

---

## 4. Re-Sig the Broken Ones with the Near-Miss Checker

**A sig that was unique yesterday may collide today, or vice versa. Don't trust your old sigs after a patch — validate.**

`tools/sig-uniqueness-checker.py` gives a verdict per sig: `UNIQUE`, `AMBIGUOUS`, `STALE`, `BRITTLE`. The `--near-misses N` flag is the killer feature on patch day — it scans for sigs whose first N bytes survive but trailing bytes drift, telling you exactly how to extend or narrow the wildcards.

```bash
# Verdict on every sig in your list:
python3 tools/sig-uniqueness-checker.py patch-new/MyGame.exe \
        --sig-file sigs.txt --near-misses 2

# Suppose this prints:
#   entity_list      UNIQUE      margin=5
#   local_player     STALE       near-miss: 48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 89
#                                           (last byte was 0x81, now 0x89 — struct offset shift)
#   view_matrix      AMBIGUOUS   3 hits — sig too broad; need 2-4 more bytes of context
```

For each broken sig:

1. **STALE with near-miss** → the instruction is still there but a register/offset byte changed. Update the sig (often a single byte) and retest.
2. **STALE with no near-miss** → the whole code path was rewritten. Go to the *xref* — find the function this sig was inside, find the new version in the patched binary by string xrefs or call patterns, derive a new sig from there.
3. **AMBIGUOUS** → tighten with 2-4 more bytes of leading or trailing context. Aim for `margin` between 2 and 6 — `margin=0` is brittle (one-byte change kills it), `margin>10` is overspecified (more likely to drift on the *next* patch).
4. **BRITTLE** (`margin=0`) → widen the sig until margin ≥ 2 even if the diff said it's fine — you got lucky this patch, you won't next time.

**Why:** Treating sigs as "either works or doesn't" misses the gradient. Most patch breakage is one-byte drift, which the near-miss check finds in seconds. Re-sigging from xrefs is the fallback when drift exceeds the threshold.

---

## 5. Re-Verify RIP-Relative Resolution After Every Sig Change

**Half of patch-day breakage is correct sig hits with wrong RIP math because the instruction length changed.**

A sig matching `48 8D 0D ?? ?? ?? ??` (7-byte `LEA rcx, [rip+disp]`) becomes `48 8B 0D ?? ?? ?? ??` (7-byte `MOV rcx, [rip+disp]`) — same length, same RIP math, fine. But a recompile can also turn a 7-byte `LEA r64, [rip+disp32]` into a 4-byte `LEA r64, [rip+disp8]` (small displacement form) — different length, different RIP math, your resolved address is now 3 bytes off. The script "works" but reads from the wrong location.

The check:

```cpp
// Always verify the resolved address lies inside the expected section.
// .text is executable code; data globals resolve to .data or .rdata.
uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
if (hit == 0) return 0;

int32 disp = p.r32(hit + 3);                  // displacement is 4 signed bytes
uint64 resolved = hit + 7 + cast<uint64>(disp); // 7 = total LEA instruction length

// Validation gate — if the resolved address points back into executable code,
// you almost certainly got the math wrong (most globals live in .data/.rdata):
if (resolved >= base && resolved < base + size) {
    // looks plausible; verify with a ru64 read and check the value shape
    uint64 first_field = p.ru64(resolved);
    println(format("resolved={x} first_field={x}", resolved, first_field));
} else {
    println(format("RIP resolve out of module: hit={x} disp={x} resolved={x}", hit, disp, resolved));
}
```

Patterns that change instruction length:

| From | To | Length delta | Common trigger |
|---|---|---|---|
| `LEA r64, [rip+disp32]` (7B) | `LEA r64, [rip+disp8]` (4B) | -3 | small-data global moved closer to code |
| `MOV r64, [rip+disp32]` (7B) | `MOV r64, mem` direct (10B) | +3 | global moved out of .rdata range |
| Standalone instruction | Instruction fused with prologue/epilogue change | varies | inliner heuristic changed in compiler |

**Why:** A wrong RIP math produces a perfectly plausible-looking address that's wrong by a small offset. Your reads return garbage that doesn't crash. You'll spend an hour blaming the struct layout for what's actually a 3-byte miscalculation in your resolver.

---

## 6. Validate End-to-End on the Live Target, Not Just "No Crash"

**Compile-clean is not the bar. Visible-correct on the live target is the bar.**

A script that doesn't crash and an overlay that draws *something* tells you almost nothing — every previous bug shipped the same way. Concrete validation:

```
End-to-end checklist after a patch fix:

[ ] Run the script on the live target (not a paused process)
[ ] Move the camera 90° — overlay tracks correctly?
[ ] Walk forward 10 meters — distance text updates plausibly?
[ ] Find a known entity (a teammate, a stationary object) — ESP box positioned over them?
[ ] Open the menu — every widget responds, no GUI freezes?
[ ] Run for 60 seconds without an exception — no late-binding errors?
[ ] Open the in-game scoreboard — entity count matches expected?
```

If you can't tick all seven, you're not done — keep bisecting.

**Why:** "It compiled" lulls you into the false sense of completion that costs you the next hour when a teammate reports the ESP is 50 pixels off. Five minutes of live verification on patch day is cheaper than any post-merge debugging.

---

## 7. Commit the Diff with a Changelog Note

**Every patch is data for the next patch. Record what moved, where it moved, and how you found it.**

A two-line note per patch turns into the most valuable file in your project after the third patch. It tells you which sigs are stable across patches (keep them), which drift every patch (rewrite from xrefs each time, don't bother updating in place), and which are version-tied (deprecate them entirely).

```
# patch-log.md
## 2026-06-17 — Game v1.42.3

### Moved
- view_matrix: +0x1C0 (recompile shift, sig still valid)
- local_player: +0x0 (no movement, listed for completeness)

### Re-sigged
- entity_list: old sig `48 8D 0D ?? ?? ?? ?? E8` matched at 3 places (ambiguous)
  new sig:     `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8` (margin=5)

### Lost — deprecated
- ammo_count: function inlined into shoot routine; not recoverable as a global,
              folded into per-weapon offset table

### Notes
- ETW Threat Intel callbacks (per anti-cheat-architecture.md) saw activity for
  the first time on this build — driver may have updated. Flag for review.
```

**Why:** Future-you needs this. The third patch when a sig regresses is when you'll discover that it's been brittle since v1.40 and you should rewrite it from xrefs once and for all instead of patching it again.

---

## Decision: When to Patch vs When to Re-RE from Scratch

Not every patch is a patch — sometimes the game shipped a real engine change and the old offsets are gone, not moved. Heuristics for when the playbook above doesn't apply and you need to start from `knowledge/offset-methodology.md` again:

| Signal | Likely cause | Action |
|---|---|---|
| Module name changed | Engine swap or major rebrand (CSGO → CS2) | Full re-RE; old offsets are reference-only |
| Module size changed >30% | Major engine update or large content drop with code refactor | Bisect aggressively; expect 30-50% sig loss |
| Most sigs `STALE` with no near-miss | Compiler upgrade (Clang version, LTO change) | Re-derive from xrefs; sigs based on RIP-relative globals usually survive better than register-allocation-sensitive ones |
| `IL2CPP` rebuild signal (Unity titles) | metadata.dat changed → entire struct layout rotated | Re-dump with IL2CPPDumper; use `tools/dumper-to-enma.py` to regenerate `offsets.em` |
| Schema system reset (Source 2 titles) | Schema registration order changed at runtime | Offsets are runtime-resolved; sigs for the schema getter are usually stable; revalidate the resolver, not the offsets |
| New anti-cheat driver loaded | AC vendor pushed an update | See `skill://anti-cheat-re` — driver behavior may have changed, not just code layout |

**The general rule:** if Steps 2-5 are fixing 70%+ of sigs with one-byte tweaks, you're in patch territory — keep going. If they're failing to find any near-misses for the broken sigs, you're in re-RE territory — close the playbook, open IDA, start over from the methodology.

---

## Summary

| # | Step | One-liner |
|---|---|---|
| 1 | Snapshot first | Save old binary, old offsets, error log before touching anything |
| 2 | Diff before editing | `offset-diff.py` triages which sigs survived, moved, lost |
| 3 | Bisect the cascade | Find the *first* failure, not the loudest |
| 4 | Re-sig with near-miss check | One-byte drift is the common case — find it in seconds |
| 5 | Re-verify RIP math | Instruction-length changes silently break resolved addresses |
| 6 | Live validation | Seven concrete in-game checks before declaring done |
| 7 | Patch log entry | Two lines per patch; the third patch will thank you |

**Decision:** if Steps 2-5 aren't recovering 70%+ of broken sigs, stop patching and re-RE from scratch via `knowledge/offset-methodology.md`.

**Cross-references:** `skill://pcx-re-discipline` (the rules of RE work), `knowledge/offset-methodology.md` (sig mechanics), `tools/offset-diff.py`, `tools/sig-uniqueness-checker.py`, `tools/dumper-to-enma.py` (for engines with structured dumpers).

---

## Source: `.claude/skills/pcx-perf-budget/SKILL.md`

---
name: pcx-perf-budget
description: >
  Turns the update/render separation rule into enforceable numeric budgets
  using mono_us() measurements. Covers per-frame targets at common refresh
  rates, per-call cost rules of thumb, a drop-in profiler recipe, and
  read-coalescing patterns. Always active when writing or reviewing
  performance-sensitive render or update routines.
license: MIT
---

# Performance Budget — Frame-Time Targets for PCX Scripts

Turns `game-cheat-guidelines` rule #4 (separate update from render) into enforceable numeric budgets, so the question "is my script too slow?" gets answered with `mono_us()` measurements instead of vibes. Covers per-frame targets at common refresh rates, per-call cost rules of thumb, the drop-in `profile_begin/end` recipe, and the read-coalescing patterns that produce the biggest wins.

**Always active when writing or reviewing performance-sensitive paths** (render routines, update routines, entity loops, pattern scans inside hot paths).

**Prerequisite:** `docs/enma/addon-time.md` for the timing primitives (`mono_us`, `now_us`, `sleep_ms`); `skill://game-cheat-guidelines` rules #4 (update/render separation) and #7 (per-frame construction).

---

## Trigger

Render stutter, FPS drop on overlay enable, "my script feels slow," profiling questions, write-up of per-feature performance, decisions about whether to cache or recompute, multi-routine scripts where update + render share a frame budget.

---

## 1. Know the Frame Budget at Your Target Refresh Rate

**The frame budget is the entire wall-clock window between two consecutive render calls. Everything — your update, your render, the game's own rendering, the GPU present — must fit inside it.**

Total frame budgets:

| Refresh | Budget per frame | PCX render budget (target) | PCX update budget (target) |
|---|---|---|---|
| 60 Hz | 16.67 ms | ≤ 2.0 ms | ≤ 4.0 ms |
| 120 Hz | 8.33 ms | ≤ 1.5 ms | ≤ 3.0 ms |
| 144 Hz | 6.94 ms | ≤ 1.5 ms | ≤ 2.5 ms |
| 240 Hz | 4.17 ms | ≤ 1.0 ms | ≤ 1.5 ms |
| 360 Hz | 2.78 ms | ≤ 0.7 ms | ≤ 1.0 ms |

The render budget is small because the game's own renderer + the GPU present + your overlay all share the frame. If your render path takes 5 ms at 144 Hz, you've eaten 72% of the frame by yourself, leaving 1.94 ms for the game's render — which causes the game to drop frames even though it would have hit 144 Hz without your overlay.

The update budget is more generous because, if you separate update from render properly (rule #4), update runs less frequently and on its own clock — it competes with the game less directly. But "less directly" is not "for free": a 10 ms update routine running at 60 Hz costs the same total CPU as a 2 ms render routine running at 144 Hz × 2.

**Heuristic:** measure once, then forget. If your script runs at the target FPS with no stutter on the lowest-spec machine you ship to, the budgets are met. If it stutters, instrument first (Step 3) before optimizing.

**Why:** Hard numeric targets prevent the "feels slow, must be fast" loop where you over-cache things that don't matter and miss the one routine that does. The render budget being tight is non-negotiable; the update budget is the negotiable lever — push work into update, off the render path, and most stutter disappears.

---

## 2. Per-Call Cost Rules of Thumb

**Order-of-magnitude costs for the operations you'll write most. Measure on your target; these are guides for *which order* of magnitude to expect, not contracts.**

| Operation | Cold (page-fault) | Warm (cached) | Notes |
|---|---|---|---|
| `proc.ru8/16/32/64` | 10-100 µs | 1-5 µs | Cold = first read of a page; warm = same page already touched this frame |
| `proc.rf32/rf64` | 10-100 µs | 1-5 µs | Same as integer reads — cost is the cross-process read, not the type |
| `proc.read_vec3_fl32` | 30-300 µs | 5-15 µs | One read of 12 bytes vs three separate reads |
| `proc.read_memory(N)` bulk | 30-500 µs depending on N | 10-100 µs | A single struct-dump is almost always cheaper than N scalar reads |
| `proc.find_code_pattern` | 5-200 ms first scan | N/A | Cold path only — never in update/render. Run in `main()` and cache. |
| `is_key_pressed` / `is_key_down` | < 1 µs | < 1 µs | Cheap; fine in hot paths |
| `draw_rect` / `draw_line` / `draw_circle` | 1-10 µs | 1-10 µs | Cost dominated by GPU command submission, not CPU |
| `draw_text` | 5-50 µs | 5-50 µs | Per-glyph atlas lookup + GPU submission; longer strings cost more |
| `world_to_screen` (pure math) | 1-5 µs | 1-5 µs | When matrix is cached; if you re-read the matrix per call, add a `read_memory` cost |
| GUI widget query (`section_*` reads) | < 1 µs | < 1 µs | Reading widget state is a local memory access |
| `now_us` / `mono_us` | < 0.5 µs | < 0.5 µs | Cheap; safe to call multiple times per frame for profiling |

**The implication:** a render path that does 50 entity boxes with one `read_vec3_fl32` per entity inside the render routine costs `50 × 5-15 µs = 0.25-0.75 ms` *if* the entity pages are warm. Cold-cache, it could be `50 × 30-300 µs = 1.5-15 ms` — already over the render budget at 144 Hz on the high end. Solution: move the reads to update (cache the cold-page cost there), draw from the cache.

**Why:** The single most important number to internalize is that cross-process memory reads are *very expensive* relative to draws and math. A NOP loop running 1000 iterations costs nothing; 1000 `ru32` calls can be 30 ms. Every performance problem in a PCX script is either too many reads or reads on the wrong thread.

---

## 3. The `profile_begin/end` Drop-In Recipe

**A minimal inline profiler with no new modules, no allocation, no rebuilds. Drop into any script, get per-routine breakdowns in console or on screen.**

The pattern uses `mono_us()` (monotonic; safe for deltas) and a small fixed-size accumulator. No `map` needed — name your buckets explicitly.

```cpp
import "vec";
import "color";

// ── Profile state — tiny fixed accumulator ──
const int32 NUM_BUCKETS = 8;
string  g_bucket_name[8];        // initialized once
int64   g_bucket_total_us[8];    // accumulated microseconds
int64   g_bucket_count[8];       // number of samples
int64   g_bucket_max_us[8];      // worst single sample
int64   g_profile_last_dump = 0;
int64   g_profile_dump_interval_us = 1000000;  // dump every second

// Push/pop pattern — name maps to bucket index 0..NUM_BUCKETS-1
int64 g_bucket_start_us[8];

void profile_begin(int32 bucket) {
    g_bucket_start_us[bucket] = mono_us();
}

void profile_end(int32 bucket) {
    int64 dur = mono_us() - g_bucket_start_us[bucket];
    g_bucket_total_us[bucket] += dur;
    g_bucket_count[bucket]    += 1;
    if (dur > g_bucket_max_us[bucket]) {
        g_bucket_max_us[bucket] = dur;
    }
}

// Call once per frame from render — prints once per second
void profile_dump_if_due() {
    int64 now = mono_us();
    if (now - g_profile_last_dump < g_profile_dump_interval_us) return;
    g_profile_last_dump = now;

    println("── PROFILE ──");
    for (int32 i = 0; i < NUM_BUCKETS; i++) {
        if (g_bucket_count[i] == 0) continue;
        int64 avg = g_bucket_total_us[i] / g_bucket_count[i];
        println(format("  {s}: avg {d}us  max {d}us  ({d} samples)",
                       g_bucket_name[i], avg, g_bucket_max_us[i], g_bucket_count[i]));
        // Reset for next window
        g_bucket_total_us[i] = 0;
        g_bucket_count[i]    = 0;
        g_bucket_max_us[i]   = 0;
    }
}

// Bucket assignments (give them stable indices)
const int32 BKT_UPDATE_ENTITIES = 0;
const int32 BKT_RESOLVE_OFFSETS = 1;
const int32 BKT_RENDER_ESP      = 2;
const int32 BKT_RENDER_HUD      = 3;

int64 main() {
    g_bucket_name[BKT_UPDATE_ENTITIES] = "update_entities";
    g_bucket_name[BKT_RESOLVE_OFFSETS] = "resolve_offsets";
    g_bucket_name[BKT_RENDER_ESP]      = "render_esp";
    g_bucket_name[BKT_RENDER_HUD]      = "render_hud";
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

void on_update(int64 data) {
    profile_begin(BKT_UPDATE_ENTITIES);
    // ... entity read loop ...
    profile_end(BKT_UPDATE_ENTITIES);
}

void on_render(int64 data) {
    profile_begin(BKT_RENDER_ESP);
    // ... ESP draws ...
    profile_end(BKT_RENDER_ESP);

    profile_begin(BKT_RENDER_HUD);
    // ... HUD draws ...
    profile_end(BKT_RENDER_HUD);

    profile_dump_if_due();
}
```

Sample output after one second:

```
── PROFILE ──
  update_entities: avg 1840us  max 4200us  (12 samples)
  render_esp:      avg 320us   max 510us   (144 samples)
  render_hud:      avg 45us    max 80us    (144 samples)
```

Interpretation:
- `update_entities` averages 1.84 ms — fine, well under the 2.5 ms update budget at 144 Hz
- But `max 4200us` is the spike to watch — a single 4.2 ms update *will* be visible if it lands on a render frame; this is the cold-page cost
- `render_esp` at 0.32 ms is healthy; `render_hud` at 45 µs is excellent

**Why:** Real numbers replace arguments. Without a profiler, every conversation about "is this fast enough" devolves into hand-wave. With one, you point at the bucket and either fix it or move on. The `max` column is more useful than the average — averages hide spikes that cause user-visible stutter.

---

## 4. Read Coalescing — The Single Biggest Win

**Cross-process memory reads dominate cost. Bundling 8 scalar reads from the same struct into one `read_memory` call is typically 5-10× faster.**

The entity loop is the canonical offender. Eight reads per entity, fifty entities = 400 cross-process reads per update. With page-warm reads at 3 µs each, that's 1.2 ms; cold, it's tens of ms.

```cpp
// SLOW — 8 reads per entity, each a separate kernel transition
void on_update(int64 data) {
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;
        g_cache[i].health    = g_proc.r32(ent + OFFSET_HEALTH);
        g_cache[i].team      = g_proc.r32(ent + OFFSET_TEAM);
        g_cache[i].position  = g_proc.read_vec3_fl32(ent + OFFSET_POSITION);
        g_cache[i].velocity  = g_proc.read_vec3_fl32(ent + OFFSET_VELOCITY);
        g_cache[i].view_yaw  = g_proc.rf32(ent + OFFSET_VIEW_YAW);
        g_cache[i].view_pit  = g_proc.rf32(ent + OFFSET_VIEW_PITCH);
    }
}

// FAST — one read per entity into a fixed buffer, parse in-script
struct entity_struct_layout {
    // Layout reflects the bytes at the entity base — adjust for your target.
    // Use [[packed]] if you depend on no padding.
} [[packed]];

void on_update(int64 data) {
    array<uint8> buf;
    buf.resize(0x200);                               // sized to span all fields you read

    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;

        // ONE read covering the whole entity record — single kernel transition
        if (!g_proc.read_memory(ent, buf, 0x200)) continue;

        // Parse from the local buffer — pure memory math, ~10x cheaper
        g_cache[i].health   = buf_read_i32(buf, OFFSET_HEALTH);
        g_cache[i].team     = buf_read_i32(buf, OFFSET_TEAM);
        g_cache[i].position = buf_read_vec3(buf, OFFSET_POSITION);
        g_cache[i].velocity = buf_read_vec3(buf, OFFSET_VELOCITY);
        g_cache[i].view_yaw = buf_read_f32(buf, OFFSET_VIEW_YAW);
        g_cache[i].view_pit = buf_read_f32(buf, OFFSET_VIEW_PITCH);
    }
}
```

Order of optimization (high impact to low):

1. **Coalesce per-entity scalar reads into struct-dumps.** Biggest single win for entity loops.
2. **Cache the view matrix once per update, share across entities.** Currently common to re-read per W2S call.
3. **Skip cold entities.** Read just the alive/team field first; if dead or friendly, skip the rest of the read.
4. **Bound entity counts.** A `MAX_ENTITIES = 64` cap on a list that's structurally bounded at 128 saves half the reads if many slots are empty.

**Why:** Cross-process reads are the dominant cost in any non-trivial script. A read-coalescing pass typically halves total CPU time of an entity-heavy script. The cost of structuring the read is a one-time `resize` and a handful of byte-offset getters — trivial relative to the win.

---

## 5. Cache What's Expensive to Get, Recompute What's Cheap

**Pattern scans, module bases, view matrix (across many entities) — cache. Colors, vec2s, format strings, font handles — recompute. Caching cheap things adds state without measurable savings.**

| Cache | Recompute |
|---|---|
| Pattern scan results (in `main()`, never again) | `color(r,g,b,a)` (4 bytes, stack-allocated, zero cost) |
| Module base / module size (until process re-attach) | `vec2(x, y)` (8 bytes, stack-allocated) |
| Resolved RIP addresses (until reload) | `get_font20()` (returns a cached handle internally) |
| View matrix once per update (shared across all W2S in this frame) | `format("{d}", n)` for short HUD text |
| Entity data in `g_cache` (the whole point of update/render separation) | World-to-screen result (it's just float math; do it where you need it) |
| Local player position once per frame (read in update, used by N features) | `is_key_down(VK_F)` (a cheap intrinsic; safe per-frame) |

Anti-cache (don't):

```cpp
// WRONG — caching a color "for performance"
color g_white;  // global state for zero gain
int64 main() {
    g_white = color(255, 255, 255, 255);
    return 1;
}

// RIGHT — construct fresh, no globals
void on_render(int64 data) {
    draw_text("HUD", vec2(10.0, 10.0), color(255, 255, 255, 255),
              get_font20(), 1, color(0, 0, 0, 180), 1.0);
}
```

Pro-cache:

```cpp
// View matrix — read once per update, reuse across N entities per render
float64 g_matrix[16];

void on_update(int64 data) {
    // 16 floats = 64 bytes in one read
    g_proc.read_memory(g_view_matrix_addr, g_matrix_buf, 64);
    // ... parse into g_matrix[16] ...
}

void on_render(int64 data) {
    for (int32 i = 0; i < g_entity_count; i++) {
        vec2 screen;
        if (world_to_screen(g_cache[i].position, g_matrix, screen)) {
            draw_circle(screen, 4.0, color(255, 0, 0, 255), 1.0, true);
        }
    }
}
```

**Why:** Caching cheap things makes the script harder to reason about (mutable globals, lifetime questions) for zero performance benefit. Caching expensive things (or things on cold paths) is the explicit purpose of rule #4 (update/render separation) — the whole point of "do it in update" is that the result lives until next update. Use that mechanism for what it's for; don't extend it to things that don't need it.

---

## 6. When to Break the Rule

**The budgets are steady-state targets. Bursts are fine. Don't split a one-frame initialization across ten frames to "meet budget" — the user-visible cost is the same and the code is worse.**

Legitimate bursts:

- **Initial process attach and sig resolution** in `main()` — can take 10-50 ms total, runs once, before the user starts using the overlay. Don't split.
- **First-frame entity cache fill** after a level load — a one-frame 5 ms spike that lets every subsequent frame run at 0.5 ms. Worth it.
- **Patch-day re-resolution** if you detect base address changed mid-session — let it stutter once.
- **Config save** on `on_unload` — file I/O takes ms; doesn't matter, the script is exiting.

Illegitimate bursts (these you DO need to fix):

- A pattern scan in a *callback* that fires periodically (should be in `main`)
- A `find_string_refs` or `struct_dump` call on the render thread (cold paths only)
- Allocating a 4 KB array inside `on_render` every frame (move to global, reuse the buffer)
- Calling `is_valid_address` on every pointer in a chain on every frame (validate at update time, cache the bool)

The test: if the user could feel the cost as a one-frame stutter, is it acceptable? A 50 ms stutter at script load is invisible (the overlay just appears 50 ms later). A 50 ms stutter mid-game is felt as a hitch.

**Why:** Performance work that makes the code uglier without changing the user-visible behavior is bad performance work. The framing of "everything must fit in 6.94 ms" applies to steady-state operation; setup, teardown, and event-driven one-shots get a pass. Save the optimization energy for the actual hot path.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | Know your budget | 16/8/7/4 ms at 60/120/144/240 Hz; render ≤ 1.5-2 ms, update ≤ 2.5-4 ms |
| 2 | Internalize per-call costs | Cross-process reads = expensive; draws and math = cheap |
| 3 | Profile with `mono_us` | Drop-in `profile_begin/end` with fixed buckets — measure before optimizing |
| 4 | Coalesce reads | One `read_memory` struct-dump replaces 8 scalar reads; biggest single win |
| 5 | Cache expensive, recompute cheap | Sigs, bases, matrix — yes; colors, vecs, fonts — no |
| 6 | Bursts are fine | Don't split one-shot setup across frames to "meet budget" |

**Cross-references:** `skill://game-cheat-guidelines` rules #4 and #7; `knowledge/common-patterns.md` for read-coalesced entity loops; `docs/enma/addon-time.md` for `mono_us` / `now_us`; `skill://pcx-patch-day-playbook` Step 5 (post-patch re-resolution that legitimately spends a frame budget).

---

## Source: `.claude/skills/pcx-re-discipline/SKILL.md`

---
name: pcx-re-discipline
description: >
  Workflow discipline for reverse engineering and offset maintenance: locating
  structs, generating signatures, resolving RIP-relative addresses, and
  keeping an offset table alive across patches. Derived from Karpathy
  principles, rewritten for RE where the failure mode is a confident wrong
  answer. Always active when doing RE or offset work.
license: MIT
---

# PCX Reverse-Engineering Discipline — Finding Offsets Without Fooling Yourself

Workflow discipline for reverse engineering and offset maintenance: locating structs, generating signatures, resolving RIP-relative addresses, and keeping an offset table alive across game patches. Derived from the four Karpathy principles — *think before coding, simplicity first, surgical changes, goal-driven execution* — rewritten for RE work, where the failure mode isn't a crash but a confident wrong answer.

**Always active when doing RE or offset work.** This complements `game-cheat-guidelines` #1 (ground every offset) and #12 (verify with the binary), and the `knowledge/offset-methodology.md` mechanics. Those cover *how* to scan; this covers *how to work* so you don't ship a guess.

## Trigger
Disassembling a function, mapping a struct layout, generating a byte signature, resolving an offset, updating an offset table after a patch, or cross-referencing an SDK against a live binary. Tools: IDA, Ghidra, radare2, and the Perception RE tools (`struct_dump`, `find_xrefs`, `analyze_vtable`, `read_rtti`, `generate_signature`, `find_code_pattern`, `build_call_graph`).

---

## 1. Hypothesize Before You Disassemble

**Form a claim about what a function or field *is*, then look for evidence — don't reverse aimlessly and rationalize whatever you find.**

A float at `entity+0x43E0` that reads `100.0` might be health. It might be armor, a timer, or a shield that happens to start at 100. Guessing wrong here is silent and expensive.

- **State the hypothesis first.** "This sig should land on the LEA that loads `CEntityList`. Expected: `48 8D 0D` followed by a RIP displacement."
- **Use the cheapest evidence before manual disasm.** RTTI names (`read_rtti`) and string xrefs (`find_xrefs`) identify a class faster than reading instructions. Reach for them first.
- **Mark unverified findings `UNVERIFIED` and cite the source** — r5sdk header path, RTTI string, IDA xref address. An offset without a citation is a rumor.
- **One value is not proof.** Confirm a field by watching it change as you'd expect in-game, or by matching the SDK layout — not by a single plausible read.

```
Before: "0x43E0 is health, it reads 100."

After:  "Hypothesis: 0x43E0 = m_iHealth (int32).
         Evidence: r5sdk/player.h offset matches; read_rtti confirms class CPlayer;
         value drops to 73 after taking damage in-game. CONFIRMED."
```

**Why:** RE has no compiler to catch you. The only thing standing between a wrong offset and an hour of debugging ESP-at-(0,0) is the evidence you demanded before believing your own hypothesis.

---

## 2. The Simplest Signature That's Unique

**The shortest byte pattern that hits exactly one location. Not longer, not vaguer.**

A sig is a tradeoff: too specific and it breaks on the next compiler tweak; too loose and it matches three places and resolves to garbage.

- **Wildcard only the relocatable bytes** — RIP-relative displacements, absolute immediates, jump targets. Keep the opcodes. `48 8D 0D ?? ?? ?? ??` wildcards the displacement, keeps the `LEA RCX` opcode.
- **Stop at the first length that's unique.** Verify it with `find_code_pattern` over the module — one hit means stop. Don't bolt on ten more bytes "to be safe"; that's the brittleness you'll pay for next patch.
- **Don't reverse a whole class to read one field.** `struct_dump` the instance and xref the accessor function. Map the entire vtable only when you actually need the entire vtable.
- **Don't build a full offset dumper for three offsets.** Three sigs in `offsets.em` is the right size for three offsets.

```cpp
// WRONG — 24 bytes, spans an immediate that changes per build → dead next patch
"48 8D 0D 30 AF 25 02 E8 1A 4C 00 00 48 8B D8 48 85 DB 74 12 8B 05 ..."

// RIGHT — shortest unique hit, displacement wildcarded
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";
// verify: find_code_pattern(base, size, SIG_ENTITY_LIST) returns exactly one hit
```

**Why:** Every non-wildcarded byte is a bet that the compiler emits it identically next build. The minimal unique sig makes the fewest bets, so it survives the most patches — which is the entire point of using sigs over hardcodes.

---

## 3. After a Patch, Re-verify Only What Broke

**Run the whole table, fix the misses, leave the hits alone. Don't regenerate offsets that still work.**

The temptation after a game update is to rebuild the offset table from scratch. That's churn: it risks the offsets that were fine and buries the one real change in noise.

- **Run every sig.** `find_code_pattern` returning 0 is a miss — that sig needs a new pattern. A hit that resolves to valid data is fine; leave it untouched.
- **Verify the survivors didn't silently shift.** A sig can still hit while the *struct field* behind it moved. Spot-check resolved pointers with `struct_dump`.
- **Touch only the broken entries.** Re-sig the misses, update their resolved addresses, bump the version stamp, and log exactly what changed in a changelog. The diff should be the patch's actual damage, nothing more.

```
Post-patch checklist:
[ ] Ran all N sigs                          → 3 misses, N-3 hits
[ ] Hits resolve to valid data              → struct_dump spot-check OK
[ ] Re-sigged ONLY the 3 misses             → no churn on working entries
[ ] Bumped version stamp + changelog        → "Season 22: re-sigged entity_list,
                                               view_matrix, local_player"
```

**Why:** A surgical post-patch diff is reviewable and reversible — you can see precisely what the update moved. A full-table rewrite hides the signal, re-introduces transcription bugs into offsets that were already correct, and turns a 20-minute fix into a re-audit.

---

## 4. Trust Live Memory, Loop Until It Agrees

**Success is a sig that resolves to an address whose *live contents* match the expected layout. Loop until the three sources agree, and when they don't, the running process wins.**

The IDB, the SDK headers, and live memory are three views that drift apart. The IDB is a snapshot; the SDK may be an old season; only live memory is the truth right now.

- **Define done concretely:** "sig hits once, RIP resolves to an address, the bytes there `struct_dump` to the layout I expect."
- **Loop:** sig hit → resolve RIP-relative (4-byte signed displacement added to the *end* of the instruction) → read at the target → `struct_dump` / `print` → does it match the hypothesis? → if not, fix the sig or the resolution math and repeat.
- **Resolve RIP correctly or everything downstream is wrong:** `target = hit + instr_len + read_i32(hit + disp_offset)`. Off-by-one on the instruction length points you at the wrong global.
- **When the SDK says one offset and the live read says another, trust the live read** and update your notes. The header was written for a build that no longer exists.

```cpp
// The verify loop, made explicit
uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
if (hit == 0) { println("MISS — sig is stale, re-RE the load instruction"); return; }
int32 disp   = p.r32(hit + 3);          // displacement at LEA+3
uint64 target = hit + 7 + cast<uint64>(disp);  // end of 7-byte LEA + signed disp
uint64 list  = p.ru64(target);
println(format("entity_list global @ 0x{x} -> 0x{x}", target, list));
// struct_dump `list` and confirm it looks like a CEntityList before trusting it
```

**Why:** A sig that compiles into your script proves nothing. A sig that resolves to live memory matching your expected struct is the only evidence that the offset is real — and demanding that evidence is what separates a maintained offset table from a pile of hopeful constants.

---

## Summary

| # | Principle (Karpathy) | In RE terms |
|---|----------------------|-------------|
| 1 | Think Before Coding | Hypothesize + cite evidence before believing a field's meaning |
| 2 | Simplicity First | Shortest unique sig; wildcard only relocatable bytes |
| 3 | Surgical Changes | Post-patch: fix only the misses, never churn working offsets |
| 4 | Goal-Driven Execution | Done = sig resolves to live memory matching the expected layout |

---

## Source: `.claude/skills/pcx-streamproof/SKILL.md`

---
name: pcx-streamproof
description: >
  Explains when PCX overlay output appears in screen captures per capture
  method (OBS, Discord, ShadowPlay, NVIDIA Highlights, capture cards,
  PrintScreen). Triggers on streaming, OBS, Discord screenshare, "my overlay
  shows on stream," "my friend can see my menu," and related capture or
  recording questions.
license: MIT
---

# Streamproof Overlay — Capture Compatibility for PCX Renders

When PCX overlay output shows up in screen captures and when it doesn't, mapped per capture method (OBS, Discord, GeForce ShadowPlay, NVIDIA Highlights, PrintScreen, Steam screenshot, capture cards). The user-recurring questions "why does my friend on Discord see my menu" and "I want my overlay invisible on stream" both reduce to which capture path each viewer is using and which PCX render surface they're seeing — this skill makes that mapping explicit.

**Trigger when:** the user mentions OBS, Twitch, streaming, capture card, Discord screenshare, GeForce Experience, ShadowPlay, NVIDIA Highlights, Steam screenshot, PrintScreen, NVENC, Elgato, replay buffer, instant replay, "my overlay shows on stream," "my friend can see my menu," or related capture / recording questions.

**Prerequisite:** `docs/perception/render-api.md` for the actual render surface taxonomy on your PCX build; `knowledge/anti-cheat-architecture.md` for context on screenshot-based scans by anti-cheats.

---

## Trigger

Streaming, recording, screen-share, capture-card, screenshot, replay-buffer, NVIDIA/AMD overlay coexistence questions; reports of friends seeing things on Discord, viewers seeing menus on Twitch, an overlay artifact appearing in a saved screenshot.

---

## 1. Capture Taxonomy — How Each Capture Method Sees the Screen

**The single fact that explains every "why can my friend see this" question: different capture methods see different layers of the rendering stack. They are not interchangeable.**

| Capture Method | What It Captures | Common Software |
|---|---|---|
| **Game Capture / Window Capture (hook)** | Hooks the game process's D3D/Vulkan/OGL swap chain; captures the frame *before* it composites with other overlays | OBS "Game Capture", Streamlabs, Twitch Studio |
| **Display Capture (DXGI Desktop Duplication)** | Captures the final composited desktop image as DWM composes it | OBS "Display Capture", Discord screenshare, Windows screenshot, Snipping Tool |
| **GPU-driver capture** | Driver-level hook of the game's render output, before window composition | NVIDIA ShadowPlay, NVIDIA Highlights, AMD ReLive |
| **Print-window GDI** | Bitblts a specific window's GDI surface | Legacy screen-capture tools, `PrintScreen` on some configurations |
| **Capture card (HDMI)** | Captures the GPU output signal at the cable; sees exactly what the monitor sees | Elgato, AverMedia, dedicated streaming PC setups |
| **Mirror driver** | Inserts a virtual display device that mirrors what would have rendered | Some VPN/remote-access tools, older streaming setups |

Three categories matter:

1. **Process-internal capture** (Game Capture, ShadowPlay) — sees only what the game process renders into its own swap chain
2. **Desktop-composited capture** (Display Capture, Discord screenshare, screenshot tools) — sees the final image after DWM merges everything
3. **Signal-level capture** (HDMI capture card) — sees the final pixels on the wire to the monitor

A PCX overlay can be visible to any subset of these depending on how it's rendered. The default question to ask any user with a capture problem is: "which of these three categories is the viewer using?"

**Why:** Most "but my friend can see it" reports are actually "my friend uses Discord screenshare (desktop-composited), and you tested with OBS Game Capture (process-internal) — different layers, different results." Pin the capture method before debugging anything else.

---

## 2. PCX Render Surface Behavior

**PCX provides multiple ways to put pixels on screen. Each one lands in a different layer of the rendering stack, and that determines which capture methods see it. The exact surface names and modes are in `docs/perception/render-api.md` — read it for your PCX version.**

The general mapping (verify against your build's docs):

| PCX Render Path | Lands In | Visible to Game Capture? | Visible to Display Capture? | Visible to ShadowPlay? | Visible to HDMI Capture? |
|---|---|---|---|---|---|
| **Direct game-process render** (overlay drawn into the game's own swap chain via PCX's swap-chain hook) | The game's swap chain, before window composition | Yes | Yes (via the composited desktop) | Yes | Yes |
| **External overlay window** (PCX renders to a separate top-most layered window) | A separate window, composited by DWM into the desktop | No (Game Capture only sees the game window) | Yes | No (driver capture is per-game) | Yes |
| **DWM composition layer hook** (where supported) | Inserted into the DWM composition pipeline | Varies by platform; treat as Display Capture in practice | Yes | No | Yes |
| **GPU compute shader visualization** (custom shader output) | Depends on how PCX exposes the shader output — typically composited similar to one of the above | Same as the surface it composites into | Same | Same | Same |

The pattern: anything that ends up *inside the game process's render output* is visible to everything. Anything that's a *separate window or DWM layer* is invisible to in-game-process captures (Game Capture, ShadowPlay) but visible to anything that captures the composited desktop.

**Why:** Capture-card and desktop-capture methods see "what the user sees" — so anything visible to the user is visible to them, period. The only capture paths that distinguish overlays from the game's own rendering are the process-internal ones, and they distinguish based on which process's swap chain the overlay landed in.

---

## 3. The Pre-Stream Checklist

**Before going live, validate against the capture method you actually use. A test against OBS Game Capture tells you nothing about what shows up on Discord screenshare.**

```
For each capture method the user cares about (typically Twitch + Discord):

[ ] Open the capture in preview (OBS preview pane, Discord call with self-view, etc.)
[ ] Walk through every PCX render path you have enabled:
    - Main overlay
    - Menu / GUI sections
    - Notification popups
    - Any custom shader output
[ ] For each: is it visible in the preview?
[ ] If visible-but-wanted-hidden: switch to a render path that doesn't land in this capture's layer
[ ] If wanted-visible-but-hidden: switch to one that does land in this capture's layer
[ ] Confirm by recording a 10-second clip and rewatching; previews are sometimes lossy
```

The matrix to fill before going live:

| Capture target | What I want visible | What I want hidden | Render path to use |
|---|---|---|---|
| Twitch stream (OBS Game Capture) | Game | PCX overlay | External overlay window |
| Twitch stream (OBS Display Capture) | Game + overlay | Nothing | Either render path; both visible |
| Discord screenshare | Same as Display Capture | Hard to hide; see Step 4 | External window won't help here |
| ShadowPlay highlight clip | Game | PCX overlay | External overlay window |
| Steam screenshot | Game | PCX overlay | External overlay window |
| HDMI capture card | Both | Nothing hideable | All renders land here |

**Why:** Going live without checking is how the "my menu just showed up on stream during a clutch" story happens. Five minutes of preview-and-record is cheaper than a clip going around.

---

## 4. Capture Cards and HDMI Are Pixel-Accurate — No Software Solution

**An HDMI capture card sees the monitor signal. If the user sees it, the capture card sees it. There is no software-rendered overlay that avoids being captured by a downstream signal-level capture.**

The only options when a capture card is in play:

- **Dual-monitor setup with the overlay on the non-captured display** (e.g. menus on monitor 2 which is not piped to the capture card). Requires PCX to render to a specific display, which depends on the render-surface options in your build.
- **Use the in-game render path and accept it's visible** — then make the overlay aesthetically discreet (low alpha, small footprint, off-screen during gameplay) so it's not eye-catching even when visible.
- **Use a streaming PC topology** where the gaming PC's HDMI goes to a capture card on a *second* PC, and the second PC composites the streamer's webcam/scenes; the overlay still shows on the captured feed but you have more control over what's composited around it.

There is no clever DWM trick that defeats the HDMI signal — pixels are pixels by the time they reach the cable.

**Why:** Newcomers ask "how do I make my overlay invisible to my capture card" expecting a software answer. There isn't one; pin this fact early and shift the conversation to the topology / aesthetic options that actually work.

---

## 5. Screenshot-Based Detection by Anti-Cheats

**Some anti-cheats capture screenshots of the game window or full desktop and analyze them for known overlay artifacts. This is a separate concern from "streamproof for viewers" but uses the same capture-path taxonomy.**

The standard mechanisms (see `knowledge/anti-cheat-architecture.md` for per-AC details):

- **In-process screenshot** — AC code running inside the game process grabs the game's swap-chain backbuffer. Sees anything that landed in the game's render output. External overlay windows do not appear in this capture.
- **Desktop screenshot** — AC service captures the full desktop via DXGI. Sees everything the user sees. External overlay windows DO appear here.
- **Game-window PrintWindow** — AC calls `PrintWindow(hwnd, ...)` on the game window. Sees only what's GDI-rendered into that window (often misses D3D-composited overlays entirely).

Historical examples (from publicly documented behavior of the named systems — see `knowledge/anti-cheat-architecture.md`):

- BattlEye's `BEClient.dll` has been observed taking screenshots via in-process capture and uploading them for analysis.
- EAC includes screenshot capability invoked by backend rule pushes.
- Vanguard does in-process capture as part of its memory-integrity scanning.

The general principle: a render path that's invisible to a given capture *for viewers* is also invisible to a screenshot taken via the same mechanism. An overlay invisible to OBS Game Capture is also invisible to in-process AC screenshots. This is coincidental alignment with anti-evasion goals — the underlying mechanism is the same render-pipeline layering.

**Note:** the appropriate response to AC screenshot detection is platform terms-of-service compliance and `skill://anti-cheat-re` for understanding the detection surface. This skill maps the *what's visible to what* fact; it does not advise on evasion of legitimate platform enforcement.

**Why:** Users conflate "streamproof" with "AC-invisible" — they aren't the same goal, but they share a technical foundation (which render surface is in which capture layer). Splitting the goals clarifies which question you're answering and prevents over-claiming "this is invisible to AC" when you've only verified one capture path.

---

## 6. Differential Diagnosis: "Friend on Discord Can See My Menu"

**The most-reported confusion. The user tests their overlay against OBS Game Capture (sees nothing — good), then a friend on Discord screenshare sees the menu. This is not a bug; it's the capture-path mismatch from Step 1.**

Standard diagnosis sequence:

1. Ask: how is the friend viewing? Discord screenshare, Discord camera passthrough, watching a Twitch stream, looking at a screenshot, watching a recorded clip?
2. Map their viewing method to a capture category from Step 1 (Discord screenshare → Display Capture; Twitch via OBS Game Capture → process-internal; etc.).
3. Confirm: the PCX render path the user is using lands in *that* capture's layer. (Refer to the Step 2 matrix.)
4. Options:
   - Switch the offending render path to one that doesn't land in the friend's capture layer
   - If unavoidable (Display Capture catches all visible overlays): change the workflow (different capture target, hide-toggle hotkey, render only off-screen)
   - If the friend uses a HDMI capture card: see Step 4 — no software fix

```
Concrete walkthrough:

User: "My friend on Discord can see my ESP."
You:  "Discord screenshare uses Display Capture (composited desktop). Your
       PCX overlay landing in either the game's swap chain OR a separate
       desktop window will both show up there.
       To hide it from Discord screenshare specifically, you'd need to
       hide the rendering itself — there's no render path that's visible
       to you-the-user but invisible to Display Capture, because both you
       and Display Capture see the same composited desktop."

User: "But I tested with OBS and it didn't show up!"
You:  "OBS Game Capture only hooks the game's swap chain. If your overlay
       renders to a separate window, OBS Game Capture misses it — but
       Discord screenshare (Display Capture) doesn't. Different layers,
       different visibility."
```

The honest answer to many "how do I hide this from Discord" questions is "you can't, because Discord screenshare sees the same desktop you do." Steer toward workflow changes (bind a hide hotkey, share game audio only, share a specific application window that excludes the overlay).

**Why:** The technical answer (capture-path layering) once explained becomes obvious in retrospect. The hours of "but why" questions disappear when the user understands the three-category model from Step 1.

---

## Summary

| # | Topic | One-liner |
|---|---|---|
| 1 | Capture taxonomy | Process-internal vs desktop-composited vs signal-level — three layers, different visibility |
| 2 | PCX render paths | Game-swap-chain hook vs external window vs DWM layer — each lands in a different capture layer |
| 3 | Pre-stream checklist | Validate against the specific capture method, not "a screen capture" generically |
| 4 | HDMI capture cards | Pixel-accurate; no software solution; topology and aesthetics only |
| 5 | AC screenshot detection | Uses the same capture taxonomy; alignment with streamproofing is coincidental, not by design |
| 6 | Differential diagnosis | "Friend on Discord sees X" almost always = capture-path mismatch, not a script bug |

**Cross-references:** `docs/perception/render-api.md` (authoritative surface list for your PCX version), `knowledge/anti-cheat-architecture.md` (per-AC screenshot mechanisms), `skill://anti-cheat-re` (detection-surface methodology), `skill://pcx-perf-budget` (overlay render cost considerations for streamers running on a single-PC topology).

---

## Source: `.claude/skills/re-evidence-log/SKILL.md`

---
name: re-evidence-log
description: >
  Discipline for recording why each offset and sig is trusted — the proof
  behind the offset table. Every offset added, every sig derived, every
  struct layout committed comes with a citable evidence entry. Always active
  during RE work; pairs with pcx-re-discipline and pcx-patch-day-playbook.
license: MIT
---

# RE Evidence Log — Every Claim Cites Its Proof

The discipline of recording *why* you trust each offset and sig in your project. The offset table is data; the evidence log is the proof behind it. Without the log, every patch day starts from zero on the same offsets you derived three months ago — you remember roughly what you did, not the citations that let you confirm it. This skill is the artifact half of `pcx-re-discipline` (which is the discipline itself) and the input to `pcx-patch-day-playbook` Step 7 (which writes a per-patch entry into the log).

**Always active when doing RE work.** Every offset you add, every sig you derive, every struct layout you commit to the project comes with an evidence entry. The cost is one paragraph per claim; the payoff is being able to answer "why do we trust this?" three months later without re-reversing.

**Prerequisite:** `skill://pcx-re-discipline` for the underlying discipline rules; `knowledge/offset-methodology.md` for the sig-derivation mechanics the log entries reference; `tools/sig-uniqueness-checker.py` for the verdict you record alongside each sig.

---

## Trigger

Starting RE work on a new binary, adding an offset to `offsets.em`, committing a struct layout to a feature, recovering from a patch (the patch-day skill produces a log entry), onboarding a teammate to existing offsets, code-review of RE claims, suspicious behavior in a script you wrote weeks ago and can't remember why a field is at +0x40.

---

## 1. One File per Binary, One Entry per Claim

**The canonical layout: `evidence/<binary-hash-prefix>.md`, one file per binary you reverse, one numbered entry per claim.** Filed by content hash, not by game name or version — the same game across patches produces different binaries with different hashes; each gets its own file.

```
project/
├── globals.em
├── offsets.em
├── ...
└── evidence/
    ├── README.md                          ← what's in here, naming convention
    ├── 7a3f4d1c-game-v1.42.3.md           ← per-binary log
    ├── 7a3f4d1c-game-v1.42.3.sha256       ← cached hash for trivial verification
    ├── 9b2e8a07-game-v1.42.4.md           ← next patch = new file
    └── archive/                           ← old entries kept for diffing
        └── 7a3f4d1c-game-v1.42.3.md
```

Inside one file, each claim is its own section:

```markdown
# Evidence Log — game.exe v1.42.3
SHA-256: 7a3f4d1c8e2b5a019f3d4c7e2b1a8f6d...
Module size: 158,720,000 bytes (.text 0x00400000–0x00C12000)
First verified: 2026-06-15
Last verified: 2026-06-17

## E-001 — entity_list global pointer
## E-002 — local_player slot
## E-003 — view matrix (4x4 row-major)
## E-004 — CEntity::m_iHealth field offset
## E-005 — CEntity::m_vecOrigin field offset
...
```

Entry IDs (`E-001` … `E-NNN`) are stable across patches — `offsets.em` references them in comments (`// E-003`), so when you rewrite the offset for the next version, you keep the same ID and update the per-version file. The ID is the cross-reference; the file is the version-specific evidence.

**Why:** Without a per-binary file, you can't diff what changed between patches. Without numbered entries, you can't reference a claim from your code or a teammate's review. The file naming by hash means the system survives renames, re-downloads, and side-by-side comparison.

---

## 2. Every Claim Cites: Binary, Address, Xref Source, Last-Verified Date

**The minimum citation per entry. Anything shorter is a vague memory dressed up as a fact.**

The required fields per entry:

| Field | Why |
|---|---|
| `id` | Stable cross-reference for `offsets.em` and patch logs |
| `name` | Human-readable label (matches the constant in `offsets.em`) |
| `binary_hash` | The binary this claim is verified against |
| `rva` (or `sig`) | Where the thing is |
| `xref_source` | Function symbol, sig pattern, or string xref that found it |
| `derived_via` | How: pattern scan? SDK header lookup? Struct dump? |
| `last_verified` | Date of the most recent successful run on this binary |
| `verified_against` | The in-game observation that confirmed it works |

```markdown
## E-001 — entity_list global pointer

| Field             | Value |
|---|---|
| name              | `OFF_ENTITY_LIST` |
| kind              | RIP-relative pointer (loaded by LEA) |
| rva               | 0x04A2B100  (resolved from sig hit at 0x00872F40) |
| sig               | `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8` |
| sig_uniqueness    | UNIQUE (margin=5, per `tools/sig-uniqueness-checker.py`) |
| xref_source       | Called by `CGameWorld::Update`, identified via string xref "entity_list_full" |
| derived_via       | Pattern scan + RIP resolve (disp@+3, insn_len=7) |
| last_verified     | 2026-06-17 |
| verified_against  | ESP showed 12 entities in a match; entity count matched scoreboard |
```

WRONG — the kind of "evidence" that's actually nothing:

```markdown
## entity_list
Found in some function, +0x18 or +0x20, I think? Worked last time I checked.
```

This will cost you an hour the next time you touch it.

RIGHT — every field present, every claim verifiable:

```markdown
## E-001 — entity_list
hash 7a3f4d1c..., rva 0x04A2B100, sig "48 8D 0D ?? ...", from CGameWorld::Update,
verified 2026-06-17 against the scoreboard entity count.
```

The detail level is up to you — a table per entry or a single dense line — but the *fields* are mandatory.

**Why:** Three months from now, you will not remember which function you found this in. The patch-day playbook Step 4 (re-sig with near-miss) needs the original `derived_via` to know what the sig was trying to match. A teammate reviewing your offsets needs `xref_source` to know where to look themselves. The `last_verified` date is the brittleness signal (rule #5).

---

## 3. Sigs Cite the Disassembly They Were Derived From

**A sig alone is a number. A sig with its disassembly context is a hypothesis you can re-derive.** When the sig breaks, the disassembly tells you what the instruction *was*, so you can find what it *became* in the patched binary.

Format: the sig as a literal, then a small fenced block of the instructions it covers, then a one-line explanation of which bytes are wildcarded and why.

```markdown
## E-001 — entity_list (sig derivation)

sig: `48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8`

Derived from (game.exe v1.42.3, at .text+0x00872F40):
    48 8D 0D 5B 80 1B 04       LEA  rcx, [rip+0x041B805B]   ; -> &g_entity_list
    E8 2A 4F 12 00             CALL CGameWorld::Lookup       ; ret in rax
    48 8B D8                   MOV  rbx, rax                 ; save list ptr

Wildcards:
  - bytes 3..6   (4-byte RIP disp32 in the LEA — relocatable)
  - bytes 8..11  (4-byte CALL target relative disp — relocatable)
Total signature length: 15 bytes.
Unique-match verdict at derivation time: UNIQUE (margin=5).
```

When this sig later returns 0 after a patch, you have *exactly* what to look for in the new binary: a `LEA rcx, [rip+disp]` immediately followed by a `CALL` and `MOV rbx, rax`, near the same string xref ("entity_list_full") that originally led you here.

**Why:** A bare hex string strips out everything you knew when you wrote it. The disassembly preserves the *intent*: this is the LEA that loads the entity-list pointer into RCX, called immediately. If the compiler changed `MOV` to `LEA` in the patch (different opcode, different sig), you still know what to look for.

---

## 4. Struct Layouts Cite SDK Header AND In-Memory Verification

**Most struct layouts are partially known: some fields come from a community SDK header, others from your own struct dumping, others from guessing. Flag which are which.**

When a struct layout is wrong, the bug is silent — your script reads garbage that doesn't crash. The cost of being wrong is high; the cost of citing your source per field is two lines.

```markdown
## E-004 — CEntity struct layout (partial)

source: `r5sdk/include/game/server/entity.h` (commit 8a4c2e7, fetched 2026-06-10)
in-memory verification: 2026-06-17, walked g_entity_list[0..3] in a live match

| offset  | size | field         | source              | confidence |
|---------|------|---------------|---------------------|------------|
| 0x0000  | 8    | vtable_ptr    | SDK header          | HIGH       |
| 0x0008  | 4    | netvar_id     | SDK header          | HIGH       |
| 0x0040  | 4    | m_iHealth     | SDK header          | HIGH       |
| 0x0044  | 4    | m_iMaxHealth  | SDK header          | HIGH       |
| 0x00F0  | 4    | m_iTeamNum    | SDK header          | HIGH       |
| 0x0170  | 12   | m_vecOrigin   | SDK header          | HIGH       |
| 0x017C  | 12   | m_vecVelocity | OBSERVED (struct dump, three entities, values match expected ranges) | MEDIUM |
| 0x0188  | 4    | m_flAimYaw    | GUESS (correlated with on-screen view direction) | LOW |
| 0x1234  | 8    | m_pPlayerCtl  | GUESS (looks like a pointer; value is within module range) | LOW |
```

Three confidence tiers, three response policies:

- `HIGH` — SDK-cited or directly observed. Use without ceremony.
- `MEDIUM` — observed but not SDK-confirmed. Flag in `offsets.em` with a one-line comment.
- `LOW` — guess. Mark `UNVERIFIED` per `game-cheat-guidelines` rule #1. Treat reads as suspect; cross-validate (e.g. compare the supposed `m_flAimYaw` against the on-screen view direction over 100 frames before trusting it).

When code-reviewing, the question "where did you get this field?" is answered by looking at the table.

**Why:** Partial-layout bugs are the worst class of RE error. The script "works" — it draws ESP, it reads health, it pulls coords — but one field is wrong and the feature using that field silently produces garbage. Marking confidence per field makes the wrong-field call inspectable instead of invisible.

---

## 5. Update the Verified-On Date After Every Successful Run

**The age of the last verification is the brittleness signal. A sig last verified six months ago is more suspect than one verified yesterday, even if both are technically "in the log."**

The discipline: at the end of any session where the script ran correctly against the live target, walk through the log and bump `last_verified` for every claim that was actually exercised. Five seconds of editing per session.

```markdown
## E-001 — entity_list
last_verified: 2026-06-17  ← yesterday, fresh
last_verified: 2026-04-02  ← two months old, recheck before trusting
last_verified: 2025-12-15  ← six months — assume stale; revalidate or re-derive
```

At code-review time or before a release, sort entries by age:

```bash
# rough one-liner — adapt to your log format
grep -E '^last_verified:' evidence/*.md | sort -k2 | head -10
```

The oldest entries are the next ones to verify (or retire if they're no longer used by any feature).

A second related discipline: when you add a NEW claim, also list which claims it *depends on*. If E-006 is "`CEntity::m_pPlayer` reads `CPlayer` at the pointed address" and `CPlayer`'s layout is E-007, then E-006's evidence cites "depends on E-007." When E-007 becomes stale, the dependent claim is suspect too.

**Why:** Without freshness tracking, every entry has the same epistemic weight, which is wrong. A six-month-old "I verified this once" is closer to a guess than to fresh evidence. Dating gives you a triage signal for free, the cost of which is one date edit per session.

---

## 6. Cite Negative Results Too

**"Tried sig X, returned 0; tried sig Y, returned 3 hits; settled on sig Z" is data. Future-you debugging a regression needs to know what's *already been ruled out*.**

Most evidence logs record only the *successful* derivation. The next time the sig breaks and you reach for one of the *other* candidates you ruled out months ago, you'll re-rule it out again — costing the same hour.

Format: under each entry, a brief "Considered and rejected" subsection.

```markdown
## E-001 — entity_list

[main entry as above]

### Considered and rejected
- Sig `48 8B 0D ?? ?? ?? ??` (just the MOV form): too short, matched 47 places in .text.
- Hardcoded offset 0x04A2B100: that's the resolved address from THIS binary; will not
  survive a patch. Kept as the resolved value but the sig is the canonical source.
- Walking from `CGameWorld::Init` (xref candidate): the init function is in .data
  and gets re-inlined per build; brittle xref starting point.
- Reading PEB.LdrData to find a "game module" data segment: technically possible
  but adds a per-frame cost we don't want.
```

The same pattern applies to struct layout dead-ends ("field at +0x180 looked like a vec3 origin but the values were screen-space coords, not world; it's actually the last frame's m_vecOldPosition") and to struct-walking dead-ends ("the second pointer in this list is null in solo play; only populated in team modes — don't use as a liveness check").

**Why:** Negative results are the second-most-valuable thing in the log after positive ones. A teammate looking at this log can immediately see "ah, the obvious short sig is ambiguous — that's why we have a long one." The cost of recording is one line; the cost of not recording is rediscovery.

---

## Template

Drop-in skeleton for `evidence/<hash>.md` — copy, fill in:

```markdown
# Evidence Log — <binary_name> <version>

SHA-256: <full hash>
Module size: <bytes>  (.text <start>–<end>)
First verified: <YYYY-MM-DD>
Last verified: <YYYY-MM-DD>

Cross-reference: this file lists entries E-001..E-NNN; each entry's ID is
stable across patches and is referenced from `offsets.em` and `patch-log.md`.

---

## E-001 — <short name matching offsets.em constant>

| Field             | Value |
|---|---|
| name              | `OFF_X` |
| kind              | <RIP-relative pointer / direct address / field offset / sig> |
| rva               | <0x...> (resolved from sig hit at <0x...>) |
| sig               | `<bytes>` |
| sig_uniqueness    | <UNIQUE margin=N / AMBIGUOUS / etc per sig-uniqueness-checker.py> |
| xref_source       | <function, string xref, or other anchor> |
| derived_via       | <pattern scan + RIP resolve / SDK header / struct dump / xref walk> |
| last_verified     | <YYYY-MM-DD> |
| verified_against  | <in-game observation that confirmed it works> |
| depends_on        | <E-NNN, E-NNN — or "none"> |

Disassembly context (for sigs):
    <4-6 lines of asm covering the matched bytes; wildcards explained below>

Wildcards:
  - bytes A..B  (<what relocatable thing they cover>)

### Considered and rejected
- <alternative sig / approach / source>: <why it didn't pan out>

---

## E-002 — ...
```

A second template for struct entries:

```markdown
## E-NNN — <StructName> layout (<partial|complete>)

source: <SDK header path or "self-derived">
in-memory verification: <date>, <how many instances walked>

| offset | size | field | source | confidence |
|--------|------|-------|--------|------------|
| 0x0000 | 8    | vtable_ptr | SDK / observed | HIGH |
| ...    |      |       |        |            |

### Considered and rejected
- <field-shape alternative>: <why rejected>
```

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | One file per binary, one entry per claim | Stable IDs (E-NNN) cross-reference `offsets.em` and patch logs |
| 2 | Cite binary + address + xref + date | Six fields mandatory per entry; vague memory is not evidence |
| 3 | Sigs cite their disassembly | The intent of the sig is the hypothesis you re-derive from |
| 4 | Structs cite source + verification per field | HIGH / MEDIUM / LOW confidence tiers; LOW = `UNVERIFIED` in code |
| 5 | Update `last_verified` per successful run | Age is the brittleness signal — six months old is suspect |
| 6 | Cite negative results too | "Tried and rejected" prevents the next person re-deriving the same dead end |

**Cross-references:** `skill://pcx-re-discipline` (the discipline rules), `skill://pcx-patch-day-playbook` (Step 7 writes a per-patch log entry), `knowledge/offset-methodology.md` (the mechanics being cited), `tools/sig-uniqueness-checker.py` (produces the `sig_uniqueness` field value), `tools/offset-diff.py` (per-patch diff feeds the negative-results section).

---

## Source: `.claude/skills/script-bundler/SKILL.md`

---
name: script-bundler
description: >
  Build and deployment workflow for PCX scripts: .em vs .emb, bundle order
  respecting the module-import graph, hot-reload survival, pre-ship hygiene
  checklist, runtime-version pinning, and distribution metadata. Triggers
  when packaging, distributing, or releasing scripts to other users.
license: MIT
---

# Script Bundler — Packaging and Shipping PCX Scripts

The build and deployment workflow for PCX scripts: when to distribute raw `.em` source vs precompiled `.emb`, the bundle order that respects the module-import graph, what survives hot-reload, the pre-ship hygiene checklist, runtime-version pinning, and the distribution metadata that goes alongside the script. Closes the "how do I package this for someone else to use" gap; sits beside `pcx-patch-day-playbook` (the inbound workflow for receiving updates) as the outbound workflow for sending them.

**Trigger when:** the user mentions building, shipping, releasing, packaging, distributing, `.emb`, `.em` archive, sharing with someone, multi-user setup, marketplace upload, or asks about what survives hot-reload, what to strip before publishing, or how to handle multi-file projects across editors.

**Prerequisite:** `docs/enma/sdk-serialization-and-linking.md` for the `.emb` binary format and `serialize` / `link` APIs; `docs/enma/sdk-hot-reload.md` for what persists across reloads; `docs/enma/lang-modules.md` for the import system the bundler resolves; `templates/full-project/` as the canonical 5-file scaffold this skill builds on.

---

## Trigger

Shipping a script to a user, packaging a project for distribution, multi-file project that needs a single-file artifact, marketplace upload requiring source stripping, hot-reload questions about what state survives, pre-release hygiene check, version compatibility planning, sharing with a teammate who is on a different PCX version.

---

## 1. When to Ship `.em` vs `.emb`

**Plain `.em` source is debuggable and user-editable; precompiled `.emb` loads faster, hides incidental file paths, and obfuscates trivially-inspectable strings. The choice is per audience, not per project.**

| Property | `.em` (source) | `.emb` (precompiled) |
|---|---|---|
| Recipient can read the code | Yes | No (XOR-obfuscated body) |
| Recipient can edit/tune | Yes (open in editor) | No (must rebuild from source) |
| Recipient sees your file paths | Yes (and your username if absolute) | No when `keep_debug=false` |
| Load time | Compile + link on every load | Deserialize only (faster) |
| Version compatibility | Source compiles against any compatible runtime | Locked to the `.emb` format version (`k_emb_version`); breaks across major bumps |
| Stack traces / error messages | Full file:line | Reduced when `keep_debug=false` (`get_last_executed_line` returns 0) |
| Casual `strings` inspection reveals API/struct names | Yes | No (header-stored salt XORs strings) |

Decision matrix:

- **Internal team / single developer** — `.em`. You're the recipient; the source-readability win compounds with editor tooling.
- **Trusted partner who will tune knobs** — `.em` with a `README` pointing at the config block. They'll tweak; `.emb` would force a rebuild round-trip.
- **Public release / marketplace** — `.emb` with `keep_debug=false`. The host-side serializer call is `serialize(mod, data, false)`; this drops the `source_map` and `debug_functions` tables so your absolute source paths don't ship.
- **Library you ship for others to depend on** — `.emb`, document the `k_emb_version` it was built against, ship a source bundle alongside for users who want to recompile.

The two formats are *not* mutually exclusive — many projects ship the `.emb` as the primary artifact and the `.em` source in an `src/` folder for users who want to inspect or modify.

**Why:** Picking `.emb` because "it's faster" is rarely the right reason — load-time difference is milliseconds either way. Picking it because you want path stripping, body obfuscation, or distribution-format consistency *is* the right reason. State the reason in the project README so a future maintainer doesn't switch formats arbitrarily.

---

## 2. The Canonical Bundle Order

**The `templates/full-project/` scaffold defines the order: `globals → offsets → feature → menu → main`. Each file imports only files above it; there are no cycles. Violating the order produces link errors at bundle time or, worse, run-time symbol resolution failures that surface only when the unlinked code path is hit.**

The import graph as ASCII:

```
                          main.em
                         /   |   \
                        /    |    \
                     menu  feature1 feature2  (... featureN)
                       \    /   |    /
                        \  /    |   /
                       offsets-<binary>.em
                              |
                          globals.em
                              |
                            (stdlib)
```

What each layer is allowed to import:

| Layer | May import |
|---|---|
| `globals.em` | stdlib only — `vec`, `color`, `math`, `time`, etc. |
| `offsets-<binary>.em` | `globals.em` plus stdlib |
| `feature-<name>.em` | `globals.em`, `offsets.em`, plus stdlib — never another feature |
| `menu.em` | `globals.em` plus stdlib (no offsets, no features — menu state is config, not gameplay) |
| `main.em` | every other file in the project |

The rules in plain language:

- A feature **never** imports another feature. If two features need the same data, the data lives in `globals.em` (read) or a `utils-*.em` module (function library). See `knowledge/script-organization-patterns.md` for the "when to extract a util" heuristic.
- The menu **never** imports a feature. Widgets bind to globals in `globals.em`; features read those globals. The decoupling means a disabled feature still has working widgets (they just don't do anything).
- `offsets.em` is per-binary, not per-feature. If you target multiple binaries (rare), `offsets-game.em` and `offsets-editor.em` each exist, and the right one is imported in `main.em` based on which binary you attached to.

When you violate the order:

- **Cycle (`featureA` imports `featureB` which imports `featureA`)** — bundle-time error from the linker.
- **Feature imports another feature** — link succeeds, but you've coupled them; touching one now risks the other.
- **Menu imports a feature** — link succeeds, but disabling the feature in the bundle breaks the menu, which is the opposite of what the layering exists to enable.

For the host-side `link()` call (when you're embedding the engine yourself and combining modules at the C++ level):

```cpp
const char* names[] = { "globals", "offsets", "feature_esp", "feature_aim", "menu", "main" };
module_t*   mods[]  = { /* compiled in the same order */ };
module_t*   linked  = link(e, names, mods, 6);
```

The `names` array is the symbol prefix per module — `globals::g_proc` is how `feature_esp` accesses a global. This means even at the linker level, the dependency graph is explicit and any forbidden reference is a compile-time error.

**Why:** Layering is the cheapest enforcement of `game-cheat-guidelines` #6 (one feature per file). It forces every cross-feature interaction through `globals.em`, which is where you can audit them. Without the layering, the project's modules drift into a hairball within a month.

---

## 3. Hot-Reload-Safe Boundaries

**Reload replaces only the script code. Globals, registered types, and native functions persist. Design state lifetimes around this.**

What survives a hot reload (per `docs/enma/sdk-hot-reload.md`):

- The target process and its memory (you do not re-attach; the `proc_t` handle remains valid in your globals if you stored one — but you should re-attach in `main()` anyway as a freshness check)
- Registered native functions and types — unchanged
- The engine and all live contexts — same `context_t*` pointers continue to work
- Host-side state — your C++ code holding the module pointer

What does NOT survive a hot reload:

- Script-level globals (in Enma terms, the script's runtime state) — reset to their declaration defaults
- Cached pattern-scan results — re-resolve in the new `main()` or in the first frame after reload
- GUI section state in the script's data — re-create the section, re-bind widgets to the new globals
- Any in-script delegate / function pointer table — must be re-built

The implication is a strict separation between *script state* (lost on reload) and *host state* (preserved):

```cpp
// In your script — assume everything resets each load
proc_t g_proc;
uint64 g_base = 0;
bool   g_resolved = false;
uint64 g_entity_list = 0;

int64 main() {
    // EVERY load runs this — sigs resolve fresh, no carry-over
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) return 0;
    g_base = g_proc.base_address();

    uint64 size = g_proc.get_module_size("game.exe");
    uint64 hit = g_proc.find_code_pattern(g_base, size, SIG_ENTITY_LIST);
    if (hit == 0) return 0;
    g_entity_list = resolve_rip(g_proc, hit, 3, 7);
    g_resolved = g_entity_list != 0;

    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
```

For state you *want* to survive a reload (config tunings the user has set, last-used hotkey), persist to disk and reload in `main()`:

```cpp
import "json";

int64 main() {
    // ... process attach ...
    load_config_from_disk();        // restores g_esp_enabled, g_smoothing, etc.
    setup_gui();                    // widgets bind to the restored values
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}
```

`knowledge/script-organization-patterns.md` covers the file/JSON persistence pattern in detail.

**Why:** Code that assumes globals survive a reload reads stale or zero data on the first frame after reload — the overlay draws nothing, the user notices, you waste twenty minutes debugging what "broke" since the last edit. Treating `main()` as the authoritative initializer (every reload, every load, fresh state) avoids the entire class of bug.

---

## 4. Pre-Ship Hygiene Checklist

**Before zipping, uploading, or sending the artifact anywhere, run through every item. Cost: five minutes. Cost of skipping: the embarrassing thing on someone else's machine.**

```
PRE-SHIP HYGIENE CHECKLIST

[ ] No hardcoded usernames, machine names, or absolute paths in default config values
    grep -nE '(C:\\Users\\|/home/|/Users/)' src/

[ ] No debug println of resolved offsets / addresses / process handles in production paths
    grep -nE 'println\(.*0x[0-9A-Fa-f]+' src/

[ ] No `// TODO`, `// FIXME`, `// HACK`, `// XXX` left in shipped code
    grep -nE '(TODO|FIXME|HACK|XXX)' src/

[ ] No file-system writes outside the documented config dir
    grep -nE 'fs_write_file\(' src/   # then audit each path

[ ] No network calls to anything that isn't a documented service
    grep -nE 'http_(get|post)|websocket' src/

[ ] No leftover XOR-encrypted strings revealing internal infrastructure
    (run tools/dump-strings-xor.py against your built .emb to check)

[ ] All offsets carry `// E-NNN` references into evidence/<hash>.md (per skill://re-evidence-log)
    grep -cE '// E-[0-9]+' offsets.em   # should be > 0

[ ] All sigs verified UNIQUE on the target binary
    (run tools/sig-uniqueness-checker.py against the offsets file)

[ ] Module name in ref_process() is the actual target, not a placeholder
    grep -nE 'ref_process\("' src/

[ ] No commented-out blocks of "old experiment" code — delete them; git keeps history

[ ] GUI defaults are sensible for a first-time user (not your tuned-for-you values)

[ ] LICENSE file present and accurate

[ ] README points at the right PCX version, the right game, the right install path

[ ] CHANGELOG entry for THIS release exists, with the user-visible changes named
```

Most of these are one-line greps you can wire into a shell script run before every release. Save it as `pre-ship.sh` in your project — when the grep output is non-empty, the release is not ready.

**Why:** Every item on the list maps to a specific class of complaint the recipient will file. Hardcoded paths break on Windows vs Linux. Debug printlns leak internals. TODOs imply the script isn't finished. Network calls to your private server make the recipient's network admin nervous. The five minutes is cheap insurance against the "but it worked on my machine" support burden.

---

## 5. Runtime Version Pinning

**The script should declare which PCX runtime version it expects. The consumer should fail fast if the runtime is too old — clear error message, not silent wrong behavior.**

PCX evolves; APIs are added across versions. A script that uses `world_to_screen_rowmajor` (added in a specific PCX version per `docs/perception/changelogs.md`) will not link on a runtime that predates it — but the error message can be confusing if the user doesn't know which runtime they're on.

The defensive pattern:

```cpp
// At the very top of main.em
#define PCX_REQUIRED_MAJOR 2
#define PCX_REQUIRED_MINOR 4

int64 main() {
    // If the runtime exposes a version-query API, use it (check docs/perception/changelogs.md
    // for the canonical accessor name; this is a defensive sketch).
    //
    // Fallback when no version API exists: rely on the link-time error from a known API
    // that exists only in PCX_REQUIRED_MAJOR.PCX_REQUIRED_MINOR+; that becomes the
    // version-check by proxy.

    println(format("script requires PCX v{d}.{d}+", PCX_REQUIRED_MAJOR, PCX_REQUIRED_MINOR));

    // ... rest of main ...
    return 1;
}
```

In the project README, document the version requirement explicitly:

```markdown
## Requirements
- Perception.cx runtime **2.4+** (this script uses `world_to_screen_rowmajor`,
  introduced in 2.4 — earlier versions will not link).
- Game build verified against: **MyGame v1.42.3** (SHA-256: 7a3f4d1c...).
- Tested with PCX scripting frontend versions: 2.4.0, 2.4.1, 2.4.3.
```

Cross-reference `knowledge/pcx-version-matrix.md` (the by-version API availability table) when deciding which version to pin to.

For `.emb` artifacts, the `k_emb_version` format version is encoded in the binary header and the host-side `deserialize` will reject too-new or too-old `.emb` files cleanly. You don't need to do anything; this is how the runtime enforces format compatibility independent of your code.

**Why:** Without explicit pinning, a user on an older runtime gets a cryptic "function not found" or, worse, silently runs on a partial-feature install. Pinning at the top of the file makes the requirement self-documenting, and the README echo means the requirement is visible *before* the user runs the script.

---

## 6. Distribution Metadata

**Alongside the script artifact: a recipient-facing `README.md`, a `LICENSE`, and a `CHANGELOG`. One page each. Cheap to write, expensive to omit.**

Template — `README.md` for the recipient (not your developer README; that's separate):

```markdown
# <project_name>

What it does: <one sentence>.
Target: <game> v<X.Y.Z> (other versions may or may not work).
Requires: Perception.cx runtime <X.Y>+ (see "Requirements" below).

## Install
1. Copy `<project>.em` (or `<project>.emb`) into your PCX scripts directory:
   - Windows: `%LOCALAPPDATA%\Perception\scripts\`
   - macOS / Linux: see the official PCX install path docs
2. In the PCX IDE, load the script.
3. Open the `<project>` GUI section in the sidebar.
4. Toggle features as desired; hotkeys default per the GUI labels.

## Requirements
- Game: <name> v<X.Y.Z>
- Runtime: PCX v<X.Y>+
- Binary hash (target): <sha256>

## Configuration
The script auto-saves your GUI tunings to `<config_path>` after every change.
On first run, defaults are loaded.

## Verify Install
- Attach the script in the IDE; expect a one-line console message: "<project> v<X.Y.Z> loaded".
- If you see "process not found", the game isn't running.
- If you see "signature scan failed", the game version doesn't match — see Patch Day.

## Patch Day
When the game updates and the script stops working, see the project's `patch-log.md` for known affected sigs. If not yet patched, the script will say which sig failed; report it back to the project.

## Known Limitations
- <list>

## Credits / License
MIT (or whatever). Author: <name>. Source: <link>.
```

`LICENSE` — pick one, ship it. Most PCX scripts use MIT; some use GPL. Don't ship anything without a `LICENSE`; recipients will redistribute and the absence makes the legal situation unclear.

`CHANGELOG.md` — one entry per release, newest first:

```markdown
# Changelog

## [1.2.0] — 2026-06-17
### Added
- Minimap with rotation.
- GUI hotkey: F8 toggles overlay.

### Fixed
- ESP no longer draws behind the camera (w > 0.001 gate).
- Entity-list sig moved in game v1.42.3 — re-derived.

### Changed
- Smoothing default 6.0 → 8.0 (felt too snappy in playtests).

## [1.1.0] — 2026-05-30
...
```

The CHANGELOG is what the user reads when "I just updated and something is different." It's the most-read file in the package after the README.

**Why:** Recipients don't read your code; they read your README. They don't grep your git log; they read your CHANGELOG. They will redistribute if there's a LICENSE and won't if there isn't (or won't legally, anyway). Each file takes five minutes; together they cover ~90% of the support burden you would otherwise field directly.

---

## Pre-Ship Checklist (Condensed)

Run through this every release:

```
[ ] No hardcoded paths / usernames / machine names
[ ] No debug println leaking offsets or addresses
[ ] No TODO / FIXME / HACK / XXX
[ ] No file-system writes outside the documented config dir
[ ] No network calls to non-public endpoints
[ ] No commented-out experimental code blocks
[ ] All offsets cite an evidence entry (skill://re-evidence-log)
[ ] All sigs verdict UNIQUE (tools/sig-uniqueness-checker.py)
[ ] Runtime version pinned at top of main.em
[ ] README.md present, current, recipient-facing
[ ] LICENSE present and accurate
[ ] CHANGELOG entry for this release exists
[ ] (If shipping .emb) serialize called with keep_debug=false
[ ] (If shipping .emb) tested by deserialize on a clean runtime
[ ] Sensible GUI defaults for a first-time user
```

If you script the checklist, save it as `pre-ship.sh` and run it before every `git tag`.

---

## Summary

| # | Topic | One-liner |
|---|---|---|
| 1 | `.em` vs `.emb` | Source for trusted users + tuning; precompiled for marketplace / path stripping |
| 2 | Bundle order | `globals → offsets → feature → menu → main`; features never import features |
| 3 | Hot-reload boundaries | Globals reset, target process survives; `main()` is the authoritative initializer |
| 4 | Pre-ship hygiene | Greppable checklist; five minutes; prevents most support tickets |
| 5 | Runtime version pinning | `#define PCX_REQUIRED_MAJOR/MINOR` at top of main.em; README echoes it |
| 6 | Distribution metadata | `README` + `LICENSE` + `CHANGELOG` — one page each, cover 90% of support |

**Cross-references:** `skill://pcx-patch-day-playbook` (inbound workflow for receiving updates; this skill is the outbound workflow for sending them); `skill://re-evidence-log` (offsets ship with stable `E-NNN` IDs cross-referenced from the bundle); `knowledge/script-organization-patterns.md` (the layered structure the bundle order respects); `knowledge/pcx-version-matrix.md` (lookup table for which APIs landed in which runtime version, used for version pinning); `docs/enma/sdk-serialization-and-linking.md` (host-side `serialize` / `link` APIs the bundler invokes); `docs/enma/sdk-hot-reload.md` (the reload semantics this skill designs around).
