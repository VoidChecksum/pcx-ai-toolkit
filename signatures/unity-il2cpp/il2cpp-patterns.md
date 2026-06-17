# Unity IL2CPP Reversal Patterns

Pattern scanning and struct resolution for Unity games compiled with IL2CPP (Ahead-Of-Time). Applies to: Escape from Tarkov, Rust, Arena Breakout Infinite, and any other Unity title using IL2CPP.

> **These are EXAMPLE patterns.** IL2CPP compiles managed C# to native code per-build — exact offsets and struct layouts change every patch. Use these as starting points, not hardcodes.

---

## Architecture Overview

IL2CPP replaces Mono's JIT with AOT compilation:

```
C# source → IL bytecode → il2cpp transpiler → C++ source → MSVC/Clang → native .dll
```

**Key binaries:**
| File | What |
|------|------|
| `GameAssembly.dll` | All game C# code, AOT-compiled to native x64 |
| `global-metadata.dat` | Class names, field names, method signatures, string literals |
| `UnityPlayer.dll` | Unity engine runtime |

**Key difference from Mono:** There is no JIT, no managed runtime — everything is native code. But `global-metadata.dat` preserves all type information, so you can recover the full class hierarchy.

---

## Step 1: Dump Metadata

Use **Il2CppDumper** to extract class definitions from `global-metadata.dat`:

```bash
# Il2CppDumper — extracts C# class/field/method metadata
Il2CppDumper.exe GameAssembly.dll global-metadata.dat output/
```

**Output:**
- `dump.cs` — All C# class definitions with field offsets
- `il2cpp.h` — C header with struct layouts (importable into IDA/Ghidra)
- `script.json` — Method addresses for IDA/Ghidra scripts

**Example dump.cs output:**
```csharp
// Namespace: EFT
public class Player : MonoBehaviour // TypeDefIndex: 12345
{
    public PlayerHealth Health; // 0x80
    public MovementContext MovementContext; // 0x88
    public ProceduralWeaponAnimation ProceduralWeaponAnimation; // 0x90
    public PlayerBody PlayerBody; // 0x98
    public Transform PlayerBones; // 0xA0
    // ...
}
```

The `// 0x80` comments are the field offsets — read them directly with `p.ru64(player + 0x80)`.

---

## Step 2: Find the GC Handle Table (Object References)

IL2CPP stores root object references in the GC handle table. Static fields are accessed through this table.

**Pattern — Il2CppGCHandle resolution:**
```
# Look for il2cpp_gc_handle_get_target or il2cpp_resolve_icall
# These are exported from GameAssembly.dll
```

**Static field access pattern:**
```
# Static fields are stored in a per-class "static fields" struct
# Access: Class -> static_fields pointer -> field offset

# Pattern to find static field access:
# MOV RAX, [RIP+disp]        ← class metadata pointer
# MOV RAX, [RAX+0xB8]        ← static_fields pointer (offset varies by Unity version)
# MOV RCX, [RAX+field_offset] ← the actual static field value
48 8B 05 ?? ?? ?? ??    # mov rax, [rip+disp]  (class info)
48 8B 80 B8 00 00 00    # mov rax, [rax+0xB8]  (static_fields — may be 0x5C, 0xB8, or 0xDC)
48 8B 48 ??             # mov rcx, [rax+??]    (field offset)
```

---

## Step 3: Common Game Object Patterns

### Camera (World-to-Screen)

```
# Unity Camera.main is a static property
# Pattern: Camera::get_main() returns the Camera* with the "MainCamera" tag

# The ViewMatrix is inside Camera::worldToCameraMatrix (4x4 float matrix)
# Access: camera + 0x??? → view-projection matrix
# Use Il2CppDumper output to find the exact offset for your build
```

### Transform (Entity Position)

```
# Transform stores position as a native Vector3 in TransformAccess
# The actual world position is computed, not stored directly
# Use Transform.get_position() — find it via Il2CppDumper method addresses

# Pattern: Transform::get_position_Injected calls into UnityPlayer.dll
# Look for the method address in script.json:
# "Transform$$get_position_Injected": "0x1A2B3C4D"
```

### GameObject Active State

```csharp
// From dump.cs — check if an entity is active:
// GameObject.m_IsActive at offset 0x?? (varies)
// Or call GameObject.get_activeInHierarchy()
```

---

## Step 4: Perception.cx Integration

```cpp
// IL2CPP reversal with Perception's RE tools

// 1. Find GameAssembly.dll base
auto ga = p.get_module("GameAssembly.dll");
uint64 base = ga.base();

// 2. Pattern scan for a known method (from Il2CppDumper script.json)
// Example: find Player::Update by scanning for its prologue
uint64 player_update = p.find_code_pattern(base, ga.size(),
    "48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 30");

// 3. Read static fields
// Class metadata pointer (found via pattern or Il2CppDumper)
uint64 class_info = p.ru64(base + CLASS_INFO_OFFSET);
uint64 static_fields = p.ru64(class_info + 0xB8);  // Unity version dependent
uint64 local_player = p.ru64(static_fields + LOCAL_PLAYER_OFFSET);

// 4. Read instance fields (offsets from dump.cs)
if (local_player != 0) {
    uint64 health = p.ru64(local_player + 0x80);  // Player.Health
    float hp = p.rf32(health + 0x10);              // PlayerHealth.Current
    println(format("HP: {}", hp));
}
```

---

## Il2CppDumper Alternatives

| Tool | When to Use |
|------|-------------|
| **Il2CppDumper** | Standard — works on most IL2CPP games |
| **Cpp2IL** | More aggressive recovery, generates pseudocode |
| **Il2CppInspector** | GUI-based, generates IDA/Ghidra scripts |
| **Frida-il2cpp-bridge** | Runtime hooking of IL2CPP methods |

---

## Anti-Cheat Considerations

- **EAC (Tarkov, Rust, ABI):** Suspending before dumping is common but detectable. Use offline metadata extraction where possible.
- **Module scanning:** Il2CppDumper runs externally — it reads `GameAssembly.dll` from disk, not from memory. No injection required.
- **Offset volatility:** IL2CPP offsets change every game update. The metadata format is stable, so re-dumping is quick.
