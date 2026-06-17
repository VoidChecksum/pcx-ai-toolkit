> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/engine.md).

# Engine

The Engine provides three global logging helpers available in every Lua script.\
Each of them targets a different part of the UI and is intended for a different use-case.

***

### **log(message: string)**

Send a standard UI log message (top-left overlay).

#### **Syntax**

```lua
log("message")
```

#### **Description**

Adds a **styled notification log** to the engine’s **top-left UI log feed**.\
These logs appear with the same formatting as other engine notifications (fade-out timers, colors, etc.).

#### **Examples**

```lua
log("Script initialized.")
log("Speed boost activated!")
```

#### **Overlay Output**

```
[LUA] Script initialized.
[LUA] Speed boost activated!
```

***

### **log\_error(message: string)**

Send an error message to the UI log panel.

#### **Syntax**

```lua
log_error("message")
```

#### **Description**

Same as `log()`, but marked as an **error**, shown with an **error style**, prefixing the message with **`[LUA][ERR]`**.

#### **Examples**

```lua
log_error("Failed to load config!")
log_error("Invalid teleport target!")
```

#### **Overlay Output**

```
[LUA][ERR] Failed to load config!
[LUA][ERR] Invalid teleport target!
```

***

### **log\_console(message: string)**

Append text to the debug console (persistent until cleared).

#### **Syntax**

```lua
log_console("message")
```

#### **Description**

Writes text directly into the **script debugging console**, where messages accumulate continuously.\
This console is separate from the UI log panel and is intended purely for development and live debugging.

Unlike `log()` and `log_error()`, **console output does not fade or disappear** — it continues to append until the user manually clears the console.

#### **Examples**

```lua
log_console("Tick: " .. tick)
log_console("Entity pos = " .. tostring(vec))
```

#### **Console Output**

```
[LUA] Tick: 4521
[LUA] Entity pos = (1024, 88, 12)
```

***

### log\_console\_error(message: string)

Append an **error message** to the debug console (persistent until cleared).

#### Syntax

```lua
log_console_error("message")
```

#### Description

Writes an error-styled message directly into the script debugging console.\
This behaves the same as `log_console()`, but marks the message as an error and prefixes it with **`[LUA][ERR]`**.

Unlike `log()` and `log_error()`, console error output:

* Does **not** appear in the UI overlay
* Does **not** fade or disappear
* Accumulates continuously until the user clears the console

Use this for:

* Debugging failures inside loops
* Tracing error conditions without spamming the UI
* Logging internal script errors or invalid states
* Development-only error output

#### Parameters

* **message** (`string`)\
  The error message to append to the debug console.

#### Examples

```lua
log_console_error("Failed to resolve entity pointer")
log_console_error("Invalid memory read at 0x0")
```

#### Console Output

```
[LUA][ERR] Failed to resolve entity pointer
[LUA][ERR] Invalid memory read at 0x0
```

***

### get\_user\_name(): string

Returns the current PCX username.

#### **Syntax**

```lua
get_user_name()
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/engine.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
