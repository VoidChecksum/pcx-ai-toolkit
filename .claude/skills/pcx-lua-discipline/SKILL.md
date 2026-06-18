---
name: pcx-lua-discipline
description: >
  Lua-specific rules for writing Perception.cx scripts in Lua 5.4.6.
  Prevents Enma-reflex errors (typed addresses, C truthiness, struct value
  types, register_routine) in the Lua scripting surface. Always active when
  editing .lua PCX scripts — applies on top of game-cheat-guidelines.
license: MIT
---

# PCX Lua Discipline — Lua Idioms for Perception.cx Scripts

Lua-specific rules for writing Perception.cx scripts in **Lua 5.4.6** (confirmed in `docs/perception/lua/render-api.md`). PCX exposes a third scripting surface alongside Enma and AngelScript; the host APIs are nearly identical in shape but the *language* underneath is Lua, and the failure modes are different. Default to Lua semantics here, not Enma idioms — Enma reflexes (typed addresses, C truthiness, struct value types, `register_routine`) produce code that silently misreads memory or never runs.

**Always active when writing or editing `.lua` PCX scripts.** These rules apply on top of `game-cheat-guidelines`, not instead of it.

**Prerequisite:** `game-cheat-guidelines` MUST be loaded alongside this skill — its 12 rules (ground offsets, validate chains, separate scan from render, sigs over hardcodes, minimize writes) still govern *what* you do to memory. This skill governs *how Lua expresses it*. **Read the relevant page in `docs/perception/lua/` before writing any host API call.**

## Trigger

Activate when: the script file is `.lua`; the user asks for a Lua overlay/ESP/aimbot/dumper; you are porting an Enma or AngelScript script to Lua; you see `ref_process`, `on_frame`, `ui.create_subtab`, `proc:ru64`, or `string.format("0x%016X", ...)`; or you catch yourself writing `uint64 x =`, `register_routine`, `cast<>`, or `color(...)` in a file that is supposed to be Lua.

---

## 1. Addresses Are 64-bit Integers — Keep Them Integer-Typed

**Lua 5.4 has one number value with two subtypes: integer and float. Addresses are integers. The moment a float touches address math, anything past 2^53 is silently wrong.**

PCX is built on Lua 5.4.6, which has a true 64-bit integer subtype — so `proc:base_address()` returns a full-width integer, not a lossy double (`docs/perception/lua/proc-api.md` documents every read as `--> number (uint64)`, and `engine-specific-api.md` calls returned pointers "integer addresses"). This is *unlike* LuaJIT/5.1, where every number is a double and high addresses are already broken. The danger in 5.4 is the silent promotion: `/`, `^`, and mixing a float literal into the expression turn an exact integer into a float, and `0x7FF6_1234_5678` cannot be represented exactly as a double.

```lua
-- WRONG — float division and a float literal poison the address
local base = proc:base_address()
local slot = base + (i / 2)          -- '/' always yields a float in 5.4
local ent  = base + index * 8.0      -- 8.0 is a float; whole expr promotes
-- ent is now a float; past 2^53 it rounds to the wrong byte, read returns garbage

-- RIGHT — stay in integer land
local base = proc:base_address()
local slot = base + (i // 2)         -- floor division keeps the integer subtype
local ent  = base + index * 8        -- integer literal, integer result
```

**Why:** A float-contaminated address does not error — `proc:ru64` happily reads from the rounded address and returns more plausible-looking garbage. You get ESP at (0,0) and no stack trace. Use `//` (floor division) not `/`, use integer literals (`8` not `8.0`), and when you must check, `math.type(addr) == "integer"` tells you the subtype. Format with `%X`/`%d`, never `%f`.

---

## 2. `0` Is Truthy in Lua — Nil-Check and Zero-Check Are Different Tests

**`if x then` is true for `0`. PCX host functions split into two failure conventions, and using the wrong test lets failures through.**

This is the single biggest Enma-to-Lua porting bug. In C/Enma, `0` is false; in Lua, only `nil` and `false` are falsy — `0`, `0.0`, and `""` are all truthy. PCX host functions fail in two different ways (`docs/perception/lua/proc-api.md`):

- Return **`nil`** on failure: `ref_process`, `proc:get_module` → `if not x then` is correct.
- Return **`0`** on failure: `proc:find_code_pattern`, `proc:get_proc_address`, and every scalar read → you MUST compare `== 0` explicitly, because `if addr then` is **true** when `addr == 0`.

```lua
-- WRONG — a missed sig returns 0, and 0 is truthy, so this branch runs anyway
local hit = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
if hit then                          -- TRUE even when hit == 0
    local list = proc:ru64(hit + 3)  -- reads from 0x3, returns garbage
end

-- RIGHT — match the test to the convention
local proc = ref_process("game.exe")
if not proc then return 0 end                 -- nil convention
local base, size = proc:get_module("game.exe")
if not base then return 0 end                 -- nil convention

local hit = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
if hit == 0 then return 0 end                 -- ZERO convention — explicit
local list = proc:ru64(base + ENTITY_LIST_OFF)
if list == 0 then return 0 end                -- reads fail to 0, check it
```

**Why:** `if addr then` reads as a null check to anyone with a C background, but in Lua it only catches `nil`. A stale sig returns `0`, the truthy check passes, and you dereference address `0`. Memorize the split: handles are `nil`-checked, addresses and reads are `== 0`-checked.

---

## 3. A Table Is an Array or a Map — Never Both in One Variable

**Pick one shape per table. Mixing 1-based integer keys with string keys breaks `#`, `ipairs`, and every reader after you.**

Lua has one container type. PCX leans on both faces of it: `proc:read_struct_array` returns a **1-based array** (`docs/perception/lua/proc-api.md`), while struct descriptors and the view tables from `unreal_engine.read_minimal_view_info` are **string-keyed maps** (`docs/perception/lua/engine-specific-api.md`). The `#` operator and `ipairs` only work on a *sequence* (contiguous integer keys `1..n`); the instant you stash a string key on an array, `#t` becomes unreliable and `ipairs` stops early.

```lua
-- WRONG — array with a bolted-on string field
local ents = {}
ents[1] = ptr_a
ents[2] = ptr_b
ents.count = 2                       -- now #ents and ipairs are unreliable
for i = 1, #ents do ... end          -- may or may not see everything

-- RIGHT — array stays a pure sequence; metadata lives elsewhere
local ents = proc:read_struct_array(list_base, MAX_ENTS, ENT_SIZE, ENT_DESC)
for i, e in ipairs(ents) do          -- ipairs for sequences
    if e.health > 0 then draw_enemy(e) end
end

-- RIGHT — a descriptor is a map; iterate with pairs, never #
local ENT_DESC = {
    health = { offset = HEALTH_OFF, type = "i32" },
    pos_x  = { offset = POS_OFF,    type = "f32" },
}
for name, field in pairs(ENT_DESC) do ... end
```

**Why:** `#t` on a mixed table returns *any* border, not the count you meant — a documented Lua quirk, not a bug you can patch around. Use `ipairs`/`#` for sequences you built contiguously, `pairs` for maps, and keep the two roles in separate variables.

---

## 4. PCX Userdata Carries a Host Metatable — Don't Replace It

**`process`, `ui_*`, and `net_ws` handles are userdata with host-owned metatables. `setmetatable` on them breaks method dispatch. Wrap, don't reparent.**

Every PCX handle is userdata whose methods (`proc:ru64`, `cb:get`, `ws:send_text`) resolve through a metatable the host installed — `docs/perception/lua/net-api.md` names the WebSocket metatable `"net_ws"` outright. If you `setmetatable` one of these to add a helper, you detach `__index` and the built-in methods vanish. The Lua-correct move when you want helpers is to wrap the handle in a *plain table* you own and forward to it.

```lua
-- WRONG — clobbers the host metatable; proc:ru64 now errors
setmetatable(proc, { __index = { read_ptr = function(self, a) ... end } })

-- RIGHT — your own wrapper table delegates to the real handle
local Mem = {}
Mem.__index = Mem
function Mem.new(proc) return setmetatable({ p = proc }, Mem) end
function Mem:chain(base, ...)        -- helper that null-checks each hop
    local addr = base
    for _, off in ipairs({...}) do
        addr = self.p:ru64(addr + off)
        if addr == 0 then return 0 end
    end
    return addr
end

local mem = Mem.new(proc)
local weapon = mem:chain(base, OFF_LOCAL, OFF_WEAPON)
```

**Why:** Host userdata is opaque on purpose. Replacing its metatable is how you get `attempt to call a nil value (method 'ru64')` three frames later. Extend behavior by composition — a table that holds the handle and adds methods — and leave the host's metatable untouched.

---

## 5. Pass Function *Values* to Callbacks; Lifecycle Hooks Are Looked Up by Global Name

**There is no `register_routine` in Lua. Button callbacks take a function value. Lifecycle hooks must exist as global functions with exact names.**

PCX Lua wires logic two ways (`docs/perception/lua/life-cycle.md`, `gui-api.md`):

- **Lifecycle** — the engine calls the *globals* `main`, `on_frame`, and `on_unload` by name. They must be global (`function main()`, not `local function main()`) and spelled exactly. There is no registration call.
- **GUI callbacks** — `panel:add_button(name, fn)` takes a **function value** (a closure or a reference), not a string name.

```lua
-- WRONG — Enma reflexes: there is no register_routine, and a name string is not a callback
register_routine(on_frame, 0)                 -- nil global -> error
pnl:add_button("Reload", "do_reload")         -- string is not callable

-- WRONG — lifecycle hook hidden behind a local; engine never finds it
local function on_frame() ... end             -- not global -> never runs

-- RIGHT — globals for lifecycle, a function value for the callback
function main()
    local st  = ui.create_subtab(0, "ESP")
    local pnl = st:add_panel("Main", false)
    pnl:add_button("Reload Offsets", function() resolve_offsets() end)
    return 1                                   -- >0 AND on_frame defined => persistent
end

function on_frame() ... end                    -- engine calls this by name every frame
function on_unload() deref_process(g_proc) end -- cleanup hook
```

**Why:** `main()` returning `> 0` only keeps the script alive *if `on_frame` exists* (`life-cycle.md`); a `local function on_frame` is invisible to the engine and your overlay silently unloads. And a callback passed as `"do_reload"` is just a string — the button does nothing. Globals for hooks, function values for callbacks.

---

## 6. Closures Capture Upvalues by Reference — The Bite Is Shared Mutable State, Not the Loop Variable

**Lua's numeric `for` gives each iteration a fresh variable, so closing over the loop counter is safe. What bites is a closure or coroutine that captures an outer mutable local and runs *later*.**

The JS `var`-in-loop trap does not exist here: in Lua 5.4 the `for i = ...` control variable is a fresh local per iteration, so buttons created in a loop capture distinct `i` values correctly. The real PCX bug is deferred execution over a *shared upvalue* — a callback or `on_frame`-resumed coroutine that reads a variable mutated after the closure was created.

```lua
-- SAFE — each iteration's `i` is a fresh local; every button prints its own index
for i = 1, 3 do
    pnl:add_button("Slot " .. i, function() print("slot", i) end)
end

-- WRONG — all closures share the single upvalue `cur`, read at click time
local cur
for _, ent in ipairs(entities) do
    cur = ent                                  -- mutated every iteration
    pnl:add_button("Lock " .. ent.name, function() lock(cur) end)
end                                            -- every button locks the LAST entity

-- RIGHT — capture a fresh per-iteration local
for _, ent in ipairs(entities) do
    local target = ent                         -- new local each iteration
    pnl:add_button("Lock " .. ent.name, function() lock(target) end)
end
```

**Why:** Closures grab the *variable*, not its value-at-creation. A loop-local declared inside the body is fresh each pass and captures cleanly; a single local declared outside the loop is one shared box that every closure sees mutate. This matters most for GUI callbacks and coroutines (rule 9) that fire long after the loop finished.

---

## 7. Wrap Genuinely-Throwing Calls in `pcall` — One Bad Pointer Must Not Kill the Frame

**Scalar reads fail soft (return `0`/`""`), so don't `pcall` them. A handful of helpers raise Lua errors — those you wrap, or an uncaught error aborts `on_frame`.**

PCX reads are designed to fail quietly: `proc:ru64` on a bad address returns `0`, `proc:rs` returns `""` (`docs/perception/lua/proc-api.md`). Wrapping those in `pcall` is noise. But some helpers *raise*: `unreal_engine.world_to_screen` "raises a Lua error" on invalid input (`docs/perception/lua/engine-specific-api.md`), and JSON/net parsing can throw. An uncaught error propagates out of `on_frame`, and returning nothing (or erroring) unloads the script mid-session.

```lua
-- WRONG — reads already fail soft; this pcall is pure overhead
local ok, hp = pcall(function() return proc:r32(ent + HEALTH_OFF) end)

-- WRONG — w2s can raise; an uncaught error here kills the whole overlay this frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local s = unreal_engine.world_to_screen(e.pos, g_view)  -- may error
        draw_box(s.x, s.y)
    end
end

-- RIGHT — pcall only the call that actually throws; degrade one entity, not the frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local ok, s = pcall(unreal_engine.world_to_screen, e.pos, g_view)
        if ok and s and s.visible then         -- w2s also returns nil behind camera
            draw_box(s.x, s.y)
        end
    end
end
```

**Why:** Reads returning `0` are handled by rule 2's zero-checks, not by `pcall` — wrapping them buys nothing and hides the real check. Reserve `pcall` for the documented throwers, and scope it to the smallest call so a single malformed entity skips a draw instead of blanking the overlay and unloading the script.

---

## 8. Build Hot-Path Strings with `table.concat`, Never `..` in `on_frame`

**Lua strings are immutable. Each `..` allocates and interns a new string; chaining them in a per-frame loop is O(n²) garbage churn. Format once, cache, or use `table.concat`.**

Every `..` produces a fresh immutable string (the engine's own example uses `table.concat` for exactly this reason — `docs/perception/lua/proc-api.md` line ~279). In `on_frame`, which runs every frame, repeated concatenation allocates per frame and thrashes the GC, dropping FPS. Best is to not build strings in render at all: compute display text in the update pass and cache it; `draw_text` takes the cached string directly.

```lua
-- WRONG — N concatenations per entity, every frame
function on_frame()
    for _, e in ipairs(g_ents) do
        local label = "[" .. e.name .. "] " .. e.hp .. "hp " .. e.dist .. "m"
        draw_text(label, e.sx, e.sy, 255,255,255,255, g_font, TE_SHADOW, 0,0,0,180, 1.0)
    end
end

-- RIGHT — format in the update pass, cache the string, draw the cache
function update_labels()                       -- runs on interval, not every frame
    for _, e in ipairs(g_ents) do
        e.label = string.format("[%s] %dhp %dm", e.name, e.hp, e.dist)
    end
end

function on_frame()
    for _, e in ipairs(g_ents) do
        draw_text(e.label, e.sx, e.sy, 255,255,255,255, g_font, TE_SHADOW, 0,0,0,180, 1.0)
    end
end

-- When you must assemble many pieces, collect and join once
local parts = {}
for i, e in ipairs(g_ents) do parts[i] = e.name end
local csv = table.concat(parts, ", ")          -- one allocation
```

**Why:** `a .. b .. c` builds two intermediate strings and a final one, all interned; do that for 64 entities at 240 FPS and the allocator is your bottleneck. `string.format` in a cached field (rule from `game-cheat-guidelines` #4: separate scan from render) keeps the render path allocation-free, and `table.concat` collapses a join to a single allocation.

---

## 9. Use Coroutines to Spread Heavy Work Across Frames

**The `coroutine` add-on is enabled. A scan that stalls one frame should `yield` periodically and be resumed a slice at a time from `on_frame` — never loop until done inside a single frame.**

`docs/perception/lua/overview.md` lists `coroutine` as a registered add-on, and `life-cycle.md` is explicit: "No infinite loops — frame updates are handled by the engine." A full-module pattern scan or a deep entity walk done synchronously in one `on_frame` freezes the overlay. Model it as a coroutine that does a bounded chunk, `coroutine.yield`s, and is resumed each frame until `coroutine.status` is `"dead"`.

```lua
-- WRONG — scans the whole module in one frame; overlay hitches
function on_frame()
    g_list = proc:find_code_pattern(base, size, SIG)   -- blocks the frame if huge
end

-- RIGHT — a coroutine that scans in slices, resumed once per frame
local scanner
function main()
    g_proc = ref_process("game.exe")
    if not g_proc then return 0 end
    scanner = coroutine.create(function()
        local base, size = g_proc:get_module("game.exe")
        if not base then return end
        local CHUNK = 0x100000                          -- 1 MiB per frame
        local off = 0
        while off < size do
            local hit = g_proc:find_code_pattern(base + off, math.min(CHUNK, size - off), SIG)
            if hit ~= 0 then g_entity_list = hit; return end
            off = off + CHUNK
            coroutine.yield()                           -- give the frame back
        end
    end)
    return 1
end

function on_frame()
    if scanner and coroutine.status(scanner) ~= "dead" then
        local ok = coroutine.resume(scanner)            -- resume returns ok, err
        if not ok then scanner = nil end                -- coroutine errored; stop
    end
    -- render from whatever state is ready
end
```

**Why:** A coroutine turns a one-frame freeze into a smooth multi-frame task without threads or callbacks. `coroutine.resume` returns `false` plus the error message if the body throws — check it (same spirit as rule 7) so a failed scan stops cleanly instead of resuming a dead coroutine. `ponytail:` only reach for coroutines when the work genuinely overruns a frame; a fast scan in `main()` needs none of this.

---

## 10. `require` for File-Per-Feature Modules — Return a Table, Don't Leak Globals

**The `package` add-on gives you `require()`. Keep one feature per file, share state through a returned module table, and reserve globals for the lifecycle hooks the engine calls by name.**

`docs/perception/lua/overview.md` registers `package` with "`require()` and module loading", so the standard Lua module pattern applies and `game-cheat-guidelines` rule #6 (one feature, one file) carries over directly. `require` runs a module once and caches the result — return a table of that feature's API instead of scattering globals. The exception is the lifecycle trio (`main`/`on_frame`/`on_unload`, rule 5): those must be globals in the entry script.

```lua
-- offsets.lua — resolves and exposes addresses
local M = {}
function M.resolve(proc)
    local base, size = proc:get_module("game.exe")
    if not base then return false end
    M.entity_list = proc:find_code_pattern(base, size, SIG_ENTITY_LIST)
    if M.entity_list == 0 then return false end          -- rule 2: zero-check
    return true
end
return M

-- esp.lua — pure render, imports shared state
local offsets = require("offsets")
local M = {}
function M.draw(proc) ... end
return M

-- main.lua — entry script; globals only for lifecycle
local offsets = require("offsets")
local esp     = require("esp")
g_proc = nil

function main()
    g_proc = ref_process("game.exe")
    if not g_proc then return 0 end
    if not offsets.resolve(g_proc) then return 0 end
    return 1
end

function on_frame() esp.draw(g_proc) end
function on_unload() deref_process(g_proc) end           -- always release the handle
```

**Why:** `require` caching means a module's top-level code runs exactly once — perfect for resolving offsets, wrong for per-frame work. Returning a table keeps each feature's surface explicit and reloadable; dumping everything into globals reintroduces the god-script you split the files to avoid. And every `ref_process` needs its matching `deref_process` in `on_unload` (`docs/perception/lua/proc-api.md`) — a leaked handle outlives the script.

---

## Summary

| # | Rule | One-liner |
|---|------|-----------|
| 1 | Integer addresses | `//` not `/`; no float literals in address math (2^53 cliff) |
| 2 | `0` is truthy | `nil`-handles use `not x`; `0`-returns need `== 0` |
| 3 | One table shape | Array or map per variable; `ipairs`/`#` vs `pairs` |
| 4 | Don't reparent userdata | Wrap host handles, never `setmetatable` them |
| 5 | Values & global hooks | Callbacks take functions; lifecycle hooks are named globals |
| 6 | Capture loop-locals | Fresh local per iteration; shared upvalues bite later |
| 7 | `pcall` only throwers | Reads fail soft; wrap w2s/json so one error ≠ dead frame |
| 8 | `table.concat` in hot paths | `..` per frame is O(n²) garbage; cache formatted strings |
| 9 | Coroutines for big work | Yield slices across frames; no in-frame loops |
| 10 | `require` per feature | Return a module table; globals only for lifecycle |
