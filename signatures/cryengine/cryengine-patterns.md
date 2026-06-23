# CryEngine / Lumberyard / O3DE Reversal Patterns

CryEngine-family games usually expose high-value roots around `gEnv`, entity
system accessors, renderer globals, and camera matrices.

> These signatures are seeds. Rebuild and uniqueness-check them per game patch.

## Primary Targets

| Target | Purpose | Verification |
|--------|---------|--------------|
| `gEnv` | Root environment pointer | Dereference subsystems and validate vtables |
| `IEntitySystem` | Entity iteration | Entity count matches visible/session state |
| `IRenderer` / camera | View/projection data | Matrix changes with camera movement |
| `ISystem` | Engine services | Stable vtable and subsystem links |

## Pattern Seeds

```json
[
  {
    "name": "gEnv_global",
    "pattern": "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 48 8B 01 FF 50 ??",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate gEnv load near subsystem virtual call"
  },
  {
    "name": "entity_system_from_env",
    "pattern": "48 8B 81 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 10",
    "kind": "direct",
    "note": "candidate gEnv->pEntitySystem field access; derive field offset from displacement"
  }
]
```

## PCX Workflow

1. Use `module-export-mapper.py` to find engine module exports first.
2. Use string/xref anchors such as entity class names or console variables.
3. Convert confirmed roots into `offsets.em` / `offsets.as`.
4. Validate with `pcx verify-project --allow-unverified` while still scaffolding.
