# Godot Reverse Engineering Reference

Engine-specific notes for Godot Engine titles (Godot 3.x C++ core, Godot 4.x rewritten core with Vulkan and dual GDScript/C# support). Read this before attaching to a Godot title — the node-tree architecture, the `ObjectDB` indirection, and the embedded-script `.pck` payload differ enough from Unreal/Unity/Source that the generic dumper workflow does not apply. This fills the gap left by the other engine references (CryEngine, Frostbite, RE Engine, REDengine, Source, Unreal, Unity).

> **Read this before** doing memory analysis on any Godot title. Godot is open-source — pull the matching engine version from `github.com/godotengine/godot` and grep the actual headers; this is a fundamental RE advantage no closed-source engine offers.

> **Scope:** Educational reference. See `skill://authorized-security-research` before pointing any offensive tool at a live multiplayer build.

---

## Engine Overview

Godot ships as a single self-contained executable that embeds the GDScript bytecode, scenes, and resources inside a PCK archive appended to (or alongside) the engine binary. The user runs `MyGame.exe`; the engine code, the game's compiled scripts, and the assets all live in or beside that one file.

Two distinct lineages:

- **Godot 3.x** — C++ core, GLES2/GLES3 renderer, GDScript 1.0. Long-tail of shipped titles. Smaller binary, simpler RE target.
- **Godot 4.x** — rewritten core, Vulkan/D3D12/Metal renderers, GDScript 2.0 (typed, partially compiled), first-class C# (Mono) support. Larger binary, more API surface, the current default for new projects.

Both share architectural primitives:

- **Node tree** — every game-world object is a `Node`; the running game is a `SceneTree` whose root node has the current scene attached. Almost every gameplay query starts at `SceneTree::get_root()` and walks children.
- **Object / RefCounted / Resource** — three lifetime models. `Object` is manually managed; `RefCounted` (Godot 4) / `Reference` (Godot 3) is refcounted; `Resource` is refcounted + serializable. Knowing which one a class inherits from tells you how to keep a pointer alive across frames.
- **ObjectDB** — every `Object` registers in a global hash table keyed by a 64-bit `ObjectID`. To find any object from outside the engine, you walk this table. `ObjectDB::instances` is the global symbol.
- **RID system** — the rendering server, physics server, and audio server allocate opaque `RID` handles (64-bit integers) for GPU resources, physics bodies, etc. The mapping from `RID` → underlying allocation is per-server.
- **Singletons** — `Engine`, `OS`, `SceneTree`, `RenderingServer`, `PhysicsServer3D`, `Input`, `ResourceLoader`. Each is accessible via `get_singleton()` and is the entry point to its subsystem.

---

## Games Using This Engine

| Game | Godot Version | Notes | Anti-Cheat |
|---|---|---|---|
| Brotato | 4.x | Bullet-heaven roguelite; widely studied for mods | None (single-player) |
| Cassette Beasts | 4.x | Open-world monster-collector | None (single-player) |
| Halls of Torment | 4.x | Diablo-meets-Vampire-Survivors | None (single-player) |
| Endoparasitic | 4.x | Single-player horror; small surface | None |
| Buckshot Roulette | 4.x | Single-player; later online expansion via separate mod | None on the base game |
| Slay the Princess | 4.x | Visual-novel hybrid | None |
| Dome Keeper | 3.x | Tower-defense hybrid | None (mostly single-player) |
| The Case of the Golden Idol | 3.x | Detective puzzle | None |
| Cruelty Squad | 3.x | First-person shooter | None |
| Cassette Beasts: Pier of the Unknown | 4.x | DLC | None |

The export-template trick: when Godot builds a release, it appends the project's compiled `.pck` (containing every script, scene, image, sound) to the end of the engine executable. The footer carries a magic header `GDPC`, a version byte, and an index. Any change to scripts changes the binary hash — a soft tamper-detect that some titles cross-reference against an online manifest.

Multiplayer Godot titles are rare and almost always lean on authoritative server logic or third-party validation; client-side enforcement is the exception.

---

## Memory Layout Patterns

The patterns to find first when attaching to a Godot binary:

- **`OS::get_singleton()`** — the OS singleton is the gateway to almost everything. Its static slot is referenced by literally every singleton accessor; find the slot, you've found a Rosetta Stone.
- **`SceneTree` root** — accessible via `OS::get_singleton()->get_main_loop()` (returns a `MainLoop*` which is the `SceneTree*` in a running game). From the root, walk children to find the active scene, then game-specific nodes by their assigned name strings (`Player`, `Enemy`, etc.).
- **`ObjectDB::instances` hash table** — a flat hash map of `ObjectID` → `Object*`. The table size is power-of-two; entries are tombstone-deletable. To enumerate every live object: walk the table, skip tombstones, deref the `Object*`. Then read `Object::_class_name` (a string ID) to figure out what each one is.
- **`ClassDB` registered classes** — the class-registration table is built at startup and never grows after engine init. A pointer scan for the string `"Object"` lands you in or near the `ClassDB` entry table; from there, walk to find every registered class name, its parent, its method table.
- **Active camera** — `RenderingServer` holds the active camera RID; resolve via `RenderingServer::camera_get_*` accessors. The camera's transform is a `Transform3D` (a 4x3 affine: 3x3 basis + 3-component origin), NOT a 4x4 view matrix — derive the view matrix yourself or use the inverse of the camera transform.
- **GDScript bytecode** — instances of `GDScript` (a `Resource`) carry their compiled bytecode in a flat `Vector<uint8_t>`. The instruction format is in `core/object/script_language.h` + `modules/gdscript/gdscript.h` upstream. For reversal of game logic, decompiling the bytecode (see Community Tools below) is faster than reading the running VM state.

Coordinate convention: Godot 4 uses **Y-up, right-handed** by default. Godot 3 also Y-up. Most games keep the default, but check the project settings (embedded in the PCK) before assuming.

---

## Common Sigs and RIP Patterns

Illustrative byte-pattern *shapes* to look for. Do not commit to specific byte sequences — they change between Godot versions and compiler builds. The shape is stable; the bytes are not.

- **Singleton accessor pattern** — `MOV rax, [rip+disp32]; TEST rax, rax; JNZ ...; CALL _init; MOV [rip+disp32], rax`. This is the lazy-init pattern for `OS::get_singleton()`, `Engine::get_singleton()`, etc. The first `MOV` reads the static slot; the slot address is what you want.
- **`ObjectDB::instances` access** — `LEA rcx, [rip+disp32]` where `rip+disp32` is the static instances-table address; followed by a hash-and-probe loop. Find the `ClassDB` init function for a reliable xref into this region.
- **`SceneTree::process` tick** — the main game loop calls `SceneTree::process(float delta)` every frame. This is one of the longer functions in the binary and contains string references to "process", "_process", "physics_process". String xref → function → top of frame.
- **GDScript VM dispatch** — a giant switch / computed-goto on opcode bytes. The dispatcher reads from the `GDScript`'s bytecode `Vector<uint8_t>`; the opcode table size matches `GDScriptFunction::Opcode` enum in the upstream source.

Always cross-reference candidate sigs against the open-source headers from the matching Godot release tag. If a sig matches no instruction the upstream source describes, you've either got the version wrong or the title has a modified engine fork.

---

## Reversal Workflow

The recommended first 60 minutes on a fresh Godot binary:

1. **Identify the version.** The engine writes a `"Godot Engine v<X.Y.Z>"` string at startup. ASCII string scan in `.rdata` finds it instantly. Note both major.minor (e.g. `4.2`) and the patch (e.g. `4.2.1.stable`).
2. **Pull the matching headers.** `git clone github.com/godotengine/godot && git checkout <X.Y.Z>-stable`. You now have the actual `Object`, `Node`, `SceneTree`, `RenderingServer`, `GDScriptFunction` definitions the binary was compiled from. This is the open-source RE advantage; use it before anything else.
3. **Locate `OS::get_singleton()`.** String xref on `"OS"` won't help (too many matches); instead, find a known accessor like `MainLoop *OS::get_main_loop()` by its symbol name in the GitHub source, find its call sites, and the slot it reads is `OS::singleton`.
4. **Enumerate `ClassDB`.** Once you have `OS`, the `ClassDB::class_list` member is reachable; walk it and dump the per-class name + parent + method table. This gives you a full class hierarchy as a starting map.
5. **Find `SceneTree::get_root()`.** From `OS::get_main_loop()`, follow to `SceneTree`; the `root` field is a `Window*` (Godot 4) or `Viewport*` (Godot 3). Walk children from there into game-specific scene structure.
6. **Locate the active camera.** Either via `RenderingServer::camera_get_current()` or by walking the scene tree looking for the `Camera3D` node. Once found, the view matrix (or its derivation) is yours.
7. **Identify gameplay nodes by string.** Most games name their player node literally `"Player"` and enemies `"Enemy"` or specific subclasses. Walk the scene tree, match by name, then read the relevant `_class_name` to know what struct to read against.

The `.pck` payload is its own RE target: use a `.pck` extractor (see Community Tools) to pull out every script, scene, and resource as readable files. For Godot 3, scripts decompile cleanly; for Godot 4, the bytecode is more compressed and decompilers may produce partial output.

---

## Anti-Cheat Considerations

Most Godot titles ship no anti-cheat. The indie norm. When AC is present, it's typically:

- **Steam-side**: VAC for Steam-released multiplayer titles. Detection is server-coordinated; the client has no AC driver.
- **Server-authoritative**: the server holds the authoritative state; client memory tampering does not affect the actual game outcome. Slay The Spire / Vampire Survivors style.
- **Soft-tamper-detect via PCK hash**: the engine checks if the embedded `.pck` has been modified; some titles cross-reference against an online manifest. Cosmetic, not enforced.

The export-template-modification path (changing the engine binary itself, repacking the `.pck`) is the most common modding path and is sometimes blocked by manifest checks. Memory-resident-only changes leave no trace on disk and are not caught by hash checks.

Cross-reference `knowledge/anti-cheat-architecture.md` for the AC ecosystem at large; Godot titles rarely appear there because they rarely ship kernel-level AC.

---

## Community Tools and Resources

Categories (no live URLs — search the named project):

- **gdsdecomp** — community GDScript bytecode decompiler; works well on Godot 3, partial on Godot 4. The standard tool for recovering script source from a compiled PCK.
- **godot-pck-explorer** — extract files from an embedded or standalone `.pck` archive (file-listing, single-file extract, full unpack).
- **Godot RE Tools (GodotREEngine)** — combined PCK extraction + GDScript decompilation in one project.
- **godot-cpp / GDExtension** — the official native-extension SDK. Useful for RE both as a *reference implementation* (how does the engine call into native code?) and as a *target* for writing your own integration (an in-game injected DLL that talks to the running engine).
- **Open-source upstream** — the largest resource. `github.com/godotengine/godot` tagged by version. Search the headers for any struct/function name you're reversing; the actual implementation is usually a few clicks away.
- **Godot debugger protocol** — Godot 4 supports remote debugging over TCP on port 6007 by default; the protocol is documented in the engine source. A live game launched with `--debug --remote-debug tcp://...` exposes the script-VM state for inspection.

---

## Cross-References

- `skill://anti-cheat-re` — kernel AC methodology (rarely needed for Godot titles, included for completeness)
- `skill://pcx-re-discipline` — RE discipline that applies to any binary
- `knowledge/anti-cheat-architecture.md` — broader AC reference (Godot rarely appears here)
- `knowledge/common-patterns.md` — Enma scripting patterns once you have the offsets you need
- `knowledge/offset-methodology.md` — sig derivation and validation
- `signatures/` — sig collections for other engines (no Godot subdirectory; the open-source headers serve that role)
