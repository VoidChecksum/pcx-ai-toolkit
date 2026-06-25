# MCP Transcript: String Xref

User: Find code that references `PlayerHealth`.

Assistant:
1. Acquire handle with `process/reference_by_name`.
2. Resolve the module with `process/get_module_by_name`.
3. Search references with `process/find_string_refs`, not `find_pattern`. Use `encoding: "ascii"`; switch to `"utf16"` if no hits and UI strings are wide.
4. For each xref, call `process/find_function_bounds`.
5. Disassemble the function with `process/disassemble`.
6. Use `process/lookup_symbol` on call targets when naming imports/exports.
7. Release handle with `process/dereference`.

Failure flow: if `-32002`, reacquire handle once. If results are truncated, narrow with `string_module` or module-specific search.
