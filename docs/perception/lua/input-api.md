> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/input-api.md).

# Input API

The Input API provides access to mouse, keyboard, and UI-hover information from Lua scripts.\
These functions are intended to be used inside `on_frame()`.

***

### 🖱 Mouse Input

#### Mouse Position

```lua
x, y = get_mouse_pos()
```

Returns the cursor position **inside the game/overlay window**.

```lua
x, y = get_mouse_pos_desktop()
```

Returns the cursor position in **desktop/screen coordinates**.

***

#### Mouse Delta

```lua
dx, dy = get_mouse_delta()
```

Movement since last frame in overlay space.

```lua
dx, dy = get_mouse_delta_desktop()
```

Movement since last frame in desktop space.

***

#### Scroll Wheel

```lua
amount = get_scroll_delta()
```

Positive for scroll up, negative for scroll down.

***

#### Movement Event

```lua
moved = mouse_movement_received()
```

Returns `true` if the mouse moved this frame.

***

#### Hover Detection

```lua
hovered = is_hovered(x, y, w, h) --overlay window
```

Returns `true` if the mouse is inside the rectangle `(x, y, w, h)`.

***

### ⌨️ Keyboard Input

#### Key Down

```lua
down = key_down(vk)
```

Returns `true` while key is held.

#### Raw Down

```lua
raw = key_raw_down(vk)
```

Reflects OS-level down state before filtering.

#### Fired

```lua
fired = key_fired(vk)
```

Behaves like text input

#### Toggle

```lua
toggle = key_toggle(vk)
```

Toggles each time the key is pressed (flip-flop behavior).

#### Single Press

```lua
single = key_singlepress(vk)
```

True only on the **first frame** the key is pressed.

#### Previous State

```lua
prev = key_prev_down(vk)
```

State from the previous frame.

***

### 🔍 Full Key State

```lua
raw_down, down, fired, toggle, single, prev =
    get_key_state(vk)
```

Returns all internal state fields for a virtual key.

***

### 🧩 Keys Down List

```lua
keys = get_keys_down()
```

Returns a Lua table of all currently pressed virtual keys.

Example:

```lua
for i, vk in ipairs(get_keys_down()) do
    log("Down: " .. get_key_name(vk))
end
```

***

### 📝 Text Input & Key Names

#### Recent Typed Characters

```lua
txt = get_recent_key_input()
```

Returns a string of recently typed characters\
(from your internal text buffer).

#### Key Name

```lua
name = get_key_name(vk)
```

Returns a readable name like `"SPACE"`, `"A"`, `"SHIFT"`.

***

## 📌 Example

```lua
local font = 0
local frame = 0
local last_keys = ""

function main()
    log("Lua Input Test Script Loaded!")
    font = get_font20()
    return 1
end

function on_frame()
    frame = frame + 1
    
    local vw, vh = get_view()
    local scale = get_view_scale()
    
    local mx, my = get_mouse_pos()
    local dx, dy = get_mouse_delta()
    local scroll = get_scroll_delta()
    
    local keys = get_keys_down()
    local recent = get_recent_key_input()
    
    -- Panel
    local w = 450 * scale
    local h = 300 * scale
    local x = 20 * scale
    local y = 20 * scale
    
    draw_rect_filled(
        x, y, w, h,
        20, 20, 25, 220,
        8 * scale,
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT
        )
    
    draw_rect(
        x, y, w, h,
        60, 120, 255, 255,
        2 * scale,
        8 * scale,
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT
        )
    
    local function text(label, value, ox, oy)
        draw_text(
            label .. value,
            x + 10 * scale, y + oy * scale,
            255, 255, 255, 255,
            font,
            TE_SHADOW,
            0,0,0,180,
            1.0,
            true
            )
    end
    
    text("Mouse Pos: ", string.format("%0.1f, %0.1f", mx, my), 10, 10)
    text("Mouse Delta: ", string.format("%0.2f, %0.2f", dx, dy), 10, 40)
    text("Scroll: ", tostring(scroll), 10, 70)
    
    -- Hover test
    local hx, hy, hw, hh = vw*0.5 - 50*scale, vh*0.5 - 50*scale, 100*scale, 100*scale
    local hovered = is_hovered(hx, hy, hw, hh)
    
    draw_rect_filled(
        hx, hy, hw, hh,
        hovered and 60 or 30,
        hovered and 200 or 60,
        hovered and 80 or 60,
        240,
        8*scale,
        RR_TOP_LEFT | RR_BOTTOM_RIGHT
        )
    
    text("Hovered (center box): ", hovered and "true" or "false", 10, 100)
    
    -- Key states
    local space_down = key_down(0x20)
    local space_name = get_key_name(0x20) or "?"
    
    text("SPACE down: ", tostring(space_down), 10, 130)
    text("SPACE name: ", space_name, 10, 190)
    
    -- Keys currently down
    local kd = ""
    for i,vk in ipairs(keys) do
        kd = kd .. get_key_name(vk) .. " "
    end  
    text("Keys down: ", kd, 10, 220)
    
    -- Recent typed characters
    if recent ~= "" then
        last_keys = recent
    end
    text("Recent typed: ", last_keys, 10, 250)
end

function on_unload()
    log("Lua Input Test Script Unloaded")
end

```

***

## 💡 Notes

* `vk` refers to Windows Virtual-Key codes (e.g., `0x41` = `'A'`, `0x20` = Space).
* The Input API is frame-based and intended to be called from inside `on_frame()`.
* `get_recent_key_input()` is ideal for text input boxes or consoles.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/input-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
