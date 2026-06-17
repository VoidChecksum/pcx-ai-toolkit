> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/net-api.md).

# Net API

The Net API provides:

* **HTTP(S)** helpers
  * `net_http_get(url, timeout_ms?)`
  * `net_http_post(url, content_type, body, timeout_ms?)`
* **WebSocket** client using WinHTTP’s WebSocket support
  * `ws_connect(url, timeout_ms?) -> websocket userdata`
  * WebSocket methods:\
    `send_text`, `send_binary`, `send_json`, `recv`, `poll`, `is_open`, `close`

Supported URL schemes:

* HTTP: `http://`, `https://`
* WebSocket: `ws://`, `wss://` (internally mapped to `http://` / `https://` for WinHTTP)
* Works with hostnames **and** IP addresses, with or without custom ports.

> ⚠ These are **low-level** primitives intended for advanced users. Higher-level helpers/wrappers can be built on top, but are not part of this page.

***

### HTTP API

#### `net_http_get`

```lua
ok, status_code, body = net_http_get(url, timeout_ms?)
```

Performs a **synchronous HTTP/HTTPS GET**.

**Parameters**

* `url : string`
  * Full URL:
    * `"https://example.com/api/test"`
    * `"http://127.0.0.1:8080/status"`
* `timeout_ms : number (optional)`
  * Total timeout (ms) applied to resolve, connect, send, receive.
  * `0` or `nil` = default WinHTTP timeouts.

**Returns**

* `ok : boolean`
  * `true` if the HTTP request succeeded at the transport level (WinHTTP OK).
  * `false` if there was a network/protocol error.
* `status_code : integer`
  * HTTP status code (200, 404, 500, ...)
  * `0` if the request failed before a response was received.
* `body : string`
  * Response body as raw bytes (Lua string).

**Example**

```lua
local ok, status, body = net_http_get("https://httpbin.org/get", 5000)

if not ok then
    log("[HTTP] GET failed, status=" .. tostring(status))
    return
end

log("[HTTP] GET status=" .. status)
log("[HTTP] GET body=" .. body)
```

***

#### `net_http_post`

```lua
ok, status_code, body = net_http_post(url, content_type, body, timeout_ms?)
```

Performs a **synchronous HTTP/HTTPS POST** with a request body.

**Parameters**

* `url : string`
  * Full URL, same as `net_http_get`.
* `content_type : string`
  * MIME type, e.g.:
    * `"application/json"`
    * `"application/x-www-form-urlencoded"`
    * `"text/plain; charset=utf-8"`
* `body : string`
  * Request body as a Lua string (raw bytes).
* `timeout_ms : number (optional)`
  * Same semantics as `net_http_get`.

**Returns**

* `ok : boolean`
* `status_code : integer`
* `body : string`\
  (Same meaning as `net_http_get`.)

**Example – POST JSON**

```lua
local payload = '{"hello":"world","value":123}'

local ok, status, resp = net_http_post(
    "https://httpbin.org/post",
    "application/json",
    payload,
    5000
)

if not ok then
    log("[HTTP] POST failed, status=" .. tostring(status))
    return
end

log("[HTTP] POST status=" .. status)
log("[HTTP] POST body=" .. resp)
```

***

### WebSocket API

The WebSocket API exposes:

* A global **constructor**: `ws_connect(url, timeout_ms?)`
* A userdata type **`net_ws`** with methods:
  * `send_text`, `send_binary`, `send_json`
  * `recv`, `poll`
  * `is_open`, `close`

Internally, the implementation uses WinHTTP:

* `ws://` → internally mapped to `http://`
* `wss://` → internally mapped to `https://`
* A background **receive thread** continuously reads frames and pushes **complete messages** into a queue.
* Lua sees messages via `ws:recv()` (blocking) or `ws:poll()` (non-blocking).

#### Global: `ws_connect`

```lua
ws, err = ws_connect(url, timeout_ms?)
```

Opens a **client WebSocket** connection.

**Parameters**

* `url : string`
  * WebSocket URL, e.g.:
    * `"wss://ws.postman-echo.com/raw"`
    * `"ws://127.0.0.1:9001/echo"`
* `timeout_ms : number (optional)`
  * WinHTTP timeouts (resolve, connect, send, receive).

**Returns**

* On success:
  * `ws : userdata` (type `net_ws`)
    * A WebSocket object with methods described below.
* On failure:
  * `nil, "error string"`

**Example**

```lua
local ws, err = ws_connect("wss://ws.postman-echo.com/raw", 5000)
if not ws then
    log("[WS] connect failed: " .. tostring(err))
    return
end

log("[WS] connected: " .. tostring(ws))  -- e.g. "websocket(open)"
```

***

### WebSocket Object (`net_ws`)

Once connected, you have a userdata with metatable `"net_ws"`, exposing these methods:

* `ws:send_text(message)`
* `ws:send_binary(data)`
* `ws:send_json(value)`
* `ws:recv()`
* `ws:poll()`
* `ws:is_open()`
* `ws:close(code?)`

And metamethods:

* `__gc` – automatic cleanup
* `__tostring` – `"websocket(open)"` or `"websocket(closed)"`

***

#### `ws:send_text`

```lua
ok = ws:send_text(message)
```

Sends a **UTF-8 text message**.

**Parameters**

* `message : string` – Lua string, treated as UTF-8.

**Returns**

* `ok : boolean` – `true` if the send call succeeded; `false` otherwise.

**Example**

```lua
local ok = ws:send_text("hello from PCX")
log("[WS] send_text ok = " .. tostring(ok))
```

***

#### `ws:send_binary`

```lua
ok = ws:send_binary(data)
```

Sends a **binary WebSocket frame**.

**Parameters**

* `data : string` – raw bytes (Lua string).

> ⚠ Some public echo servers (e.g. Postman’s) **close the connection** when they receive binary frames. That’s a server behavior, not a bug in the API.

**Returns**

* `ok : boolean`

**Example**

```lua
local bin = string.char(0,1,2,3,4,5)
local ok = ws:send_binary(bin)
log("[WS] send_binary ok = " .. tostring(ok))
```

***

#### `ws:send_json`

```lua
ok = ws:send_json(value)
```

Sends a **JSON text message**. Supports:

* `value` = **string**: sent directly as UTF-8.
* `value` = **table**: encoded via global Lua function `json_encode`.

**Parameters**

* `value : string | table`
  * `string` – assumed to already be valid JSON.
  * `table` – will call `json_encode(value)` to produce JSON.

**Requirements**

* For `table`:
  * A global function `json_encode` must exist:

    ```lua
    function json_encode(tbl) -> string
    ```
  * If `json_encode` is missing or throws, `ws:send_json` raises a Lua error.

**Returns**

* `ok : boolean`

**Example – string**

```lua
local js = '{"type":"ping","time":123.45}'
ws:send_json(js)
```

**Example – table**

```lua
-- Assuming json_encode is registered globally in this environment.

ws:send_json({
    type = "ping",
    time = perf_time(),
    source = "pcx"
})
```

***

#### `ws:recv` (blocking)

```lua
msg, is_text = ws:recv()
```

**Blocking** receive that waits for a **complete WebSocket message** to be available in the queue.

* Uses the internal message queue (filled by a background thread).
* Does **not** block WinHTTP directly; it loops until:
  * A message is dequeued, or
  * The socket is closed and the queue is empty.

**Returns**

* On message:
  * `msg : string` – message payload (text or binary).
  * `is_text : boolean`
    * `true` for text frames
    * `false` for binary frames
* On closed and empty:
  * `nil`

> ⚠ This is a **blocking loop with a small sleep** (`Sleep(1)`).\
> Best used in worker scripts or one-shot tests, not every frame in the UI thread.

**Example**

```lua
local msg, is_text = ws:recv()
if not msg then
    log("[WS] recv: connection closed or error")
else
    log("[WS] recv: kind=" .. (is_text and "text" or "binary")
        .. " len=" .. #msg)
end
```

***

#### `ws:poll` (non-blocking)

```lua
msg, is_text_or_closed = ws:poll()
```

**Non-blocking** receive from the internal message queue.

You get **three possible outcomes**:

1. **Message available**
   * `msg : string` – message payload
   * `is_text_or_closed : boolean` – `true` = text, `false` = binary
2. **No message yet, still open**
   * `msg = nil`
   * `is_text_or_closed` is **nil**
3. **Socket closed and queue empty**
   * `msg = nil`
   * `is_text_or_closed = false`

This makes it easy to integrate in per-frame loops:

* `msg != nil` → handle it
* `msg == nil and is_text_or_closed == nil` → nothing yet
* `msg == nil and is_text_or_closed == false` → closed

**Example: per-frame polling**

```lua
function on_frame()
    if not ws then return end

    local msg, flag = ws:poll()
    if msg then
        local kind = flag and "text" or "binary"
        log("[WS] poll: " .. kind .. " msg=" .. msg)
    elseif flag == false then
        log("[WS] poll: socket closed")
        ws = nil
    end
end
```

***

#### `ws:is_open`

```lua
is_open = ws:is_open()
```

Checks whether the socket is currently open.

* Reflects the internal `is_open` flag updated by the background thread and close logic.

**Returns**

* `true` if the socket is open.
* `false` if it is closed or has encountered a fatal error.

**Example**

```lua
if ws and ws:is_open() then
    ws:send_text("still here")
else
    log("[WS] socket is closed")
end
```

***

#### `ws:close`

```lua
ws:close(code?)
```

Closes the WebSocket connection.

* Signals the background receive thread to stop.
* Sends a WebSocket close frame (best effort).
* Waits for the thread to exit, then closes all WinHTTP handles.

**Parameters**

* `code : integer (optional)`
  * WebSocket close status. Defaults to `WINHTTP_WEB_SOCKET_SUCCESS_CLOSE_STATUS`.

**Example**

```lua
if ws then
    ws:close()  -- normal clean shutdown
    ws = nil
end
```

***

#### Metamethods

**`__gc`**

Called automatically when the Lua userdata is garbage collected.

* Calls `ws_close_internal`, deletes the critical section, frees `lua_ws_t`.
* You don’t call this directly; it’s tied to object lifetime.

**`__tostring`**

Used when you do:

```lua
tostring(ws)
```

* Returns `"websocket(open)"` or `"websocket(closed)"`.

Example:

```lua
log("WS object: " .. tostring(ws))
```

***

### Summary

**Global HTTP:**

```lua
ok, status, body = net_http_get(url, timeout_ms?)
ok, status, body = net_http_post(url, content_type, body, timeout_ms?)
```

**Global WebSocket:**

```lua
ws, err = ws_connect(url, timeout_ms?)
```

**WebSocket object (`net_ws`):**

```lua
ws:send_text(message)         -- bool
ws:send_binary(data)          -- bool
ws:send_json(value)           -- bool (string or table with json_encode)
ws:recv()                     -- msg, is_text | nil  (blocking)
ws:poll()                     -- msg, is_text | nil | nil,false
ws:is_open()                  -- bool
ws:close(code?)               -- nil
tostring(ws)                  -- "websocket(open)" / "websocket(closed)"
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/net-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
