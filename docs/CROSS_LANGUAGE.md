# Enma vs AngelScript Binding Reference

Side-by-side mapping of common Perception.cx scripting patterns across the two
supported languages in this toolkit: Enma (`.em`) and AngelScript (`.as`).

Use this when porting code, reviewing LLM output, or checking that an answer did
not mix bindings.

## Lifecycle

| Operation | Enma (`.em`) | AngelScript (`.as`) |
|---|---|---|
| Entry point | `int64 main()` | `int main()` |
| Repeating work | `register_routine(cast<int64>(fn), data)` | `register_callback(fn, interval_ms, data_index)` |
| Callback shape | `void fn(int64 data)` | `void fn(int id, int data_index)` |
| Cleanup | RAII destructors; no callback unregister needed | `on_unload()`, `unregister_callback`, `deref()` |
| Logging | `println(...)` | `log(...)` |

## Process Handles

| Operation | Enma (`.em`) | AngelScript (`.as`) |
|---|---|---|
| Open process | `proc_t p = ref_process("game.exe");` | `proc_t@ p = ref_process("game.exe");` |
| Null/alive check | `if (!p.alive()) return 0;` | `if (p is null || !p.alive()) return 0;` |
| Base address | `p.base_address()` | `p.base_address()` |
| Module size | `p.get_module_size(name)` | `p.get_module(name, base, size)` |
| Release | automatic | `p.deref()` |

## Memory Reads And Pattern Scans

| Operation | Enma (`.em`) | AngelScript (`.as`) |
|---|---|---|
| 8-bit unsigned | `p.ru8(addr)` | `p.ru8(addr)` |
| 32-bit unsigned | `p.ru32(addr)` | `p.ru32(addr)` |
| 64-bit unsigned | `p.ru64(addr)` | `p.ru64(addr)` |
| 32-bit float | `p.rf32(addr)` | `p.rf32(addr)` |
| Pattern scan | `p.find_code_pattern(base, size, sig)` | `p.find_code_pattern(base, size, sig)` |
| Find all patterns | `p.find_all_code_patterns(base, size, sig, results)` | `p.find_all_code_patterns(base, size, sig, results)` |

Use `uint64` for addresses in both languages.

## Render API Shape

| Primitive | Enma (`.em`) | AngelScript (`.as`) |
|---|---|---|
| Viewport | `get_view_width()` / `get_view_height()` | `get_view(width, height)` out-params |
| Position | `vec2(x, y)` value | raw `x, y` parameters unless the AS page says otherwise |
| Color | `color(r, g, b, a)` value | raw RGBA integer parameters unless the AS page says otherwise |
| Text | `draw_text(text, vec2(...), color(...), font, effect, color(...), amount)` | `draw_text(text, x, y, r, g, b, a, font, effect, er, eg, eb, ea, amount)` |
| Font handle | `get_font20()` | `get_font20()` |

Do not port render calls by only renaming variables. Enma and AngelScript often
use different argument shapes for the same conceptual operation.

## Containers And Types

| Concept | Enma (`.em`) | AngelScript (`.as`) |
|---|---|---|
| Array | `T[]`, `.push()`, `.pop()`, `.length` property | `array<T>`, `.insertLast()`, `.removeLast()`, `.length()` |
| Map | `map<K,V>` / `imap<V>` | `dictionary` |
| String | `string` | `string` |
| Float | `float64`, `float32` | `double`, `float` |
| Pointer/handle style | value types and RAII | `@` handles and explicit cleanup |

## AI Review Checklist

Before accepting generated code:

1. Confirm the file extension and target language.
2. Verify every host API with `pcx api <symbol> --lang enma|angelscript` or MCP
   `api_lookup`.
3. Run `pcx symbol-check <file.em|file.as>` or MCP `validate_code`.
4. Reject Enma code containing `register_callback`, `log`, `get_view(...)`, `@`,
   `is null`, or `deref()`.
5. Reject AngelScript code containing `register_routine`, `println`,
   `get_view_width()`, `get_view_height()`, Enma `vec2/color` render call shapes,
   or `map<K,V>`.

If an API shape is not proven by the target language docs, do not guess.
