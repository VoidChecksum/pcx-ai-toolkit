> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/net-api.md).

# Net API

All net natives are auto-registered into every loaded script.

All network calls are gated by the `network_access` permission. Without it, calls return a transport-failure value (`status=0` / null handle / empty array).

## HTTP — sync, with timeout

```cpp
http_response_t http_get (string url, int64 timeout_ms);
http_response_t http_get (string url, map<string, string> headers, int64 timeout_ms);

http_response_t http_post(string url, string content_type, string body, int64 timeout_ms);
http_response_t http_post(string url, string content_type, string body,
                          map<string, string> headers, int64 timeout_ms);
```

Both always return a non-null `http_response_t`. Read via methods:

```cpp
int64  response.status();    // 0 on transport failure / permission denied
string response.body();
bool   response.ok();        // true if status is 200..299
```

`content_type` may be empty for `http_post`. The 3-arg `http_get` / 5-arg `http_post` overloads take a `map<string, string>` of extra request headers — useful for `Authorization: Bearer ...`, `X-API-Key`, `Accept`, custom protocol headers, etc. Pass `null` or an empty map to skip.

### Headers example

```cpp
map<string, string> headers;
headers.set("Authorization", "Bearer " + g_token);
headers.set("Accept", "application/json");

http_response_t r = http_get("https://api.example.com/me", headers, 5000);
if (r.ok()) println(r.body());
```

```cpp
map<string, string> headers;
headers.set("X-API-Key", "abc123");

http_response_t r = http_post(
    "https://api.example.com/events",
    "application/json",
    "{\"event\":\"login\"}",
    headers,
    5000);
```

## WebSocket

```cpp
ws_t ws_connect(string url, int64 timeout_ms);
```

Connects to `ws://`, `wss://` (also `http://` / `https://` accepted). Spawns a background recv thread. Returns a null handle on failure or permission denied.

### `ws_t` methods

```cpp
bool         ws.is_open();
bool         ws.send_text  (string msg);
bool         ws.send_binary(array<uint8> data);

ws_message_t ws.recv();      // blocks until a message arrives or the connection closes
ws_message_t ws.poll();      // non-blocking

void         ws.close(int64 code);    // standard WS close codes (1000 = normal)
```

### `ws_message_t` methods

```cpp
bool   msg.ok();          // true if a message was returned
bool   msg.is_text();     // payload framing
bool   msg.is_closed();   // peer / local close has fired
string msg.payload();
```

## UDP — raw datagrams

```cpp
udp_t udp_create();
```

Creates a fresh UDP socket. Returns a null handle on failure / permission denied. Send-only sockets can skip `bind()`; sockets that receive must `bind()` to a local port first.

### `udp_t` methods

```cpp
bool         udp.bind(string addr, int64 port);                      // "0.0.0.0" / port — port 0 = OS-picked
bool         udp.send_to(array<uint8> data, string addr, int64 port);
array<uint8> udp.recv(int64 timeout_ms);                             // blocking with timeout; empty on timeout/error

string       udp.last_sender_addr();    // IP of the most recent successful recv()
int64        udp.last_sender_port();    // port of the most recent successful recv()

void         udp.close();
```

`recv` returns up to one full UDP datagram (max 65535 bytes). Timeout is in milliseconds — `timeout_ms = 0` means block indefinitely. After a successful `recv`, `last_sender_addr()` / `last_sender_port()` give you the peer to reply to.

### UDP example — Source Query Protocol (A2S\_INFO)

```cpp
udp_t s = udp_create();
if (cast<int64>(s) == 0) return 0;

// A2S_INFO request: FF FF FF FF 54 "Source Engine Query" 00
array<uint8> q;
q.push(0xFF); q.push(0xFF); q.push(0xFF); q.push(0xFF); q.push(0x54);
string banner = "Source Engine Query";
for (int32 ch : banner) q.push(cast<uint8>(ch));
q.push(0x00);

if (!s.send_to(q, "1.2.3.4", 27015)) {
    println("send failed");
    return 0;
}

array<uint8> reply = s.recv(2000);  // 2-second timeout
if (reply.length() == 0) {
    println("no reply (timeout)");
} else {
    println(format("got {d} bytes from {s}:{d}",
        reply.length(), s.last_sender_addr(), s.last_sender_port()));
}
```

### UDP example — listener

```cpp
udp_t s = udp_create();
s.bind("0.0.0.0", 9999);

for (int32 i = 0; i < 10; i = i + 1) {
    array<uint8> pkt = s.recv(1000);
    if (pkt.length() == 0) continue;
    println(format("from {s}:{d} ({d} bytes)",
        s.last_sender_addr(), s.last_sender_port(), pkt.length()));
}
```

## HTTP example

```cpp
http_response_t r = http_get("https://api.example.com/status", 5000);
if (r.ok()) {
    println("got: " + r.body());
} else if (r.status() == 0) {
    println("transport failed or permission denied");
} else {
    println("server returned " + cast<string>(r.status()));
}
```

## WebSocket example

```cpp
ws_t ws = ws_connect("wss://echo.example.com/", 5000);
if (cast<int64>(ws) == 0) return 0;

ws.send_text("hello");
ws_message_t m = ws.recv();
if (m.ok()) {
    println("got: " + m.payload());
}
ws.close(1000);
```

## Permission

`network_access` gates every native in this file (HTTP, WebSocket, UDP). When off, every call returns a transport-failure value.

## Lifetime

`ws_t` and `udp_t` close + free via the destructor at scope exit. If the script forgets, the host sweeps remaining sockets at unload — connections closed, threads joined, no permanent leak. UDP packets in flight are not buffered host-side; once you close, anything still on the wire is dropped by the OS.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/net-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
