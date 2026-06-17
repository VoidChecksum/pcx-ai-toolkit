> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/cs2-extended-api.md).

# CS2 Extended API

This API is available in both the Uni API and the CS2 product.

This API is strictly allowed to be used for local and educational purposes only, any online-multiplayer usage will result in termination from the platform. Any violation of our [TOS](https://perception.cx/help/terms/) will result in termination from the platform.

In the CS2 product, all standard Proc API functions are supported **except**:

* Process referencing by PID/name
* Engine-specific helpers
* Virtual memory allocation (`alloc_vm` / `free_vm`)

On CS2 Product, `ref_process()` always returns the **CS2 process only**, so it is used like:

```cpp
proc_t cs2 = ref_process();  // for CS2 Product only
```

There is **no memory allocation API** exposed in the CS2 product.

***

### 🔗 `uint64 proc_t::cs2_get_interface(uint64 module_base, const string &in name) const`

Resolves a **CreateInterface-style** interface exported by a CS2 module.

```cpp
uint64 proc_t::cs2_get_interface(
    uint64 module_base,
    const string &in name
) const
```

#### **Parameters**

* **`module_base`**\
  Base address of the module containing `CreateInterface`\
  (e.g. `"tier0.dll"`).
* **`name`**\
  Interface name, e.g.\
  `"VEngineCvar007"`.

#### **Returns**

* An **absolute pointer** to the resolved interface.
* `0` if the interface wasn’t found.

***

### 🧬 `array<dictionary@>@ proc_t::cs2_get_schema_dump() const`

Dumps every field exposed by the **Source 2 Schema System** for `client.dll`.

```cpp
array<dictionary@>@ proc_t::cs2_get_schema_dump() const
```

#### **Return Format**

Returns an array of dictionaries.\
Each element has:

| Key        | Type   | Description                             |
| ---------- | ------ | --------------------------------------- |
| `"name"`   | string | `"ClassName::fieldName"` (UTF-8)        |
| `"offset"` | int64  | Field offset relative to the class base |

#### **Example element**

```json
{
  "name": "C_BaseEntity::m_iHealth",
  "offset": 16
}
```

***

### 🧪 Full Example — Interface Lookup + Schema Dump

<pre class="language-cpp"><code class="lang-cpp">void dump_schema(proc_t cs2)
{
    array&#x3C;dictionary@>@ entries = cs2.cs2_get_schema_dump();
    if (entries is null || entries.length() == 0)
    {
        log("[AS] schema dump empty");
        return;
    }
    
    log("[AS] Dumping " + entries.length() + " schema fields...");
    
    for (uint i = 0; i &#x3C; entries.length(); i++)
    {
        dictionary@ d = entries[i];
        if (d is null)
            continue;
        
        string name;
        int64  offset;
        
        d.get("name",   name);
        d.get("offset", offset);
        
        log(name + " @ 0x" + formatUInt(uint(offset), "0H", 8));
    }
    
    log("[AS] Schema dump complete.");
    
    // Format example:
    // CPulse_CallInfo::m_nEditorNodeID @ 0x00000010
}

int main()
{
    proc_t cs2 = ref_process("cs2.exe");
<strong>    // If you're using the CS2 Product edition, call ref_process() with no arguments.
</strong>    if (!cs2.alive())
    {
        log("[AS] cs2.exe not found");
        return 0;
    }
    
    uint64 tierBase, tierSize;
    if (!cs2.get_module("tier0.dll", tierBase, tierSize))
    {
        log("[AS] tier0.dll not found");
        return 0;
    }
    
    uint64 iface = cs2.cs2_get_interface(tierBase, "VEngineCvar007");
    
    if (iface == 0)
    {
        log("[AS] interface not found!");
        return 0;
    }
    
    log("VEngineCvar007 interface at 0x" + formatUInt(iface, "0H", 16));
        
    dump_schema(cs2);
    return 1;
}
</code></pre>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/cs2-extended-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
