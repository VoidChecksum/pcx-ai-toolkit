# Full Project — AngelScript Scaffold

3-file AngelScript scaffold parallel to `templates/full-project/` (which is the Enma version).

## Files

| File | Purpose |
|---|---|
| `globals.as` | Shared state — `proc_t@` handle, base/size, config, resolved offsets, callback ID |
| `feature.as` | One example feature combining update + render in a single tick callback |
| `main.as`    | Entry — attach, resolve offsets, register the tick callback. `on_unload` cleans up. |

## Differences From the Enma Scaffold

See `skill://pcx-angelscript-discipline` for the full discipline. Highlights:

- **Handles, not values.** `proc_t@` (handle) instead of Enma's `proc_t` (value). Null-check with `is null`; release with `.deref()` in `on_unload()`.
- **No `import`.** AngelScript doesn't have Enma's `import "module"` statement. At compile time the script is one unit; the multi-file split is for the human reader. If your AS host bundles multiple files into one script context, follow its convention.
- **`register_callback`, not `register_routine`.** Different signature for the callback itself: `void on_X(int id, int data_index)`. Interval is milliseconds.
- **`log(...)`, not `println(...)`.**
- **Raw RGBA ints in draw calls.** `draw_rect_filled(x, y, w, h, r, g, b, a, rounding, RR_*)` — no `color` struct.
- **`int main()` returns `int`,** not `int64`. `1` = stay loaded, `0` = unload.
- **`f` suffix on float32 literals** (`1.5f`, not `1.5`). Same as Enma rule #8.
- **`array<T>`,** not `T[]`. Methods are `insertLast` / `removeLast` / `length`.

## What's NOT in This Scaffold

To keep the scaffold tight, the following are intentionally not included — add them as the project grows:

- A `menu.as` with GUI widgets (depends on the AS GUI API surface of your PCX build; see `docs/perception/angelscript/gui-api.md`).
- A per-binary `offsets.as` if you do multi-binary targeting (see `skill://multi-binary-targeting`).
- An `evidence/<hash>.md` per binary (see `skill://re-evidence-log`).

## Discipline

This scaffold honors the 12 `game-cheat-guidelines`:

- ✓ #1 Ground every offset — sigs use `// UNVERIFIED` markers, ready for evidence-citation
- ✓ #2 `uint64` for all addresses
- ✓ #3 Null-check every pointer chain link
- ✓ #4 Update / render discipline (combined in one tick callback per AS norms, but reads happen first, draws second, never interleaved)
- ✓ #5 Sigs over hardcodes
- ✓ #6 One feature per file
- ✓ #7 Construct primitives per frame (raw RGBA ints inline in draw calls)
- ✓ #8 `f` suffix on float32 literals
- ✓ #9 Minimize memory writes (this scaffold has none)
- ✓ #11 GUI for every tunable (`g_color_*`, `g_max_distance`, `g_enabled` — wire to widgets when you add `menu.as`)
- ✓ #12 Verify against the live binary (`// UNVERIFIED` markers everywhere offsets/sigs are placeholders)

## Cross-References

- `templates/full-project/` — the Enma version
- `skill://pcx-angelscript-discipline` — the 10 AS-specific rules
- `skill://game-cheat-guidelines` — the underlying 12 rules
- `docs/perception/llm-routing.md` — when to pick AS vs Enma and how not to mix bindings
- `docs/perception/angelscript/` — the AS API surface
