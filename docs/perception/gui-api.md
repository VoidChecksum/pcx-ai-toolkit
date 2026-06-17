> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/gui-api.md).

# GUI API

All GUI natives are auto-registered into every loaded script.

The API is in two parts:

* **Part 1 — sidebar sections + widgets.** A `sidebar_section_t` is a select-button in the host sidebar plus a content panel auto-attached to the main frame. The panel renders only when the section's button is selected. Widgets are created on the section directly.
* **Part 2 — frames, layers, custom widgets, menus, file pickers.** Lower-level primitives for floating windows and custom drawing.

All GUI handles are `int64`-backed. The script doesn't own the underlying resources — calling a destructor on a handle is a noop. At script unload, every handle the script created gets cleaned up automatically.

## Sidebar sections

```cpp
sidebar_section_t create_sidebar_section(string name, string icon);
void              create_sidebar_separator();
```

`name` renders as the sidebar label. `icon` accepts a codicon string (e.g. `"\xEE\xAC\xA3"` for file-code U+EB23) or `""` for no icon.

Each section is a radio-style sidebar entry: clicking one auto-deselects siblings and shows that section's panel.

```cpp
void section.set_active(bool active);   // toggle selection programmatically
```

### Widget builders on `sidebar_section_t`

Every widget builder returns a typed handle. Each is also `int64`-backed; pass to other natives via the typed name.

```cpp
label_t              section.create_label(string text, ui_align align);
void                 section.create_separator();
button_t             section.create_button(string label, ui_align align);
checkbox_t           section.create_checkbox(string label, bool initial);
slider_t             section.create_slider(string label, float64 initial, float64 minv, float64 maxv, float64 step);
slider_icon_t        section.create_slider_icon(string icon, float64 initial, float64 minv, float64 maxv, float64 step);
value_input_t        section.create_value_input(string label, float64 initial, float64 minv, float64 maxv, float64 step);
options_t            section.create_options(string label, array<string> items, int64 selected);
multi_options_t      section.create_multi_options(string label, array<string> items, int64 selected_mask);
dropdown_t           section.create_dropdown(string label, array<string> items, int64 selected);
multi_dropdown_t     section.create_multi_dropdown(string label, array<string> items, int64 selected_mask);
list_t               section.create_list(string label, array<string> info1, array<string> info2,
                                          bool selectable, int64 selected,
                                          int64 visible_rows, bool filterable);
inline_button_t      section.create_inline_button(string label, float64 width, string icon);
inline_text_input_t  section.create_inline_text_input(string initial, float64 width, string placeholder);
tabs_t               section.create_tabs(array<string> items, int64 selected);
keybind_t            section.create_keybind(string label);
progress_bar_t       section.create_progress_bar(string label, float64 initial, float64 minv, float64 maxv, bool show_pct);
spinner_t            section.create_spinner(string label);
range_slider_t       section.create_range_slider(string label, float64 minv, float64 maxv,
                                                  float64 lo, float64 hi, float64 step);
table_t              section.create_table(string label, array<string> col_names,
                                           array<float64> col_widths, int64 visible_rows);
text_input_t         section.create_text_input(string label, string initial, int64 max_lines);
text_editor_t        section.create_text_editor(string label, string initial, int64 visible_lines, string lexer);
colorpicker_t        section.create_colorpicker(string label, color initial);
```

## Common widget operations

Every widget type (except `text_editor_t`, which has no `set_active`) supports:

```cpp
void widget.set_active(bool active);
void widget.set_tooltip(string s);
void widget.on_change(int64 fn_handle);   // closure: void cb(int64 widget_handle)
```

`on_change` fires on `CALLBACK_VALUE_CHANGED` — which means click for buttons, value mutation for sliders / checkboxes / dropdowns / etc. Pass the closure via `cast<int64>(my_callback)`.

## Per-widget typed get / set

```cpp
// label
void label.set_text(string s);

// button
void button.attach_to(button_t other);   // group buttons into one row

// checkbox
bool checkbox.get();
void checkbox.set(bool v);

// slider, slider_icon, value_input
float64 X.get();
void    X.set(float64 v);

// options, dropdown, tabs
int64 X.get();
void  X.set(int64 i);

// multi_options, multi_dropdown
int64 X.get_mask();
void  X.set_mask(int64 m);

// list
int64 list.get_selected();
void  list.set_selected(int64 i);
void  list.set_items(array<string> info1, array<string> info2);
int64 list.size();

// inline_text_input, text_input, text_editor
string X.get();
void   X.set(string s);

// keybind
void  keybind.bind(int64 vk, bool ctrl, bool shift, bool alt, keybind_mode mode);
bool  keybind.is_active();      // true when any binding is currently active per its mode; poll to react to activation
int64 keybind.binding_count();  // number of bindings on this row

// progress_bar
void progress_bar.set(float64 v);

// range_slider — split lo/hi getters since there's no natural pair type
float64 range_slider.get_lo();
float64 range_slider.get_hi();
void    range_slider.set(float64 lo, float64 hi);

// table
void  table.add_row(array<string> cells);
void  table.clear();
int64 table.size();

// colorpicker — uses the registered `color` type
void  colorpicker.attach_to(colorpicker_t other);
color colorpicker.get();
void  colorpicker.set(color c);
```

## Frames (Part 2)

`frame_t` wraps any of four host frame kinds — distinguished by which factory you call:

```cpp
frame_t create_frame(string name, vec2 pos, vec2 size, layer_t layer);
//   raw frame, no chrome. Pass 0 for layer to use the default layer.
frame_t create_default_frame(string name, vec2 pos, vec2 size, layer_t layer);
//   frame with title bar / logo / drag chrome.
frame_t create_draggable_frame(string name, vec2 pos, vec2 size, layer_t layer);
frame_t create_popup(string name, vec2 pos, vec2 size, layer_t layer);
```

```cpp
void    frame.set_pos(vec2 pos);
void    frame.set_size(vec2 size);
vec2    frame.get_pos();
vec2    frame.get_size();
void    frame.set_visible(bool v);
bool    frame.is_visible();
void    frame.set_anchors(int64 mask);   // ui_anchor::* OR'd
void    frame.attach(frame_t parent);
void    frame.set_float(int64 hash, float64 v);   // widget_attr::* keys
void    frame.install_hook(int64 hook_id, int64 fn_handle);
void    frame.remove_hook(int64 hook_id);
void    frame.set_focused();
frame_t get_focused_frame();
bool    ui_is_focused();
```

## Layers

A layer is a z-stacked frame group; frames in higher layers paint over lower ones.

```cpp
layer_t create_layer(string name, bool input_passthrough, bool force_topmost);
layer_t get_default_layer();
int64   layer_count();

void  layer.promote_to_top();
void  layer.set_visible(bool v);
int64 layer.frame_count();
```

## Custom widgets on a script-owned frame

Drop a `widget_t` into one of your `frame_t`s for a custom render callback that fires every tick during the frame's render pass:

```cpp
widget_t create_widget(frame_t parent, string name, int64 execute_cb_handle, bool consume_input);
//   execute_cb shape: void cb(int64 widget_handle) — called every tick.

void widget.set_pos(vec2 pos);
void widget.set_size(vec2 size);
void widget.set_active(bool v);
void widget.set_tooltip(string s);
void widget.set_float(int64 hash, float64 v);
void widget.set_anchors(int64 mask);
void widget.install_hook(int64 hook_id, int64 fn_handle);
void widget.remove_hook(int64 hook_id);
```

## Menus

A `menu_t` is a context menu — a popup list of items. Attach it to any widget to make right-click on that widget open it.

```cpp
menu_t create_menu();
void   menu.add_item(string label, int64 on_click_cb, string shortcut, string icon);
//   shortcut: visible label only (e.g. "Ctrl+C"); not bound by add_item itself.
//   icon: codicon string or "" for none.
//   on_click_cb shape: void cb(int64 menu_user_data).
void   menu.add_separator();
```

`menu_t.attach_to_widget` is split per widget type because enma's overloading is by arity, not by parameter type. Use the variant matching the widget you're attaching to:

```cpp
void menu.attach_to_widget(widget_t target);
void menu.attach_to_button(button_t target);
void menu.attach_to_label(label_t target);
void menu.attach_to_checkbox(checkbox_t target);
void menu.attach_to_slider(slider_t target);
void menu.attach_to_slider_icon(slider_icon_t target);
void menu.attach_to_value_input(value_input_t target);
void menu.attach_to_options(options_t target);
void menu.attach_to_multi_options(multi_options_t target);
void menu.attach_to_dropdown(dropdown_t target);
void menu.attach_to_multi_dropdown(multi_dropdown_t target);
void menu.attach_to_list(list_t target);
void menu.attach_to_inline_button(inline_button_t target);
void menu.attach_to_inline_text_input(inline_text_input_t target);
void menu.attach_to_tabs(tabs_t target);
void menu.attach_to_keybind(keybind_t target);
void menu.attach_to_progress_bar(progress_bar_t target);
void menu.attach_to_spinner(spinner_t target);
void menu.attach_to_range_slider(range_slider_t target);
void menu.attach_to_table(table_t target);
void menu.attach_to_text_input(text_input_t target);
void menu.attach_to_text_editor(text_editor_t target);
void menu.attach_to_colorpicker(colorpicker_t target);
```

## File picker

```cpp
file_picker_t create_file_picker(string title, string start_path,
                                  string filter_extension, bool folder_mode);
void   picker.open();
void   picker.close();
string picker.get_selected();
```

## Theme

```cpp
bool  is_dark_theme();
void  set_dark_theme(bool dark);
color get_theme_color(int64 color_hash);
void  set_theme_color(int64 color_hash, color c);
```

`color_hash` is a value from the `ui_color` enum.

## Toasts and queries

```cpp
void show_toast(toast_kind kind, string title, string msg);
bool gui_active();
```

## Enums

All exposed without needing a header import:

| Enum           | Values                                                                                                                     |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `ui_anchor`    | `none`, `left`, `right`, `top`, `bottom`, `all`                                                                            |
| `ui_edge`      | `left`, `top`, `right`, `bottom`                                                                                           |
| `ui_align`     | `left`, `center`, `right`                                                                                                  |
| `ui_layout`    | `none`, `vertical`, `horizontal`                                                                                           |
| `ui_hook`      | 33 hook IDs incl. `pre_execute`, `post_execute`, `clicked`, `right_clicked`, `should_render`, `editor_*`, `widget_execute` |
| `ui_callback`  | `value_changed`, `item_activated`                                                                                          |
| `widget_attr`  | well-known position / size / scroll / rounding hashes                                                                      |
| `ui_color`     | 35 color hashes (`bg`, `text`, `accent`, `frame_bg`, `sidebar_bg`, `element_button_bg`, etc.)                              |
| `keybind_mode` | `off`, `on`, `single`, `toggle`, `always_on`                                                                               |
| `toast_kind`   | `info`, `success`, `warning`, `error`                                                                                      |

## Lifecycle and cleanup

GUI resources you create (sections, frames, layers, custom widgets, menus, file pickers) are tracked per-script and torn down automatically at script unload. You don't need to destroy them manually — the destructor on each handle is a noop.

Caveats:

* **Sidebar slots persist.** Sections you create occupy a sidebar slot for the lifetime of the host. Hot-reloading scripts that create many sections will leave stale slots in the sidebar.
* **Separators** stay visible after unload (no remove path).

Hook callbacks fire on the UI thread. Heavy work inside a `pre_execute` or `on_change` (running every tick on every widget) shows up in profile — keep them lightweight.

## Example

A comprehensive script exercising most of the widget builders, `on_change` plumbing through typed handles, an attached-button row, an attached colorpicker chain, a context menu, a tabs widget with per-tab content, and a routine polling `keybind.is_active()`.

```cpp
sidebar_section_t g_sec;
menu_t            g_menu;

keybind_t g_kb_aim;
keybind_t g_kb_esp;
bool g_aim_was_active = false;
bool g_esp_was_active = false;
int64 g_kb_routine = 0;

tabs_t       g_tabs;
label_t      g_t0_label; slider_t  g_t0_slider;
label_t      g_t1_label; checkbox_t g_t1_check;

void on_apply(int64 _)  { print_console("[demo] Apply clicked"); }
void on_cancel(int64 _) { print_console("[demo] Cancel clicked"); }

void on_volume(int64 self) {
    slider_t s = cast<slider_t>(self);
    print_console("Volume -> " + cast<string>(s.get()));
}

void on_features(int64 self) {
    multi_options_t mo = cast<multi_options_t>(self);
    print_console("features mask -> " + cast<string>(mo.get_mask()));
}

void on_accent(int64 self) {
    colorpicker_t cp = cast<colorpicker_t>(self);
    color c = cp.get();
    print_console("accent -> " +
        cast<string>(c.r()) + "," + cast<string>(c.g()) + "," +
        cast<string>(c.b()) + "," + cast<string>(c.a()));
}

void on_view_tabs(int64 self) {
    tabs_t t = cast<tabs_t>(self);
    int64 sel = t.get();
    // selected tab's widgets active, others inactive
    g_t0_label.set_active(sel == 0);
    g_t0_slider.set_active(sel == 0);
    g_t1_label.set_active(sel == 1);
    g_t1_check.set_active(sel == 1);
}

void on_kb_aim_changed(int64 self) {
    keybind_t kb = cast<keybind_t>(self);
    print_console("aim bindings -> " + cast<string>(kb.binding_count()));
}

// keybinds don't fire a callback on hardware-key activation —
// poll keybind.is_active() to react.
void kb_poll_routine(int64 _data) {
    bool now = g_kb_aim.is_active();
    if (now != g_aim_was_active) {
        print_console(now ? "Aim ACTIVE" : "Aim inactive");
        g_aim_was_active = now;
    }
    bool esp = g_kb_esp.is_active();
    if (esp != g_esp_was_active) {
        print_console(esp ? "ESP ACTIVE" : "ESP inactive");
        g_esp_was_active = esp;
    }
}

int32 main() {
    g_sec = create_sidebar_section("demo", "");

    g_sec.create_label("Settings panel demo.", ui_align::left);
    g_sec.create_separator();

    // Attached button row — children share the primary's row.
    button_t apply  = g_sec.create_button("Apply",  ui_align::right);
    button_t cancel = g_sec.create_button("Cancel", ui_align::right);
    cancel.attach_to(apply);
    apply.on_change(cast<int64>(on_apply));
    cancel.on_change(cast<int64>(on_cancel));

    g_sec.create_separator();
    g_sec.create_checkbox("Notifications", true);

    slider_t vol = g_sec.create_slider("Volume", 0.6, 0.0, 1.0, 0.0);
    vol.on_change(cast<int64>(on_volume));
    g_sec.create_value_input("Port", 8080.0, 1.0, 65535.0, 1.0);

    // Codicon UTF-8 byte sequence — `\xHH` lexer escape required.
    g_sec.create_slider_icon("\xEE\xA9\xB0", 0.75, 0.0, 1.0, 0.0);

    g_sec.create_separator();
    array<string> features;
    features.push("Autosave"); features.push("Spell check");
    features.push("Auto-complete"); features.push("Line numbers");
    multi_options_t mo = g_sec.create_multi_options("Editor features", features, 13);
    mo.on_change(cast<int64>(on_features));

    g_sec.create_separator();
    array<string> tab_items;
    tab_items.push("Overview"); tab_items.push("Logs");
    g_tabs = g_sec.create_tabs(tab_items, 0);
    g_tabs.on_change(cast<int64>(on_view_tabs));

    g_t0_label  = g_sec.create_label("Overview content.", ui_align::left);
    g_t0_slider = g_sec.create_slider("FOV", 90.0, 60.0, 120.0, 1.0);
    g_t1_label  = g_sec.create_label("Logs content.", ui_align::left);
    g_t1_check  = g_sec.create_checkbox("Verbose logging", false);
    g_t1_label.set_active(false);
    g_t1_check.set_active(false);

    g_sec.create_separator();
    g_kb_aim = g_sec.create_keybind("Aimbot");
    g_kb_aim.bind(0x01, false, false, false, keybind_mode::on);    // VK_LBUTTON
    g_kb_aim.on_change(cast<int64>(on_kb_aim_changed));

    g_kb_esp = g_sec.create_keybind("ESP toggle");
    g_kb_esp.bind(0x45, false, false, false, keybind_mode::toggle); // 'E'

    g_sec.create_separator();
    colorpicker_t accent = g_sec.create_colorpicker("Accent", color(180, 180, 180, 255));
    accent.on_change(cast<int64>(on_accent));

    // Attached colorpicker chain — children render as swatches in the parent's popup.
    colorpicker_t theme_cp  = g_sec.create_colorpicker("Theme",     color(120, 120, 120, 255));
    colorpicker_t primary   = g_sec.create_colorpicker("Primary",   color( 80,  80,  80, 255));
    colorpicker_t secondary = g_sec.create_colorpicker("Secondary", color(200, 200, 200, 255));
    primary.attach_to(theme_cp);
    secondary.attach_to(theme_cp);

    // Context menu attached to a button — opens on the host's right-click path.
    button_t actions = g_sec.create_button("Actions", ui_align::center);
    g_menu = create_menu();
    g_menu.add_item("Reset",     cast<int64>(on_apply),  "Ctrl+R", "");
    g_menu.add_separator();
    g_menu.add_item("About...",  cast<int64>(on_cancel), "",       "");
    g_menu.attach_to_button(actions);

    g_kb_routine = register_routine(cast<int64>(kb_poll_routine), 0);
    return 1;   // keep loaded so the section stays interactive
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/gui-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
