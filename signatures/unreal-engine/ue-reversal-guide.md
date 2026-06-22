# Unreal Engine Reversal Guide

**These are EXAMPLE patterns and offsets only.** Unreal Engine is a *template* — every shipped game recompiles it with custom classes, custom field layouts, and (increasingly) custom encryption. The base `UObject` / `UWorld` / `AActor` hierarchy stays structurally similar, but every concrete offset varies by engine version and game build. Always verify against the actual binary you are targeting.

Source: Perception.cx Learning & Research forum (mk17, underscore).

## Core Globals

Almost every UE cheat bootstraps from three global objects. Find these first; everything else is reachable from them.

### GWorld

Global pointer to the current `UWorld` instance — the root of all live game state.

```cpp
class UWorld : public UObject {
    ULevel*          PersistentLevel;     // 0x0030 (typical)
    UNetDriver*      NetDriver;           // 0x0038 (typical)
    UGameInstance*   OwningGameInstance;  // varies per game
    AGameStateBase*  GameState;           // varies per game
    // TArray<ULevel*> Levels;            // streamed sublevels
};
```

`GWorld` is a *pointer to a pointer* in the module's data section. Resolve the address with a sig scan, then dereference once to get the live `UWorld*`.

### GObjects

Global container (`FUObjectArray` / `TUObjectArray`) holding a reference to every alive `UObject`. Every UE object — actors, components, classes, structs — inherits from `UObject`, so `GObjects` is the master enumeration table.

Use it to:
- Enumerate all live objects
- Find a `UClass` by name (then match instances against it)
- Locate actors when you don't have a direct pointer chain

```cpp
class UObject {
    void*    VTable;        // 0x00
    int32    Flags;         // 0x08 (EObjectFlags)
    int32    InternalIndex; // 0x0C — index into GObjects
    UClass*  ClassPrivate;  // 0x10
    FName    NamePrivate;   // 0x18 — index into GNames
    UObject* OuterPrivate;  // 0x20
};
```

`GObjects` layout differs between the old `TArray`-style and the newer chunked `FUObjectArray` (objects stored in fixed-size chunks). Dumper-7 detects which variant is in use.

### GNames

Global name pool (`FNamePool` / `TNameEntryArray`) — a centralized string table. Objects do **not** store their names as strings; they store an `FName`, which is an index (and on modern UE, a `ComparisonIndex` + `Number`) into `GNames`. Resolving a human-readable name means looking the index up in this pool.

```cpp
struct FName {
    int32 ComparisonIndex; // index into GNames
    int32 Number;          // disambiguation suffix (e.g. "Pawn_3")
};
```

Like `GObjects`, the pool is chunked on modern engines. Reading a name = decode the chunk/offset from the index, then read the `FNameEntry` (which carries a length header + raw bytes, ANSI or wide).

## Finding the Globals

### Method 1: Dumper-7 (recommended)

[Dumper-7](https://github.com/Encryqed/Dumper-7) (and the maintained fork at `github.com/djlorenzouasset/Dumper-7`) is an injectable DLL that auto-detects engine internals, resolves the three globals, and emits a full C++ SDK plus the offsets.

Step by step:

1. **Build the dumper.** Clone Dumper-7, open in Visual Studio, compile `Release | x64` to produce `Dumper-7.dll`.
2. **Launch the target game.** Get fully into a match/level — UE loads objects *dynamically*, so classes that aren't spawned yet won't appear in the dump.
3. **Stage the right scene.** Some classes only exist in specific game states (lobby vs match, menu vs in-world). You may need to dump multiple times in different states and merge.
4. **Inject `Dumper-7.dll`** with any manual-map / LoadLibrary injector. Wait for it to finish (it logs to a console or a file in the game directory).
5. **(Anti-cheat)** For protected games (e.g. EAC), suspend the process with Cheat Engine *before* injection so the dumper runs without the anti-cheat heartbeat catching the foreign module, then resume. Treat this as engagement-dependent — only on systems you are authorized to test.
6. **Collect output.** Dumper-7 writes:
   - A full SDK (`SDK/` folder of `.h`/`.cpp` per package)
   - `GObjects`, `GNames`, `GWorld` offsets (relative to module base)
   - `Offsets.hpp` / `Basic.hpp` with core struct offsets

> SDK dumps are **version-specific**. A game update changes offsets — re-dump after every patch.

### Method 2: Manual RE with IDA / Ghidra

When a dumper fails (encryption, packing, custom allocator) fall back to manual analysis:

- **Pattern-scan known UE code shapes** for the instruction that loads each global, then RIP-resolve (see [offset-methodology.md](../../knowledge/offset-methodology.md)).
- **Anchor on string literals.** UE ships with thousands of stable strings — `"SeamlessTravel"`, `"PersistentLevel"`, engine class names, `.uasset` paths. Xref a string → reach the function that uses the global → copy the load instruction.
- **GNames anchor:** xref the string `"None"` or `"ByteProperty"`; the name-pool init/lookup routines reference these constants.
- **GWorld anchor:** functions handling level transitions (`UEngine::LoadMap`, seamless travel) read/write `GWorld`.
- **GObjects anchor:** `StaticFindObject` / object-iteration helpers walk the array; xref `"StaticConstructObject"` style strings.

#### Example sigs (illustrative — re-derive per build)

These follow the same construction and RIP-resolution rules as the [Source Engine sigs](../source-engine/common-sigs.md). The 4-byte RIP displacement is wildcarded; resolve with `resolve_rip(hit, disp_offset, insn_len)`.

```
GWorld
Description: MOV/LEA reg, [rip+????] loading the GWorld pointer-to-pointer
Sig shape:   48 8B 05 ?? ?? ?? ?? 48 3B 05      (MOV RAX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → deref once for UWorld*
```

```
GObjects (FUObjectArray)
Description: LEA reg, [rip+????] referencing the global object array
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B          (LEA RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → FUObjectArray base
```

```
GNames (FNamePool)
Description: LEA reg, [rip+????] referencing the global name pool
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 4C 8B          (LEA RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → FNamePool base
```

Verify each produces exactly one hit in the module; extend with surrounding bytes if not.

## Key UE Structures

The canonical reference is the dumped SDK headers, but these are the structures you walk most. **Offsets shown are typical defaults — confirm against your dump.**

```cpp
// UWorld — the live game world (GWorld dereferences to this)
class UWorld : public UObject {
    ULevel*         PersistentLevel;     // 0x0030
    UNetDriver*     NetDriver;           // 0x0038
    AGameStateBase* GameState;           // varies
    UGameInstance*  OwningGameInstance;  // varies
};

// ULevel — owns the actor list for a level
class ULevel : public UObject {
    TArray<AActor*> Actors;              // offset varies per game
    // TArray = { AActor** Data; int32 Count; int32 Max; }
};

// AActor — base for everything placed in the world
class AActor : public UObject {
    USceneComponent* RootComponent;      // location lives on the component
    // Location = RootComponent->RelativeLocation (FVector)
};

// APawn — a possessable actor (the physical body)
class APawn : public AActor {
    APlayerState*      PlayerState;
    AController*        Controller;
};

// APlayerController — the local player's input/view authority
class APlayerController : public AController {
    APawn*             AcknowledgedPawn;  // the pawn we control
    UPlayer*           Player;
    AHUD*              MyHUD;
    FRotator           ControlRotation;   // view angles
    // PlayerCameraManager — world->screen projection source
};

// UGameInstance — persists across level loads
class UGameInstance : public UObject {
    TArray<ULocalPlayer*> LocalPlayers;  // LocalPlayers[0] = us
};
```

### The standard local-player chain

```
GWorld → UWorld
       → OwningGameInstance → UGameInstance
       → LocalPlayers[0]    → ULocalPlayer
       → PlayerController    → APlayerController
       → AcknowledgedPawn    → APawn (our body)
```

For enemy enumeration, walk `GWorld → PersistentLevel → Actors[]` and class-filter against the pawn/character `UClass` you resolved from `GObjects`. World→screen projection uses the `PlayerCameraManager` view (POV location + rotation + FOV) rather than a raw view matrix as on Source.

## Using the Generated SDK in Visual Studio

1. Create an **empty C++ project** (Console App or DLL) in Visual Studio, `x64`.
2. **Import the dumped SDK** — add all generated `.h`/`.cpp` files (or the merged single-header variant) to the project.
3. Use **IDE search / Go-To-Definition** to navigate classes, fields, and engine structures — the SDK is just C++, so IntelliSense gives you the full layout, offsets, and method signatures.
4. Include the SDK headers in your cheat, cast game pointers to the SDK types, and access fields by name (the compiler computes the offsets for you):

```cpp
#include "SDK.hpp"
using namespace SDK;

UWorld* World = *reinterpret_cast<UWorld**>(ModuleBase + GWorld_Offset);
auto* GameInstance = World->OwningGameInstance;
auto* LocalPlayer  = GameInstance->LocalPlayers[0];
auto* PC           = LocalPlayer->PlayerController;
auto* MyPawn       = PC->AcknowledgedPawn;
```

> The SDK assumes you read/write the *target* process. In an injected DLL you can use the pointers directly; from an external reader, replace dereferences with your `ReadProcessMemory` wrapper and use the SDK only as an offset reference.

## Manual RE Workflow (IDA / Ghidra)

When you can't (or won't) inject a dumper:

1. **Resolve the three globals** via the string-xref anchors above.
2. **Read `GNames`** so you can turn any `FName` index into text — this makes every other object self-describing.
3. **Walk `GObjects`** to find `UClass` objects; match `ClassPrivate` on instances to identify actor types without a full SDK.
4. **Discover field offsets with `struct_dump`** (read raw memory, classify pointer/vtable/float/int — see [offset-methodology.md](../../knowledge/offset-methodology.md)). Cross-check candidates against engine-default offsets.
5. **Confirm with a live read** before hardcoding. Pattern-scan the globals; hardcode struct fields only after verifying, and document the source.

Stability rules are the same as everywhere: sigs for anything the linker relocates (the global loads), hardcoded offsets for struct fields within a known class, re-verified each patch.

## Perception AngelScript Helpers for UE

Perception's AngelScript runtime ships read helpers that map directly onto UE types, so you decode engine structures without hand-rolling readers:

- `FString` / `FText` readers (handle the `TArray<wchar>` backing buffer + length)
- `FName` → string resolution against the name pool
- `FVector` / `FRotator` / `FMatrix` / `FQuat` read helpers (matrix + quaternion math for world→screen)
- TArray iteration helpers

See **underscore's** open-source GUI base on the Perception forums for a working UE attachment example (global resolution → local player chain → actor loop → ESP draw). It demonstrates wiring the resolved offsets into the script reader and projecting actor world positions through the camera manager.

```cpp
// Sketch — resolve GWorld, walk to the local pawn (AngelScript-style pseudocode)
uint64 gworld = resolve_rip(p, base, size, SIG_GWORLD);   // sig scan + RIP
uint64 world  = p.ru64(gworld);                           // deref pointer-to-pointer
if (world == 0) return;
uint64 gi     = p.ru64(world + OFF_OWNING_GAME_INSTANCE);
uint64 lp0    = p.ru64(p.ru64(gi + OFF_LOCALPLAYERS) + 0); // LocalPlayers[0]
uint64 pc     = p.ru64(lp0 + OFF_PLAYERCONTROLLER);
uint64 pawn   = p.ru64(pc + OFF_ACKNOWLEDGED_PAWN);
```

## Encryption & Anti-Cheat Considerations

- **Encrypted engines defeat dumpers.** Titles using **Theia** (e.g. *The Finals*, *ARC Raiders*) encrypt `GObjects`/`GNames` and other internals; Dumper-7 will fail or emit garbage. These require a custom decryption routine reversed from the binary (find the decrypt stub, replicate the XOR/rotate/lookup scheme) before the standard methodology applies.
- **`GNames` / `GObjects` index encryption** is common even on otherwise-unprotected games — the index is run through a per-build cipher before pool lookup. If names decode to junk, look for an inline decrypt around the lookup.
- **Anti-cheat (EAC / BattlEye / Theia):** kernel-mode anti-cheats scan for foreign modules, hook integrity, and handle access. Suspending before injection (per Method 1) only dodges naive user-mode heartbeats; kernel AC needs a far more involved approach. **Only operate on systems and engagements you are authorized to test** — see the `authorized-security-research` skill before pointing any of this at a live target.
- **VAC/server-side detection:** behavioral and statistical detection is independent of how you read memory. Out of scope here, but real.

## Common Offset Patterns — Where They Typically Live

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| `GWorld` | Module data section, sig + RIP | None (address) / High (sig) | Pointer-to-pointer; deref once |
| `GObjects` | Module data section, sig + RIP | None / High | `FUObjectArray`, often chunked |
| `GNames` | Module data section, sig + RIP | None / High | `FNamePool`, often chunked/encrypted |
| `UWorld::PersistentLevel` | `+0x0030` (typical) | Medium | Confirm per dump |
| `UWorld::OwningGameInstance` | varies | Medium | Used for local-player chain |
| `ULevel::Actors` (TArray) | varies | Medium | Enemy enumeration source |
| `AActor::RootComponent` | varies | Medium | Location = `RootComponent->RelativeLocation` |
| `APawn::PlayerState` | varies | Medium | Team / name / score |
| `APlayerController::AcknowledgedPawn` | varies | Medium | Our controlled pawn |
| `UObject::ClassPrivate` | `+0x10` (typical) | High | Class identity for filtering |
| `UObject::NamePrivate` (FName) | `+0x18` (typical) | High | Resolve via GNames |
| `FName::ComparisonIndex` | `+0x00` | High | Index into name pool |

**Rules of thumb:**
- The three globals are **pointers in the module image** → pattern-scan + RIP-resolve, never hardcode the address.
- Core `UObject` header offsets (`VTable@0x00`, `ClassPrivate@0x10`, `NamePrivate@0x18`) are the most stable layout in the whole engine.
- Everything below `AActor` is **game-specific** — devs add gameplay fields constantly, so re-derive per build from the SDK dump.
- Engine version drives the *shape* (chunked vs flat `GObjects`/`GNames`, `FName` with/without `Number`). Identify the UE version first (Dumper-7 reports it; or read the engine version string) and pick the matching reader.
