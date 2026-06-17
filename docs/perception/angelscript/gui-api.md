> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/gui-api.md).

# GUI API

This page documents the **AngelScript GUI API** used to build and interact with the Perception.cx UI.

> ❗ All GUI types are **owned** and cleaned up by the engine.\
> You never `delete` or free them from AngelScript.

***

### Overview

```cpp
 /* This gives you position and size of the main GUI window */
void get_gui_position(float &out x, float &out y)
void get_gui_size(float &out w, float &out h)
```

Typical usage flow:

1. Create a **subtab** under one of the fixed top-level tabs.
2. Create a **panel** inside that subtab.
3. Add UI elements (checkboxes, keybinds, sliders, inputs, color pickers, lists, multi/single-select, buttons) to that panel.
4. Read/update values in your `main()` or `on_frame()` loop.
5. Optionally, attach a **callback** to a button.

Example:

```cpp
subtab_t st = create_subtab(0, "My Script");
if (!st.is_valid())
{
    log("[GUI] failed to create subtab");
    return -1;
}

panel_t p = st.add_panel("Main Panel", false); // false = large panel

checkbox_t cb = p.add_checkbox("Enable Feature", false);
slider_double_t dist = p.add_slider_double("Distance", "m", 100.0, 0.0, 500.0, 1.0);

// Each frame:
void on_frame(int cb_index, int data_index)
{
    bool enabled = cb.get();
    double d = dist.get();
    // ... use enabled + d ...
}
```

***

### Subtabs & Panels

#### `subtab_t`

A `subtab_t` represents a subtab under one of the fixed top-level tabs.

**Create**

```cpp
subtab_t create_subtab(int parent_tab, const string &in name);
```

* `parent_tab`: 0–(FIXED\_TAB\_COUNT-1) – which main tab to attach to.
* `name`: label shown in the UI subtab bar.

**Methods**

```cpp
panel_t add_panel(const string &in name, bool is_small);
bool is_valid() const;
void subtab_t::set_active(bool active);
void panel_t::set_active(bool active);
```

* `add_panel` – creates a new panel inside this subtab.
  * `is_small = true` → small panel layout; `false` → normal/large.
* `is_valid()` – `true` if the handle is non-null. Only needed for error-checking in `main()`.

#### `panel_t`

Represents a panel inside a subtab.\
All other UI elements are added **to a panel**.

You don’t manually free panels; they’re destroyed when the owning subtab is destroyed (usually when the script unloads).

***

### Checkbox

#### Create

```cpp
checkbox_t panel_t::add_checkbox(
    const string &in name,
    bool initial,
    bool draw_title = true,
    bool find_protect = false,
    bool draw_just_label = false
);
```

* `name`: label.
* `initial`: initial on/off state.
* `draw_title`: whether to render the title text.
* `find_protect`: if `true`, protects the element from naive find/replace patterns (internal anti-scan behavior).
* `draw_just_label`: When enabled, the checkbox is non-interactive and functions purely as a label. This is useful when you only want to attach a color picker or keybind without toggle behavior.

> ❗ Design rule:
>
> * A checkbox can act as a **parent** for either:
>   * up to **two color pickers**, or
>   * up to **two keybinds** or
>   * one **colorpicker +** one **keybind**
> * Color pickers / keybind must be added **immediately after** the checkbox on the panel.

#### Methods

```cpp
bool checkbox_t::get() const;
void checkbox_t::set(bool v);
void checkbox_t::set_active(bool active);
```

Example:

```cpp
checkbox_t cb = p.add_checkbox("Enable ESP", false);
cb.set(true);
bool enabled = cb.get();
```

***

### Keybind

Keybinds let you bind a virtual-key and mode to a checkbox-controlled feature.

#### Create

```cpp
keybind_t panel_t::add_keybind(
    const string &in name,
    int key,
    const string &in mode,
    bool draw_title = true,
    bool find_protect = false
);
```

* **Must** appear right after its parent checkbox.
* `key`: a Win32 virtual-key code (e.g. `0x2E` for Delete, `0x2C` for PrintScreen).
* `mode`: `"off"`, `"on"`, `"single"`, `"toggle"`, or `"always_on"`.

#### Methods

```cpp
void keybind_t::get(int &out key, string &out mode) const;
void keybind_t::set(int key, const string &in mode);
void keybind_t::set_active(bool active);
bool keybind_t::is_pressed() const
```

Example:

```cpp
checkbox_t cb = p.add_checkbox("Aimbot", false);
keybind_t kb = p.add_keybind("Aimbot Hotkey", 0x2E, "toggle");

int k; string m;
kb.get(k, m); // -> 0x2E, "toggle"

kb.set(0x2C, "single");
kb.get(k, m); // -> 0x2C, "single"
```

***

### Color Picker

Color pickers store RGBA as **0–255 floats**.

#### Create

```cpp
color_picker_t panel_t::add_color(
    const string &in name,
    const array<float> &in rgba,
    bool find_protect = false
);
```

* Must follow a checkbox or keybind within that chain (according to your UI layout rules).
* `rgba` – `array<float>` of size 4: `{R, G, B, A}`, each in \[0–255].

#### Methods

```cpp
void color_picker_t::get(array<float> &out rgba) const;
void color_picker_t::set(const array<float> &in rgba);
void color_picker_t::set_active(bool active);
```

Example:

```cpp
checkbox_t cb = p.add_checkbox("Chams", true);

array<float> rgba = {255.0f, 0.0f, 0.0f, 255.0f};
color_picker_t col = p.add_color("Enemy Color", rgba);

// read back
array<float> out = array<float>(4);
col.get(out); // out[0..3] now contain 0–255

// change
array<float> new_rgba = {77.0f, 204.0f, 26.0f, 255.0f};
col.set(new_rgba);
```

***

### Sliders

#### Double slider

```cpp
slider_double_t panel_t::add_slider_double(
    const string &in name,
    const string &in postfix,
    double value,
    double minv,
    double maxv,
    double step,
    bool draw_title = true,
    bool find_protect = false
);
```

#### Methods

```cpp
double slider_double_t::get() const;
void   slider_double_t::set(double v);
void   slider_double_t::set_active(bool active);
```

Example:

```cpp
slider_double_t dist = p.add_slider_double("Distance", "m", 150.0, 0.0, 500.0, 1.0);
double d0 = dist.get();
dist.set(275.0);
double d1 = dist.get();
```

#### Int slider

```cpp
slider_int_t panel_t::add_slider_int(
    const string &in name,
    const string &in postfix,
    int value,
    int minv,
    int maxv,
    int step,
    bool draw_title = true,
    bool find_protect = false
);
```

#### Methods

```cpp
int  slider_int_t::get() const;
void slider_int_t::set(int v);
void slider_int_t::set_active(bool active);
```

***

### Input Text Box

```cpp
input_t panel_t::add_input(
    const string &in name,
    const string &in initial,
    bool draw_title = true,
    bool find_protect = false
);

string input_t::get() const;
void   input_t::set(const string &in v);
```

Example:

```cpp
input_t user = p.add_input("Username", "DefaultUser");
string s0 = user.get();
user.set("AS_User");
string s1 = user.get();
```

***

### List

Lists are 2-column rows (`info1`, `info2`).

#### Create

```cpp
list_t panel_t::add_list(
    const string &in name,
    const array<dictionary@> &in members,
    bool draw_title = true,
    bool find_protect = false
);
```

Each `dictionary` is expected to have:

* `"info1"` – string
* `"info2"` – string

#### Methods

<pre class="language-cpp"><code class="lang-cpp">int list_t::get() const;
int  list_t::get_count() const;
void list_t::clear();
void list_t::append(const string &#x26;in info1, const string &#x26;in info2);
void list_t::set_active(bool active);
<strong>void list_t::remove(int index) const;
</strong>void list_t::highlight(int index) const;
void list_t::remove_highlight(int index) const;
void list_t::hide(int index) const;
void list_t::show(int index) const;
</code></pre>

Example:

```cpp
array<dictionary@> members;
dictionary@ d0 = dictionary();
d0.set("info1", "Row0-Col0");
d0.set("info2", "Row0-Col1");
members.insertLast(d0);

dictionary@ d1 = dictionary();
d1.set("info1", "Row1-Col0");
d1.set("info2", "Row1-Col1");
members.insertLast(d1);

list_t lst = p.add_list("Test List", members);
int c0 = lst.get_count();
lst.append("Extra", "Info");
int c1 = lst.get_count();
```

***

### Multi-Select

A multi-select lets you toggle multiple options.

#### Create

```cpp
multi_select_t panel_t::add_multi_select(
    const string &in name,
    const array<dictionary@> &in options,
    bool is_expandable,
    bool draw_title = true,
    bool find_protect = false
);
```

Each `dictionary` in `options` should contain:

* `"label"` – string
* `"selected"` – bool (optional; defaults to false)

#### Methods

```cpp
void multi_select_t::get(array<bool> &out states) const;
void multi_select_t::set(int index, bool state);
void multi_select_t::set_active(bool active);
```

Example:

```cpp
array<dictionary@> mopts;

dictionary@ m0 = dictionary();
m0.set("label", "A");
m0.set("selected", true);
mopts.insertLast(m0);

dictionary@ m1 = dictionary();
m1.set("label", "B");
m1.set("selected", false);
mopts.insertLast(m1);

multi_select_t ms = p.add_multi_select("Modes", mopts, true);

array<bool> states;
ms.get(states); // states.length=2, [true,false]

ms.set(1, true);
ms.get(states); // [true,true]
```

***

### Single-Select

Single-select is a dropdown/radio list with a single active index.

#### Create

```cpp
single_select_t panel_t::add_single_select(
    const string &in name,
    const array<string> &in options,
    int initial_index,
    bool is_expandable,
    bool draw_title = true,
    bool find_protect = false
);
```

#### Methods

```cpp
int  single_select_t::get() const;
void single_select_t::set(int index);
void single_select_t::set_active(bool active);
```

Example:

```cpp
array<string> sopts = { "One", "Two", "Three" };
single_select_t ss = p.add_single_select("Select One", sopts, 1, true);

int idx0 = ss.get(); // 1
ss.set(2);
int idx1 = ss.get(); // 2
```

***

### Buttons & Callbacks

Buttons are clickable UI elements with an AngelScript callback.

#### Funcdef

```cpp
funcdef void button_callback_t();
```

#### Create

```cpp
button_t panel_t::add_button(
    const string &in name,
    button_callback_t@ cb,
    bool find_protect = false
);
```

* `cb` is a function with signature `void f()`.

#### Methods

```cpp
void button_t::set_active(bool active);
```

#### Example

```cpp
int g_hits = 0;

void OnTestButton()
{
    g_hits++;
    Print("[GUI] Test button clicked " + g_hits + " times");
}

int main()
{
    subtab_t st = create_subtab(0, "Button Demo");
    if (!st.is_valid()) return -1;

    panel_t p = st.add_panel("Main", false);
    button_t btn = p.add_button("Click Me", @OnTestButton);

    return 1;
}
```

When you click the button in the UI, `OnTestButton` will be executed.

***

## `bool gui_active()`

Checks if the gui is currently visible or not

***

### Finding Existing Elements (`find_*`)

If your script needs to **attach** to UI created elsewhere (or from config), use the `find_*` helpers.

Each `find_*` searches by:

* `tab` – top-level tab index (0..FIXED\_TAB\_COUNT-1)
* `subtab` – subtab name (string)
* `panel` – panel name(string)
* `name` – element label (string)
* element type (encoded in the function name)

#### Signatures

```cpp
checkbox_t      find_checkbox(int tab, const string &in subtab, const string &in panel, const string &in name);
slider_double_t find_slider_double(int tab, const string &in subtab, const string &in panel, const string &in name);
slider_int_t    find_slider_int(int tab, const string &in subtab, const string &in panel, const string &in name);
input_t         find_input(int tab, const string &in subtab, const string &in panel, const string &in name);
multi_select_t  find_multi_select(int tab, const string &in subtab, const string &in panel, const string &in name);
single_select_t find_single_select(int tab, const string &in subtab, const string &in panel, const string &in name);
keybind_t       find_keybind(int tab, const string &in subtab, const string &in panel, const string &in name);
button_t        find_button(int tab, const string &in subtab, const string &in panel, const string &in name);
color_picker_t  find_color(int tab, const string &in subtab, const string &in panel, const string &in name);
list_t          find_list(int tab, const string &in subtab, const string &in panel, const string &in name);
```

These return handle `0` if no element is found.

Example:

```cpp
void on_frame()
{
    checkbox_t cb = find_checkbox(0, "AS GUI Test", "Panel Name", "Color Feature");
    if (cb != 0)
    {
        bool v = cb.get();
        // use v ...
    }

    slider_double_t sld = find_slider_double(0, "AS GUI Test", "Panel Name", "Distance Slider");
    if (sld != 0)
    {
        double d = sld.get();
        // ...
    }
}
```

> ❗ Internally, `find_*` marks elements as "referenced" for cleanup when the script unloads.\
> You don’t need (and must not try) to free them manually.

***

### Config Helpers

These are global functions for saving/loading the UI configuration (all tabs, subtabs, elements).

```cpp
string construct_config();
void   apply_config(const string &in cfg);
```

* `construct_config()` – builds a serialized config string of the current UI state.
* `apply_config(cfg)` – applies a serialized config string.

Example:

```cpp
void save_ui()
{
    string cfg = construct_config();
    // write cfg to file or elsewhere
}

void load_ui(const string &in cfg)
{
    apply_config(cfg);
}
```

***

### Name Prefixing for Elements (`##prefix_`)

Multiple UI elements with the **same visible name** are supporte&#x64;**,** but the **configuration system cannot uniquely identify them** unless you explicitly assign a prefix.

The `##prefix_` syntax allows you to attach an **internal unique ID** to an element while keeping the **visible label unchanged**.

***

#### ✔ What Prefixing Does

* The part **after** `##prefox_` is the **visible label** shown in the UI and the rest is Unique ID.
* Prefixing is **optional**, but required if you want your elements to save/load uniquely in configs.
* *find\_ functions completely ignore the prefix*\* and search only by the visible label.

***

#### ✔ Example

```cpp
// Both show "Player Name" on screen
p.add_input("##elem1_Player Name", "Alex");
p.add_input("##elem2_Player Name", "Alex");
```

Both inputs look identical to the user, but internally:

* Internal IDs: `elem1_Player Name`, `elem2_Player Name`
* Visible name: `Player Name`
* Config system will save/load each one correctly.

***

### Behavior Summary

| System / Functionality      | Prefix Used?                    | Notes                                                        |
| --------------------------- | ------------------------------- | ------------------------------------------------------------ |
| **UI Rendering**            | ❌ No — prefix hidden            | Only the text after `##` is shown.                           |
| **Internal ID / Config**    | ✅ Yes — full prefixed name used | Required for unique config entries.                          |
| *find\_ API*\*              | ❌ No — prefix ignored           | Searches only by visible name.                               |
| **Duplicate visible names** | ✔ Allowed, even without prefix  | But: config will **not** differentiate them unless prefixed. |

***

### ⚠ Important Notes

#### 1. Duplicate names *without* prefix

These **work in the UI**, but the configuration system will treat them as the **same element**, causing:

* overwritten values
* incorrect load order
* mismatched element states

#### 2. Duplicate names *with* prefix

These behave perfectly:

* visible name is the same
* internal ID is unique
* config system saves & loads correctly
* find\_\* still searches by visible name only

#### 3. find\_\* and duplicates

Because find\_\* searches by visible name, if you have two labels both named `"Player Name"`, then:

```cpp
auto inp = find_input(0, "Tab", "Panel", "Player Name");
```

…it will always return the **first** one created, regardless of prefixes.

***

### When Should You Use Prefixing?

Use `##prefix_` whenever:

* You create multiple repeated UI blocks (e.g. per-player, per-item, per-weapon).
* You have identical element names inside the same panel or subtab.
* You want your configuration to properly remember each element’s value.

***

### Quick Example

```cpp
panel_t p = st.add_panel("Players", false);

// These two will look identical to the user
p.add_slider_double("##p1_Speed", 0.0, 100.0, 50.0);
p.add_slider_double("##p2_Speed", 0.0, 100.0, 60.0);

// Without prefixes, the config system would conflict them
// With prefixes, each one saves/loads separately
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/gui-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
