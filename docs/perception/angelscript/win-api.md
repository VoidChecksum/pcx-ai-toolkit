> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/win-api.md).

# Win API

This API allows AngelScript scripts to interact with Windows:

* Find windows by title or class
* Read window titles, classes, positions, sizes
* Detect whether a window is foreground or active
* Read or write clipboard text
* Discover the thread & process IDs for a window
* Send messages (WM\_CHAR, WM\_KEYDOWN, WM\_KEYUP, etc.)
* Send global keyboard/mouse events (SendInput)

Handles (`hwnd`) are represented as **uint64** values.

***

## **Window Lookup**

#### `uint64 find_window(const string &in title)`

Finds a top-level window by its title.

Returns 0 if not found.

***

### Window Enumeration

#### &#x20;`array<WindowInfo>@ get_all_hwnds()`

Enumerates all top-level windows on the system and returns detailed information about each.

**Returns:** Handle to an array of `WindowInfo` objects, or `null` on failure.

#### WindowInfo Type

A value type containing window details:

| Property       | Type     | Description                             |
| -------------- | -------- | --------------------------------------- |
| `hwnd`         | `uint64` | Window handle                           |
| `pid`          | `uint`   | Process ID                              |
| `tid`          | `uint`   | Thread ID                               |
| `process_name` | `string` | Executable name (e.g., `"notepad.exe"`) |
| `title`        | `string` | Window title text                       |
| `class_name`   | `string` | Window class name                       |

**Example:**

```cpp
int main()
{
    array<WindowInfo>@ windows = get_all_hwnds();
    
    if (windows is null)
    {
        log("Failed to get windows list");
        return 0;
    }
    
    log("Found " + windows.length() + " windows\n");
    
    for (uint i = 0; i < windows.length(); i++)
    {
        WindowInfo w = windows[i];
        
        if (w.title.isEmpty())
           continue;
        
        log("=== Window " + (i + 1) + " ===");
        log("  HWND:         " + w.hwnd);
        log("  PID:          " + w.pid);
        log("  TID:          " + w.tid);
        log("  Process:      " + w.process_name);
        log("  Title:        " + w.title);
        log("  Class:        " + w.class_name);
        log("");
    }
    
    for (uint i = 0; i < windows.length(); i++)
    {
        if (windows[i].process_name == "notepad.exe")
        {
            log("Found Notepad! HWND: " + windows[i].hwnd);
            break;
        }
    }
      return 0;
}


```

***

#### `uint64 find_window(const string &in title, const string &in className)`

Finds a window by **title** and **class name**.

Pass empty string (`""`) to ignore a filter.

Returns 0 if not found.

***

## **Window Information**

#### `bool get_window_size(uint64 hwnd, int &out w, int &out h)`

Retrieves the window’s width and height (outer size).

Returns `false` if the window is invalid.

***

#### `bool get_window_rect(uint64 hwnd, int &out x, int &out y, int &out w, int &out h)`

Retrieves full window rect:

* `x, y` — top-left screen coordinates
* `w, h` — size in pixels

Returns `false` on failure.

***

#### `bool get_window_title(uint64 hwnd, string &out title)`

Gets the window’s title text (UTF-8).

* Returns `true` even for empty titles.
* Returns `false` only when the hwnd is invalid.

***

#### `bool get_window_class(uint64 hwnd, string &out cls)`

Gets the Win32 window class name.

Returns `false` if the window is invalid.

***

## **Foreground / Activity**

#### `bool set_foreground_window(uint64 hwnd)`

Attempts to bring the window to foreground.

***

#### `bool is_foreground_window(uint64 hwnd)`

Returns `true` if the given window is currently foreground.

***

#### `bool is_window_active(uint64 hwnd)`

Checks whether the window:

* is valid
* is visible
* is **not minimized**

This is a broader “is active” check.

***

## **Clipboard**

All clipboard strings are UTF-8.

#### `bool copy_to_clipboard(const string &in text)`

Copies text into the Windows clipboard.

***

#### `bool copy_from_clipboard(string &out text)`

Reads text from the Windows clipboard.

* Returns `true` if any text was successfully retrieved.
* Empty clipboard → empty string.

***

## **Thread & Process Info**

#### `bool get_window_thread_process_id(uint64 hwnd, uint &out tid, uint &out pid)`

Retrieves:

* `tid` — thread ID
* `pid` — process ID

Returns `false` if the hwnd is invalid.

***

## **Messaging**

#### `bool post_message(uint64 hwnd, uint msg, uint64 wparam, uint64 lparam)`

Posts a raw Win32 message to a window.

Examples:

* `post_message(hwnd, 0x0010, 0, 0)` → WM\_CLOSE
* `post_message(hwnd, 0x0100, VK_A, 0)` → WM\_KEYDOWN for ‘A’

Returns `false` if the hwnd is invalid.

***

## **Keyboard Input**

### Global keyboard (SendInput)

These functions simulate real keyboard events globally.

#### `void win_key_down(uint vk)`

Simulates a key-down.

#### `void win_key_up(uint vk)`

Simulates a key-up.

#### `void win_key_press(uint vk, uint delay_ms = 30)`

Press → delay → release.

* `delay_ms` clamped to `0..1000`.

***

### Window-targeted typing (PostMessage)

#### `bool send_char(uint64 hwnd, const string &in text)`

Sends a single character to a window using `WM_CHAR`.

* Only the **first UTF-16 code unit** is used.

***

#### `bool send_key(uint64 hwnd, uint vk)`

Sends:

* `WM_KEYDOWN`
* `WM_KEYUP`

…to a specific window.

***

## **Mouse Input**

Mouse input uses real global `SendInput` events.

#### `void mouse_move(int x, int y)`

Moves the mouse to absolute screen coordinates.

#### `void mouse_move_relative(int dx, int dy)`

Moves the mouse relative to the current cursor position.

***

#### `void mouse_left_click()`

Left button click.

#### `void mouse_right_click()`

Right button click.

#### `void mouse_middle_click()`

Middle button click.

Each sends DOWN → small wait → UP.

***

#### `void mouse_scroll(int amount)`

Scroll amount in “wheel notches”:

* positive → scroll up
* negative → scroll down

***

#### `void send_mouse_input(int64 dx, int64 dy, uint flags, uint mouse_data)`

Send input manually via raw input.

***

## **Util**

`int64 get_tickcount64()`

* GetTickCount64()

***

## **Examples**

### Find a window & print info

```cpp
string title;
string cls;

uint64 hwnd = find_window("Untitled - Notepad");

if (hwnd != 0)
{
    int x, y, w, h;
    get_window_rect(hwnd, x, y, w, h);

    get_window_title(hwnd, title);
    get_window_class(hwnd, cls);

    log("Title: " + title);
    log("Class: " + cls);
    log("Rect: " + x + "," + y + "  size " + w + "x" + h);
}
```

***

### Clipboard

```cpp
copy_to_clipboard("AngelScript clipboard test こんにちは 🌸");

string out;
copy_from_clipboard(out);

log("Clipboard: " + out);
```

***

### Global keyboard

<pre class="language-cpp"><code class="lang-cpp">// Type “HELLO”
win_key_press(0x48); // H
win_key_press(0x45); // E
win_key_press(0x4C); // L
win_key_press(0x4C); // L
<strong>win_key_press(0x4F); // O
</strong>
// Ctrl+V
win_key_down(0x11); // Ctrl
win_key_press(0x56); // V
win_key_up(0x11);
</code></pre>

***

### Send chars to a window

```cpp
uint64 hwnd = find_window("Untitled - Notepad");

set_foreground_window(hwnd);

send_char(hwnd, "H");
send_char(hwnd, "i");
send_char(hwnd, " ");
send_char(hwnd, "🌸");

send_key(hwnd, 0x0D); // Enter
```

***

### Mouse interaction

```cpp
mouse_move(100, 200);
mouse_left_click();

mouse_move_relative(50, 0);
mouse_right_click();

mouse_scroll(3);   // up
mouse_scroll(-3);  // down
```

## Full API Test

```cpp
const string TARGET_TITLE = "Untitled - Notepad"; // change as you like

void log_line(const string &in msg)
{
    log("[AS-WINAPI] " + msg);
}

void dump_window_info(uint64 hwnd)
{
    if (hwnd == 0)
    {
        log_line("HWND = 0");
        return;
    }
    
    log_line("HWND = 0x" + formatInt(int64(hwnd), "H"));
    
    string title, cls;
    if (get_window_title(hwnd, title))
    log_line("  title: " + title);
    else
    log_line("  title: <failed>");
    
    if (get_window_class(hwnd, cls))
    log_line("  class: " + cls);
    else
    log_line("  class: <failed>");
    
    int x, y, w, h;
    if (get_window_rect(hwnd, x, y, w, h))
    log_line("  rect:  x=" + x + " y=" + y + " w=" + w + " h=" + h);
    else
    log_line("  rect:  <failed>");
    
    uint tid, pid;
    if (get_window_thread_process_id(hwnd, tid, pid))
    log_line("  tid=" + tid + " pid=" + pid);
    else
    log_line("  tid/pid: <failed>");
}

uint64 get_target_hwnd()
{
    log_line("Target window title: " + TARGET_TITLE);
    
    uint64 hwnd = find_window(TARGET_TITLE);
    if (hwnd == 0)
    {
        log_line("Window not found.");
        return 0;
    }
    
    log_line("Found window.");
    dump_window_info(hwnd);
    
    bool fg = set_foreground_window(hwnd);
    log_line("set_foreground_window -> " + (fg ? "true" : "false"));
    
    return hwnd;
}

void test_mouse_basic()
{
    log_line("=== TEST: mouse movement & clicks ===");
    log_line("Move your eyes to where the cursor goes. :)");
    
    mouse_move(100, 100);
    mouse_left_click();
    log_line("  mouse_move(100,100) + left click");
    
    mouse_move_relative(80, 0);
    mouse_right_click();
    log_line("  mouse_move_relative(80,0) + right click");
    
    mouse_move_relative(0, 60);
    mouse_middle_click();
    log_line("  mouse_move_relative(0,60) + middle click");
    
    mouse_scroll(3);
    mouse_scroll(-3);
    log_line("  mouse_scroll(3) then mouse_scroll(-3)");
}

void test_clipboard()
{
    log_line("=== TEST: clipboard ===");
    
    string src = "Hello from AngelScript WinAPI! こんにちは 🌸";
    bool okSet = copy_to_clipboard(src);
    log_line("  copy_to_clipboard -> " + (okSet ? "true" : "false"));
    
    string got;
    bool okGet = copy_from_clipboard(got);
    log_line("  copy_from_clipboard -> " + (okGet ? "true" : "false"));
    log_line("  clipboard text: " + got);
}

void test_send_char_key(uint64 hwnd)
{
    log_line("=== TEST: send_char / send_key ===");
    
    if (hwnd == 0)
    {
        log_line("No hwnd, skipping send_char/send_key test.");
        return;
    }
    
    log_line("Make sure the target window has a focused text field.");
    
    // Send "Hi " + a flower
    bool ok1 = send_char(hwnd, "H");
    bool ok2 = send_char(hwnd, "i");
    bool ok3 = send_char(hwnd, " ");
    bool ok4 = send_char(hwnd, "🌸"); // first UTF-16 unit is used
    
    log_line("  send_char H -> " + (ok1 ? "true" : "false"));
    log_line("  send_char i -> " + (ok2 ? "true" : "false"));
    log_line("  send_char ' ' -> " + (ok3 ? "true" : "false"));
    log_line("  send_char 🌸 -> " + (ok4 ? "true" : "false"));
    
    // send Enter via WM_KEYDOWN/UP
    const uint VK_RETURN = 0x0D;
    bool okEnter = send_key(hwnd, VK_RETURN);
    log_line("  send_key(VK_RETURN) -> " + (okEnter ? "true" : "false"));
}

void test_global_keys()
{
    log_line("=== TEST: global key_press ===");
    log_line("Make sure some text field is focused if you want to see output.");
    
    // Type 'HELLO'
    const uint VK_H = 0x48;
    const uint VK_E = 0x45;
    const uint VK_L = 0x4C;
    const uint VK_O = 0x4F;
    
    win_key_press(VK_H, 40);
    win_key_press(VK_E, 40);
    win_key_press(VK_L, 40);
    win_key_press(VK_L, 40);
    win_key_press(VK_O, 40);
    
    // Ctrl+V (paste)
    const uint VK_CONTROL = 0x11;
    const uint VK_V       = 0x56;
    
    win_key_down(VK_CONTROL);
    win_key_press(VK_V, 30);
    win_key_up(VK_CONTROL);
    
    log_line("  typed HELLO and sent Ctrl+V");
}

int main()
{
    log_line("=== AS WinAPI Input Test START ===");
    
    uint64 hwnd = get_target_hwnd();
    
    test_mouse_basic();
    test_clipboard();
    test_global_keys();
    test_send_char_key(hwnd);
    
    log_line("=== AS WinAPI Input Test END ===");
    return 1; // keep script loaded if your host uses this
}


```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/win-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
