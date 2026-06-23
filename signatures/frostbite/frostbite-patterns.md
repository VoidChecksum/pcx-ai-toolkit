# Frostbite Reversal Patterns

Frostbite titles vary heavily by generation and game branch. Use type info,
manager singletons, and data-driven entity systems instead of one-size offsets.

> Treat these as research anchors. EAAC-protected live targets require strict
> authorization and read-only workflows.

## Primary Targets

| Target | Purpose | Verification |
|--------|---------|--------------|
| TypeInfo / class registry | Runtime type names and layouts | Names match dumped SDK/classes |
| ClientGameContext | Player/entity root | Local player pointer resolves during match |
| GameRenderer | View/projection matrices | Matrix tracks camera movement |
| EntityManager | Entity iteration | Entity count and class names are plausible |

## Pattern Seeds

```json
[
  {
    "name": "client_game_context",
    "pattern": "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 48 8B 01 FF 50 ??",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate singleton load; verify by local player chain"
  },
  {
    "name": "game_renderer",
    "pattern": "48 8B 05 ?? ?? ?? ?? 48 8B 88 ?? ?? ?? ?? 48 85 C9",
    "kind": "rip",
    "rip_offset": 3,
    "insn_len": 7,
    "note": "candidate renderer load; verify view/projection fields"
  }
]
```

## PCX Workflow

- Build a per-build evidence log before script creation.
- Use `tools/binary-diff-summary.py` before deciding whether old signatures are reusable.
- Run `tools/offset-diff.py` on confirmed signatures after every patch.
