# Network Protocol Reverse Engineering Reference

How to reverse-engineer a game's network protocol — capture, dissect, identify message boundaries, decode payloads. The defensive / educational half of network RE; pairs with the engine-RE references for the on-disk and in-memory sides. Useful for understanding what a game tells the server (anti-cheat telemetry shape, replay format design, server-message bus structure), for protocol documentation, and for legitimate research on private/community-run servers.

> **Scope:** Educational reference for authorized targets only. Network RE against live commercial servers may violate the game's Terms of Service or local computer-misuse statutes; see `skill://authorized-security-research` before pointing tooling at any non-owned endpoint. Private servers, your own development environment, packet captures from your own machine, and protocol research published by the game's own developers are the normal authorized scope.

---

## What This File Covers

- The packet-capture toolchain (Wireshark, tshark, mitmproxy, eBPF-tracing alternatives) and when to use which
- Identifying message-boundary patterns in TCP / UDP / WebSocket / QUIC game protocols
- Common encoding schemes games use (length-prefixed, type-tagged, varint-encoded, protobuf-shaped, FlatBuffers-shaped, custom-shaped)
- Encryption recognition — what TLS / DTLS / custom XOR / custom block-cipher looks like at the wire level
- Cross-referencing wire data to in-memory structures (the "this packet field is the same as the entity struct's m_iHealth" link)
- What to do when the protocol is over QUIC / HTTP3 (most modern AAA titles have moved here)

What this file does NOT cover:

- Server-side server-emulator authoring (out of scope; see project-specific server-emulator communities)
- Live MITM against production servers (not legal in most jurisdictions; not described here)
- Protocol cracking for the purpose of bypassing server-side validation (an exploit category outside this toolkit's scope)

---

## Capture Toolchain

Pick the tool by what you're capturing:

| Tool | Best for | Notes |
|---|---|---|
| **Wireshark** (GUI) | Interactive dissection, custom Lua dissectors, named TCP/UDP streams | The default. Filter syntax (`tcp.port == 27015 && data.len > 8`) is the productive surface. |
| **tshark** (CLI) | Scripted captures, batch processing, pcap-to-text pipelines | Same engine as Wireshark; CLI lets you grep raw payload bytes. |
| **mitmproxy / mitmweb** | HTTP / HTTPS / WebSocket traffic (with cert injection) | Useful for the increasing number of games that use HTTPS endpoints for matchmaking / inventory / telemetry. Requires the game to trust the mitmproxy CA. |
| **dumpcap** (Wireshark backend) | Long-running unattended captures, headless servers | Lighter-weight than full Wireshark; saves to `.pcap` / `.pcapng`. |
| **tcpdump** | Quick captures on Linux / macOS; minimal install | Older but ubiquitous. Output goes to `.pcap` for offline analysis. |
| **bpftrace / eBPF** | In-kernel filtering of high-volume traffic, custom sampling | Modern alternative when packet rates exceed userspace capture. |
| **PCAP-NG with comment annotations** | Persisted analysis context | Annotate packets with notes; survives reopening. |

For QUIC / HTTP3 (the increasing default for modern AAA titles): regular `.pcap` capture works at the IP/UDP level, but you need the connection's TLS keys to see inside. Browsers can dump these to `SSLKEYLOGFILE`; games typically don't. Without the keys, you see encrypted blobs and per-packet timing only.

The recommended starter setup: Wireshark with a Lua dissector for the game (described below), capturing the game's process traffic via the right interface (loopback if you're running a local server; the LAN interface if you're inspecting traffic to a remote server).

---

## Identifying Message Boundaries

Game protocols universally have a structure on top of TCP/UDP for delimiting application-level messages. Identifying that structure is step one of any dissection.

### TCP-based protocols

TCP is a byte stream; the game has to delimit its own messages on top. The three common patterns:

**Length-prefixed** — the most common modern pattern. Each message starts with N bytes encoding the rest of the message's length:

```
[ 2-byte length ] [ N-byte payload ]
or
[ 4-byte length ] [ N-byte payload ]
or
[ varint length ] [ N-byte payload ]
```

Recognize by: opening a Wireshark stream, looking at the first 2-4 bytes of each `tcp.stream` flow; the small integer value (matching the rest of the payload's byte count) is the length field.

**Type-tagged** — message starts with a type byte, then a per-type fixed or known-shape payload:

```
[ 1-byte type ] [ type-specific payload ]
```

Recognize by: the same byte value (e.g. `0x07`) appearing at regular intervals; the bytes following it have a stable shape for that type.

**Self-describing (rare in games, common in protobuf RPC)** — each message carries its own wire format hints:

```
[ varint tag ] [ varint length ] [ payload ] [ varint tag ] [ varint length ] [ payload ] ...
```

Recognize by: byte values 0x08-0x7F appearing as type tags, with varint length following.

### UDP-based protocols

UDP datagrams are inherently message-bounded — one datagram = one application message (or a fragment, if the game does its own fragmentation). The patterns:

- **Sequence-numbered** — header carries sequence + ack info for reliability layering. Quake/Source-engine style.
- **Type-prefixed** — same as TCP type-tagged but at datagram start.
- **Encrypted-blob** — datagram is opaque; key is exchanged during the initial handshake (often DTLS or a custom equivalent).

### Worked example: a length-prefixed TCP protocol

Suppose Wireshark shows you a TCP stream with payload starting:

```
0c 00 07 00 14 00 41 6c 69 63 65 00
0e 00 09 00 26 00 42 6f 62 73 31 32 33 00
05 00 12 00
```

Pattern recognition:
- Byte 0-1: `0c 00` = 12 (little-endian uint16) — and the payload after the length is exactly 12 bytes (`07 00 14 00 41 6c 69 63 65 00` is 10, plus the next 2 bytes... wait, count: 0c 00 means 12 bytes follow). Re-checking: 12 bytes after position 2 = positions 2..13. That includes `07 00 14 00 41 6c 69 63 65 00` (10 bytes) + 2 more. Yes, 12.
- Byte 14-15: `0e 00` = 14 (uint16 LE). 14 bytes follow.
- Byte 30-31: `05 00` = 5. 5 bytes follow.

The protocol shape:
```
struct Message {
    uint16_t length;          // little-endian
    uint8_t  type;            // example: 0x07 = login, 0x12 = heartbeat
    uint8_t  reserved;        // padding or flags
    uint16_t subtype_or_seq;  // 0x0014 / 0x0009 / etc
    // ... type-specific payload, ending with a null-terminated string in cases
}
```

Once you've identified the boundary mechanism, you can write a Wireshark dissector that splits the stream correctly.

---

## Wireshark Lua Dissector — the Productive Surface

Wireshark's Lua dissector API turns "raw byte stream" into "annotated tree of named fields" in the packet view. For any game you'll spend more than a few sessions reversing, the dissector is worth writing.

Minimal example for the length-prefixed protocol above:

```lua
-- mygame.lua — save in ~/.config/wireshark/plugins/ (Linux/macOS)
--                          or %APPDATA%\Wireshark\plugins\ (Windows)

local mygame_proto = Proto("mygame", "MyGame Protocol")

local f_length  = ProtoField.uint16("mygame.length",  "Length",  base.DEC)
local f_type    = ProtoField.uint8 ("mygame.type",    "Type",    base.HEX)
local f_subtype = ProtoField.uint16("mygame.subtype", "Subtype", base.HEX)
local f_payload = ProtoField.bytes ("mygame.payload", "Payload")

mygame_proto.fields = { f_length, f_type, f_subtype, f_payload }

function mygame_proto.dissector(tvbuf, pktinfo, root)
    pktinfo.cols.protocol = "MyGame"
    local subtree = root:add(mygame_proto, tvbuf())

    subtree:add_le(f_length,  tvbuf(0, 2))
    subtree:add   (f_type,    tvbuf(2, 1))
    subtree:add_le(f_subtype, tvbuf(4, 2))
    subtree:add   (f_payload, tvbuf(6))

    -- Optional: per-type sub-dissection
    local t = tvbuf(2, 1):uint()
    if t == 0x07 then
        pktinfo.cols.info = "LOGIN  " .. tvbuf(6):string()
    elseif t == 0x12 then
        pktinfo.cols.info = "HEARTBEAT"
    end
end

-- Register on the game's TCP port (replace with the actual port)
DissectorTable.get("tcp.port"):add(27015, mygame_proto)
```

Reload Wireshark; reopen the pcap; messages now show as MyGame instead of raw bytes. Iteratively add types as you identify them.

The dissector becomes the documentation of the protocol — sharing the `.lua` file is sharing the spec.

---

## Common Encoding Schemes

Game protocols converge on a handful of payload-encoding strategies:

### Plain-old struct dump

Fields written in declaration order, native byte order (usually little-endian on x86 / x64 games). The simplest case; recognize by per-field alignment matching a known struct.

### Length-prefixed strings

A length byte (or short) followed by N characters. Sometimes UTF-8, sometimes UTF-16LE (Windows-influenced engines), sometimes the game's own encoding for known character set restrictions (e.g. ASCII-only for usernames).

### Varint encoding (protobuf-style)

Each byte's high bit indicates "more to follow"; the low 7 bits accumulate into the integer. Recognize: bytes in range `0x80-0xFF` followed eventually by a byte `< 0x80`. Used by Protocol Buffers, FlatBuffers' varint helpers, and many custom encodings inspired by protobuf.

### Protobuf-shaped payloads

If the game uses Protocol Buffers (common for Google-stack games and many modern titles), the wire format is well-documented (https://protobuf.dev/programming-guides/encoding/). Per field: varint tag (combining field number and wire type), then payload (varint / fixed64 / length-delimited / start-group / end-group / fixed32). With the `.proto` schema (sometimes leaked, sometimes inferrable), the data decodes cleanly.

Even without the schema, you can identify protobuf by the tag byte pattern: low 3 bits encode wire type (0-5), upper 5+ bits the field number. Field 1, wire-type 0 (varint) = tag byte `0x08`. Field 1, length-delimited = `0x0A`. Field 2, length-delimited = `0x12`. Lots of `0x08`, `0x0A`, `0x10`, `0x12` etc. at message starts = protobuf.

### FlatBuffers-shaped payloads

Random-access binary format from Google. Recognize by the file/message header carrying a root-table offset, vtable indirection inside tables. More complex to decode without the schema; less common in games than protobuf.

### Custom-shaped — bit-packed fields

Some performance-sensitive game protocols (especially older Quake-derived ones) pack fields into bits to save bandwidth. Recognize by: byte values that don't decode cleanly as bytes; field boundaries that don't align to byte boundaries. Requires bit-level analysis.

### Compressed payloads

Larger payloads are often compressed before the wire — zlib / LZ4 / Zstd / LZF / Snappy. Recognize by: payload starting with a known magic number (`78 9C` for zlib default level, `78 DA` for max, `04 22 4D 18` for LZ4 frame, `28 B5 2F FD` for Zstd) or by entropy that's near uniform (compressed data looks like noise).

Decompress before dissecting the inner payload.

---

## Encryption Recognition

Games are increasingly TLS-wrapped, but not all. Identifying whether (and how) a stream is encrypted is step one of any deeper analysis.

### TLS / SSL on TCP

Recognize by:
- Stream starts with the TLS handshake (`16 03 01` for TLS 1.0 ClientHello, `16 03 03` for TLS 1.2)
- Wireshark identifies it as `tls` protocol automatically
- Application data records have header `17 03 03 <len-16>`

To see inside: you need the session keys. Browsers and many tools dump these to a file pointed at by `SSLKEYLOGFILE`; games rarely do. Without keys, you see encrypted blobs only.

### DTLS on UDP

The UDP equivalent of TLS. Recognize by similar handshake bytes at datagram start (`16 fe ff` ClientHello, etc.) and the `dtls` protocol detection in Wireshark.

### Custom XOR / stream cipher

Older / simpler games sometimes apply a per-byte XOR with a static or short-rotating key. Recognize by:
- Entropy is higher than plain text but lower than CSPRNG output (encrypted "looks like noise but not quite as noisy as TLS")
- Same byte positions across many messages have a repeating value-distribution (a fixed key betrays itself)
- The XOR key sometimes leaks via the game binary (search `tools/dump-strings-xor.py` for the key recovery angle on the on-disk side)

### Custom block cipher (AES / similar)

The game may apply AES-CBC or AES-GCM with a key negotiated in a custom handshake. Recognize by: 16-byte-aligned payload chunks (block boundary), high entropy throughout, deterministic-looking IV/nonce field at message start.

Without the key, indistinguishable from random; recover the key by reversing the game's handshake code on the binary side.

### Compression + obfuscation combo

Some games compress then XOR (or vice versa). Decompress first if you can identify the compression magic; XOR-recover then.

---

## Cross-Referencing Wire Data to In-Memory Structures

The synthesis step: wire-format field X corresponds to in-memory struct field Y. Once you have this, the game's protocol becomes a window into the game's state.

The workflow:

1. **Identify a known field in memory.** E.g. `m_iHealth` at offset 0x40 of the entity struct, value 100, observed via PCX's `mcp:struct_dump`.
2. **Take an in-game action that changes that field.** Take damage; health drops to 87.
3. **Capture the network traffic around the action.** Wireshark or tshark with a tight time filter.
4. **Find the byte pattern that changed correspondingly.** A 4-byte field that was `64 00 00 00` (100 LE) in a pre-action packet, now `57 00 00 00` (87 LE) in a post-action packet.
5. **Confirm with a second action.** Take more damage; verify the wire field tracks.

Once you've mapped one field, the same packet's neighboring bytes are candidates for other fields. Build the mapping incrementally; document in the dissector.

The cross-reference is bidirectional:
- Wire → memory: "this server-sent field updates the in-memory health field"
- Memory → wire: "this in-memory field is sent at this byte position in this message type"

Both directions are useful: the first for understanding what the server tells the client; the second for understanding what the client tells the server (which is the more interesting half for anti-cheat-telemetry research and replay-format work).

---

## When the Protocol Is QUIC / HTTP3

Increasing fraction of modern AAA titles use QUIC (HTTP/3) for matchmaking, telemetry, and sometimes game traffic. QUIC is UDP-based and encrypted by default; capture without keys shows you UDP datagrams with QUIC-protocol headers but no payload visibility.

Options:

- **Connection-side key dump.** If you control either endpoint (your own game client running in a dev environment, or a private-server target you own), tools like `keylogger.so` or `SSLKEYLOGFILE` (where supported by the QUIC library) dump the session keys. Wireshark + the keylog file decrypts the QUIC stream.
- **Process-side hooking.** Hook the game's QUIC library (msquic, quiche, ngtcp2, the game's own custom QUIC implementation) before encryption to capture cleartext. This is much more invasive (DLL injection or LD_PRELOAD on the client) and only legal on systems you own.
- **Endpoint observation, not wire observation.** Use the game's own logs / debug builds / leaked SDK to see what *would* be sent at the application layer, even without decrypting the wire. Often easier than full QUIC decryption.

QUIC's encryption-by-default has made wire-level RE materially harder than it was during the TCP-with-optional-TLS era; expect to pair wire analysis with binary-side analysis to a much greater extent for modern titles.

---

## Replay Files — the Persisted Cousin

Many games persist game state in a `.dem` / `.replay` / `.rec` file. The replay format is often a *recording of the network protocol* — the server-to-client message stream, written to disk verbatim plus a header. If so, decoding the replay file is the same problem as decoding the network protocol.

For Source-engine games, `.dem` files are well-documented community-side; for modern titles, the format is typically reverse-engineered per-game by community replay-parser projects.

The dissector you wrote for the network protocol is usually directly reusable for the replay file — point it at the `.dem` instead of a `.pcap`. This makes replay-based RE much cheaper than live capture (no game required, no server required, deterministic for repeated analysis).

---

## Cross-References

- `skill://authorized-security-research` — what's in scope for any network-side analysis
- `knowledge/anti-cheat-architecture.md` — the AC side of network telemetry
- `knowledge/kernel-re-tools.md` — the binary-side counterpart for understanding the game's network code
- `knowledge/engine-cryengine.md` / `engine-frostbite.md` / etc. — engine-specific network architecture notes
- `tools/dump-strings-xor.py` — recovers XOR keys from a game binary (the on-disk side of custom-XOR-encrypted protocols)
- `tools/identify-protector.py` — flags binaries with anti-tamper layers that often also wrap the network code
- `.claude/skills/re-evidence-log` — the per-binary evidence-citation discipline applies to wire-format field mappings the same way it applies to in-memory ones
- Wireshark docs — https://www.wireshark.org/docs/ (the comprehensive reference for the toolchain)
