> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/perception-analyzer.md).

# Perception Analyzer

The Perception Analyzer is an integrated binary analysis tool built into the Perception.cx platform. It provides IDA-style disassembly, a full F5 decompiler, source reconstruction, hex viewing, memory scanning, and structure editing — all operating directly on live processes through Perception's memory access layer.

The Analyzer is designed from the ground up for speed. Analysis that takes minutes in traditional tools completes in seconds. Function detection, cross-reference building, string scanning, and decompilation all run in parallel across multiple threads, keeping the UI fully responsive throughout.

I am also actively working on the **Reconstruct Source** feature shown in the screenshots below. This feature is still experimental and not yet fully mature, but it is being continuously developed with the goal of becoming a truly state-of-the-art reconstruction system.

If this feature interests you and you would like to help improve it, please feel free to share suggestions and bug reports.

— **Timefall / Admin**

<div data-with-frame="true"><figure><img src="/files/FZZ90AC37miYmZdG7Xkb" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/DMNE7GLLFImh6p02hgkb" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/2rC0qAp57uTxmqTCz9ym" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/Taw90mKYeYLQoZzWkxkP" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/sjHvNmCl2y4E8mBFc2ne" alt=""><figcaption></figcaption></figure></div>

F5 Decompiler (Advance Decompiler - Generates Pseudo C) - This feature is still under development with ongoing tests and improvements.&#x20;

<div data-with-frame="true"><figure><img src="/files/IbCwMY3qnzViLJxa5mEz" alt=""><figcaption></figcaption></figure></div>

<div align="center"><figure><img src="/files/dV6BHzb2Gv5D1Wc990Cs" alt=""><figcaption></figcaption></figure></div>

The experimental **Reconstruct Source** feature generates a full project-style source reconstruction from a binary with a single click.

The output includes:

* **Header files** — types, structs, enums, globals, imports, vtables, string constants, and static data references
* **Source files** — decompiled functions grouped into named modules (e.g., `module_render`, `module_network`, `module_audio`)
* **Common helpers** — frequently used utility functions extracted into `common.cpp`
* **Hostile / unresolved functions** — obfuscated or failed functions emit `__asm {}` blocks with the raw disassembly
* **Analysis metadata** — cross-references and module assignments exported as JSON

The project structure and files shown below are generated automatically using the **Reconstruct Source** button.

<div data-with-frame="true"><figure><img src="/files/24iiTjKioUQI4O0NNCmX" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/7SdoNUWpj7CDYk6e9U9d" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/X7Zs63fV4KgDdutN4cMI" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/PJCb9CIkhrwfELmO87Hp" alt=""><figcaption></figcaption></figure></div>

<div data-with-frame="true"><figure><img src="/files/PqTklI8yNA79mAmL4Fzi" alt=""><figcaption></figcaption></figure></div>

***

### Getting Started

#### Attaching to a Process

<div align="left" data-with-frame="true"><figure><img src="/files/iKnctDv3lTMF4jZsnFID" alt=""><figcaption></figcaption></figure></div>

When the Analyzer opens, you are presented with a process selection screen. All active processes detected by Perception are listed. You can filter the list by typing in the search field at the top.

Click a process to select it, then click **Attach** to begin analysis.

#### Module Loading Modes

<div align="left" data-full-width="false" data-with-frame="true"><figure><img src="/files/LV0wC6heTp5rWgInem85" alt=""><figcaption></figcaption></figure></div>

Before attaching, you can choose how modules are loaded using the **Module Loading** pills at the bottom of the process selection card:

| Mode         | Behavior                                                                                                                                              |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Disabled** | No modules are analyzed.                                                                                                                              |
| **Primary**  | Only the main executable is fully analyzed. Other modules receive header-only loading (exports + sections visible, disassembly via on-demand decode). |
| **Selected** | After attaching, a checkbox list lets you choose which modules to fully analyze. The main executable and critical system DLLs are always included.    |
| **All**      | Every loaded module is fully analyzed. This can take significantly longer for large processes.                                                        |

> **Header-only modules** are still browsable — you can view exports, navigate sections, and disassemble code on the fly. Full analysis adds function detection, cross-references, and string identification.

**Module Switching**

Once attached, the module badge in the toolbar (e.g., `smss.exe`) acts as a dropdown. Click it to switch between loaded modules. A filter field at the top of the dropdown lets you search by module name.

***

#### Views

The Analyzer has five main views, accessible from the tab bar at the top of the workspace:

**Disasm (Disassembly)**

The primary view. Displays a linear disassembly of the current module with:

* **Address column** — Virtual addresses or symbol labels (e.g., `str_7FF7D1C92778:` for strings)
* **Bytes column** — Raw instruction bytes (toggle in Settings)
* **Mnemonic column** — Instruction mnemonic with syntax coloring (calls, jumps, returns, NOPs)
* **Operands column** — Instruction operands with resolved targets
* **Comment column** — Auto-generated cross-reference hints and string previews

**Function headers** appear as highlighted bars showing the function name, size, and xref count. **Labels** (`loc_xxxx:`, `sub_xxxx:`) mark branch targets and function entries. **String references** display IDA-style with the symbol name in the address column and the quoted string value at the mnemonic position.

**Navigation**

| Action                      | Effect                                                                    |
| --------------------------- | ------------------------------------------------------------------------- |
| Click a branch target       | Navigate to that address                                                  |
| `Ctrl+G`                    | Go to address (supports hex, decimal, and expressions like `base+0x1000`) |
| `Alt+Left` / `Alt+Right`    | Navigate back / forward                                                   |
| `M4` / `M5` (mouse buttons) | Navigate back / forward                                                   |
| `Ctrl+F`                    | Open search popup                                                         |
| `Page Up` / `Page Down`     | Scroll by screen                                                          |
| `Shift+Scroll`              | Horizontal scroll                                                         |
| `Home`                      | Reset horizontal scroll                                                   |

**Search**

Click the **Search** button or press `Ctrl+F` to open the search popup. Toggle between **Hex** and **String** mode using the pills:

* **Hex mode** — Pattern search with wildcards: `48 8B ?? 4C 89 ...` (`??` matches any byte)
* **String mode** — Case-insensitive text search

Results are navigated with the **Prev** / **Next** buttons. The status bar shows the current match index and total count.

> Searches scan PE sections only — headers, padding, and zero-filled regions are excluded.

**Symbols and Comments**

| Key | Action                                       |
| --- | -------------------------------------------- |
| `N` | Rename the symbol at the current address     |
| `;` | Add or edit a comment at the current address |

Renames and comments are saved with the session and persist across restarts.

***

**Hex**

A traditional hex editor view of the module's raw image. Displays bytes in configurable columns with an ASCII sidebar. Useful for inspecting data regions, padding, and raw binary content.

***

**Types (Structure Editor)**

A ReClass-style structure editor for defining and inspecting memory layouts.

**Creating Structures**

1. Click **New** in the left panel to create a new struct.
2. Set the **Name** and **Base Address** fields at the top.
3. Click any type button in the toolbar to add a field:

| Category | Types                                                        |
| -------- | ------------------------------------------------------------ |
| Integer  | `Hex8`, `U8`, `U16`, `U32`, `U64`, `I8`, `I16`, `I32`, `I64` |
| Float    | `Float`, `Double`                                            |
| Other    | `Bool`, `Ptr`, `UTF8`, `UTF16`, `Pad`                        |
| Vector   | `Vec2`, `Vec3`, `Vec4`, `Vec2D`, `Vec3D`, `Vec4D`            |
| Matrix   | `M3x4`, `M4x4`, `M3x4D`, `M4x4D`                             |

Fields are displayed with their offset, type, name, and live value read from the target process.

**Editing Fields**

| Key             | Action                                              |
| --------------- | --------------------------------------------------- |
| `T` / `Shift+T` | Retype the selected node (cycle forward / backward) |
| `R`             | Rename the selected node                            |
| `Delete`        | Delete the selected node                            |

**Import / Export**

* **Import** — Paste a C-style struct definition to auto-generate fields.
* **Export: C++** / **Export: AS** / **Export: Lua** — Export the struct as code in the selected language.

> Structures are saved automatically and persist across sessions.

***

**Scan (Memory Scanner)**

A live memory scanner for finding values in the target process's address space.

**First Scan**

1. Select the **Type** (UInt8 through Double, String, or WString).
2. Select the **Compare** mode:

| Compare       | Description                                  |
| ------------- | -------------------------------------------- |
| Exact         | Value equals the input exactly               |
| Greater Than  | Value is greater than the input              |
| Less Than     | Value is less than the input                 |
| Unknown Value | Capture all addresses (for later refinement) |

3. Enter a **Value** (not needed for Unknown Value).
4. Click **First Scan**.

**Next Scan**

After the first scan, refine results with additional compare modes:

| Compare   | Description                   |
| --------- | ----------------------------- |
| Changed   | Value changed since last scan |
| Unchanged | Value stayed the same         |
| Increased | Value increased               |
| Decreased | Value decreased               |

Click **Next Scan** to filter. Click **Clear** to reset and start over.

**Options**

* **Aligned Only** — Only scan addresses aligned to the data type size (faster, may miss unaligned values).
* **Heap Only** — Restrict scanning to heap memory regions.

> String and WString scans compare the full byte pattern. WString automatically converts the input to UTF-16 (little-endian) before scanning.

***

**Settings**

Configure Analyzer behavior:

| Setting                       | Description                                                           |
| ----------------------------- | --------------------------------------------------------------------- |
| **Scroll Speed**              | Adjusts scroll sensitivity across all views (slider, 0.01–2.0)        |
| **Hex Refresh Interval**      | How often live values refresh in the Hex and Types views (50–5000 ms) |
| **Show bytes in disassembly** | Toggle the raw bytes column in the Disasm view                        |
| **Show inspector panel**      | Toggle the right-side inspector panel                                 |

All settings are saved automatically and persist across restarts.

***

#### Inspector Panel

The right-side panel displays context-sensitive information about the currently selected address:

**Location**

Shows the virtual address (VA), relative virtual address (RVA), section name, containing function, and symbol name.

**Xrefs To**

All cross-references pointing **to** the current address — calls, jumps, conditional jumps, and data references. Each entry shows the xref type and the source function name. Click to navigate.

**Xrefs From**

All cross-references going **from** the current address to other locations.

**Bytes**

A hex dump of the bytes at the current address.

**Callers**

Functions that call the current function (derived from call-type xrefs to the function's entry point).

**Callees**

Functions called by the current function (unique call targets within the function body).

> All inspector sections have a fixed height with independent scrolling and scrollbar indicators.

***

#### Sidebar

The left panel provides filtered, searchable lists:

| Tab           | Contents                                                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Functions** | All detected functions with xref counts. Click to navigate.                                                               |
| **Imports**   | Imported functions grouped by DLL. Click to navigate to the IAT entry.                                                    |
| **Exports**   | Exported functions. The entry point is listed as `DllMain` or `WinMain`.                                                  |
| **Strings**   | Detected strings with their section and value. Click to navigate.                                                         |
| **Sections**  | PE sections with flags (XRW), virtual address, size, and entropy. Process information (PID, module count) is shown below. |

All tabs support text filtering. Type in the filter field to narrow results.

***

#### Toolbar

The toolbar provides quick access to common actions:

| Button          | Action                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Search**      | Opens the hex/string search popup                                                                                                    |
| **Detach**      | Saves the session and returns to the process selection screen                                                                        |
| **Dump**        | Opens the dump popup for saving the module image to disk                                                                             |
| **Reconstruct** | Opens the source reconstruction popup — decompiles all functions and exports a full project with headers, source files, and metadata |
| **Re-resolve**  | Re-reads zero-filled pages from the target process and rebuilds data cross-references                                                |

**Dump**

The dump popup lets you save the current module's memory image to disk:

* **Output Path** — The file path for the dump. Defaults to `[module_name]_dump.exe` or `[module_name]_dump.dll` in the scripting directory.
* **Wait for VEH** — Enable this for processes with page encryption (e.g., games using VEH-based decryption). The dumper will repeatedly read zero-filled / invalid pages within the timeout, waiting for the VEH handler to decrypt them.
* **Timeout** — How long to wait for VEH decryption (1–60 seconds).

After dumping, the status bar reports how many pages were recovered via VEH.

***

#### Sessions

The Analyzer automatically saves and loads session data per module:

* **Cursor position** — Restored on next attach
* **Custom renames** — Symbol names you've assigned with `N`
* **Comments** — Annotations you've added with `;`
* **Bookmarks** — Saved address bookmarks

Sessions are stored as encrypted `.pak` files in the scripting directory and are keyed by module name.

***

#### Context Menu

Right-click in the disassembly or sidebar function list to access context actions:

| Action                 | Description                                                                                                                                                                                   |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Make Function**      | Define a new function starting at the selected address                                                                                                                                        |
| **Copy Address**       | Copy the virtual address to the clipboard                                                                                                                                                     |
| **Copy Function ASM**  | Copy the full disassembly of the containing function                                                                                                                                          |
| **Dump Function Info** | Copy a complete analysis dump: the function's assembly, its F5 decompiled output, and the assembly of all called/referenced functions. Useful for sharing context with AI tools or teammates. |
| **Make Signature**     | Generate a byte pattern signature with wildcards for the instruction at the current address                                                                                                   |

***

#### Keyboard Shortcuts

| Shortcut        | Action                         |
| --------------- | ------------------------------ |
| `Ctrl+G`        | Go to address                  |
| `Ctrl+F`        | Search (hex pattern or string) |
| `Alt+Left`      | Navigate back                  |
| `Alt+Right`     | Navigate forward               |
| `M4` / `M5`     | Navigate back / forward        |
| `Ctrl+S`        | Save session                   |
| `Ctrl+M`        | Switch module                  |
| `T` / `Shift+T` | Retype struct node             |
| `R`             | Rename struct node             |
| `Delete`        | Delete struct node             |
| `N`             | Rename symbol (disasm)         |
| `;`             | Add comment (disasm)           |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/perception-analyzer.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
