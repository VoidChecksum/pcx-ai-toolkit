> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/gui-api.md).

# GUI API

The Lua GUI API allows scripts to dynamically create UI inside the Perception.cx interface.\
UI created by a script is **owned** by that script and is automatically removed when the script unloads.

#### ✔ Supported Features

* Create subtabs inside the main UI
* Add panels inside subtabs
* Add UI elements inside panels
* Read/write element values
* Hide/show elements at runtime (`set_active`)
* Keybinds, color pickers, and buttons that belong to a parent checkbox
* List controls with highlight, insert, remove, set active index
* Script-level button callbacks

***

## **UI Hierarchy**

```
Tab (index 0–4)
 └─ Subtab
      └─ Panel (small or large)
           ├─ Checkbox
           │     ├─ Keybind (child)
           │     └─ Color Picker(s) (child, up to 2)
           │     └─ Button (child)
           ├─ Slider (double or int)
           ├─ Input Text Box
           ├─ Multi Select
           ├─ Single Select
           ├─ List
           └─ Other elements…
```

***

## **Element Creation Rules**

#### 🔥 **Important Ordering Constraint**

Some elements must be created *immediately after a checkbox*, because the UI engine uses the checkbox as their parent:

| Child Element    | Rule                                                             |
| ---------------- | ---------------------------------------------------------------- |
| **keybind**      | MUST be created right after its parent checkbox (1 or 2 allowed) |
| **color picker** | MUST be created right after its parent checkbox (1 or 2 allowed) |

If you break this rule, the element will not get created.

* **2 color pickers**, or
* **2 keybinds**, or
* **1 color picker + 1 keybind**

***

## **Global Entry**

### `ui.create_subtab(tab_index, name)`

Creates a new subtab in a given tab.

#### **Parameters**

| Name        | Type          | Description                                  |
| ----------- | ------------- | -------------------------------------------- |
| `tab_index` | integer (0–4) | Index of the main tab to place the subtab in |
| `name`      | string        | Display name of the subtab                   |

#### **Returns**

`ui_subtab` userdata.

#### **Example**

```lua
local st = ui.create_subtab(0, "ESP Settings")
```

***

## **Subtab API**

### `subtab:add_panel(name, is_small)`

Creates a panel inside the subtab.

#### **Parameters**

| Name       | Type    | Description                       |
| ---------- | ------- | --------------------------------- |
| `name`     | string  | Panel title                       |
| `is_small` | boolean | Whether panel uses compact layout |

#### **Returns**

`ui_panel` userdata.

#### **Example**

```lua
local pnl = st:add_panel("Aimbot", false)
```

#### **Common**

```lua
subtab:set_active(true/false)
```

***

## **Panel Element APIs**

All elements are created using methods on a panel.

***

## **Checkbox**

### `panel:add_checkbox(name, initial_value, [draw_title], [find_protect], [draw_just_label])`

#### **Parameters**

| Name              | Type               | Description                                                                                                                                                                   |
| ----------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`            | string             | Checkbox label                                                                                                                                                                |
| `initial_value`   | boolean            | Starting state                                                                                                                                                                |
| `draw_title`      | boolean (optional) | Show the label (default: true)                                                                                                                                                |
| `find_protect`    | boolean (optional) | Internal protection flag                                                                                                                                                      |
| `draw_just_label` | boolean (optional) | When enabled, the checkbox is non-interactive and functions purely as a label. This is useful when you only want to attach a color picker or keybind without toggle behavior. |

#### **Returns**

`ui_checkbox` userdata.

#### **Example**

```lua
local cb = pnl:add_checkbox("Enable ESP", true)
```

#### **Methods**

```lua
cb:get() → bool
cb:set(true/false)
cb:set_active(true/false)
```

***

## **Slider (Double)**

### `panel:add_slider_double(name, postfix, value, min, max, step, [draw_title], [find_protect])`

#### **Parameters**

| Name           | Type               | Description                                           |
| -------------- | ------------------ | ----------------------------------------------------- |
| `name`         | string             | Slider label                                          |
| `postfix`      | string             | Text shown after numeric value (“°”, “ms”, “x”, etc.) |
| `value`        | number             | Initial value                                         |
| `min`          | number             | Minimum                                               |
| `max`          | number             | Maximum                                               |
| `step`         | number             | Step size                                             |
| `draw_title`   | boolean (optional) | Show the name (default: true)                         |
| `find_protect` | boolean (optional) | Internal flag                                         |

#### **Returns**

`ui_slider_double` userdata.

#### **Methods**

```lua
s:get() → number
s:set(number)
s:set_active(true/false)
```

***

## **Slider (Int)**

### `panel:add_slider_int(name, postfix, value, min, max, step, [draw_title], [find_protect])`

Same parameters as the double slider, all integers.

#### **Methods**

```lua
s:get() → integer
s:set(integer)
s:set_active(true/false)
```

***

## **Input Text Box**

### `panel:add_input(name, initial_text, [draw_title], [find_protect])`

#### **Parameters**

| Name           | Type   | Description      |
| -------------- | ------ | ---------------- |
| `name`         | string | Display name     |
| `initial_text` | string | Starting content |

#### **Returns**

`ui_input` userdata.

#### **Methods**

```lua
inp:get() → string
inp:set("text")
inp:set_active(true/false)
```

***

## **Multi Select**

### `panel:add_multi_select(name, options_table, is_expandable, [draw_title], [find_protect])`

#### **`options_table` Format**

```lua
{
    {"Option 1", true},
    {"Option 2", false},
    {"Option 3", true},
}
```

#### **Methods**

```lua
ms:get() → { bool, bool, bool }
ms:set(index, bool)   -- 0-based index!
ms:set_active(true/false)
```

***

## **Single Select**

### `panel:add_single_select(name, options_table, initial_index, is_expandable, [draw_title], [find_protect])`

#### **Methods**

```lua
ss:get() → index
ss:set(index)        -- 0-based
ss:set_active(true/false)
```

***

## **Keybind (Checkbox Child Only)**

### `panel:add_keybind(name, vk_keycode, mode_string, [draw_title], [find_protect])`

⚠ **Must be created immediately after a checkbox**, or it will not attach properly.

#### **Modes**

* `"off"`
* `"on"`
* `"single"`
* `"toggle"`
* `"always_on"`

#### **Methods**

```lua
key, mode = kb:get()
kb:set(0x46, "toggle")
kb:set_active(true/false)
kb:is_pressed()
```

#### **Example**

```lua
local cb = pnl:add_checkbox("Enable Toggle", true)
local kb = pnl:add_keybind("Hotkey", 0x46, "toggle")
```

***

## **Color Picker (Checkbox Child)**

### `panel:add_color(name, {r,g,b,a}, [find_protect])`

⚠ Must be placed immediately after a checkbox.\
Supports **1–2** color pickers per checkbox.

#### **Parameters**

| Channel | Type    | Range |
| ------- | ------- | ----- |
| `r`     | integer | 0–255 |
| `g`     | integer | 0–255 |
| `b`     | integer | 0–255 |
| `a`     | integer | 0–255 |

#### **Methods**

```lua
col:get() → {r,g,b,a}
col:set({255,0,0,128})
col:set_active(true/false)
```

***

## **Button**

### `panel:add_button(name, callback_function)`

#### **Behavior**

* When clicked, the Lua function is executed

#### **Example**

```lua
local btn = pnl:add_button("Reload Script", function()
    print("Reload pressed!")
end)
```

#### **Methods**

```lua
btn:set_active(true/false)
```

***

## **List**

### `panel:add_list(name, entries_table, [draw_title], [find_protect])`

#### **`entries_table` Format**

```lua
{
    {"Name1", "Info1"},
    {"Name2", "Info2"},
}
```

#### **Methods**

**Append**

```lua
lst:append("Enemy3", "HP:50")
```

**Append After (insert)**

```lua
lst:append_after("EnemyX", "HP:99", 1)
```

Inserts after index `1` (0-based).

**Read / Manage**

```lua
lst:get() -> integer
lst:get_all() → { {name, info}, ... }
lst:get_count() → integer
lst:clear()

lst:highlight(index)
lst:remove_highlight(index)
lst:remove(index)   -- 0-based
lst:set_active_index(index)

lst:set_active(true/false)
```

***

## **Visibility (set\_active)**

All elements support:

```lua
element:set_active(true)
element:set_active(false)
```

This applies to all elements

***

## **Full Example**

```lua
local st = ui.create_subtab(0, "Demo UI")
local pnl = st:add_panel("Aimbot Settings", false)

local cb = pnl:add_checkbox("Enable Aimbot", true)

local fov = pnl:add_slider_double("FOV", "°", 90, 1, 180, 1)
local smooth = pnl:add_slider_int("Smoothness", "", 5, 1, 20, 1)

local cb_col_a = pnl:add_checkbox("Primary", true)
local colA = pnl:add_color("Primary", {255, 0, 0, 255})
local cb_col_b = pnl:add_checkbox("Secondary", true)
local colB = pnl:add_color("Secondary", {0, 0, 255, 200})

local lst = pnl:add_list("Targets", {
        {"Player1", "HP:100"},
        {"Player2", "HP:90"},
    })

local btn = pnl:add_button("Print Info", function()
    print("FOV:", fov:get())
    print("Smooth:", smooth:get())
end)

function on_frame()
    
end

function main()
    return 1;
end
```

***

## **Script Unload Behavior**

When a script unloads:

* All subtabs created by it are deleted
* All panels and elements inside them are deleted
* All button callbacks are unregistered
* No UI leftovers remain

***

## **Lookup API**

### `ui.find_element(parent_tab_index, subtab_name, panel_name, element_name, type_string)`

Looks up an existing UI element anywhere in the menu and returns the correct Lua userdata (the same type returned when you created it with `panel:add_*`).

If nothing is found → returns `nil`.

***

#### **Parameters**

| Name               | Type          | Description                           |
| ------------------ | ------------- | ------------------------------------- |
| `parent_tab_index` | integer (0–4) | Which main tab the subtab is in       |
| `subtab_name`      | string        | Name of the subtab                    |
| `panel_name`       | string        | Name of the panel                     |
| `element_name`     | string        | Exact display name of the element     |
| `type_string`      | string        | Type of the element (see table below) |

***

#### **Valid `type_string` Values**

| Type String       | Returns            |
| ----------------- | ------------------ |
| `"checkbox"`      | `ui_checkbox`      |
| `"slider_double"` | `ui_slider_double` |
| `"slider_int"`    | `ui_slider_int`    |
| `"input"`         | `ui_input`         |
| `"multi_select"`  | `ui_multi_select`  |
| `"single_select"` | `ui_single_select` |
| `"keybind"`       | `ui_keybind`       |
| `"color_picker"`  | `ui_color`         |
| `"button"`        | `ui_button`        |
| `"list"`          | `ui_list`          |

***

#### **Return Value**

| Condition     | Returns                                            |
| ------------- | -------------------------------------------------- |
| Element found | Correct UI userdata (checkbox, slider, list, etc.) |
| Not found     | `nil`                                              |

***

#### **Usage Examples**

**Toggle a checkbox**

```lua
local cb = ui.find_element(0, "ESP Settings", "Panel Name", "Enable ESP", "checkbox")
if cb then
    cb:set(not cb:get())
end
```

**Adjust a slider by name**

```lua
local fov = ui.find_element(0, "Aimbot", "Panel Name", "FOV", "slider_double")
if fov then
    fov:set(math.min(180, fov:get() + 5))
end
```

**Highlight list entry by name**

```lua
local lst = ui.find_element(0, "Radar", "Panel Name", "Entities", "list")
if lst then
    lst:highlight(0)
end
```

***

## 🧾 **Config API**

Perception.cx supports saving/loading the entire UI configuration, including all elements, values, and states.

These two APIs allow Lua scripts to trigger that behavior.

***

### `ui.construct_config() → string`

Builds a **full configuration snapshot** of all UI elements.

Returns a config string you can save to disk or use however you like.

#### Example

```lua
local cfg = ui.construct_config()
host.write_file("settings.cfg", cfg) -- using your file API
```

***

### `ui.apply_config(config_string)`

Applies a config previously generated by `ui.construct_config()`.

#### Example

```lua
local cfg = host.read_file("settings.cfg")
if cfg then
    ui.apply_config(cfg)
end
```

***

## `ui.is_active()`

Checks if the gui is currently visible or not

***

### 🏷 Name Prefixing for Elements (`##prefix_`)

The  GUI API supports **name prefixing** so that multiple UI elements can share the **same visible label** while still being uniquely identified by the configuration system.

This is important when you have repeated layouts (per-player, per-item, etc.) and want each control to save/load separately.

#### How It Works

When you pass the `name` parameter to `panel:add_*`:

* The part **after** `##prefix_` is the **visible label** shown in the UI and the rest is unique id
* The **configuration system** (`ui.construct_config` / `ui.apply_config`) uses the **full prefixed name**
* `ui.find_element(...)` **does not take prefix** and matches based on the **visible label only**

So:

```lua
pnl:add_input("##elem1_Player Name", "Alex")
pnl:add_input("##elem2_Player Name", "Bob")
```

Both controls render as:

> Player Name

…but their internal IDs and config entries are different.

***

#### Duplicate Names and Config Behavior

* **Duplicate visible names are allowed even without prefixes.**\
  The UI will render and behave normally.
* However, **without prefixes**, the internal configuration system **cannot uniquely differentiate** those elements:
  * Their saved values can overwrite each other
  * Loading a config may apply the wrong value to the wrong element
* With `##prefix_`, each element has a distinct internal ID, so:
  * `ui.construct_config()` stores them separately
  * `ui.apply_config()` restores each one correctly

***

#### `ui.find_element` and Prefixes

```lua
ui.find_element(parent_tab_index, subtab_name, panel_name, element_name, type_string)
```

* `element_name` is matched against the **visible name only** (the part after `##`).
* If multiple elements share the same visible label:
  * `ui.find_element` will return the **first matching element** of that type in that panel.

Example:

```lua
local pnl = st:add_panel("Players", false)

pnl:add_input("##p1_Name", "Alice")
pnl:add_input("##p2_Name", "Bob")

-- Both show "Name" in the UI

local inp = ui.find_element(0, "Players Tab", "Players", "Name", "input")
if inp then
    -- This will refer to the *first* "Name" input (##p1_Name)
    print(inp:get())
end
```

***

#### When to Use Prefixing

Use the `##prefix_` pattern whenever:

* You have **multiple elements with the same visible label** in the same panel/subtab.
* You care that each element’s value is **saved and loaded distinctly** via the config system.

Example pattern:

```lua
for i, player in ipairs(players) do
    local label = string.format("##p%d_Player Name", i)
    pnl:add_input(label, player.name)
end
```

All rows show **“Player Name”**, but each has its own internal ID and config entry.

***

## 🔒 **Reference Tracking (Internal Behavior)**

Whenever you call:

```
ui.find_element(...)
```

The element is automatically tracked by the script.\
If the element is destroyed elsewhere (e.g., its panel or subtab is removed), the script can safely unregister that reference later.

(You do **not** need to manage this manually — it is just here for understanding the lifecycle.)


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/gui-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
