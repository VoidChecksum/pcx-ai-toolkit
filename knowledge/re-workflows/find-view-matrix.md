# Find View Matrix

## Claim
Prove the address or offset for `view/projection matrix` for this exact build.

## Required evidence
- module version/hash, camera/render string, matrix-shaped read, world-to-screen sanity check, stale camera candidates rejected
- evidence IDs: `E-001` anchor, `E-002` xref/signature, `E-003` live validation
- claim ID: `C-001`

## Perception MCP workflow
1. `process/reference_by_name`
2. `process/get_module_by_name`
3. `process/find_string_refs` or `process/find_all_patterns`
4. `process/find_function_bounds`
5. `process/disassemble`
6. `process/read_pointer_chain` or `process/read_typed_value`
7. `process/is_valid_address`
8. `process/dereference`

## Done when
- signature hits once in the expected module `.text` range
- RIP target or pointer-chain leaf resolves correctly
- live memory matches expected structure/type/range
- at least one plausible negative candidate is ruled out
- evidence graph links `C-001` to all evidence IDs
- handle cleanup is recorded
