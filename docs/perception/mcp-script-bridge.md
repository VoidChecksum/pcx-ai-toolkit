# MCP Script Bridge

Perception MCP exposes Enma compiler/runtime bridge tools that are stronger than static validation alone.

## `script/get_context`

Call once per MCP session before generating Enma. It returns the full Enma language and Perception API context. Cache it in the agent session; do not call it before every snippet.

## `script/validate`

Compile-only validation. It registers all Perception addons, including GUI, thread, render, proc, cpu, zydis, sound, win, unicorn, net, input, and filesystem.

Use it after pcx knowledge MCP `validate_code`: pcx catches known hallucination patterns cheaply; Perception catches real compiler/type errors.

## `script/execute`

Compiles and runs `main()` once. GUI and thread addons are intentionally not registered because one-shot execution would leak long-lived resources. Use the in-app script editor for overlays, GUI, routines, and threads.

## Recommended LLM pipeline

1. pcx `api_lookup` or MCP `api_lookup` for uncertain symbols.
2. pcx `validate_code` / `validate_answer`.
3. Perception `script/get_context` once.
4. Perception `script/validate`.
5. Only use `script/execute` for a bounded, non-GUI, non-thread one-shot script.

## Error handling

Validation errors are source-level defects. Fix the smallest snippet, rerun pcx validation, then rerun `script/validate`. Do not suppress errors by deleting imports or changing language mode.
