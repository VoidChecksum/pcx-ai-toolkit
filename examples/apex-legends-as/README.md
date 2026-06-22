# Apex Legends — PCX AngelScript Offset Resolver

Verified-compatible PCX AngelScript signature resolver for Apex Legends (`r5apex.exe`).

## What this demonstrates

- Correct use of `proc_t::find_code_pattern` and `proc_t::find_all_code_patterns` (the original LLM output mixed Enma and AS APIs).
- RIP-relative displacement resolution with sign-extended `int32`.
- Unique-sig verification using the real `find_all_code_patterns(uint64, uint64, string, array<uint64>&)` signature.
- Strict adherence to the [PCX AngelScript coding standards](../../.github/copilot-instructions.md).

## Files

| File | Purpose |
|---|---|
| `globals.as` | Process handle, base/size, resolved globals |
| `offsets.as` | Pattern signatures, RIP resolver, `resolve_all()` |
| `main.as` | Entry point: attach, resolve, register callbacks |

## Important

- All struct offsets marked `UNVERIFIED` are placeholders. Confirm them with `struct_dump` or live reads before trusting them in production.
- Replace signatures after every Apex patch (they go stale when code moves).
- The `.text` size is obtained from `proc_t::get_module`, not hardcoded.
