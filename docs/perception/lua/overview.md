> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/overview.md).

# Overview

This environment provides a lightweight scripting layer for UI, rendering, memory analysis and interaction in Perception.cx. It uses **Lua** with core add-ons and PCX-specific APIs enabled by default.

This API is strictly allowed to be used for malware analysis and educational purposes only, any violation of our [TOS](https://perception.cx/help/terms/) will result in termination from the platform.

### Core Add-ons

The following standard AngelScript modules are registered:

* **base** — core Lua functions
* **package** — `require()` and module loading
* **coroutine** — coroutine creation & scheduling
* **table** — table helpers (`insert`, `remove`, `sort`, ...)
* **string** — pattern matching & string utilities
* **math** — numeric functions
* **utf8** — UTF-8 text helpers

***

### PCX APIs

Custom host APIs extend the scripting environment:

* **Render API** — draw shapes, text, images, and gradients
* **Input API** — mouse, keyboard, and scroll input
* **Host Utilities** — logging and script lifecycle helpers
* **Proc API** — memory inspection and manipulation
* **GUI API** — create and interact with UI elements
* **System API** — CPU info, instruction utilities, disassembly
* **Net API** — HTTP, HTTPS, and WebSocket networking
* **File System API** — read, write, and manage files/folders
* **Extended Math API** — vectors, matrices, quaternions, and math helpers
* **Engine Specific API**  — read engine specific structures easier
* **Json API**
* **Utilities** — encoding, decoding, etc
* **Sound API**&#x20;


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/overview.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
