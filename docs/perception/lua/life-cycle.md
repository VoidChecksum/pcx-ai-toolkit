> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/life-cycle.md).

# Life Cycle

Every Lua script **must define** an entry function:

***

#### **main()**

```lua
function main()
    ...
    return number
end
```

| Return Value | Meaning                                              |
| ------------ | ---------------------------------------------------- |
| **> 0**      | Script stays active **only if** `on_frame()` exists. |
| **≤ 0**      | Script unloads immediately after `main()` finishes.  |

***

#### **on\_frame()**

```lua
function on_frame()
    ...
end
```

| Behavior    | Meaning                                                        |
| ----------- | -------------------------------------------------------------- |
| **Missing** | Script unloads right after `main()` (even if it returned > 0). |
| **Exists**  | Runs every frame. Returning **≤ 0** unloads the script.        |

***

### on\_unload()

```lua
function on_unload()
    ...
end
```

* Called once **when the script is about to be unloaded**.
* Use this to clean up state, save data, etc.
* Cannot prevent the script from unloading

***

### ◆ Execution Flow

1. The engine runs the script’s `main()` function.
2. After `main()` returns:
   * If return value **≤ 0** → script unloads.
   * If return value **> 0**:
     * If `on_frame()` exists → script becomes persistent.
     * If `on_frame()` is missing → script unloads immediately.
3. For persistent scripts, `on_frame()` runs every frame until:
   * It returns **≤ 0**, or
   * The script is manually unloaded.
4. When the script is unloading, `on_unload()` is called once (if defined)

***

### ◆ Example #1 — Persistent Script

```lua
function main()
    log("Persistent script.")
    return 1
end

function on_frame()
    log("Tick")
end
```

***

### ◆ Example #2 — One-shot Script

```lua
function main()
    log("This runs once.")
    return 1   -- still unloads because on_frame() is missing
end
```

***

### ◆ Engine Notes

* `main()` is **required**.
* `on_frame()` is **optional**, but required for a script to stay active.
* Returning **≤ 0** from either function unloads the script.
* No infinite loops — frame updates are handled by the engine.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/life-cycle.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
