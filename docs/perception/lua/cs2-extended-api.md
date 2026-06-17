> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/cs2-extended-api.md).

# CS2 Extended API

This API is available in both the Uni API and the CS2 product.

This API is strictly allowed to be used for local and educational purposes only, any online-multiplayer usage will result in termination from the platform. Any violation of our [TOS](https://perception.cx/help/terms/) will result in termination from the platform.

In the CS2 product, all standard Proc API functions are supported **except**:

* Process referencing by PID/name
* Engine-specific helpers
* Virtual memory allocation (`alloc_vm` / `free_vm`)

On CS2 Product, `ref_process()` always returns the **CS2 process only**, so it is used like:

```lua
local cs2 = ref_process()  -- for CS2 Product only
```

There is **no memory allocation API** exposed in the CS2 product.

***

**🔗 `process:cs2_get_interface(module_base, name)`**

Resolves a **CreateInterface-style** interface exported by a CS2 module.

```lua
addr = process:cs2_get_interface(module_base, name)
```

**Parameters**

* `module_base`\
  Base address of the module that exports `CreateInterface`, e.g.:

  * `"tier0.dll"`

  Typically obtained via:

  ```lua
  local base, size = process:get_module("tier0.dll")
  ```
* `name`\
  Interface name string, e.g.:
  * `"VEngineCvar007"`

**Returns**

* Absolute pointer to the resolved interface (Lua integer).
* `0` if the interface cannot be found or the arguments are invalid.

***

**🧬 `process:cs2_get_schema_dump()`**

Dumps all Schema System fields for `client.dll` via `schemasystem.dll`.

```lua
entries = process:cs2_get_schema_dump()
```

**Return value**

A **Lua array-style table** (`1..N`) where each element is a table:

```lua
{
    name   = "ClassName::fieldName", -- string
    offset = 0x10,                   -- integer offset
}
```

**Fields**

* `name` — `"ClassName::fieldName"`, UTF-8 string\
  e.g. `"CPulse_CallInfo::m_nEditorNodeID"`, `"C_BaseEntity::m_iHealth"`
* `offset` — field offset from the base of that class.

If no schema data can be read, returns an **empty table**.

***

#### 🧪 Example – Interface Lookup + Schema Dump (Lua)

```lua
local function dump_schema(proc)
    local entries = proc:cs2_get_schema_dump()
    if not entries or #entries == 0 then
        log("[LUA] schema dump empty")
        return
    end

    log("[LUA] Dumping " .. #entries .. " schema fields...")

    for i = 1, #entries do
        local e = entries[i]
        if e then
            -- format: CPulse_CallInfo::m_nEditorNodeID @ 0x00000010
            log(string.format(
                "%s @ 0x%08X",
                e.name,
                e.offset
            ))
        end
    end

    log("[LUA] Schema dump complete.")
end

function main()
    -- Uni API build:
    local cs2 = ref_process("cs2.exe")

    -- On the CS2 Product build, just use:
    --   local cs2 = ref_process()

    if not cs2 or not cs2:alive() then
        log("[LUA] cs2.exe not found")
        return 0
    end

    local tierBase, tierSize = cs2:get_module("tier0.dll")
    if not tierBase then
        log("[LUA] tier0.dll not found")
        return 0
    end

    local iface = cs2:cs2_get_interface(tierBase, "VEngineCvar007")
    if iface == 0 then
        log("[LUA] interface not found!")
        return 0
    end

    log(string.format(
        "VEngineCvar007 interface at 0x%016X",
        iface
    ))

    dump_schema(cs2)
    return 1
end
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/cs2-extended-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
