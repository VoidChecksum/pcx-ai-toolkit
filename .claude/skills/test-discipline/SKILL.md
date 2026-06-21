---
name: test-discipline
description: >
  Guides the AI and developer to build small, modular verification scripts or test
  routines that read target memory and validate struct layouts, offsets, and type shapes
  before writing complex rendering or logic code.
license: MIT
---

# Test Discipline & Memory Verification

Ensure every offset, pointer chain, and struct layout is verified with live memory reads BEFORE committing it to a production overlay or aimbot loop.

## Trigger
Writing new memory scan/read logic, resolving offsets, debugging incorrect data rendering, initializing a new script, or modifying structs and pointer chains.

## Core Philosophy: Verify Before You Build

When writing scripts for Perception.cx, it is easy to write a large amount of overlay and helper code before verifying if the underlying memory reading logic works. This leads to complex debugging scenarios.

**Test Discipline** means writing a separate, single-purpose verification script (or an isolated test routine) that:
1. Attaches to the game process.
2. Reads the target structure (e.g., Local Player, Entity List).
3. Prints the raw read values to the console or log.
4. Validates that the fields change correctly with live action (e.g., coordinates change as you move, health decreases as you take damage).

---

## 3-Step Verification Checklist

### Step 1: Write a Minimum Viable Reader (MVR)
Before writing ESP drawing code, write a script that does nothing but print variables.

*WRONG (Monolithic guess-work):*
```enma
// Writing 100 lines of ESP box calculations and text drawing on untested offsets
void draw_esp() {
    uint64 local = proc_read_uint64(g_proc, g_local_player);
    // ... ESP rendering code ...
}
```

*RIGHT (Isolated test verification):*
```enma
// test-player-coords.em
import "proc";

void main() {
    proc_t proc = ref_process_by_name("game.exe");
    if (!proc.alive()) {
        print("[-] Game process not found");
        return;
    }
    
    uint64 base = proc_module_base(proc, "game.exe");
    uint64 local = proc_read_uint64(proc, base + 0x1A2B3C); // player base pointer
    print("[+] Local Player Ptr: 0x" + hex(local));
    
    if (local == 0) return;
    
    // Read and verify coordinates
    float x = proc_read_float(proc, local + 0x90);
    float y = proc_read_float(proc, local + 0x94);
    float z = proc_read_float(proc, local + 0x98);
    
    print("[+] Player Position: " + x + ", " + y + ", " + z);
}
```

### Step 2: Validate Under Mutation
Do not trust static values. Make sure values change dynamically as expected:
- **Movement:** Check if position coordinates change in real-time when the player moves.
- **State Change:** Check if health/shield values decrease/increase when taking damage or healing.
- **Pointers:** Restart the game and verify that the pattern scanner resolves the correct offsets dynamically.

### Step 3: Validate with `pcx lint`
Run `pcx lint <test_file.em>` to verify your test script adheres to safety guidelines (e.g., using `uint64` for addresses, adding proper null guards).

---

## Logging & Formatting Guidelines
When writing test verification logs, format outputs cleanly so that failures stand out:
- Use `[+]` for successful checks.
- Use `[-]` or `[!]` for failures, null pointers, or unexpected values.
- Print address values in hex format (`0x` prefix) using the `hex()` helper.
