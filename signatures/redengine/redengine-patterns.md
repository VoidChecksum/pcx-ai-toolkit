# REDengine Reversal Patterns

REDengine games expose useful anchors through RTTI, REDscript/CET ecosystems,
entity/component roots, and renderer/camera state.

> Do not hardcode community offsets without local proof. Use them as import
> candidates and cite live or binary evidence.

## Primary Targets

| Target | Purpose | Verification |
|--------|---------|--------------|
| RTTI/type registry | Class and component names | Names match RED4ext/CET dumps |
| World / entity roots | Entity traversal | Known player/NPC pointers resolve |
| Camera manager | W2S matrix inputs | Matrix follows camera movement |
| Script VM roots | REDscript object relations | Cross-check with known script symbols |

## Pattern Seeds

```json
[
  {
    "name": "rtti_registry",
    "pattern": "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 48 8B 01 FF 50 ??",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate runtime type registry reference"
  },
  {
    "name": "camera_manager",
    "pattern": "48 8B 05 ?? ?? ?? ?? F3 0F 10 88 ?? ?? ?? ??",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate camera/global load; verify with view changes"
  }
]
```

## Import Path

Use `tools/re-importer.py --format ida-names --out-format enma-offsets` on named
exports or labels from IDA/Ghidra/Binary Ninja, then replace every UNVERIFIED
claim with evidence-backed `E-NNN` comments.
