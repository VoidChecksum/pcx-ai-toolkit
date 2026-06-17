> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/perception-ide/extensions-api.md).

# Extensions API

> **Some of the Perception.cx AngelScript APIs are available in extensions.** This includes: logging, rendering, input, CPU intrinsics, WinAPI, JSON, utilities, and Zydis encoding. **Not available:** process memory (`proc_t`/`ref_process`), mutexes, PCX script GUI API (`subtab_t`/`panel_t`/`checkbox_t`/`slider_double_t`/`button_t`/etc.), Unicorn emulation, extended math, engine-specific API, atomic API, and `register_callback`/`unregister_callback`. Extensions additionally get editor-specific APIs documented below.

**Available platform functions:** `log`, `log_error`, `log_console`, `log_console_error`, `get_username`, all `draw_*` / `clip_*` / `create_font*` / `create_bitmap` / `get_font*` / `get_text_size` rendering functions, all `key_*` / `get_mouse_*` / `get_scroll_delta` / `is_hovered` input functions, CPU intrinsics, WinAPI, JSON (`json_parse`/`json_stringify`), Zydis encoder, and utility functions.

> **Extensions also have:** file I/O (`read_file`/`write_file`/`file_exists`/`list_directory`), clipboard access, synchronous HTTP requests (`http_get`/`http_post`), and editor manipulation APIs documented below.

> **AngelScript string note:** Extensions use the standard AngelScript `string` type. Use `.isEmpty()` (not `.empty()`), `.length()` (not `.size()`), and `.findFirst()` / `.findLast()` for search.

***

**Structure**

One `.as` file per extension. Drop it in `<scripting_main_path>/extensions/`. Three optional metadata constants:

```cpp
const string EXT_NAME = "My Extension";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Short description";
```

All hook functions are optional — implement only what you need.

***

**Rules & Constraints**

* **No `main()` or `on_unload()`** — use `on_activate()` and `on_deactivate()` instead
* **`on_tick()` locals reset every call** — use global variables for persistent state across frames
* **No lambdas** — buttons return `bool`, use `if (create_button("X")) { ... }` instead of callbacks
* **Only `create_slider`** — no `create_slider_double` or `create_slider_int` variants
* **`on_settings_render` uses widget API only** — do NOT use `draw_*` render calls inside it. The widget functions handle all rendering and layout automatically
* **RGBA values are 0–255** — not 0.0–1.0
* **Keybinds and color pickers** must be created immediately after their parent checkbox

**Validation**

Extension scripts can be validated using `check_script` / `validate_script` or the **Verify** toolbar button. The editor automatically detects files in `extensions/` and uses a dedicated compile-only validator with the extension API surface registered.

* `validate_script` with `run=true` is **not supported** for extensions — they are event-driven with no `main()`
* `execute_script` **cannot** be used with extension code — extensions use a different API surface
* After validation returns PASS, the extension is correct and will be auto-loaded by the editor

***

**Hooks**

**Lifecycle**

```cpp
void on_activate()    // loaded & enabled
void on_deactivate()  // about to unload/disable
void on_tick()        // every frame (main thread)
```

**Editor Events**

```cpp
void on_file_opened(const string &in path)
void on_file_saved(const string &in path)
void on_buffer_changed(const string &in path, int line)
void on_tab_changed(const string &in path)
```

**AI Pipeline**

```cpp
bool on_ai_before_send(const string &in prompt, const string &in system_prompt)
// return false to cancel. call override_prompt() to change the prompt.

void on_ai_after_response(const string &in response)

string on_ai_tool_call(const string &in name, const string &in args)
// only fires for tools YOU registered. return result JSON.

void on_ai_after_tool(const string &in name, const string &in args, const string &in result)
// observation hook, fires for ALL tool calls

string on_ai_system_inject()
// return text appended to system prompt every request
```

**IntelliSense**

Extensions can provide completions and hover tooltips for **any file type** — not just AngelScript or Lua. The extension receives the file path, line text, and cursor column, and decides what to offer based on the file being edited. This means you can build HTML, CSS, Python, or any custom language IntelliSense via extensions.

```cpp
void on_completion(const string &in file, const string &in line_text, int col,
    array<string>@ labels, array<string>@ inserts, array<string>@ details)

void on_hover(const string &in file, const string &in word, int line, string &out tooltip)
```

**Settings UI**

```cpp
void on_settings_render(float x, float y, float w)
// render widgets in the Extensions panel sidebar
```

***

**Editor API**

```cpp
string get_active_file()
string get_active_file_content()
string get_active_language()
int    get_cursor_line()
int    get_cursor_col()
void   set_cursor_pos(int line, int col)
string get_selection_text()
int    get_line_count()
string get_line_text(int line)
string get_root_path()
void   get_open_files(array<string> &out files)
int    get_tab_count()
string get_tab_file(int index)
int    get_active_tab()
void   show_notification(const string &in msg)
void   set_status(const string &in msg)
void   send_chat_message(const string &in msg)
void   override_prompt(const string &in new_prompt) // only in on_ai_before_send
void   insert_text(const string &in text)           // insert at cursor position
void   replace_selection(const string &in text)     // replace current selection (or delete if empty)
void   set_selection(int start_line, int start_col, int end_line, int end_col)  // 0-based
bool   open_file(const string &in path)             // open file in new tab
bool   save_active_file()                           // save current buffer
void   goto_line(int line)                          // jump to line and scroll into view
```

**File I/O API**

Read and write files from extension code. Paths are resolved relative to the project root, or can be absolute.

```cpp
string read_file(const string &in path)                  // returns file contents (empty on failure)
bool   write_file(const string &in path, const string &in content)  // overwrites file
bool   file_exists(const string &in path)                // check if file exists
void   list_directory(const string &in path, array<string> &out entries)  // list directory contents
```

**Clipboard API**

```cpp
string get_clipboard()                          // read system clipboard text
void   set_clipboard(const string &in text)     // set system clipboard text
```

**Network API**

Synchronous HTTP requests via WinHTTP with a 10-second timeout. **Do not call these in `on_tick()`** — they block the main thread.

```cpp
string http_get(const string &in url, const string &in headers = "")   // returns response body
string http_post(const string &in url, const string &in body, const string &in headers = "")
int    http_get_status(const string &in url, const string &in headers = "")  // returns HTTP status code
```

Headers are passed as `"Key: Value\nKey2: Value2"` (newline-separated).

**Utility API**

```cpp
uint64 get_tick_count()                // system tick count (milliseconds)
string get_active_model()              // current AI model name
int    get_chat_message_count()        // number of messages in current chat
void   get_chat_message(int index, string &out role, string &out content)  // read chat message
```

**Settings API**

Persisted per-extension as JSON in the `extensions/` folder (e.g. `extensions/my_extension.json`). Settings survive editor restarts, extension reloads, and ON/OFF toggles. The enabled/disabled state of each extension is also persisted in the editor's workspace state.

```cpp
string setting_get(const string &in key)
void   setting_set(const string &in key, const string &in value)
bool   setting_get_bool(const string &in key)
void   setting_set_bool(const string &in key, bool value)
double setting_get_number(const string &in key)
void   setting_set_number(const string &in key, double value)
```

**Widget API**

Used inside `on_settings_render` to draw interactive UI.

```cpp
void   create_label(const string &in text)
void   create_label_colored(const string &in text, int r, int g, int b)
void   create_separator()
void   create_spacing(double px)
bool   create_checkbox(const string &in label, const string &in key)   // returns value
bool   create_button(const string &in label)                           // returns true on click
double create_slider(const string &in label, const string &in key,
                     double min, double max, double step = 0)          // returns value
string create_input_text(const string &in label, const string &in key) // single-line
string create_text_area(const string &in label, const string &in key,
                        int visible_lines = 4)                         // multi-line
void   create_progress_bar(const string &in label, double value, double max)
int    create_dropdown(const string &in label, const string &in key,
                       array<string>@ options)                         // cycle-on-click, returns selected index
int    create_color_picker(const string &in label, const string &in key) // RGBA swatch, returns packed RGBA int
int    create_keybind(const string &in label, const string &in key)    // click to capture VK code, Escape cancels
```

> **Widget rules:** Keybinds and color pickers must be created immediately after their parent checkbox. The `create_dropdown` cycles through options on each click and persists the selected index. The `create_color_picker` stores individual R/G/B/A channels as `key_r`, `key_g`, `key_b`, `key_a` in settings. The `create_keybind` widget shows a red border during capture mode and returns the Windows virtual key code.

**Tool Registration API**

Register custom AI tools. Only your extension can handle calls to tools it registered.

```cpp
void register_tool(const string &in name, const string &in desc, const string &in params_json = "")
void register_tool_param(const string &in tool, const string &in param,
                         const string &in type, const string &in desc, bool required = true)
void unregister_tool(const string &in name)
```

***

**Examples**

**Custom AI Tool**

```cpp
const string EXT_NAME = "Doc Lookup";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Gives the AI a documentation search tool";

void on_activate() {
    register_tool("search_docs", "Search project documentation for a query");
    register_tool_param("search_docs", "query", "string", "Search terms", true);
    register_tool_param("search_docs", "max_results", "integer", "Max results to return", false);
    log("Doc Lookup extension loaded");
}

string on_ai_tool_call(const string &in name, const string &in args) {
    if (name == "search_docs") {
        // parse args JSON, search your docs, return results
        return "{\"results\": [\"Found: memory_read documentation\", \"Found: pattern_scan guide\"]}";
    }
    return "{\"error\": \"unknown tool\"}";
}

void on_deactivate() {
    unregister_tool("search_docs");
}
```

**Widget Settings Panel**

```cpp
const string EXT_NAME = "Config Panel";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Extension with custom settings UI";

void on_settings_render(float x, float y, float w) {
    create_label("--- Configuration ---");
    create_separator();

    bool enabled = create_checkbox("Enable feature", "feat_enabled");
    if (enabled) {
        double speed = create_slider("Speed", "speed_val", 0, 100, 1);
        string name = create_input_text("Name", "user_name");
        create_label("Current: " + name + " @ " + formatInt(int(speed)));
    }

    create_separator();
    if (create_button("Reset Defaults")) {
        setting_set_bool("feat_enabled", false);
        setting_set_number("speed_val", 50);
        setting_set("user_name", "");
        show_notification("Settings reset");
    }
}
```

**IntelliSense Provider**

```cpp
const string EXT_NAME = "Custom Completions";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Adds project-specific completions";

void on_completion(const string &in file, const string &in line_text, int col,
    array<string>@ labels, array<string>@ inserts, array<string>@ details)
{
    // add completions when user types "myapi."
    if (line_text.findFirst("myapi.") >= 0) {
        labels.insertLast("myapi.init");
        inserts.insertLast("myapi.init()");
        details.insertLast("Initialize the API");

        labels.insertLast("myapi.shutdown");
        inserts.insertLast("myapi.shutdown()");
        details.insertLast("Shut down the API");
    }
}

void on_hover(const string &in file, const string &in word, int line, string &out tooltip) {
    if (word == "myapi")
        tooltip = "Project API namespace\nSee docs/api.md for reference";
}
```

**AI System Prompt Injection**

```cpp
const string EXT_NAME = "Context Injector";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Adds project context to every AI request";

string on_ai_system_inject() {
    string file = get_active_file();
    string lang = get_active_language();
    return "The user is editing: " + file + " (language: " + lang + ")\n"
         + "Project root: " + get_root_path() + "\n"
         + "Open tabs: " + formatInt(get_tab_count());
}

bool on_ai_before_send(const string &in prompt, const string &in system_prompt) {
    log("[AI] Sending: " + prompt.substr(0, 100));
    return true; // allow send
}

void on_ai_after_response(const string &in response) {
    log("[AI] Response length: " + formatInt(response.length()));
}
```

**Periodic Background Worker**

```cpp
const string EXT_NAME = "Auto-Saver";
const string EXT_VERSION = "1.0";
const string EXT_DESCRIPTION = "Logs a reminder every ~60 seconds";

int tick_count = 0;

void on_tick() {
    tick_count++;
    // ~60fps, so 3600 ticks ≈ 60 seconds
    if (tick_count % 3600 == 0) {
        log_console("Reminder: save your work!");
    }
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/perception-ide/extensions-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
