> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/perception-ide.md).

# Perception IDE

Perception.cx ships with a fully integrated code editor and AI assistant. It's a native overlay panel — no Electron, no browser runtime. Write, test, and iterate on scripts without ever leaving the platform.

AI chat connects to OpenAI-compatible endpoints, GitHub Models, and GitHub Copilot via OAuth — so your existing Copilot subscription works out of the box.

***

<figure><img src="/files/IhVOyNPkf1v5KeVdtFxu" alt=""><figcaption></figcaption></figure>

<figure><img src="/files/K0kNtz2C80twuKuP74pe" alt=""><figcaption></figcaption></figure>

<figure><img src="/files/gQiJrSah7s9NQJFCrAix" alt=""><figcaption></figcaption></figure>

<figure><img src="/files/G5S15XY6gXRyqE4TrnjT" alt=""><figcaption></figcaption></figure>

<figure><img src="/files/9YhgGmCIq9f9RAPGc6RY" alt=""><figcaption></figcaption></figure>

**Editor**

**Multi-Tab Editing**

Open as many files as you want. Drag tabs to reorder, middle-click or click the × to close. Each tab tracks its own undo history, cursor position, and unsaved state.

**Syntax Highlighting**

17 languages are supported: AngelScript, Lua, C/C++, Rust, JavaScript, Python, PHP, HTML, XML, CSS, JSON, Shell, PowerShell, Batch, INI, Markdown, tsx, jsx, vue, go, cs, and log files.

**IntelliSense**

Full autocompletion for the Perception.cx API surface in both AngelScript and Lua. Includes function signatures, parameter hints, type info, and namespace-aware resolution (e.g. `sdk::player_t` resolves correctly). Trigger manually with **Ctrl+Space** or let it appear automatically as you type.

**Find & Replace**

Open with **Ctrl+F** (find) or **Ctrl+H** (find & replace). Supports regex, case sensitivity, and whole-word matching. Navigate matches with Enter/Shift+Enter or the arrow buttons.

**Line Operations**

* **Ctrl+D** — Duplicate line or selection
* **Ctrl+/** — Toggle line comment
* **Tab / Shift+Tab** — Indent / unindent selection
* **Ctrl+A** — Select all
* Standard clipboard: **Ctrl+C**, **Ctrl+X**, **Ctrl+V**

Undo (**Ctrl+Z**) and Redo (**Ctrl+Y**) use coalesced history — fast typing gets grouped into single undo steps.

**Font Scaling**

**Ctrl+Scroll** to zoom the editor font in or out.

***

**Sidebar**

The left sidebar has six tabs accessible via the activity bar icons:

* **Explorer** — project file tree
* **Chat** — AI chat panel
* **Settings** — editor configuration
* **Timeline** — file backup history and diff viewer
* **Extensions** — manage loaded extensions

***

**File Explorer**

The left sidebar shows your project's file tree with expand/collapse for folders. Right-click any item to access the context menu:

* **New File** — create a file in the selected directory
* **New Folder** — create a subdirectory
* **Rename** — rename the selected file or folder
* **Delete** — remove the selected item
* **AI Root** — set or remove the selected folder as an AI Root (see **AI Root** below)

**Workspace Folders**

You can add additional folders to your workspace from **Settings → Project → Workspace Folders**. These appear alongside the root directory in the Explorer and are included in cross-project operations like `find_references`. Click **Add Folder** to browse, and **×** to remove. Workspace folders persist across sessions.

***

**Script Toolbar**

The toolbar across the top of the editor provides one-click access to the script lifecycle:

| Button      | Action                                                             |
| ----------- | ------------------------------------------------------------------ |
| **Execute** | Compile and run the current script immediately                     |
| **Reload**  | Hot-reload a running script without restarting                     |
| **Unload**  | Stop and unload the script cleanly                                 |
| **Verify**  | Compile-check only (no execution) — shows errors with line numbers |
| **Bundle**  | Resolve all `#include` directives into a single merged output file |

The **Bundle** button uses the built-in `#include` resolver by default. You can replace it with a custom build command using **Custom Commands**.

***

**Integrated Terminal**

A built-in `cmd.exe` terminal lives at the bottom of the editor. Toggle it with **Ctrl+\`**.

**Terminal Tabs**

The terminal supports up to **8 independent tabs**, each running its own `cmd.exe` process with a separate output buffer, scroll position, and command history.

* Click **+** to open a new tab
* Click a tab to switch to it
* Click **×** on a tab to close it (at least one tab is always kept)
* Each tab shows a colored status dot: green = alive, red = process exited

**Terminal Shortcuts**

| Key           | Action                           |
| ------------- | -------------------------------- |
| **Ctrl+\`**   | Expand / collapse terminal       |
| **Ctrl+L**    | Clear terminal output            |
| **Up / Down** | Navigate command history         |
| **Ctrl+C**    | Send interrupt signal to process |
| **Esc**       | Return keyboard focus to editor  |

> **AI integration:** When the AI runs shell commands, they always execute in the **active terminal tab**. You can dedicate one tab for AI operations and keep another for manual commands.

***

**AI Chat**

The editor includes a full AI chat panel with built-in support for three API providers, plus any custom OpenAI-compatible endpoint.

**Providers**

The **Settings → Chatbot → Provider** section lets you choose between three provider modes. Each provider has completely independent settings — switching providers never overwrites another provider's configuration.

* **Default** — connect to any OpenAI-compatible API endpoint. Enter a URL, API key, and model name manually. Works with OpenRouter, LM Studio, Ollama, Together, Groq, or any cloud/local provider that speaks the standard chat completions format
* **GitHub Models** — connect to GitHub's inference API at `models.github.ai`. Enter a GitHub Personal Access Token (PAT) with `models:read` scope, then click **Fetch Models** to populate the model list from the catalog. Free tier has strict rate limits (50 req/day, 4K input tokens on most models) — enable paid billing in GitHub settings for production-grade limits
* **Copilot** — connect to the GitHub Copilot API at `api.githubcopilot.com` using your existing Copilot subscription (Pro, Pro+, Business, or Enterprise). Click **Sign in with GitHub** to authenticate via OAuth device flow — the editor opens your browser, you enter the code shown, and the token is saved automatically. Then click **Fetch Models** to get available models. Uses your Copilot subscription's rate limits and premium request allowance — no separate billing needed

**Getting Started**

1. Open the **Settings** sidebar (gear icon)
2. Under **Chatbot**, choose a **Provider** (Default, GitHub, or Copilot)
3. **Default**: enter your endpoint **URL**, **API Key**, and add a model to the **Planning / Reasoning** list
4. **GitHub**: paste your PAT in the **GitHub Token** field, click **Fetch Models**, then select a model from the dropdown
5. **Copilot**: click **Sign in with GitHub**, complete the OAuth flow in your browser, then click **Fetch Models** and select a model
6. Optionally configure an **Implementation / Coder** model for tandem mode (see **Tandem AI**)
7. Open the **Chat** sidebar tab and start typing

You can configure multiple endpoints and switch between them from the dropdown at the top of the chat panel.

**Model Selection**

Each provider maintains its own model lists for planning and coder roles. Models can be managed in two ways:

* **Manual entry** (Default provider) — click **+ Add Model** in the settings model list, enter a display name and model ID
* **Catalog fetch** (GitHub / Copilot) — click **Fetch Models** to pull all available models from the API. The model list populates automatically

Select your active model from the **filterable dropdown** at the bottom of the chat panel. Type to search, scroll with the mouse wheel, and click to select. Both planner and coder dropdowns support filtering and scrolling.

**Chat Features**

* **Streaming responses** with real-time token usage display in the header bar
* **Live generation stats** — while streaming, an animated spinner shows alongside the current speed (`~35 tok/s · 1.3s`). After completion, final stats persist below each assistant message (`456 tokens · 99.1 tok/s · 4.6s`) using the accurate token count from the API's usage response
* **Auto-continue** — if the model hits its max output token limit mid-response, the editor automatically sends a "Continue" message and resumes streaming. This repeats up to 5 times per user turn, so long analysis sessions (e.g. multi-step reverse engineering) don't require manual intervention
* **Full markdown rendering** — headings, bold/italic, inline code, fenced code blocks with syntax highlighting, tables with word-wrapped cells and per-cell clipping, horizontal rules, lists, and blockquotes
* **Thinking / reasoning** — models that output reasoning tokens get collapsible "Thinking" blocks. When collapsed, an auto-generated summary appears (e.g. "Read 3 files, edited 2 files"). Non-thinking models work normally without the thinking block
* **Conversation management** — the dropdown menu offers:
  * **New Chat** — start a fresh conversation
  * **History** — browse and load previous chat sessions (tool call badges and results are fully preserved across save/load)
  * **Clear** — wipe the current conversation
  * **Summarize & Continue** — compress older messages to free up context space. Uses structured summaries that preserve goal, changes made, validation results, pending work, and key technical details
* **Automatic context optimization** — when the assistant fully completes a response (all tool loops finished, no pending follow-ups), older tool results and tool call arguments are automatically trimmed. Large file reads become one-line summaries (e.g. `[Previously read 45 lines from foo.cpp]`), write\_file arguments are replaced with compact stubs, and RE tool outputs are condensed. Context is never trimmed mid-loop — the AI keeps full unmodified context for its entire working session
* **Tandem AI** — optionally use two models cooperatively. A planning model handles reasoning and architecture, a coder model handles implementation. See **Tandem AI** below
* **Extra system prompt** — add your own persistent instructions in the multiline text area at the bottom of the AI Chat settings section. These are injected into every API request
* **Panel positioning** — pin the chat panel on the left or right side of the editor via the **AI Chat on Right Side** checkbox

**Stopping a Response**

Click **Stop** or press **Ctrl+C** while the AI is streaming or running tools to cancel immediately. The Stop button appears in red during both streaming and tool execution (including long-running memory scans). You can then edit your message or send a new one without any issues.

**Text Selection in Chat**

You can select and copy text from any message in the chat:

* **Click and drag** on any user or assistant message text to select a range
* **Thinking blocks** (when expanded) support independent text selection
* **Ctrl+C** copies the selected text, or the full hovered message if no selection exists
* The **Copy** button on assistant messages copies the full message content

**Web Search**

The AI can search the web for current information using the `web_search` tool. Two backends are supported:

* **OpenRouter** — if your active endpoint is on OpenRouter, web search works automatically with no additional configuration. It uses OpenRouter's web plugin which is powered by native search (for OpenAI, Anthropic, Perplexity, xAI models) or Exa for other models. OpenRouter charges $4 per 1000 results ($0.02 per request at default 5 results). For example, `openai/gpt-5.2:online` works well as a search-capable model
* **Brave Search** — for non-OpenRouter endpoints, enter a Brave Search API key in Settings → **Brave Search Key**. Get a key at [brave.com/search/api](https://brave.com/search/api/)

Enable the **Web Search** toggle in Settings → Tools to make the tool available to the AI.

***

**AI Code Fill**

Separate from the chat, the editor supports inline AI code completions — similar to Copilot but running on your own model.

* Triggers automatically after a configurable delay while typing
* **Ghost text** appears inline in grey — press **Tab** to accept, **Esc** to dismiss
* Supports **FIM (Fill-in-the-Middle)** tokens for models like Qwen Coder
* Uses a **separate endpoint, model, and API key** from the chat — run a small fast model for completions and a larger model for chat
* Configurable **context window** (number of surrounding lines sent to the model)
* Platform API context is injected automatically so the model knows the Perception.cx API

**Code Fill Settings**

| Setting                      | Description                                   |
| ---------------------------- | --------------------------------------------- |
| Enable Code Fills            | Master toggle                                 |
| URL / Model / API Key        | Endpoint for completions (separate from chat) |
| Max Tokens                   | Maximum completion length                     |
| Trigger Delay (ms)           | Idle time before requesting a completion      |
| Context Lines                | Number of surrounding code lines to include   |
| Use FIM Tokens               | Enable Fill-in-the-Middle token wrapping      |
| FIM Prefix / Suffix / Middle | Custom FIM token strings for your model       |

***

**Tandem AI**

Tandem AI lets two models cooperate on tasks — a **Planning / Reasoning** model handles analysis, architecture, and review while an **Implementation / Coder** model handles code writing, edits, and validation loops.

**How It Works**

The planner model starts every conversation. When it has a detailed plan ready, it calls the `switch_model` tool to hand off to the coder. The coder implements the plan, validates the code, then switches back to the planner for review. The models self-route — no heuristic decides for them.

Both models see the full conversation history, so handoff is seamless. The `switch_model` tool call itself documents the transition in the message history.

**Setting Up**

1. In **Settings → Chatbot**, add your planning model to the **Planning / Reasoning** model list (e.g. `anthropic/claude-sonnet-4`)
2. Add your coding model to the **Implementation / Coder** model list (e.g. `google/gemini-2.5-flash`)
3. Select the desired model from each dropdown at the bottom of the chat panel
4. For the **Default** provider, you can optionally set a separate **Coder URL** and **Coder API Key** if the coder model runs on a different endpoint (e.g. planner on OpenRouter, coder on local Ollama). Leave these empty to use the planner's endpoint for both models

Select "No Coder" in the coder dropdown to disable tandem and use a single model. If both dropdowns point to the same model name, tandem is also disabled automatically.

**Separate Endpoints (Default Provider Only)**

By default, the coder uses the same URL and API key as the planner — just with a different model name in the request. If you want the coder to hit a completely different server:

* **Coder URL** — set a different API endpoint for the coder model
* **Coder API Key** — set a different API key for the coder model

Leave these empty to use the planner's endpoint. These fields are only available on the Default provider — GitHub and Copilot providers use a single endpoint for all models.

**Tips**

* The planner sets the quality ceiling. A thorough plan with exact files, functions, and changes lets even a cheap coder model execute precisely
* Use a strong model for planning (Claude, GPT-4, etc.) and a fast/cheap model for coding (Gemini Flash, Qwen Coder, etc.) to balance quality and cost
* The planner is instructed to read code before planning, produce detailed plans with exact changes, and include edge cases and validation steps
* The coder is instructed to work autonomously through the full implementation and only switch back when done, when hitting an unplanned design decision, or after 5+ validation failures

***

**AI Tool Use**

The AI doesn't just chat — it can take actions. When **Enable Tool Calls** is checked in settings, the AI has access to **65+ tools** and loops automatically until the task is done (up to the configurable **Tool Loop Limit**). Heavy reverse engineering tools run asynchronously on a background thread, keeping the UI responsive during multi-second scans. The AI keeps full context during its working session — trimming only happens after the assistant fully completes.

**File & Code Tools**

| Tool                             | Description                                                                                                                                                                |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `read_file`                      | Read a file's contents (truncated at 16KB for large files — use `read_lines` for targeted access)                                                                          |
| `read_lines`                     | Read a specific line range                                                                                                                                                 |
| `write_file`                     | Write full file contents (shows diff for review)                                                                                                                           |
| `edit_file`                      | Search/replace edit — old text must match exactly                                                                                                                          |
| `batch_edit`                     | Apply multiple search/replace edits atomically                                                                                                                             |
| `replace_all`                    | Find and replace ALL occurrences in a file                                                                                                                                 |
| `create_file`                    | Create a new file (fails if it already exists)                                                                                                                             |
| `create_directory`               | Create a directory and all parent directories                                                                                                                              |
| `insert_lines`                   | Insert text before a specific line                                                                                                                                         |
| `delete_lines`                   | Delete a range of lines                                                                                                                                                    |
| `replace_lines`                  | Replace a line range with new text. More efficient than `edit_file` when line numbers are known — no content duplication                                                   |
| `replace_selection`              | Replace the current editor selection                                                                                                                                       |
| `search_text`                    | Search across open files                                                                                                                                                   |
| `find_references`                | Search across ALL project files on disk (all workspace roots)                                                                                                              |
| `get_file_info`                  | Get file info: path, language, lines, size in bytes. Accepts optional path (defaults to active file). Use to check size before reading unknown files                       |
| `get_open_files`                 | List all open buffers with line counts and modified status                                                                                                                 |
| `list_files`                     | List directory contents (lists all workspace roots when given `.`)                                                                                                         |
| `get_symbols`                    | List function/struct/class/enum definitions in a file                                                                                                                      |
| `open_file`                      | Open a file in a new editor tab                                                                                                                                            |
| `save_file`                      | Save a file to disk                                                                                                                                                        |
| `goto_line`                      | Move cursor to a line number                                                                                                                                               |
| `get_clipboard`                  | Read system clipboard text                                                                                                                                                 |
| `get_recent_changes`             | Get last 20 undo history entries                                                                                                                                           |
| `add_bookmark` / `get_bookmarks` | Manage named bookmarks                                                                                                                                                     |
| `check_script`                   | Compile-check a script for errors without executing. Automatically uses the extension API surface for files in `extensions/`                                               |
| `validate_script`                | Compile and optionally run a script. Extensions are compile-only (no `run=true` — they have no `main()`)                                                                   |
| `get_script_api`                 | Load the Perception.cx scripting API reference for a language (`angelscript`, `lua`, or `extension`). **Mandatory** — the AI must call this before writing any script code |

**Shell & Automation Tools**

| Tool                 | Description                                                                                                                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exec_shell_command` | Run a command in the active terminal tab (30s timeout)                                                                                                                             |
| `run_custom_command` | Run a user-defined custom command by name                                                                                                                                          |
| `execute_script`     | Write and run an AngelScript/Lua script on the fly                                                                                                                                 |
| `ask_user`           | Pause and ask you a question, then resume after you respond                                                                                                                        |
| `ask_mcq`            | Pause and ask you multiple questions in one tool call, then result after you respond                                                                                               |
| `web_search`         | Search the web via Brave Search API or OpenRouter web plugin                                                                                                                       |
| `manage_context`     | AI self-optimizes its context window: `drop_tools` removes unneeded tool categories (saves tokens), `trim_history` trims old turns                                                 |
| `update_notes`       | Persistent working notes (2KB) that survive context trimming. The AI uses this to preserve key discoveries from RE sessions — addresses, offsets, struct layouts, decrypted values |
| `switch_model`       | Switch between planning and coder models during tandem AI. Only available when an Implementation / Coder model is configured                                                       |

**Diff Review Tools**

| Tool                   | Description                               |
| ---------------------- | ----------------------------------------- |
| `get_diff`             | Get current pending diff state            |
| `wait_for_diff_review` | Pause until you resolve all pending diffs |

**Reverse Engineering Tools**

| Tool                 | Description                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `list_processes`     | List processes with PID, name, base address, EPROCESS                                                                |
| `get_process_info`   | Detailed process info: modules, threads, PEB, DTB                                                                    |
| `read_memory`        | Read bytes as hex dump + ASCII (max 4096 bytes)                                                                      |
| `read_typed_value`   | Read typed values: uint8–64, float, double, pointer arrays                                                           |
| `find_pattern`       | IDA-style byte pattern scanning with `?` wildcards                                                                   |
| `read_pointer_chain` | Follow pointer chain with offsets at each dereference                                                                |
| `read_string`        | Read ASCII or Unicode string from memory                                                                             |
| `get_module_exports` | List exported functions from a module's PE export table                                                              |
| `get_module_imports` | List imported functions from a module's PE import table (DLL names, function names, IAT addresses, resolved targets) |

**Advanced Tools**

These are gated behind the **Allow Advanced Writing Tools** checkbox in settings:

| Tool                           | Description                                                                                                                                                                                     |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `memory_write`                 | Write bytes to process memory (works on any section including `.text` — no protection changes needed)                                                                                           |
| `scan_string` / `scan_wstring` | Scan ALL committed process memory for ASCII/Unicode strings. Full VAD scan — no range limit                                                                                                     |
| `disassemble`                  | Disassemble x86-64 instructions at an address (Zydis)                                                                                                                                           |
| `delete_file`                  | Permanently delete a file                                                                                                                                                                       |
| `scan_pointer_to`              | Reverse pointer scan — find all memory locations containing a pointer to a target address. Full VAD scan                                                                                        |
| `scan_value`                   | Scan ALL process memory for typed values (uint16–64, int32/64, float, double) with optional tolerance                                                                                           |
| `scan_changed`                 | Cheat Engine-style iterative scanning: first scan → filter by changed/increased/decreased/unchanged/exact                                                                                       |
| `diff_memory`                  | Snapshot a memory region, wait, snapshot again, report all changed bytes with hex + float interpretations                                                                                       |
| `struct_dump`                  | Read memory and heuristically classify each 8-byte field: pointers, vtables, floats, doubles, ints, nulls                                                                                       |
| `find_xrefs`                   | Find all code cross-references to an address. Scans entire module in 4MB chunks — no size cap, works on 400MB+ modules                                                                          |
| `find_string_refs`             | Find code that references a string. Combines `scan_string` + `find_xrefs` in one call — scans all memory for the string, then sweeps entire module code for LEA/MOV instructions pointing to it |
| `find_function_bounds`         | Given any address inside a function, detect prologue/epilogue to find function start and end                                                                                                    |
| `analyze_function`             | Annotated disassembly with basic block labels, CALL targets, stack frame size, and control flow markers                                                                                         |
| `trace_register`               | Static backward trace: find where a register gets its value, resolve RIP-relative globals                                                                                                       |
| `analyze_vtable`               | Read vtable slots and verify each is a valid function pointer by decoding prologue bytes                                                                                                        |
| `read_rtti`                    | Read MSVC RTTI from an object pointer or vtable address. Returns class name, base classes, and inheritance hierarchy                                                                            |
| `generate_signature`           | Auto-generate IDA-style byte signatures with automatic wildcarding of RIP-relative displacements                                                                                                |
| `build_call_graph`             | Build recursive call graph from a function showing call relationships, instruction counts, and depth                                                                                            |
| `get_module_imports`           | List imported functions from a module's PE import directory                                                                                                                                     |

> **Physical memory:** All process memory operations use physical memory page table translation. This means you can read and write any memory including executable `.text` sections without changing page protection — no `VirtualProtect` needed.

***

**Diff Review**

When the AI edits a file, it doesn't overwrite your code directly. Every change goes through a diff review:

* Changes are displayed as individual **hunks** with green (added) / red (removed) highlighting
* Navigate between hunks with **Up / Down** arrow keys
* **Enter** — accept the focused hunk
* **Delete** — reject the focused hunk
* **Ctrl+Shift+A** — accept all hunks at once
* **Esc** — reject all remaining hunks

The AI can call `wait_for_diff_review` to pause until you've resolved all pending diffs before it continues. Alternatively, enable **Auto-accept AI edits** in settings to skip review entirely.

***

**AI Root**

AI Root lets you scope where the AI operates within your project. When set, the AI will only read, write, and browse files within the designated folder(s).

**Setting an AI Root**

1. In the **File Explorer** sidebar, right-click any folder
2. Click **AI Root** to toggle it on or off
3. Folders marked as AI Root show a visual indicator in the tree

You can set multiple AI Roots. When at least one is set, the AI's file operations are restricted to those directories. When no AI Roots are set, the AI can access the entire project.

AI Roots persist across sessions and are saved with your editor state.

***

**Custom Commands**

Custom Commands let you define named shell commands that integrate into the editor and AI workflow. Define them in **Settings → Custom Commands**.

**Creating a Command**

1. Click **+ Add Command**
2. Enter a **Name** (e.g. "Build", "Test", "Deploy")
3. Enter a **Command** (e.g. `build.bat`, `python test.py`, `npm run build`)
4. Optionally check **Use as Bundler** to replace the toolbar's Bundle button with this command

**Bundler Override**

When a custom command has **Use as Bundler** enabled, clicking the **Bundle** button in the script toolbar will run your custom command in the terminal instead of the built-in `#include` resolver. Only one command can be the active bundler at a time.

This is useful for custom build pipelines — C-preprocessor macro expansion, hash baking, minification, or any project-specific processing the built-in bundler doesn't cover.

**AI Integration**

Custom commands are automatically exposed to the AI as the `run_custom_command` tool. The AI can invoke any of your defined commands by name during agentic workflows. For example, after editing files the AI could run your custom build command to verify compilation.

***

**Extensions**

The editor supports AngelScript-based extensions that hook into the editor lifecycle, AI chat pipeline, and provide custom UI widgets. Extensions have full access to the Perception.cx platform API — the same surface available to regular scripts.

**Installing Extensions**

Place `.as` files in the `extensions/` folder inside your scripting main directory. The editor scans this directory every 3 seconds and automatically picks up new files or removes deleted ones.

**Managing Extensions**

Click the 🧩 puzzle icon in the activity bar to open the **Extensions** panel. Each extension shows a card with its name, version, description, ON/OFF toggle, Reload button, and any compile errors. Extension state persists across sessions.

**What Extensions Can Do**

* **Editor events** — react to files being opened, saved, edited, or tabs switching
* **AI pipeline** — intercept prompts before sending, inject system prompt text, observe or handle tool calls, register custom AI tools
* **IntelliSense** — provide custom completions and hover tooltips for any file type (not limited to AngelScript/Lua)
* **Custom UI** — render checkboxes, sliders, buttons, text inputs, progress bars, dropdowns, color pickers, and keybind capture widgets in the sidebar
* **Editor manipulation** — insert text, replace selection, set selection range, open files, save files, and jump to lines programmatically
* **File I/O** — read files, write files, check existence, and list directories from extension code
* **Clipboard** — get and set system clipboard text
* **Network** — synchronous HTTP GET/POST requests with custom headers (10s timeout)
* **Platform access** — use a selection of Perception.cx APIs including rendering, input, CPU intrinsics, WinAPI, JSON, Zydis, and utilities. Process memory, mutexes, and extended math are not available in extensions

**Validation**

Extension scripts can be validated using the same `check_script` and `validate_script` tools (or the Verify toolbar button). The editor automatically detects that the file is in `extensions/` and uses a dedicated validator with the extension API surface. Note that `validate_script` with `run=true` is not supported for extensions — they are event-driven and have no `main()` entry point. The `execute_script` tool also cannot be used with extension code.

For the full extension API reference, examples, and hook documentation, see the **Extension Development** page.

***

**File Backups & Timeline**

Every save creates a timestamped backup. The **Timeline** sidebar tab lets you browse and compare backups:

* All backups for the current file are listed, sorted by date
* Click any backup to open a **side-by-side diff view** comparing it against the current version
* Line-level add/remove/change highlighting
* Configurable **max backup count** and **backup directory** in settings
* Deleted file recovery — the most recent backup of removed files is preserved

***

**Settings**

All configuration lives in the **Settings** sidebar tab (gear icon). Everything persists to disk automatically.

**Project**

* **Root Directory** — your project folder. Set via the text field and click Apply
* **Workspace Folders** — additional folders to include alongside the root directory. Click **Add Folder** to browse, **×** to remove
* **AI Root** — managed via right-click in the file explorer (see **AI Root**)

**Editor**

* **Scroll Speed** — mouse wheel scroll multiplier
* **Autoscroll Speed** — speed when auto-scrolling during selection drag

**Bundler**

* **Strip comments from output** — remove comments when bundling `#include` files

**Chatbot**

| Setting                        | Description                                                                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| AI Chat on Right Side          | Pin the chat panel to the right side of the editor                                                                           |
| Auto-accept AI edits           | Skip diff review and apply AI changes immediately                                                                            |
| Allow Advanced Writing Tools   | Enable dangerous tools: memory write, disassemble, delete file, string scan, and advanced RE analysis tools                  |
| Enable Tool Calls              | Allow the AI to use tools (file ops, RE tools, shell, etc.)                                                                  |
| Provider                       | Choose **Default**, **GitHub**, or **Copilot**. Each provider has independent settings that don't affect the others          |
| URL *(Default only)*           | API endpoint URL (OpenAI-compatible)                                                                                         |
| API Key *(Default only)*       | Bearer token for authentication                                                                                              |
| GitHub Token *(GitHub only)*   | Personal Access Token with `models:read` scope                                                                               |
| Sign in *(Copilot only)*       | OAuth device flow — click to authenticate with your GitHub Copilot subscription                                              |
| Planning / Reasoning           | Model list for the planning model. Add models manually (Default) or fetch from catalog (GitHub/Copilot)                      |
| Implementation / Coder         | Model list for the coder model. Select "No Coder" to disable tandem mode                                                     |
| Coder URL *(Default only)*     | Separate API endpoint for the coder model. Leave empty to use the planner's endpoint                                         |
| Coder API Key *(Default only)* | Separate API key for the coder model. Leave empty to use the planner's key                                                   |
| Tool Loop Limit                | Maximum number of consecutive tool call rounds                                                                               |
| Temperature                    | Sampling temperature (0.0–2.0). Not sent for GitHub/Copilot providers — models use their own defaults                        |
| Top P                          | Nucleus sampling threshold. Not sent for GitHub/Copilot providers                                                            |
| Brave Search Key               | API key for Brave web search (not required if using OpenRouter — web search works automatically via OpenRouter's web plugin) |
| Extra System Prompt            | Your own persistent instructions appended to every request                                                                   |

**Code Fill**

See **AI Code Fill** for details on each setting.

**Backups**

| Setting          | Description                        |
| ---------------- | ---------------------------------- |
| Max Backups      | Maximum number of backups per file |
| Backup Directory | Where backup files are stored      |

**Custom Commands**

See **Custom Commands** for details.

***

**Keyboard Shortcuts**

**Editor**

| Key         | Action                             |
| ----------- | ---------------------------------- |
| Ctrl+S      | Save file                          |
| Ctrl+W      | Close tab                          |
| Ctrl+F      | Find                               |
| Ctrl+H      | Find & Replace                     |
| Ctrl+Z      | Undo                               |
| Ctrl+Y      | Redo                               |
| Ctrl+D      | Duplicate line / selection         |
| Ctrl+/      | Toggle comment                     |
| Ctrl+Space  | Trigger code fill manually         |
| Ctrl+Scroll | Zoom font size                     |
| Tab         | Accept AI suggestion / Indent      |
| Esc         | Dismiss AI suggestion / Close find |

**Diff Review**

| Key          | Action                 |
| ------------ | ---------------------- |
| Enter        | Accept hunk            |
| Delete       | Reject hunk            |
| Up / Down    | Navigate between hunks |
| Ctrl+Shift+A | Accept all hunks       |
| Esc          | Reject all hunks       |

**Chat**

| Key         | Action                                                                     |
| ----------- | -------------------------------------------------------------------------- |
| Enter       | Send message                                                               |
| Shift+Enter | New line in message                                                        |
| Ctrl+C      | Cancel AI stream (while streaming) / Copy selected text or hovered message |

**Terminal**

| Key       | Action                     |
| --------- | -------------------------- |
| Ctrl+\`   | Expand / collapse terminal |
| Ctrl+L    | Clear terminal output      |
| Up / Down | Command history            |
| Ctrl+C    | Send interrupt to process  |
| Esc       | Return focus to editor     |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/perception-ide.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
