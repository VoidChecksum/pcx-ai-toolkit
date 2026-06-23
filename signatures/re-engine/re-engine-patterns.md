# RE Engine Reversal Patterns

Capcom RE Engine titles use a reflected `via.*` runtime type system. Prefer
runtime metadata and known plugin ecosystems over hardcoded one-build offsets.

> These are workflow patterns, not copy-paste offsets. Verify every pattern per
> target build and cite evidence IDs before shipping.

## Primary Targets

| Target | Purpose | Verification |
|--------|---------|--------------|
| `via.TypeInfo` table | Reflected class and field metadata | Cross-check names against REFramework/TDB output |
| `via.SceneManager` | Scene graph and game object traversal | Validate object counts in a paused scene |
| `via.Camera` / view globals | World-to-screen inputs | Compare matrix against visible camera movement |
| `via.Transform` | Position/rotation/scale | Live read a known actor and move it |

## Workflow

1. Identify the exact game build and hash `.text`.
2. Dump or load `TDB` metadata with REFramework-compatible tooling.
3. Resolve class/field names from metadata before writing PCX offsets.
4. Use `tools/re-importer.py --format reclass-json` for struct seeds.
5. Add `E-NNN` citations for every class field used by an Enma/AS script.

## Pattern Seeds

```json
[
  {
    "name": "via_typeinfo_registry",
    "pattern": "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 48 8B 01 FF 50 ??",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate TypeInfo registry load; verify by walking reflected names"
  },
  {
    "name": "scene_manager_singleton",
    "pattern": "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 88 ?? ?? ?? ??",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate singleton load; confirm by scene object enumeration"
  }
]
```

## PCX Notes

- Keep reflected field names in comments next to generated constants.
- Prefer metadata-derived offsets over pointer-chain folklore.
- Treat plugin exports and community SDKs as evidence candidates, not authority.
