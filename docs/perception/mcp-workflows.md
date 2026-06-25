# Perception MCP Workflows

Use these chains instead of ad-hoc tool calls. Tool params are documented in `mcp-api.md`; tool names are kept in sync in `../../mcp/perception-mcp-config.json`.

## Attach and read typed value

1. `process/reference_by_name` → `$handle`.
2. `process/get_module_by_name` → `$module`.
3. `process/is_valid_address` for the hex address.
4. `process/read_typed_value` with `type: "u32"` / `i32` / `ptr` / etc.
5. `process/dereference`.

Use this for one scalar. Use `process/read_virtual_memory` only for byte ranges/struct blobs.

## Module map

1. `process/reference_by_name`.
2. `process/get_modules`.
3. `process/get_module_sections` for the module you will scan.
4. `process/get_pe_header` if image metadata matters.
5. `process/dereference`.

## String xref to owning function

1. `process/reference_by_name`.
2. `process/get_module_by_name`.
3. `process/find_string_refs` with `encoding: "ascii"` or `"utf16"`, `heap_only: true`, and `string_module` when the string should live in that module.
4. `process/find_function_bounds` on each xref address.
5. `process/disassemble` at the function start.
6. `process/lookup_symbol` for call targets.
7. `process/dereference`.

Do not use `process/find_pattern` for string search.

## Pattern to function

1. `process/reference_by_name`.
2. `process/get_module_by_name`.
3. `process/get_module_sections` and choose `.text`.
4. `process/find_all_patterns` bounded to `.text`.
5. Require one hit unless the evidence log explains why multiple hits are safe.
6. `process/find_function_bounds`.
7. `process/disassemble`.
8. `process/generate_signature` only after the function identity is confirmed.
9. `process/dereference`.

## Pointer-chain validation

1. `process/reference_by_name`.
2. `process/get_module_by_name`.
3. `process/read_pointer_chain` with a verified base and offsets.
4. `process/is_valid_address` on the leaf.
5. `process/read_typed_value` or `process/read_virtual_memory` for the actual field.
6. `process/dereference`.

## Script validate before run

1. pcx knowledge MCP `api_lookup` for uncertain symbols.
2. pcx knowledge MCP `validate_code`.
3. Perception MCP `script/get_context` once per session.
4. Perception MCP `script/validate` for real compiler validation.
5. Use `script/execute` only for one-shot scripts that do not need GUI/thread addons.
