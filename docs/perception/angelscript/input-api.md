> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/input-api.md).

# Input API

The Input API provides full access to mouse, keyboard, and scroll states from AngelScript.\
All functions are **safe** — no pointers or raw memory are exposed to scripts.

***

### 📍 Mouse

#### Get Mouse Position

```cpp
void get_mouse_pos(float &out x, float &out y)
```

Returns the current mouse position **within the viewport**.

***

#### Get Mouse Position Relative To Desktop

```cpp
void get_mouse_pos_desktop(float &out x, float &out y)
```

Returns the absolute mouse position in **desktop coordinates** (OS-space).

***

#### Get Mouse Movement Delta

```cpp
void get_mouse_delta(float &out dx, float &out dy)
```

Returns the **delta movement** of the mouse since the last frame (viewport space).

***

#### Get Mouse Movement Delta Relative To Desktop

```cpp
void get_mouse_delta_desktop(float &out dx, float &out dy)
```

Returns the **desktop-space delta** of mouse movement since the last frame.

***

#### Was Mouse Movement Received

```cpp
bool mouse_movement_received()
```

Returns `true` if any mouse movement has been received during this frame.

***

#### Get Scroll Delta

```cpp
float get_scroll_delta()
```

Returns the scroll wheel delta value for the current frame.

***

#### Is Hovered Over Region

```cpp
bool is_hovered(float x, float y, float w, float h)
```

Returns `true` if the mouse is hovering over a given rectangular region.

* `(x, y)` — Top-left corner of the region.
* `(w, h)` — Width and height of the region.

***

### ⌨️ Keyboard

Keyboard functions use **virtual key (VK)** codes (standard Windows-style, e.g., `0x41` = A).

***

#### Key State Queries

Each of the following functions takes an `int vk` (the virtual key code):

```cpp
bool key_down(int vk)
bool key_raw_down(int vk)
bool key_fired(int vk)
bool key_toggle(int vk)
bool key_singlepress(int vk)
bool key_prev_down(int vk)
```

| Function          | Description                                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------------------- |
| `key_down`        | Returns `true` if the key is currently held down.                                                         |
| `key_raw_down`    | Returns raw (unfiltered) down state.                                                                      |
| `key_fired`       | Returns `true` if the key transitioned from up→down this frame (WinProc like input for input boxes, etc). |
| `key_toggle`      | Returns toggle state (for keys like CapsLock).                                                            |
| `key_singlepress` | True only once per press event (useful for UI).                                                           |
| `key_prev_down`   | Returns `true` if the key was down in the previous frame.                                                 |

***

#### Get Key State

```cpp
void get_key_state(int vk,
    bool &out raw_down, bool &out down,
    bool &out fired, bool &out toggle,
    bool &out singlepress, bool &out prev_down)
```

Fetches **all key state flags at once** for the specified key.

***

#### Get Keys Down

```cpp
void get_keys_down(array<int> &out indices)
```

Fills an array with the **virtual key codes** of all keys currently held down.

Example:

```cpp
array<int> pressed;
get_keys_down(pressed);

for (uint i = 0; i < pressed.length(); ++i)
{
    print("Key down: " + get_key_name(pressed[i]) + "\n");
}
```

***

### 🔡 Text Input

#### Get Latest Key Input

```cpp
string get_recent_key_input()
```

Returns a string containing the most recently typed characters since the last frame.\
Use this for text fields or console input.

***

#### Get Key Name By VK

```cpp
string get_key_name(int vk)
```

Returns a **human-readable name** for the specified virtual key code.\
Example: `get_key_name(0x41)` → `"A"`

***

### 🧠 Notes

* All keyboard queries use the Windows-style **VK codes** (`0x01` = LMB, `0x41` = A, `0x1B` = ESC, etc.).
* Mouse functions operate in **viewport space** unless the “desktop” variant is used.
* Functions are designed to be **safe and lightweight** — they only read internal copies of state.
* You can safely call any of these from UI, game logic, or render scripts.

***

#### 🧩 Example Usage

```cpp
void update_ui()
{
    float mx, my;
    get_mouse_pos(mx, my);

    if (is_hovered(100,100,200,80))
        draw_rect_filled(100,100,200,80, 50,120,255,180, 6.0f, RR_TOP_LEFT|RR_TOP_RIGHT);

    if (key_fired(0x1B)) // ESC key
        print("Escape pressed!\n");

    string input = get_recent_key_input();
    if (input.length() > 0)
        draw_text("Typed: " + input, mx + 10, my + 10,
                  255,255,255,255, get_font18(), TE_NONE, 0,0,0,0, 0.0f, true);
}
```

***

#### Version


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/input-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
