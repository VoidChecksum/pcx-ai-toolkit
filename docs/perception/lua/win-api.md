> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/win-api.md).

# Win API

This API exposes a small subset of the Win32 window, clipboard, keyboard, mouse and messaging functions to Lua:

* Work with windows via **handles** (`hwnd` as integer).
* Inspect window rectangles and sizes.
* Check if a window is foreground or “active”.
* Read / write text to the **clipboard** (UTF-8).
* Look up the **thread & process IDs** for a window.
* Send **messages**, **keys**, and **characters** to a window.
* Send **global keyboard and mouse input** via `SendInput`.

***

### Window Lookup & Info

#### `find_window(title [, class]) -> hwnd | nil`

Search for a top-level window.

* `title` — window title to match (UTF-8 string).
* `class` — optional window class name (UTF-8 string).

If both are provided, both must match.\
Returns `hwnd` (integer) or `nil` if not found.

***

### Window Enumeration

#### `get_all_hwnds()`

Enumerates all top-level windows on the system and returns detailed information about each.

**Returns:** A 1-based Lua array of window info tables.

**Window Info Table Fields:**

| Field          | Type     | Description                             |
| -------------- | -------- | --------------------------------------- |
| `hwnd`         | `int`    | Window handle                           |
| `pid`          | `int`    | Process ID                              |
| `tid`          | `int`    | Thread ID                               |
| `process_name` | `string` | Executable name (e.g., `"notepad.exe"`) |
| `title`        | `string` | Window title text                       |
| `class_name`   | `string` | Window class name                       |

```lua
log("Found " .. #windows .. " windows")

for i, w in ipairs(windows) do
    -- Only show windows with titles
    if w.title ~= "" then
        log(string.format("[%s] %s (PID: %d)", 
            w.process_name, w.title, w.pid))
    end
end

-- Find a specific window by process name
for _, w in ipairs(windows) do
    if w.process_name == "notepad.exe" then
        log("Found Notepad! HWND: " .. w.hwnd)
        set_foreground_window(w.hwnd)
        break
    end
end

return 0
```

***

#### `get_window_size(hwnd) -> width, height | nil, nil`

Get the window’s **outer** size in pixels.

* `hwnd` — window handle (integer).

Returns:

* `width`, `height` (integers), or
* `nil, nil` if the handle is invalid or the call fails.

***

#### `get_window_rect(hwnd) -> x, y, width, height | nil, nil, nil, nil`

Get the window’s full rectangle in screen coordinates.

* `x`, `y` — top-left screen coordinates.
* `width`, `height` — size in pixels.

Returns all `nil` on failure.

***

### Window Focus & Activity

#### `is_foreground_window(hwnd) -> bool`

Checks if `hwnd` is the **current foreground window**.

***

#### `is_window_active(hwnd) -> bool`

Checks if a window is “active” in a broad sense:

* is a valid window,
* is visible,
* is **not minimized**.

Returns `true` or `false`.

***

### Window Text & Class

#### `get_window_title(hwnd) -> string | nil`

Get the window’s title as a UTF-8 string.

* Returns `""` for empty titles.
* Returns `nil` if the handle is invalid.

***

#### `get_window_class(hwnd) -> string | nil`

Get the window’s **class name**.

* Returns `""` if class name can’t be read.
* Returns `nil` if the handle is invalid.

***

#### `set_foreground_window(hwnd) -> bool`

Attempts to bring the given window to the foreground.

Returns `true` on success, `false` otherwise.

***

### Clipboard

All clipboard operations use UTF-8 strings.

#### `copy_to_clipboard(text) -> bool`

Copies a Lua string into the system clipboard.

* `text` — UTF-8 string.
* Returns `true` on success, `false` on failure.

***

#### `copy_from_clipboard() -> string`

Reads UTF-8 text from the system clipboard.

* Returns `""` (empty string) if:
  * clipboard cannot be opened,
  * the clipboard doesn’t contain text, or
  * any error occurs.

***

### Thread / Process Info

#### `get_window_thread_process_id(hwnd) -> thread_id, process_id | nil, nil`

Returns IDs associated with a given window.

* `thread_id` — thread that owns the window.
* `process_id` — process that owns the thread.

If the handle is invalid or the IDs can’t be obtained, returns `nil, nil`.

***

### Messages & Keys

#### `post_message(hwnd, msg, wparam, lparam) -> bool`

Low-level API to post a message to a window.

* `hwnd` — window handle.
* `msg` — message ID (e.g., `0x0010` for `WM_CLOSE`).
* `wparam`, `lparam` — integer parameters.

Returns `true` on success.

***

#### Global key input (`SendInput`)

These functions send **global** keyboard input (not scoped to a specific window). Use when you simply want to simulate key presses.

Virtual keys are integers (e.g. `0x41` for `A`, `0x11` for Ctrl, `0x0D` for Enter).

**`win_key_down(vk)`**

Simulate key down for virtual key `vk`.

&#x20; **`win_key_up(vk)`**

Simulate key up for virtual key `vk`.

**`win_key_press(vk [, delay_ms])`**

Press and release a key, with an optional delay.

* `vk` — virtual key code.
* `delay_ms` — optional delay in milliseconds between down and up (default \~30, clamped to `0..1000`).

***

#### Message-based character & key sending

These functions target a specific window using messages (`WM_CHAR`, `WM_KEYDOWN`, `WM_KEYUP`).

**`send_char(hwnd, text) -> bool`**

Sends a single character via `WM_CHAR`.

* `text` — Lua string; only the **first UTF-16 code unit** is used, which is fine for most BMP characters.

Returns `true` on success.

**`send_key(hwnd, vk) -> bool`**

Sends a key to a specific window using `WM_KEYDOWN` and `WM_KEYUP`.

* `vk` — virtual key code.

Returns `true` if both messages were posted successfully.

***

### Mouse Input

All mouse functions send **global** input via `SendInput`.

Coordinates are in **screen pixels** (primary monitor), unless noted otherwise.

#### `mouse_move(x, y)`

Moves the cursor to absolute screen coordinates.

* `(0,0)` is top-left of the primary display.
* Coordinates are converted to the normalized range expected by `SendInput`.

***

#### `mouse_move_relative(dx, dy)`

Moves the cursor relative to its current position.

* `dx` — horizontal delta (pixels).
* `dy` — vertical delta (pixels).

***

#### `mouse_left_click()`

Performs a left button click at the current cursor position.

#### `mouse_right_click()`

Performs a right button click.

#### `mouse_middle_click()`

Performs a middle button click.

Each click sends a down event, waits \~10 ms, then sends an up event.

***

#### `send_mouse_input(dx, dy, flags, mouse_data)`

Send input manually via raw input.

***

#### `mouse_scroll(amount)`

Scrolls the mouse wheel vertically.

* `amount` is in “notches”:
  * positive → scroll **up**
  * negative → scroll **down**

Example: `mouse_scroll(3)` scrolls up 3 notches.

***

## **Util**

`get_tickcount64()`

* GetTickCount64()

***

### Usage Examples

#### Find a window and print info

```lua
local title   = "Untitled - Notepad"
local hwnd    = find_window(title)

if not hwnd then
  print("Window not found:", title)
  return
end

print("HWND:", string.format("0x%X", hwnd))

local x, y, w, h = get_window_rect(hwnd)
print("Rect:", x, y, w, h)

local winTitle = get_window_title(hwnd) or "<nil>"
local winClass = get_window_class(hwnd) or "<nil>"
print("Title:", winTitle)
print("Class:", winClass)

local tid, pid = get_window_thread_process_id(hwnd)
print("Thread ID:", tid, "Process ID:", pid)
```

***

#### Clipboard

```lua
copy_to_clipboard("Hello from Lua! こんにちは 🌸")

local txt = copy_from_clipboard()
print("Clipboard:", txt)
```

***

#### Global keystrokes

```lua
-- Type 'HELLO'
local letters = { 0x48, 0x45, 0x4C, 0x4C, 0x4F } -- H E L L O
for _, vk in ipairs(letters) do
  win_key_press(vk, 40)
end

-- Ctrl+V
local VK_CONTROL = 0x11
local VK_V       = 0x56

win_key_down(VK_CONTROL)
win_key_press(VK_V, 30)
win_key_up(VK_CONTROL)
```

***

#### Message-based typing into a window

```lua
local hwnd = find_window("Untitled - Notepad")
if not hwnd then return end

-- make sure Notepad has focus (if you expose set_foreground_window)
set_foreground_window(hwnd)

send_char(hwnd, "H")
send_char(hwnd, "i")
send_char(hwnd, " ")
send_char(hwnd, "🌸")

local VK_RETURN = 0x0D
send_key(hwnd, VK_RETURN)
```

***

#### Mouse movement & clicks

```lua
-- Move to near top-left, left-click
mouse_move(100, 100)
mouse_left_click()

-- Move a bit to the right and right-click
mouse_move_relative(80, 0)
mouse_right_click()

-- Move down and middle-click
mouse_move_relative(0, 60)
mouse_middle_click()

-- Scroll up then down
mouse_scroll(3)
mouse_scroll(-3)
```

## Full API Test

<pre class="language-lua"><code class="lang-lua"><strong>local TARGET_TITLE = "Untitled - Notepad"  -- change to your target window
</strong>
local function has_global(name)
    return _G[name] ~= nil
end

local function get_target_hwnd()
    if not has_global("find_window") then
        log("ERROR: find_window is not available.")
        return nil
    end

    local hwnd = find_window(TARGET_TITLE)
    if not hwnd then
        log("Window not found:", TARGET_TITLE)
        return nil
    end

    log("Found hwnd:", string.format("0x%X", hwnd))

    if has_global("set_foreground_window") then
        local ok = set_foreground_window(hwnd)
        log("set_foreground_window:", ok)
    else
        log("set_foreground_window not available, skipping.")
    end

    return hwnd
end

local function test_mouse_basic()
    log("=== TEST: mouse movement &#x26; clicks ===")
    log("Move your eyes to where the cursor goes. :)")

    -- Move to approximate top-left of the primary screen
    mouse_move(100, 100)
    mouse_left_click()
    log("  mouse_move(100,100) + left click")

    -- Move a bit to the right and right-click
    mouse_move_relative(80, 0)
    mouse_right_click()
    log("  mouse_move_relative(80,0) + right click")

    -- Move a bit down and middle-click
    mouse_move_relative(0, 60)
    mouse_middle_click()
    log("  mouse_move_relative(0,60) + middle click")

    -- Scroll up then down a bit
    mouse_scroll(3)   -- up 3 notches
    mouse_scroll(-3)  -- down 3 notches
    log("  mouse_scroll(3) then mouse_scroll(-3)")
end

local function test_send_char_key(hwnd)
    if not hwnd then
        log("No hwnd, skipping send_char/send_key test.")
        return
    end

    if not has_global("send_char") or not has_global("send_key") then
        log("send_char / send_key not available, skipping.")
        return
    end

    log("=== TEST: send_char / send_key ===")
    log("Make sure the target window has a focused text field.")

    -- Send "Hi " + emoji via WM_CHAR
    send_char(hwnd, "H")
    send_char(hwnd, "i")
    send_char(hwnd, " ")
    send_char(hwnd, "🌸") -- only 

    -- Press Enter via WM_KEYDOWN/UP
    local VK_RETURN = 0x0D
    local ok = send_key(hwnd, VK_RETURN)
    log("send_key(VK_RETURN) ->", ok)
end

function main()
    log("Target window title:", TARGET_TITLE)

    local hwnd = get_target_hwnd()

    test_mouse_basic()
    test_send_char_key(hwnd)

    log("=== winapi_input_test.lua done ===")
    return 1;
end
</code></pre>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/win-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
