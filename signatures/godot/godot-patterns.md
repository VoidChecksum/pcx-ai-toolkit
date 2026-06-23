# Godot Reversal Patterns

Godot is open source, so the best signature is often a version-matched symbol,
source file, or structure definition. Reverse only what you cannot prove from
the matching engine source and exported project data.

## Primary Targets

| Target | Purpose | Verification |
|--------|---------|--------------|
| `ObjectDB` | Live object registry | Object count and class names match scene |
| `SceneTree` | Node traversal | Root viewport and child nodes resolve |
| `Camera2D` / `Camera3D` | World-to-screen data | Transform follows camera movement |
| `.pck` manifest | Assets/scripts | Hash against extracted package |

## Pattern Seeds

```json
[
  {
    "name": "objectdb_instance",
    "pattern": "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 48 8B 01",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate ObjectDB singleton; validate by object count"
  },
  {
    "name": "scene_tree_singleton",
    "pattern": "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 88 ?? ?? ?? ??",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate SceneTree/root viewport path"
  }
]
```

## PCX Workflow

1. Identify Godot major/minor from strings or package metadata.
2. Pull matching Godot headers/source for struct names.
3. Extract `.pck` with a trusted local tool and map script names to runtime objects.
4. Use PCX scripts only after the source-level layout and live reads agree.
