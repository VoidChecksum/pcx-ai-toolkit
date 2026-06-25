# Unreal MCP Workflow

    Use with [Two-MCP Workflow](../../docs/perception/two-mcp-workflow.md) and [Perception MCP Workflows](../../docs/perception/mcp-workflows.md). Treat every offset as build-local until live evidence confirms it.

    ## Target modules
    - `Game-Win64-Shipping.exe`
- `UE4Game-Win64-Shipping.exe`
- `UnrealEditor-*.exe`

    ## Best first strings
    - `UWorld`
- `GNames`
- `GObjects`
- `ProcessEvent`
- `BeginPlay`
- `PersistentLevel`

    ## RTTI/reflection strategy
    Use reflected UObject/GName paths before raw pattern scanning; vtables confirm class ownership. Start with reflection/name systems, then prove code ownership through xrefs, function bounds, disassembly, and a unique signature.

    ## Recommended Perception MCP tool chain
    1. `process/reference_by_name`
    2. `process/get_module_by_name`
    3. `process/list_module_exports` or `process/find_string_refs`
    4. `process/find_xrefs`
    5. `process/find_function_bounds`
    6. `process/disassemble`
    7. `process/generate_signature`
    8. `process/dereference`

    ## Known false leads
    - Old public dumps without a matching build hash.
    - Strings with many xrefs and no unique owning function.
    - Heap-only values treated as static module globals.
    - One successful read without pointer-chain or structure validation.

    ## Signature strategy
    Generate signatures from stable function prolog/control-flow bytes, not immediates, RIP targets, or patch-day addresses. Re-run `process/find_all_patterns` and require one hit in the owning module `.text` range.

    ## Evidence-log fields
    - target process and module
    - module hash/build
    - anchor string/export/type name
    - xref address
    - function bounds
    - generated signature and hit count
    - live validation read
    - negative candidates rejected

    ## Patch-day revalidation workflow
    1. Re-acquire handle with `process/reference_by_name`.
    2. Re-read module map and hash.
    3. Re-run signature search in `.text`.
    4. Recompute RIP targets/pointer chains.
    5. Re-run live validation and update evidence IDs.

    ## Sample plan prompt
    ```bash
    pcx mcp-plan "unreal find owner for UWorld" --target game.exe
    ```
