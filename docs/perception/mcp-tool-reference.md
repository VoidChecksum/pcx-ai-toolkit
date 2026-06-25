# Perception MCP Tool Reference

Generated companion to `mcp-api.md`. JSON schema: `mcp-tool-schemas.json`; examples: `../../mcp/perception-mcp-examples.json`.

Tools covered: 59.

## Categories
- `lifecycle`: 9 tools
- `memory_code_analysis`: 22 tools
- `module_pe`: 11 tools
- `process`: 3 tools
- `scan_xref_signature`: 9 tools
- `script_bridge`: 3 tools
- `system`: 2 tools

## No-handle tools
- `process/list`
- `process/info_by_pid`
- `process/info_by_name`
- `process/reference_by_pid`
- `process/reference_by_name`
- `process/dereference`
- `process/cleanup_references`
- `process/list_references`
- `system/info`
- `system/list_drivers`
- `script/get_context`
- `script/validate`
- `script/execute`

## Permission-gated tools
- `process/write_virtual_memory`: write_memory
- `process/write_typed_value`: write_memory
- `process/write_string`: write_memory
- `process/copy_memory`: write_memory
- `process/fill_memory`: write_memory
- `process/allocate_memory`: virtual_memory_operations
- `process/free_memory`: virtual_memory_operations
- `system/list_drivers`: kernel_rw_access

## Expensive tools
Avoid these in loops; bound the search region.
- `process/enumerate_memory_regions`
- `process/find_pattern`
- `process/find_all_patterns`
- `process/scan_value`
- `process/scan_next`
- `process/scan_string`
- `process/scan_pointer_to`
- `process/find_xrefs`
- `process/find_string_refs`
- `process/diff_memory`
- `process/find_function_bounds`
- `process/find_function_by_signature`
- `process/find_function_by_name`

## All tools
- `process/list` (lifecycle, handle=False, cost=medium)
- `process/info_by_pid` (lifecycle, handle=False, cost=cheap)
- `process/info_by_name` (lifecycle, handle=False, cost=cheap)
- `process/reference_by_pid` (lifecycle, handle=False, cost=cheap)
- `process/reference_by_name` (lifecycle, handle=False, cost=cheap)
- `process/dereference` (lifecycle, handle=False, cost=cheap)
- `process/cleanup_references` (lifecycle, handle=False, cost=cheap)
- `process/list_references` (lifecycle, handle=False, cost=cheap)
- `process/read_virtual_memory` (memory_code_analysis, handle=True, cost=medium)
- `process/write_virtual_memory` (memory_code_analysis, handle=True, cost=medium)
- `process/is_valid_address` (memory_code_analysis, handle=True, cost=cheap)
- `process/read_typed_value` (memory_code_analysis, handle=True, cost=cheap)
- `process/write_typed_value` (memory_code_analysis, handle=True, cost=cheap)
- `process/read_string` (memory_code_analysis, handle=True, cost=medium)
- `process/write_string` (memory_code_analysis, handle=True, cost=medium)
- `process/copy_memory` (memory_code_analysis, handle=True, cost=medium)
- `process/fill_memory` (memory_code_analysis, handle=True, cost=medium)
- `process/read_pointer_chain` (memory_code_analysis, handle=True, cost=medium)
- `process/disassemble` (memory_code_analysis, handle=True, cost=medium)
- `process/get_modules` (module_pe, handle=True, cost=medium)
- `process/get_threads` (process, handle=True, cost=medium)
- `process/get_module_by_name` (module_pe, handle=True, cost=medium)
- `process/get_export_address` (module_pe, handle=True, cost=medium)
- `process/get_import_address` (module_pe, handle=True, cost=medium)
- `process/get_module_imports` (module_pe, handle=True, cost=medium)
- `process/list_module_exports` (module_pe, handle=True, cost=medium)
- `process/get_module_sections` (module_pe, handle=True, cost=medium)
- `process/get_pe_header` (module_pe, handle=True, cost=medium)
- `process/get_module_strings` (module_pe, handle=True, cost=medium)
- `process/get_exception_table` (module_pe, handle=True, cost=medium)
- `process/get_data_directory` (module_pe, handle=True, cost=medium)
- `process/query_memory_region` (memory_code_analysis, handle=True, cost=medium)
- `process/enumerate_memory_regions` (memory_code_analysis, handle=True, cost=high)
- `process/allocate_memory` (memory_code_analysis, handle=True, cost=medium)
- `process/free_memory` (memory_code_analysis, handle=True, cost=medium)
- `process/find_pattern` (scan_xref_signature, handle=True, cost=high)
- `process/find_all_patterns` (scan_xref_signature, handle=True, cost=high)
- `process/scan_value` (scan_xref_signature, handle=True, cost=high)
- `process/scan_next` (scan_xref_signature, handle=True, cost=high)
- `process/scan_string` (scan_xref_signature, handle=True, cost=high)
- `process/scan_pointer_to` (scan_xref_signature, handle=True, cost=high)
- `process/find_xrefs` (scan_xref_signature, handle=True, cost=high)
- `process/find_string_refs` (memory_code_analysis, handle=True, cost=high)
- `process/generate_signature` (scan_xref_signature, handle=True, cost=medium)
- `process/diff_memory` (memory_code_analysis, handle=True, cost=high)
- `process/find_function_bounds` (memory_code_analysis, handle=True, cost=high)
- `process/find_function_by_signature` (scan_xref_signature, handle=True, cost=high)
- `process/analyze_vtable` (memory_code_analysis, handle=True, cost=medium)
- `process/read_rtti` (memory_code_analysis, handle=True, cost=medium)
- `process/lookup_symbol` (memory_code_analysis, handle=True, cost=medium)
- `process/find_function_by_name` (memory_code_analysis, handle=True, cost=high)
- `process/enum_handles` (process, handle=True, cost=medium)
- `system/info` (system, handle=False, cost=cheap)
- `system/list_drivers` (system, handle=False, cost=medium)
- `process/get_command_line` (process, handle=True, cost=medium)
- `process/list_environment` (lifecycle, handle=True, cost=medium)
- `script/get_context` (script_bridge, handle=False, cost=medium)
- `script/validate` (script_bridge, handle=False, cost=medium)
- `script/execute` (script_bridge, handle=False, cost=medium)
