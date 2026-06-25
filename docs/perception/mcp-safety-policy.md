# Perception MCP Safety Policy

These rules apply to any agent using Perception runtime MCP.

## Write tools

Write tools are `process/write_virtual_memory`, `process/write_typed_value`, `process/write_string`, `process/copy_memory`, and `process/fill_memory`.

Rules:
- Never call write tools unless the user explicitly asks for a write/patch.
- Always read and log old bytes before writing.
- Always provide rollback bytes.
- Always validate the address and module ownership before writing.
- Never patch based only on a pattern hit; confirm function identity first.

## Allocation tools

`process/allocate_memory` and `process/free_memory` require `virtual_memory_operations`.

Rules:
- Never allocate executable memory without explicit authorization.
- Free allocations when done.
- Prefer read-only analysis and Enma script validation first.

## Kernel-gated tools

`kernel_rw_access` gates kernel addresses, driver listing, eprocess/ethread fields, and kernel-range reads/disassembly/scans.

Rules:
- Never use kernel-gated tools unless the user confirms scope and permission.
- Treat permission denial as a stop condition, not a retry loop.

## Scan bounds

- Use `heap_only: true` unless full user-space scan is explicitly needed.
- Bound `find_pattern` to a module section, usually `.text`.
- Do not run repeated scan loops without a cap and a reason.
