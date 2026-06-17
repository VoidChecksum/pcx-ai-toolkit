> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/life-cycle.md).

# Life Cycle

## 🧠 Script Lifecycle & Entry Point

Every AngelScript module loaded by the PCX engine **must define** an entry function:

The engine automatically looks up and executes this function when the script is started.

***

### Load Event

```cpp
int main()
```

| Return Value | Meaning                                                                                                                    |
| ------------ | -------------------------------------------------------------------------------------------------------------------------- |
| > 0          | Keep the script **loaded and active**. Callbacks, draw events, and per-frame updates continue to run.                      |
| <= 0         | **Unload** the script immediately after `main()` completes. All registered callbacks and allocated resources are released. |

***

### &#x20;Unload Event

```cpp
void on_unload()
```

* Called once **when the script is about to be unloaded**.
* Use this to clean up state, save data, etc.
* Cannot prevent the script from unloading

***

### 🔹 Execution Flow

1. When a script is loaded, the engine locates and runs its `main()` function.
2. Inside `main()`, you typically register callbacks or set up states.
3. After `main()` returns:
   * If the return value > 0 → the script remains active (engine thread persists).
   * If the return value ≤ 0 → the script is unloaded, memory is freed, and its callbacks are destroyed.

***

### 🔹 Example #1 — Persistent Script

```cpp
void on_tick(int id, int data_index)
{
    float vw, vh; get_view(vw, vh);
    float cx = vw * 0.5f, cy = vh * 0.5f;

    uint64 font = get_font20();

    draw_rect_filled(cx - 100, cy - 50, 200, 100,
                     40, 40, 40, 255, 8.0f, RR_TOP_LEFT|RR_TOP_RIGHT);

    draw_text("Hello World", cx - 60, cy - 10,
              255,255,255,255, font, TE_SHADOW,
              0,0,0,180, 1.0f, true);
}

int main()
{
     log("Starting persistent script...");

    // Run every 16 ms (~60 FPS)
    register_callback(on_tick, 16 , 0);

    // Stay loaded indefinitely
    return 1;
}

void on_unload()
{
     log("Unloaded script...");
}
```

The engine will keep this script alive until it’s explicitly unloaded.

***

### 🔹 Example #2 — One-shot Script

```cpp
int main()
{
    log("One-shot initialization...");
    // Return 0 to indicate we’re done — unload immediately
    return 0;
}
```

After this executes, the script and its thread context are released.

***

### 🔹 Engine Integration Notes

* The engine checks the return value of `main()` immediately after execution.
* Scripts with `main() > 0` are marked as *persistent* and remain loaded in the module table.
* Scripts returning `0` or negative values are **unloaded** and their memory is freed.
* `unregister_callback(id)` can be called at any time to stop background threads gracefully.
* `main` should never have any infinite loops.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/life-cycle.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
