> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/engine.md).

# Engine

### ⚙️ Overview

A callback is a **script function** that executes repeatedly on a background thread created by the engine.\
Each callback receives a unique **callback ID** (integer) and runs at a defined interval in milliseconds.

***

### 🧩 Registration Functions

#### Register Callback

```angelscript
int register_callback(const __Internal_CallbackFn@ fn, int every_ms, int data_index, bool render_on_top = false)
```

Registers a new recurring callback function.\
The engine launches a lightweight thread that periodically invokes your callback, passing both its unique ID and the `data_index` you supplied.

| **Parameter**   | **Type**                 | **Description**                                                                                                                                                                                     |
| --------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fn`            | `__Internal_CallbackFn@` | Function pointer to the callback (takes two integer arguments — the callback ID and the data index).                                                                                                |
| `every_ms`      | `int`                    | Delay in milliseconds between callback executions.                                                                                                                                                  |
| `data_index`    | `int`                    | User-defined integer value forwarded to your callback each time it runs. This can represent a dataset slot, UI layer, or logic group.                                                               |
| `render_on_top` | `bool`                   | Optional flag. Set to `true` to render this callback’s output above everything else. If multiple callbacks use this, registration order still determines which one is topmost. Defaults to `false`. |

**Returns:**\
A unique callback ID (`int`) if successful, or `0` on failure. Drawing And Input is unique for each thread.

> 🧠 The callback executes in its own thread. Each iteration:
>
> 1. Begins input collection
> 2. Executes your callback function
> 3. Submits the current draw list
> 4. Ends input and sleeps for `every_ms`

***

#### Unregister Callback

```cpp
void unregister_callback(int id)
```

Stops a previously registered callback and terminates its thread.

| Parameter | Type | Description                                      |
| --------- | ---- | ------------------------------------------------ |
| id        | int  | The callback ID returned by `register_callback`. |

***

### 🧠 Callback Function Type

The callback function type is defined internally by the engine:

```cpp
funcdef void __Internal_CallbackFn(int callback_id, int data_index)
```

Your script callback must accept **two integer parameters**:

| **Parameter** | **Type** | **Description**                                                                                                                                                          |
| ------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `callback_id` | `int`    | The callback ID returned by `register_callback`. This uniquely identifies the running callback instance.                                                                 |
| `data_index`  | `int`    | A user-defined or engine-supplied index value associated with this callback execution. Can be used to differentiate multiple data contexts handled by the same callback. |

***

#### Example

```cpp
void on_update(int callback_id, int data_index)
{
    log("Callback " + callback_id + " tick (data=" + data_index + ")");

    // draw something using data_index
    float x = 100 + data_index * 40;
    draw_circle(x, 200, 10, 255,200,100,255, 2.0f, false);
}

int main()
{
    // Run callback every 50ms
    int cb = register_callback(on_update, 50, 34);
    log("Registered callback " + cb);

    return 1; // keep script running
}
```

***

### 🪵 Logging Helper

```cpp
void log(const string &in message)
// Displays a standard informational message in the UI log overlay.

void log_error(const string &in message)
// Displays an error-styled message in the UI log overlay and raises an exception.

void log_console(const string &in message)
// Writes a message to the debug console (persistent until the console is cleared).

void log_console_error(const string &in message)
// Writes an error-styled message to the debug console in red and raises an exception.
```

Example:

```cpp
log("Log Example");
log_error("Error Log Example");
log_console("Current HP : 100");
log_console_error("Error Log Example");
```

***

#### get\_username(): string

Returns the current PCX username as a string.

**Syntax**

```cpp
string get_username()
```

***

### 📜 Example: Animated Cursor

```cpp
float r = 0.0f;

void animate_cursor(int id, int data_index)
{
    float x, y;
    get_mouse_pos(x, y);
    
    r += 2.0f;
    
    draw_circle(x, y, 12 + sin(r * 0.1f) * 4,
    255, 100, 50, 255,
    2.0f, false);
}

int main()
{
    register_callback(animate_cursor, 1, 0);
    return 1;
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/engine.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
