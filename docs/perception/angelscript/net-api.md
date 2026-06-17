> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/net-api.md).

# Net API

The **Net API** provides AngelScript access to:

* **HTTP(S)** requests
* **WebSocket** (ws / wss) connections
* Background message buffering
* Safe multi-threaded operation&#x20;
* Automatic cleanup on script unload

***

### Overview

#### HTTP

* `net_http_get(url, status, body, timeout_ms)`
* `net_http_post(url, content_type, body, status, out_body, timeout_ms)`

#### WebSocket

* `ws_t ws_connect(url, timeout_ms)`
* `ws_t` methods:
  * `is_open()`
  * `send_text()`
  * `send_json()`
  * `send_binary()`
  * `recv()` (blocking)
  * `poll()` (non-blocking)
  * `close()`

#### Supported URL Schemes

| Type      | Schemes                              |
| --------- | ------------------------------------ |
| HTTP      | `http://`, `https://`                |
| WebSocket | `ws://`, `wss://`                    |
| Hostnames | `example.com`, `sub.domain.net`      |
| IPs       | `127.0.0.1`, `192.168.x.x`           |
| Ports     | Fully supported: `ws://ip:port/path` |

> `ws://` and `wss://` automatically map to WinHTTP’s `http://` / `https://` internally.

***

## HTTP API

### `bool net_http_get(...)`

```cpp
bool net_http_get(
    const string &in url,
    uint &out status_code,
    string &out body,
    uint timeout_ms = 0
);
```

#### Parameters

| Name          | Type         | Description                                     |
| ------------- | ------------ | ----------------------------------------------- |
| `url`         | `string`     | Full URL (`https://httpbin.org/get`)            |
| `status_code` | `out uint`   | HTTP status (200, 404, etc.)                    |
| `body`        | `out string` | Response body                                   |
| `timeout_ms`  | `uint`       | Optional timeout (resolve/connect/send/receive) |

#### Returns

`true` = request succeeded (transport level, not HTTP success)\
`false` = network/connection error

#### Example

```cpp
uint status;
string body;

bool ok = net_http_get("https://httpbin.org/get", status, body, 5000);

if (ok)
{
    log("GET " + status);
    log("Body: " + body);
}
```

***

### `bool net_http_post(...)`

```cpp
bool net_http_post(
    const string &in url,
    const string &in content_type,
    const string &in body,
    uint &out status_code,
    string &out response,
    uint timeout_ms = 0
);
```

#### Example

```cpp
uint status;
string response;

bool ok = net_http_post(
    "https://httpbin.org/post",
    "application/json",
    "{\"hello\":\"pcx\"}",
    status,
    response,
    5000
);
```

***

## WebSocket API

WebSockets are exposed as a handle type:

```cpp
ws_t ws_connect(const string &in url, uint timeout_ms = 0);
```

Internally, each websocket:

* Opens a WinHTTP WebSocket handle
* Launches a **background message receive thread**
* Buffers complete messages into a protected queue
* Cleans up automatically on script unload (using AS ref-tracking like `proc_t`)

***

## `ws_t ws_connect(...)`

```cpp
ws_t ws_connect(const string &in url, uint timeout_ms = 0);
```

#### Return value

* A valid `ws_t` handle on success
* `0` on failure

#### Example

```cpp
ws_t ws = ws_connect("wss://ws.postman-echo.com/raw", 5000);
if (ws == 0)
{
    log("Connection failed");
    return;
}
log("Connected");
```

***

## WebSocket Methods

All websocket operations are methods on the `ws_t` type.

***

### `bool ws_t::is_open() const`

Returns `true` while:

* The socket is open, AND
* The background receive thread is still running.

***

### `bool ws_t::send_text(const string &in msg)`

Sends a UTF-8 text frame.

```cpp
ws.send_text("hello from AS!");
```

***

### `bool ws_t::send_json(const string &in json)`

Sends a JSON UTF-8 message.

Example:

```cpp
ws.send_json("{\"type\":\"ping\",\"from\":\"as\"}");
```

***

### `bool ws_t::send_binary(const array<uint8> &in data)`

Sends a binary WebSocket frame.

```cpp
array<uint8> bin = { 0, 1, 2, 3 };
ws.send_binary(bin);
```

> Some public echo servers may close on binary frames.\
> Your API supports them natively.

***

## Receiving Messages

Messages are delivered as **complete frames** into an internal queue.

***

### `bool ws_t::recv(string &out msg, bool &out is_text)`

Blocking receive (waits for next message).

* Returns `true` when a message is dequeued.
* Blocks with a 1ms sleep inside the engine.
* Returns `false` if the socket closed and queue is empty.

#### Example

```cpp
string msg;
bool isText;

if (ws.recv(msg, isText))
    log("Received: " + msg);
```

***

### `bool ws_t::poll(string &out msg, bool &out is_text, bool &out is_closed)`

Non-blocking check.

#### Outcomes

1. **Message available**
   * Returns `true`
   * Fills `msg`
   * `is_text = true/false`
   * `is_closed` reflects final socket state
2. **No message yet**
   * Returns `false`
   * `msg = ""`
   * `is_closed = false`
3. **Socket closed and queue empty**
   * Returns `false`
   * `is_closed = true`

#### Example (frame update)

```cpp
string msg;
bool text, closed;

bool has = ws.poll(msg, text, closed);

if (has)
{
    log("WS message: " + msg);
}
else if (closed)
{
    log("WS closed");
}
```

***

## Closing

### `void ws_t::close(uint16 code = 1000)`

* Signals the receive thread to stop
* Sends a close frame
* Waits for the thread to terminate
* Frees all WinHTTP handles
* Removes itself from the internal AS websocket ref-tracker

#### Example

```cpp
ws.close();
```

***

## Automatic Cleanup (Important)

This API integrates with your existing **AngelScript resource tracking model**:

* All websockets created within a script are tracked
* On script unload, the engine loops through these refs and frees them

This guarantees:

* No leaked sockets
* No zombie threads
* Safe hot-reload

***

## Full Example

```cpp
int main()
{
    uint status;
    string body;
    
    // HTTP
    if (net_http_get("https://httpbin.org/get", status, body, 3000))
    log("GET OK: " + status);
    
    // WS
    ws_t ws = ws_connect("wss://ws.postman-echo.com/raw", 3000);

    ws.send_text("hello from AS");
    
    string msg; bool text;
    if (ws.recv(msg, text))
    log("Echo: " + msg);
    
    ws.close();
    return 0;
}
```

***

## Summary

#### HTTP

* `net_http_get(url, out status, out body, timeout)`
* `net_http_post(url, content_type, body, out status, out response, timeout)`

#### WebSocket

* `ws_t ws_connect(url, timeout)`
* `ws_t` methods:
  * `is_open()`
  * `send_text()`
  * `send_json()`
  * `send_binary()`
  * `recv(out msg, out is_text)`
  * `poll(out msg, out is_text, out is_closed)`
  * `close(code)`


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/net-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
