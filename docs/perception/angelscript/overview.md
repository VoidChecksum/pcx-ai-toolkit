> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/overview.md).

# Overview

This environment provides a lightweight scripting layer for UI, rendering, memory analysis and interaction in Perception.cx. It uses **AngelScript** with core add-ons and PCX-specific APIs enabled by default.

This API is strictly allowed to be used for malware analysis and educational purposes only, any violation of our [TOS](https://perception.cx/help/terms/) will result in termination from the platform.

***

### Core Add-ons

The following standard AngelScript modules are registered:

* **string** — native string support.
* **array** — dynamic arrays with value semantics.
* **dictionary** — key/value associative maps.
* **math** — standard math utilities.
* **any** — variant type for mixed data.
* **grid** — 2D grid storage type.
* **script helper** — Exception helper functions

***

### PCX Addons

Custom host APIs extend the scripting environment:

* **Unicorn** — A CPU Emulator&#x20;
* **Atomic Types**  — thread-safe lock-free integer primitives
* **Render API** — draw shapes, text, images, and gradients, now advance gpu math + advance functions.
* **Input API** — mouse, keyboard, and scroll input
* **Host Utilities** — logging and script lifecycle helpers
* **Proc API** — memory inspection and manipulation
* **Mutex API** — thread-safety primitives for synchronized access
* **GUI API** — create and interact with UI elements
* **System API** — CPU info, instruction utilities, disassembly
* **Net API** — HTTP, HTTPS, and WebSocket networking
* **File System API** — read, write, and manage files/folders
* **Extended Math API** — vectors, matrices, quaternions, and math helpers
* **Engine Specific API**  — read engine specific structures easier
* **Json API** — JSON parsing and serialization utilities for AngelScript dictionaries
* **Utilities** — encoding, decoding, etc
* **Zydis Encoder**  — Assemble x86/x64 instructions into machine code bytes
* **Intrinsics** — Intrinsics (SSE / Bit Operations)
* **Sound API**&#x20;
* **Bit Reinterpret Helpers** — convert values by reinterpreting their underlying bit patterns
* **CS2 Extended API** - For Official CS2 Product


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/overview.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
