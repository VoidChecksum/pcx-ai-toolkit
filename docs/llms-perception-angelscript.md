# AngelScript Context Pack

> Single-file context pack for AI tools writing AngelScript scripts on Perception.cx. Bundles the AngelScript API surface, the discipline skill, and cross-references to the underlying 12 guidelines.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 55**

---

## Source: `docs/perception/angelscript/atomic-types.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/atomic-types.md).

# Atomic Types

This page documents the **atomic integer** types exposed to AngelScript. Use these for **thread-safe counters, flags, and shared state** across callbacks/threads without needing a mutex for simple operations.

### Overview

Two value types are available:

* `atomic_int32` — 32-bit signed atomic integer
* `atomic_int64` — 64-bit signed atomic integer

These types provide common atomic operations such as load/store, exchange, compare-and-swap, arithmetic, and bitwise ops.

***

### `atomic_int32`

#### Constructors

| Signature                                    | Description                                 |
| -------------------------------------------- | ------------------------------------------- |
| `atomic_int32()`                             | Creates an atomic value initialized to `0`. |
| `atomic_int32(int32 v)`                      | Creates an atomic value initialized to `v`. |
| `atomic_int32(const atomic_int32 &in other)` | Copy-constructs from another atomic.        |

#### Assignment

| Signature                                              | Returns         | Description                            |
| ------------------------------------------------------ | --------------- | -------------------------------------- |
| `atomic_int32 &opAssign(const atomic_int32 &in other)` | `atomic_int32&` | Assigns the value from another atomic. |

#### Methods

| Method                                                 | Returns | Description                                                                                          |
| ------------------------------------------------------ | ------- | ---------------------------------------------------------------------------------------------------- |
| `int32 load() const`                                   | `int32` | Atomically reads the current value.                                                                  |
| `void store(int32 v)`                                  | `void`  | Atomically stores `v`.                                                                               |
| `int32 exchange(int32 v)`                              | `int32` | Atomically sets to `v` and returns the previous value.                                               |
| `bool compare_exchange(int32 expected, int32 desired)` | `bool`  | Atomically sets to `desired` **only if** current value equals `expected`. Returns `true` on success. |
| `int32 add(int32 v)`                                   | `int32` | Atomically adds `v`. Returns the **previous** value.                                                 |
| `int32 sub(int32 v)`                                   | `int32` | Atomically subtracts `v`. Returns the **previous** value.                                            |
| `int32 and_op(int32 v)`                                | `int32` | Atomically ANDs with `v`. Returns the **previous** value.                                            |
| `int32 or_op(int32 v)`                                 | `int32` | Atomically ORs with `v`. Returns the **previous** value.                                             |
| `int32 xor_op(int32 v)`                                | `int32` | Atomically XORs with `v`. Returns the **previous** value.                                            |
| `int32 increment()`                                    | `int32` | Atomically increments by 1. Returns the **new** value.                                               |
| `int32 decrement()`                                    | `int32` | Atomically decrements by 1. Returns the **new** value.                                               |

***

### `atomic_int64`

#### Constructors

| Signature                                    | Description                                 |
| -------------------------------------------- | ------------------------------------------- |
| `atomic_int64()`                             | Creates an atomic value initialized to `0`. |
| `atomic_int64(int64 v)`                      | Creates an atomic value initialized to `v`. |
| `atomic_int64(const atomic_int64 &in other)` | Copy-constructs from another atomic.        |

#### Assignment

| Signature                                              | Returns         | Description                            |
| ------------------------------------------------------ | --------------- | -------------------------------------- |
| `atomic_int64 &opAssign(const atomic_int64 &in other)` | `atomic_int64&` | Assigns the value from another atomic. |

#### Methods

| Method                                                 | Returns | Description                                                                                          |
| ------------------------------------------------------ | ------- | ---------------------------------------------------------------------------------------------------- |
| `int64 load() const`                                   | `int64` | Atomically reads the current value.                                                                  |
| `void store(int64 v)`                                  | `void`  | Atomically stores `v`.                                                                               |
| `int64 exchange(int64 v)`                              | `int64` | Atomically sets to `v` and returns the previous value.                                               |
| `bool compare_exchange(int64 expected, int64 desired)` | `bool`  | Atomically sets to `desired` **only if** current value equals `expected`. Returns `true` on success. |
| `int64 add(int64 v)`                                   | `int64` | Atomically adds `v`. Returns the **previous** value.                                                 |
| `int64 sub(int64 v)`                                   | `int64` | Atomically subtracts `v`. Returns the **previous** value.                                            |
| `int64 and_op(int64 v)`                                | `int64` | Atomically ANDs with `v`. Returns the **previous** value.                                            |
| `int64 or_op(int64 v)`                                 | `int64` | Atomically ORs with `v`. Returns the **previous** value.                                             |
| `int64 xor_op(int64 v)`                                | `int64` | Atomically XORs with `v`. Returns the **previous** value.                                            |
| `int64 increment()`                                    | `int64` | Atomically increments by 1. Returns the **new** value.                                               |
| `int64 decrement()`                                    | `int64` | Atomically decrements by 1. Returns the **new** value.                                               |

***

### Return Value Notes (Important)

Some methods return the **old value**, while others return the **new value**:

* Returns **previous value**: `exchange`, `add`, `sub`, `and_op`, `or_op`, `xor_op`
* Returns **new value**: `increment`, `decrement`
* Returns **bool**: `compare_exchange` (success/failure)

***

### Example Usage (Test Script)

```cpp
atomic_int32 g_counter32;
atomic_int64 g_counter64;

void test_atomic_32()
{
    log("=== Testing atomic_int32 ===");
    
    atomic_int32 val;
    val.store(42);
    log("store/load: " + val.load());
    
    int32 old = val.exchange(100);
    log("exchange: old=" + old + ", new=" + val.load());
    
    bool cas = val.compare_exchange(100, 200);
    log("CAS (100->200): " + cas + ", val=" + val.load());
    
    val.store(10);
    log("add: prev=" + val.add(5) + ", now=" + val.load());
    log("sub: prev=" + val.sub(3) + ", now=" + val.load());
    log("increment: " + val.increment());
    log("decrement: " + val.decrement());
    
    val.store(0xFF);
    log("and_op: " + val.and_op(0x0F) + ", now=" + val.load());
    log("or_op: " + val.or_op(0xF0) + ", now=" + val.load());
    log("xor_op: " + val.xor_op(0xAA) + ", now=" + val.load());
}

void test_atomic_64()
{
    log("=== Testing atomic_int64 ===");
    
    atomic_int64 val;
    val.store(1234567890123);
    log("store/load: " + val.load());
    
    int64 old = val.exchange(9876543210);
    log("exchange: old=" + old + ", new=" + val.load());
}

void test_spinlock()
{
    log("=== Spinlock Pattern ===");
    
    atomic_int32 lock;
    
    while (!lock.compare_exchange(0, 1)) { }
    log("Lock acquired");
    
    g_counter32.increment();
    log("Counter: " + g_counter32.load());
    
    lock.store(0);
    log("Lock released");
}

int main()
{
    log("=== Atomic API Test ===");
    test_atomic_32();
    test_atomic_64();
    test_spinlock();
    
    return 0;
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/atomic-types.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/bit-reinterpret-helpers.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/bit-reinterpret-helpers.md).

# Bit Reinterpret Helpers

The **Bit Reinterpret Helpers** allow scripts to inspect the raw bit-pattern of numeric values by converting them into a `uint32`.

These functions **do not convert or scale values** — they reinterpret the raw memory bits of the input

***

#### `uint32 f_to_u32(float f)`

Returns the raw 32-bit IEEE-754 representation of a float.

```cpp
uint32 bits = f_to_u32(1.0f);     // 0x3F800000
```

***

#### `uint32 u8_to_u32(uint8 v)`

Reinterprets a `uint8` as a `uint32`.

```cpp
uint32 bits = u8_to_u32(255);     // 0x000000FF
```

***

#### `uint32 u16_to_u32(uint16 v)`

Reinterprets the lower 16 bits of a `uint16` as a 32-bit integer.

```cpp
uint32 bits = u16_to_u32(50000);
```

***

#### `uint32 u64_to_u32(uint64 v)`

Returns the **lower 32 bits** of a 64-bit unsigned integer.

```cpp
uint32 bits = u64_to_u32(0x1122334455667788);
```

***

#### `uint32 i8_to_u32(int8 v)`

Reinterprets a signed 8-bit integer as a 32-bit unsigned integer.

```cpp
uint32 bits = i8_to_u32(-5);      // 0xFFFFFFFB
```

***

#### `uint32 i16_to_u32(int16 v)`

Reinterprets a signed 16-bit integer as 32 bits.

```cpp
uint32 bits = i16_to_u32(-1234);
```

***

#### `uint32 i32_to_u32(int32 v)`

Reinterprets a signed 32-bit integer as an unsigned one **without numerical conversion**.

```cpp
uint32 bits = i32_to_u32(-1);     // 0xFFFFFFFF
```

***

#### `uint32 i64_to_u32(int64 v)`

Returns the lower 32 bits of a 64-bit signed integer.

```cpp
uint32 bits = i64_to_u32(-1);     // 0xFFFFFFFF
```

***

#### `uint32 d_to_u32(double v)`

Returns the first 4 bytes of a 64-bit double (the lower half of the binary representation).

```cpp
uint32 bits = d_to_u32(3.1415926535);
```

***

#### **`float bits_to_float(uint raw)`**

Reinterprets a 32-bit unsigned integer as an IEEE-754 `float`.

```cpp
float f = bits_to_float(0x3F800000);    // 1.0f
```

***

#### **`double bits_to_double(uint64 raw)`**

Reinterprets a 64-bit unsigned integer as an IEEE-754 `double`.

```cpp
double d = bits_to_double(0x400921FB54442D18);   // 3.141592653589793
```

***

#### **`uint float_to_bits(float value)`**

Returns the exact 32-bit IEEE-754 bit pattern of a `float`.

```cpp
uint bits = float_to_bits(1.0f);        // 0x3F800000
```

***

#### **`uint64 double_to_bits(double value)`**

Returns the exact 64-bit IEEE-754 bit pattern of a `double`.

```cpp
uint64 bits = double_to_bits(3.141592653589793); // 0x400921FB54442D18
```

***

#### **`float u32_to_f(uint raw)`**

Convenience alias for `bits_to_float(raw)`.

```cpp
float f = u32_to_f(0xBF800000);         // -1.0f
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/bit-reinterpret-helpers.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/cs2-extended-api.md`

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

---

## Source: `docs/perception/angelscript/custom-draw-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/custom-draw-api.md).

# Custom Draw API

The Custom Draw API gives scripts direct access to the **D3D11 GPU pipeline** — custom HLSL vertex, pixel, and compute shaders, vertex/index/constant/structured buffers, textures, render targets, depth buffers, and all primitive topologies.

Custom draw commands respect draw order with all other render functions. If you call `draw_rect_filled`, then `custom_draw`, then `draw_text`, they render in exactly that order.

All handles are `uint64` **encrypted handles** — pass them back into other calls, never dereference them. Every resource is automatically destroyed when the script unloads.

***

**📐 Constants**

**Topology**

```cpp
const int TOPO_TRIANGLE_LIST    // Default. 3 vertices per triangle.
const int TOPO_TRIANGLE_STRIP   // Shared edges. N vertices = N-2 triangles.
const int TOPO_LINE_LIST        // 2 vertices per line segment.
const int TOPO_LINE_STRIP       // Connected line segments.
const int TOPO_POINT_LIST       // Individual points.
```

**Depth Comparison**

```cpp
const int CMP_NEVER
const int CMP_LESS           // Standard 3D depth testing
const int CMP_EQUAL
const int CMP_LESS_EQUAL
const int CMP_GREATER
const int CMP_NOT_EQUAL
const int CMP_GREATER_EQUAL
const int CMP_ALWAYS         // Disable depth test (still writes if depth_write=true)
```

**Cull / Fill Modes**

```cpp
const int CULL_NONE          // Render both sides
const int CULL_FRONT
const int CULL_BACK          // Default — cull back-facing triangles

const int FILL_SOLID         // Default
const int FILL_WIREFRAME
```

**Blend Factors / Operations**

```cpp
const int BLEND_ZERO
const int BLEND_ONE
const int BLEND_SRC_ALPHA
const int BLEND_INV_SRC_ALPHA
const int BLEND_DEST_ALPHA
const int BLEND_INV_DEST_ALPHA
const int BLEND_SRC_COLOR
const int BLEND_INV_SRC_COLOR
const int BLEND_DEST_COLOR
const int BLEND_INV_DEST_COLOR

const int BLEND_OP_ADD
const int BLEND_OP_SUBTRACT
const int BLEND_OP_REV_SUBTRACT
const int BLEND_OP_MIN
const int BLEND_OP_MAX
```

**Texture Filter / Address Modes**

```cpp
const int FILTER_POINT
const int FILTER_LINEAR
const int FILTER_ANISOTROPIC

const int ADDRESS_WRAP
const int ADDRESS_CLAMP
const int ADDRESS_MIRROR
const int ADDRESS_BORDER
```

**Vertex Layout Element Types**

```cpp
const int ELEM_FLOAT1       // 4 bytes
const int ELEM_FLOAT2       // 8 bytes
const int ELEM_FLOAT3       // 12 bytes
const int ELEM_FLOAT4       // 16 bytes
const int ELEM_BYTE4_UNORM  // 4 bytes (normalized 0-1)
const int ELEM_UINT1        // 4 bytes
```

**Bind Stage**

```cpp
const int STAGE_VS   // Vertex shader (0)
const int STAGE_PS   // Pixel shader (1)
const int STAGE_CS   // Compute shader (2)
```

***

**🧵 Layout String Format**

`create_shader` takes the vertex input layout as a comma-separated string of `SEMANTIC:semantic_index:TYPE` entries:

```
"POSITION:0:FLOAT2, COLOR:0:FLOAT4"
"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2"
"POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2"
```

Supported types: `FLOAT1` (4B), `FLOAT2` (8B), `FLOAT3` (12B), `FLOAT4` (16B), `BYTE4` (4B unorm), `UINT1` (4B). The sum of element sizes is the vertex **stride** — it must match the `stride` passed to `create_vertex_buffer` and the bytes you pack into `vertex_data`.

***

**🧩 Shaders**

```cpp
uint64 create_shader(const string &in vs_source, const string &in ps_source,
                     const string &in layout)
void   destroy_shader(uint64 shader)
```

Compiles `vs_5_0` + `ps_5_0` from HLSL source strings. Both entry points must be `main`. Returns `0` on compilation failure — always check before use.

***

**🎮 Resource Creation**

All creation functions return a `uint64` handle, or `0` on failure.

```cpp
uint64 create_vertex_buffer(uint stride, uint max_vertices, bool dynamic)
uint64 create_index_buffer(uint max_indices, bool use_32bit, bool dynamic)
uint64 create_constant_buffer(uint size)
uint64 create_blend_state(int src, int dst, int op, int src_alpha, int dst_alpha, int op_alpha)
uint64 create_sampler(int filter, int address_u, int address_v)
uint64 create_texture(uint width, uint height, const array<uint8> &in rgba_data)
uint64 create_render_target(uint width, uint height)
uint64 create_depth_buffer(uint width, uint height)
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func)
uint64 create_rasterizer_state(int cull_mode, int fill_mode, bool scissor_enable)
```

* `create_vertex_buffer` — `stride` is bytes per vertex (must match the shader layout). `dynamic` = `true` for per-frame updates (typical), `false` for static geometry.
* `create_index_buffer` — `use_32bit` = `true` for 32-bit (`uint`) indices, `false` for 16-bit (`uint16`). Use 32-bit past 65535 vertices.
* `create_constant_buffer` — `size` is auto-aligned to 16 bytes.
* `create_blend_state` — Standard alpha: `(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD, BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD)`. Premultiplied (recommended for overlays): `(BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD, BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD)`.
* `create_sampler` — `FILTER_LINEAR` for smooth scaling, `FILTER_POINT` for pixel-perfect.
* `create_texture` — `rgba_data` must be exactly `width * height * 4` bytes.
* `create_render_target` — Offscreen color target. Pass `0, 0` to match the viewport size.
* `create_depth_buffer` — D24S8 depth/stencil buffer. Pass `0, 0` to match the viewport size.
* `create_depth_stencil_state` — For solid 3D use `create_depth_stencil_state(true, true, CMP_LESS)`.
* `create_rasterizer_state` — `scissor_enable` should usually be `true` so clipping works.

***

**🔺 Drawing**

```cpp
void custom_draw(uint64 shader, uint64 vb,
                 const array<uint8> &in vertex_data, uint vertex_count,
                 int topology,
                 uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
                 uint64 cb, const array<uint8> @cb_data, int cb_slot)

void custom_draw_indexed(uint64 shader, uint64 vb,
    const array<uint8> &in vertex_data, uint vertex_count,
    uint64 ib, const array<uint8> &in index_data, uint index_count,
    int topology,
    uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
    uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

* `shader`, `vb` — Required handles.
* `vertex_data` — Raw vertex bytes packed into `array<uint8>`, matching the shader's layout stride.
* `vertex_count` — Number of vertices to draw.
* `ib` / `index_data` / `index_count` (indexed only) — Index buffer handle, 16- or 32-bit index bytes, and count.
* `topology` — One of the `TOPO_*` constants.
* `blend` / `sampler` / `texture` / `cb` — Optional; pass `0` to skip binding.
* `tex_slot` — Texture/sampler register slot (usually `0`).
* `cb_data` — Raw constant data as `array<uint8>`, or `null` if no constants.
* `cb_slot` — Constant buffer register slot (usually `0`).

`custom_draw_indexed` reuses shared vertices through the index buffer — use it for cubes, grids, and any geometry with shared edges.

> Custom draw commands respect draw order with all other render functions.

**Packing Vertex Data**

`custom_draw` takes raw bytes, so floats must be packed into `array<uint8>`. Use `fpToIEEE`:

```cpp
void pack_float(array<uint8> &b, int offset, float val)
{
    uint bits = fpToIEEE(val);
    b[offset]     = uint8(bits & 0xFF);
    b[offset + 1] = uint8((bits >> 8) & 0xFF);
    b[offset + 2] = uint8((bits >> 16) & 0xFF);
    b[offset + 3] = uint8((bits >> 24) & 0xFF);
}
```

***

**🖼️ Render Target Operations**

```cpp
void custom_set_render_target(uint64 rt)
void custom_set_render_target_ext(uint64 rt, uint64 depth_buffer)
void custom_reset_render_target()
void custom_bind_rt_as_texture(uint64 rt, int slot)
void custom_clear_render_target(uint64 rt, float r, float g, float b, float a)
void custom_clear_depth_buffer(uint64 db)
void custom_restore_state()
```

* `custom_set_render_target` — Redirects subsequent `custom_draw` calls to an offscreen render target.
* `custom_set_render_target_ext` — Binds an RT with a depth buffer for proper 3D occlusion. Auto-clears both and sets viewport/scissor to RT dimensions. Pass `0` for the depth buffer for color-only.
* `custom_reset_render_target` — Switches back to the main backbuffer.
* `custom_bind_rt_as_texture` — Binds an RT's contents as a sampleable texture at `slot` — used to blit an offscreen pass to the screen.
* `custom_clear_render_target` — Clears an RT to a color without re-binding it.
* `custom_clear_depth_buffer` — Clears depth to 1.0 and stencil to 0.
* `custom_restore_state` — Resets the D3D11 pipeline state. **Call after any custom-pipeline sequence** before returning control to the 2D layer.

***

**🧊 State Management**

```cpp
void custom_set_depth_stencil_state(uint64 ds)
void custom_set_rasterizer_state(uint64 rs)
void custom_set_viewport(float x, float y, float w, float h)
void custom_reset_viewport()
void custom_bind_texture(uint64 texture, uint64 sampler, int slot)
void custom_bind_constant_buffer(uint64 cb, const array<uint8> &in data, int slot, int stage)
```

* `custom_set_depth_stencil_state` — Applies a depth-stencil state; pass `0` to reset to default (no depth testing).
* `custom_set_rasterizer_state` — Applies a rasterizer state; pass `0` to reset to default.
* `custom_set_viewport` — Restricts rendering to a sub-region — split-screen, picture-in-picture, or a 3D panel.
* `custom_reset_viewport` — Restores the full viewport.
* `custom_bind_texture` — Binds a texture + sampler to `slot`, persisting across draws. Pass `0` for the texture to bind the latest backbuffer capture.
* `custom_bind_constant_buffer` — Binds a constant buffer to a `slot` and `stage` independently of draw calls, persisting until changed. Enables multi-buffer setups (camera on `b0`, material on `b1`, lighting on `b2`). When binding the MVP this way, pass `0` for the draw call's `cb` so it doesn't overwrite your manual bindings.

***

**🏔️ Mesh & Texture Loading**

```cpp
uint64 create_mesh_raw(const array<uint8> &in vertex_data, uint vertex_count, uint stride,
                       const array<uint8> &in index_data, uint index_count, bool use_32bit)
uint64 load_mesh(const string &in path)
uint64 load_mesh_mem(const array<uint8> &in data)
void   get_mesh_info(uint64 mesh, float &out vert_count, float &out index_count,
                     float &out min_x, float &out min_y, float &out min_z,
                     float &out max_x, float &out max_y, float &out max_z)
float  get_mesh_stride(uint64 mesh)
void   destroy_mesh(uint64 mesh)

uint64 create_texture_from_file(const string &in path)   // alias of load_texture
uint64 load_texture(const string &in path)
uint64 load_texture_mem(const array<uint8> &in data)
uint64 create_dynamic_texture(uint width, uint height)
void   custom_update_texture(uint64 tex, uint x, uint y, uint w, uint h,
                             const array<uint8> &in rgba_data)
void   get_texture_info(uint64 tex, float &out w, float &out h)

void draw_mesh(uint64 mesh, uint64 shader, int topology,
               uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
               uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

* `create_mesh_raw` — Builds a mesh from raw vertex + index byte arrays with any layout. The shader must match the stride. Use for procedural terrain, generated geometry, or particle quads.
* `load_mesh` / `load_mesh_mem` — Parses Wavefront OBJ (`v`, `vn`, `vt`, 3+ vertex faces auto-triangulated, negative indices). Fixed layout `POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2` — 32 bytes/vertex; shaders must match. `load_mesh` tries the script directory first.
* `get_mesh_info` — Vertex/index counts and the axis-aligned bounding box. `get_mesh_stride` returns the vertex stride in bytes.
* `load_texture` / `load_texture_mem` — Decodes PNG, JPG, BMP, TGA, or GIF. `load_texture` tries the script directory first, then the absolute path. `create_texture_from_file` is an alias of `load_texture`.
* `create_dynamic_texture` — Allocates an updatable texture; feed it per-frame with `custom_update_texture`.
* `custom_update_texture` — Partial update; `rgba_data` must be exactly `w * h * 4` bytes. Use for sprite sheets, minimaps, or procedural atlases.
* `draw_mesh` — Convenience draw: binds the mesh's internal buffers and issues `DrawIndexed` in one call. Pass `0` for optional handles. The shader layout must match the mesh's vertex format.

***

**💻 Compute Shaders & Structured Buffers**

```cpp
uint64 create_compute_shader(const string &in cs_source)
void   destroy_compute_shader(uint64 cs)
void   dispatch_compute(uint64 cs, uint x, uint y, uint z)

uint64 create_structured_buffer(uint element_size, uint element_count, bool cpu_write, bool gpu_write)
void   destroy_structured_buffer(uint64 sb)
void   update_structured_buffer(uint64 sb, const array<uint8> &in data)
void   bind_structured_buffer(uint64 sb, int slot, int stage)
array<uint8> read_structured_buffer(uint64 sb)
```

* `create_compute_shader` — Compiles a `cs_5_0` shader. Entry point must be `main`.
* `dispatch_compute` — Dispatches with thread group counts `(x, y, z)`. A state-only command — no geometry is drawn.
* `create_structured_buffer` — `element_size` is bytes per element (16 for `float4`). `cpu_write` creates an SRV updatable from script; `gpu_write` creates a UAV writable from compute shaders. A buffer can be both.
* `update_structured_buffer` — Uploads new element bytes from script (requires `cpu_write`).
* `bind_structured_buffer` — Binds to a `slot` on `stage`. The `STAGE_CS` stage with `gpu_write` binds as a UAV; otherwise as an SRV.
* `read_structured_buffer` — Reads element bytes back to script (GPU → CPU).

**Example: GPU particle buffer**

```cpp
// 16 bytes per particle (float4), 1024 particles, GPU-writable
uint64 sb = create_structured_buffer(16, 1024, false, true);

bind_structured_buffer(sb, 0, STAGE_CS);   // bind as UAV for writing
dispatch_compute(cs, 16, 1, 1);            // 16 groups × 64 threads = 1024 particles

bind_structured_buffer(sb, 0, STAGE_PS);   // bind as SRV for reading in the pixel shader
```

***

**📷 Backbuffer Capture**

```cpp
void capture_backbuffer(int slot)
```

Captures the current backbuffer to a staging texture and binds it as a shader resource at `slot`. Combine with a custom pixel shader for post-processing — bloom, blur, color grading, screen-space reflections:

```cpp
capture_backbuffer(0);
custom_bind_texture(0, sampler, 0);  // texture=0 uses the captured backbuffer
custom_draw(post_fx_shader, vb, fullscreen_quad, 6, TOPO_TRIANGLE_LIST,
            blend, sampler, 0, 0, cb, fx_cb, 0);
```

***

**🟢 Example: Basic Colored Triangle**

```cpp
uint64 g_shader = 0;
uint64 g_vb = 0;
uint64 g_blend = 0;

void pack_float(array<uint8> &b, int o, float v)
{
    uint bits = fpToIEEE(v);
    b[o] = uint8(bits & 0xFF); b[o+1] = uint8((bits >> 8) & 0xFF);
    b[o+2] = uint8((bits >> 16) & 0xFF); b[o+3] = uint8((bits >> 24) & 0xFF);
}

int main()
{
    string vs =
        "struct vi { float2 pos : POSITION; float4 col : COLOR; };\n"
        "struct vo { float4 pos : SV_Position; float4 col : COLOR; };\n"
        "vo main(vi i) { vo o; o.pos = float4(i.pos, 0.0, 1.0); o.col = i.col; return o; }\n";
    string ps =
        "struct vo { float4 pos : SV_Position; float4 col : COLOR; };\n"
        "float4 main(vo i) : SV_Target { return i.col; }\n";

    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb     = create_vertex_buffer(24, 3, true);  // 8 + 16 = 24 bytes/vertex
    g_blend  = create_blend_state(BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                   BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
    if (g_shader == 0 || g_vb == 0) { log_error("triangle setup failed"); return -1; }

    register_callback(@on_frame, 1, 0);
    return 1;
}

void on_frame(int cb_id, int data)
{
    array<uint8> v(3 * 24);
    // pos.xy, col.rgba per vertex
    pack_float(v, 0,  -0.5f); pack_float(v, 4,  -0.5f);
    pack_float(v, 8,   1.0f); pack_float(v, 12,  0.0f); pack_float(v, 16, 0.0f); pack_float(v, 20, 1.0f);
    pack_float(v, 24,  0.5f); pack_float(v, 28, -0.5f);
    pack_float(v, 32,  0.0f); pack_float(v, 36,  1.0f); pack_float(v, 40, 0.0f); pack_float(v, 44, 1.0f);
    pack_float(v, 48,  0.0f); pack_float(v, 52,  0.5f);
    pack_float(v, 56,  0.0f); pack_float(v, 60,  0.0f); pack_float(v, 64, 1.0f); pack_float(v, 68, 1.0f);

    custom_draw(g_shader, g_vb, v, 3, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, 0, null, 0);
    custom_restore_state();
}
```

***

**🧊 Example: Depth-Tested 3D Scene**

```cpp
uint64 rt = create_render_target(400, 300);
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);
uint64 rs = create_rasterizer_state(CULL_NONE, FILL_SOLID, true);

// Render pass
custom_set_render_target_ext(rt, db);
custom_clear_render_target(rt, 0, 0, 0, 1);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs);
draw_mesh(mesh1, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb, mvp1_data, 0);
draw_mesh(mesh2, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb, mvp2_data, 0);
custom_reset_render_target();
custom_set_rasterizer_state(0);
custom_set_depth_stencil_state(0);

// Blit result to screen
custom_bind_rt_as_texture(rt, 0);
custom_draw(blit_shader, vb, quad, 6, TOPO_TRIANGLE_LIST, blend, sampler, 0, 0, cb, screen_cb, 0);
custom_restore_state();
```

***

**💻 Example: Compute Shader**

```cpp
string cs =
    "RWStructuredBuffer<float4> particles : register(u0);\n"
    "[numthreads(64, 1, 1)]\n"
    "void main(uint3 id : SV_DispatchThreadID) {\n"
    "    particles[id.x].xy += particles[id.x].zw;  // advance by velocity\n"
    "}\n";

uint64 compute = create_compute_shader(cs);
uint64 sb = create_structured_buffer(16, 1024, false, true);  // float4 x 1024, GPU-writable

bind_structured_buffer(sb, 0, STAGE_CS);
dispatch_compute(compute, 16, 1, 1);        // 16 groups × 64 threads = 1024 particles

bind_structured_buffer(sb, 0, STAGE_PS);    // read positions in the pixel shader
```

***

**🌀 Example: Post-Processing (full-screen blur of the current frame)**

```cpp
void on_frame(int cb_id, int data)
{
    capture_backbuffer(0);                  // current frame -> texture slot 0
    custom_bind_texture(0, g_sampler, 0);
    custom_draw(g_blur_shader, g_vb, g_fullscreen_quad, 6, TOPO_TRIANGLE_LIST,
                g_blend, g_sampler, 0, 0, g_cb, g_fx_cb, 0);
    custom_restore_state();
}
```

***

**🧹 Resource Cleanup**

All custom draw resources are automatically destroyed when a script is unloaded. Manual destruction is optional and only needed to free a resource mid-script:

```cpp
destroy_shader(shader);
destroy_compute_shader(cs);
destroy_vertex_buffer(vb);
destroy_index_buffer(ib);
destroy_constant_buffer(cb);
destroy_structured_buffer(sb);
destroy_blend_state(blend);
destroy_sampler(sampler);
destroy_texture(tex);
destroy_render_target(rt);
destroy_depth_buffer(db);
destroy_depth_stencil_state(ds);
destroy_rasterizer_state(rs);
destroy_mesh(mesh);
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/custom-draw-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/engine-specific-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/engine-specific-api.md).

# Engine Specific API

### Unreal Engine Helpers

The following helpers are designed for Unreal Engine–based games (UE4 & UE5), including both float-precision and double-precision view structures.

***

#### `bool unreal_read_tarray(proc_t &in proc, uint64 tarray_addr, array<uint64> &out result, uint max_count = 4096)`

Reads an Unreal `TArray` from memory and fills a script array with the pointer values inside it.

**Parameters**

* **proc** — target process handle
* **tarray\_addr** — memory address of the `TArray`
* **result** — output array that will receive the entries
* **max\_count** — safety limit for max number of elements (default 4096)

**Returns**

`true` on success, `false` on invalid address, invalid process, or corrupted data.

On failure, `result` will be empty.

**Example**

```cpp
array<uint64> actors;
if (unreal_read_tarray(proc, actors_addr, actors))
{
    for (uint i = 0; i < actors.length(); i++)
        log("Actor pointer: " + actors[i]);
}
```

***

#### `bool unreal_read_minimal_view_info(proc_t &in proc, uint64 pov_addr, vector3 &out location, vector3 &out rotation, double &out fov)`

Reads a **float-precision** Unreal camera view.

**Parameters**

* **proc** — process handle
* **pov\_addr** — address of camera/view structure
* **location** — output camera world position
* **rotation** — output camera rotation (pitch, yaw, roll)
* **fov** — output field-of-view

**Returns**

`true` on success, `false` on invalid input.

***

#### `bool unreal_read_minimal_view_info_f64(proc_t &in proc, uint64 pov_addr, vector3 &out location, vector3 &out rotation, double &out fov)`

Same as above but for **double-precision** UE5 view structures.

Use this if the game uses large-world coordinates or 64-bit FOV/rotation data.

***

#### `bool unreal_world_to_screen(const vector3 &in world_pos, const vector3 &in cam_location, const vector3 &in cam_rotation, double fov_deg, vector2 &out screen_pos)`

Projects a 3D world point into 2D screen coordinates using a UE-style camera.

**Parameters**

* **world\_pos** — world-space position
* **cam\_location** — camera location
* **cam\_rotation** — camera rotation (pitch, yaw, roll)
* **fov\_deg** — vertical field-of-view in degrees
* **screen\_pos** — output pixel coordinate

**Returns**

* `true` if the point is visible, and `screen_pos` is valid
* `false` if the point is behind the camera

**Example**

```cpp
vector2 screen;
if (unreal_world_to_screen(targetPos, viewLoc, viewRot, viewFov, screen))
{
    draw_text("Target", screen.x, screen.y);
}
```

***

#### World-to-Screen Projection&#xD;

Convert 3D world coordinates to 2D screen positions using view matrices.

```cpp
// Row-major matrix layout (DirectX-style, Source engine, etc.)
bool world_to_screen_rowmajor(
    const vector3 &in world_pos,
    const matrix4x4 &in view_matrix,
    vector2 &out screen_pos,
    const vector2 &in viewport = vector2(0, 0)
);

// Transposed/column-major layout (Unity, OpenGL-style)
bool world_to_screen_transposed(
    const vector3 &in world_pos,
    const matrix4x4 &in view_matrix,
    vector2 &out screen_pos,
    const vector2 &in viewport = vector2(0, 0)
);

//Example
matrix4x4 view_matrix;
view_matrix.readas_float(proc, view_matrix_address);

vector3 enemy_head(100.0, 200.0, 50.0);
vector2 screen;

if (world_to_screen_rowmajor(enemy_head, view_matrix, screen))
{
    draw_circle(screen.x, screen.y, 5, 255, 0, 0, 255, 1, true);
    draw_text("Enemy", screen.x, screen.y - 20, 255, 255, 255, 255, get_font18(), 0, 0, 0, 0, 0, 0);
}
```

***

### Fortnite Helper

#### `string fortnite_get_player_name(proc_t &in proc, uint64 addr)`

Reads and decrypts a Fortnite player name from memory.

**Returns**

* Player name on success
* Empty string `""` on failure

**Example**

```cpp
string name = fortnite_get_player_name(proc, name_addr);
if (name.length() > 0)
    log("Player: " + name);
```

***

### Rust Helper

#### `vector3 rust_get_transform_position(proc_t &in proc, uint64 addr)`

Resolves the world-space position of a Rust (Unity) transform hierarchy.

**Returns**

* A `vector3` world position on success
* `(0,0,0)` on invalid memory or failure

**Example**

```cpp
vector3 pos = rust_get_transform_position(proc, transform_ptr);
if (pos.x != 0 || pos.y != 0 || pos.z != 0)
{
    vector2 s;
    if (unreal_world_to_screen(pos, camLoc, camRot, camFov, s))
        draw_point(s.x, s.y, color_green);
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/engine-specific-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/engine.md`

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

---

## Source: `docs/perception/angelscript/extended-math-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/extended-math-api.md).

# Extended Math API

The Extended Math API supplies:

* Double-precision scalar helpers
* 2D vectors (`vector2`)
* 3D vectors (`vector3`)
* Quaternions (`quaternion`)
* 4×4 matrices (`matrix4x4`)
* Read/write helpers for interacting with raw memory values

All math types support operator overloading and can be used naturally in AngelScript expressions.

***

## **2. Constants**

All constants are `const double` and available globally:

| Name        | Description               |
| ----------- | ------------------------- |
| `M_PI`      | Pi (3.14159…)             |
| `M_TAU`     | Tau (2π)                  |
| `M_PI_2`    | π/2                       |
| `M_PI_4`    | π/4                       |
| `RAD2DEG`   | Convert radians → degrees |
| `DEG2RAD`   | Convert degrees → radians |
| `M_ZERO`    | 0.0                       |
| `M_ONE`     | 1.0                       |
| `M_EPSILON` | Small epsilon (1e-6)      |

***

## **3. Scalar Math Functions**

#### **clamp(x, a, b) → double**

Clamp `x` into range `[a, b]`.

#### **saturate(x) → double**

Clamp `x` into `[0,1]`.

#### **sign(x) → int**

Returns `-1`, `0`, or `1`.

#### **round / round\_up / round\_down**

#### **fract(x)**

Positive fractional part.

#### **wrap(x, min, max)**

Wrap value into interval like modulo.

#### **lerp(a, b, t)**

Linear interpolate.

#### **inverse\_lerp(a, b, v)**

Returns `t` such that `lerp(a,b,t) = v`.

#### **remap(a1, b1, a2, b2, v)**

Map a value between ranges.

#### **smoothstep(edge0, edge1, x)**

Smoothed curve between two edges.

#### **step(edge, x)**

Binary step function.

#### **is\_nan(x)**

Check for NaN.

#### **is\_inf(x)**

Check for infinity.

***

## **4. vector2**

```cpp
struct vector2 {
    double x;
    double y;
}
```

### **Constructors**

```cpp
vector2()                    // (0,0)
vector2(double x, double y)
vector2(const vector2 &in)
```

### **Operators**

```cpp
vector2 opAdd(const vector2 &in) const
vector2 opSub(const vector2 &in) const
vector2 opNeg() const
vector2 opMul(double s) const
vector2 opDiv(double s) const
bool    opEquals(const vector2 &in) const
```

### **Methods**

```cpp
double  length() const
double  distance(const vector2 &in other) const
double  distance_to(const vector2 &in other) const
vector2 lerp(const vector2 &in other, double t) const
vector2 min(const vector2 &in other) const
vector2 max(const vector2 &in other) const
```

### **Memory Helpers**

```cpp
void readas_double(proc_t& in, uint64 addr)
void readas_float(proc_t& in, uint64 addr)
bool writeas_double(proc_t& in, uint64 addr) const
bool writeas_float(proc_t& in, uint64 addr) const
```

***

## **5. vector3**

```cpp
struct vector3 {
    double x, y, z;
}
```

### **Constructors**

```cpp
vector3()
vector3(double x, double y, double z)
vector3(const vector3 &in)
```

### **Operators**

```cpp
vector3 opAdd(const vector3 &in) const
vector3 opSub(const vector3 &in) const
vector3 opNeg() const
vector3 opMul(double s) const
vector3 opDiv(double s) const
bool    opEquals(const vector3 &in) const
```

### **Methods**

```cpp
double length() const
double length2d() const
double distance(const vector3 &in) const
double distance2d(const vector3 &in) const
double distance_to(const vector3 &in) const
double distance2d_to(const vector3 &in) const
vector3 lerp(const vector3 &in, double t) const
vector3 min(const vector3 &in) const
vector3 max(const vector3 &in) const
double  dot_product(const vector3 &in) const
vector3 cross_product(const vector3 &in) const
```

### **Memory Helpers**

```cpp
void readas_double(proc_t& in, uint64 addr)
void readas_float(proc_t& in, uint64 addr)
bool writeas_double(proc_t& in, uint64 addr) const
bool writeas_float(proc_t& in, uint64 addr) const
```

***

## **6. quaternion**

```cpp
struct quaternion {
    double x, y, z, w;
}
```

### **Constructors**

```cpp
quaternion()                              // identity
quaternion(double x, double y, double z, double w)
```

### **Static**

```cpp
quaternion quat_from_euler(double pitch, double yaw, double roll)
```

(Euler angles in degrees.)

### **Operators**

```cpp
quaternion opMul(const quaternion &in) const
quaternion opMul(double s) const
quaternion opDiv(double s) const
quaternion opAdd(const quaternion &in) const
quaternion opSub(const quaternion &in) const
quaternion opNeg() const
bool       opEquals(const quaternion &in) const
```

### **Methods**

```cpp
double     length() const
quaternion normalized() const
double     dot(const quaternion &in) const
quaternion conjugate() const
quaternion inverse() const
void       to_euler(double &out pitch, double &out yaw, double &out roll) const
vector3    rotate(const vector3 &in v) const
```

### **Memory Helpers**

```cpp
void readas_double(proc_t& in, uint64 addr)
void readas_float(proc_t& in, uint64 addr)
bool writeas_double(proc_t& in, uint64 addr) const
bool writeas_float(uproc_t& in, uint64 addr) const
```

***

## **7. matrix4x4**

```cpp
struct matrix4x4 {
    double m[16];   // Internal storage — not meant to be accessed as mat.m
};

// Instead of mat.m, you should access elements using either:
//   mat[index]          — linear index
//   mat[row][col]       — row/column indexing
```

### **Constructor**

```cpp
matrix4x4()     // zero matrix
```

### **Global Functions**

```cpp
matrix4x4 mat4_identity()
matrix4x4 mat4_zero()
matrix4x4 mat4_translate(double tx, double ty, double tz)
matrix4x4 mat4_scale(double sx, double sy, double sz)
matrix4x4 mat4_rotate_euler(double pitch, double yaw, double roll)
matrix4x4 mat4_from_quaternion(const quaternion &in q)
```

### **Operators**

```cpp
matrix4x4 opMul(const matrix4x4 &in) const
```

### **Methods**

```cpp
vector3 transform(const vector3 &in v) const
void    readas_float(proc_t& in, uint64 addr) // Reading precision is float
bool    writeas_float(proc_t& in, uint64 addr) const // Writing precision is float
void    readas_double(proc_t& in, uint64 addr) // Reading precision is double
bool    writeas_double(proc_t& in, uint64 addr) const // Writing precision is double
```

***

## **8. Memory Helpers Summary**

Every math type supports reading/writing data from a 64-bit address:

#### **Read**

* `readas_double(`proc\_t& in`, addr)` – read consecutive doubles
* `readas_float(`proc\_t& in`, addr)` – read consecutive floats

#### **Write**

* `writeas_double(`proc\_t& in`, addr)` – write consecutive doubles
* `writeas_float(`proc\_t& in`, addr)` – write consecutive floats

***

## **9. Random**

```cpp
void random_seed(uint64 seed): set RNG seed 
double random(): random value in [0.0, 1.0)
double random_range(double min, double max): random in [min, max]
int64 random_int(int64 min, int64 max): random integer in [min, max]
bool random_bool(): random true or false
double random_gaussian(double mean, double stddev): normal distribution
vector2 random_unit_vec2(): random unit direction 2D
vector3 random_unit_vec3(): random unit direction on sphere
```

***

## **10. Example Usage**

#### **Vector math**

```cpp
vector2 a(1,2);
vector2 b(4,-1);
vector2 c = a + b;
double d = a.distance(b);
```

#### **3D vector operations**

```cpp
vector3 velocity = direction.normalized() * speed;
```

#### **Quaternion rotation**

```cpp
quaternion q = quat_from_euler(0, 90, 0);
vector3 forward(1,0,0);

vector3 rotated = q.rotate(forward);
```

#### **Matrix transform**

```cpp
matrix4x4 T = mat4_translate(10, 0, 0);
vector3 pos = T.transform(vector3(1,2,3));
```

#### **Reading a position from memory**

```cpp
vector3 pos;
pos.readas_float(proc, address);
```

#### **Writing back**

```cpp
pos.x += 5;
pos.writeas_float(proc, address);
```

## Full API Test

```cpp
void print_vec2(const string &in label, const vector2 &in v)
{
    log(label + " = (" + v.x + ", " + v.y + ")");
}

void print_vec3(const string &in label, const vector3 &in v)
{
    log(label + " = (" + v.x + ", " + v.y + ", " + v.z + ")");
}

void print_quat(const string &in label, const quaternion &in q)
{
    log(label + " = (" + q.x + ", " + q.y + ", " + q.z + ", " + q.w + ")");
}

int main()
{
    log("=== AS Extended Math FULL TEST ===");
    
    // ----------------------------------------------------------------
    // Scalars & constants
    // ----------------------------------------------------------------
    log("M_PI        = " + M_PI);
    log("M_TAU       = " + M_TAU);
    log("RAD2DEG(PI) = " + (M_PI * RAD2DEG));
    log("DEG2RAD(180)= " + (180.0 * DEG2RAD));
    
    log("clamp(5,0,3)       = " + clamp(5.0, 0.0, 3.0));
    log("saturate(-0.5)     = " + saturate(-0.5));
    log("saturate(0.5)      = " + saturate(0.5));
    log("saturate(2.0)      = " + saturate(2.0));
    log("sign(-2.0)         = " + sign(-2.0));
    log("sign(0.0)          = " + sign(0.0));
    log("sign(3.0)          = " + sign(3.0));
    log("round(1.4)         = " + round(1.4));
    log("round(1.5)         = " + round(1.5));
    log("fract(-1.25)       = " + fract(-1.25));
    log("wrap(370,0,360)    = " + wrap(370.0, 0.0, 360.0));
    log("lerp(0,10,0.25)    = " + lerp(0.0, 10.0, 0.25));
    log("inverse_lerp(0,10,2.5) = " + inverse_lerp(0.0, 10.0, 2.5));
    log("remap(0..100 -> -1..1, 25) = " + remap(0.0, 100.0, -1.0, 1.0, 25.0));
    log("smoothstep(0,1,0.5)= " + smoothstep(0.0, 1.0, 0.5));
    log("step(0.5, 0.25)    = " + step(0.5, 0.25));
    log("step(0.5, 0.75)    = " + step(0.5, 0.75));
    // Basic sanity; your C++ doesn’t expose make_nan/make_inf so just use 0
    log("is_nan(0.0)        = " + (is_nan(0.0) ? "true" : "false"));
    log("is_inf(1.0)        = " + (is_inf(1.0) ? "true" : "false"));
    
    // ----------------------------------------------------------------
    // vector2
    // ----------------------------------------------------------------
    vector2 v2a;            // default (0,0)
    v2a.x = 1.0;
    v2a.y = 2.0;
    
    vector2 v2b(4.0, -1.0); // ctor
    
    print_vec2("v2a", v2a);
    print_vec2("v2b", v2b);
    
    vector2 v2_add = v2a + v2b;
    vector2 v2_sub = v2a - v2b;
    vector2 v2_neg = -v2a;
    vector2 v2_mul = v2a * 2.0;
    vector2 v2_div = v2b / 2.0;
    
    print_vec2("v2a + v2b", v2_add);
    print_vec2("v2a - v2b", v2_sub);
    print_vec2("-v2a",      v2_neg);
    print_vec2("v2a * 2",   v2_mul);
    print_vec2("v2b / 2",   v2_div);
    
    log("v2a == v2a ? " + (v2a == v2a ? "true" : "false"));
    log("v2a == v2b ? " + (v2a == v2b ? "true" : "false"));
    
    log("v2a.length()        = " + v2a.length());
    log("v2a.distance(v2b)   = " + v2a.distance(v2b));
    log("v2a.distance_to(v2b)= " + v2a.distance_to(v2b));
    
    vector2 v2_lerp = v2a.lerp(v2b, 0.5);
    print_vec2("v2a.lerp(v2b,0.5)", v2_lerp);
    
    print_vec2("v2a.min(v2b)", v2a.min(v2b));
    print_vec2("v2a.max(v2b)", v2a.max(v2b));
    
    // ----------------------------------------------------------------
    // vector3
    // ----------------------------------------------------------------
    vector3 v3a;            // default (0,0,0)
    v3a.x = 1.0; v3a.y = 2.0; v3a.z = 3.0;
    
    vector3 v3b(4.0, -1.0, 0.5);
    
    print_vec3("v3a", v3a);
    print_vec3("v3b", v3b);
    
    print_vec3("v3a + v3b", v3a + v3b);
    print_vec3("v3a - v3b", v3a - v3b);
    print_vec3("-v3a",      -v3a);
    print_vec3("v3a * 2",   v3a * 2.0);
    print_vec3("v3b / 2",   v3b / 2.0);
    
    log("v3a.length()        = " + v3a.length());
    log("v3a.length2d()      = " + v3a.length2d());
    log("v3a.distance(v3b)   = " + v3a.distance(v3b));
    log("v3a.distance2d(v3b) = " + v3a.distance2d(v3b));
    
    vector3 v3_lerp = v3a.lerp(v3b, 0.5);
    print_vec3("v3a.lerp(v3b,0.5)", v3_lerp);
    
    print_vec3("v3a.min(v3b)", v3a.min(v3b));
    print_vec3("v3a.max(v3b)", v3a.max(v3b));
    log("v3a.dot_product(v3b) = " + v3a.dot_product(v3b));
    print_vec3("v3a.cross_product(v3b)", v3a.cross_product(v3b));
    
    // ----------------------------------------------------------------
    // quaternion
    // ----------------------------------------------------------------
    quaternion q;   // default (0,0,0,1)
    print_quat("q (default)", q);
    
    quaternion qEuler = quat_from_euler(30.0, 45.0, 10.0);
    print_quat("qEuler (30,45,10)", qEuler);
    
    log("qEuler.length()     = " + qEuler.length());
    print_quat("qEuler.normalized()", qEuler.normalized());
    
    quaternion q2(0.1, 0.2, 0.3, 0.9);
    print_quat("q2", q2);
    
    log("qEuler.dot(q2)      = " + qEuler.dot(q2));
    print_quat("qEuler.conjugate()", qEuler.conjugate());
    print_quat("qEuler.inverse()",   qEuler.inverse());
    print_quat("qEuler * q2",        qEuler * q2);
    print_quat("qEuler * 0.5",       qEuler * 0.5);
    print_quat("qEuler / 2.0",       qEuler / 2.0);
    print_quat("qEuler + q2",        qEuler + q2);
    print_quat("qEuler - q2",        qEuler - q2);
    print_quat("-qEuler",            -qEuler);
    
    log("qEuler == qEuler ? " + (qEuler == qEuler ? "true" : "false"));
    log("qEuler == q2 ? "      + (qEuler == q2      ? "true" : "false"));
    
    double pitch, yaw, roll;
    qEuler.to_euler(pitch, yaw, roll);
    log("qEuler.to_euler() -> pitch=" + pitch + ", yaw=" + yaw + ", roll=" + roll);
    
    vector3 v3Test(1.0, 0.0, 0.0);
    vector3 v3Rot = qEuler.rotate(v3Test);
    print_vec3("qEuler.rotate(1,0,0)", v3Rot);
    
    // ----------------------------------------------------------------
    // matrix4x4
    // ----------------------------------------------------------------
    matrix4x4 I = mat4_identity();
    matrix4x4 T = mat4_translate(1.0, 2.0, 3.0);
    matrix4x4 S = mat4_scale(2.0, 3.0, 4.0);
    matrix4x4 R = mat4_rotate_euler(30.0, 45.0, 10.0);
    matrix4x4 Qm = mat4_from_quaternion(qEuler);
    
    vector3 v3_id = I.transform(v3a);
    vector3 v3_t  = T.transform(v3a);
    vector3 v3_s  = S.transform(v3a);
    vector3 v3_r  = R.transform(v3a);
    vector3 v3_qm = Qm.transform(v3a);
    
    print_vec3("I.transform(v3a)",  v3_id);
    print_vec3("T.transform(v3a)",  v3_t);
    print_vec3("S.transform(v3a)",  v3_s);
    print_vec3("R.transform(v3a)",  v3_r);
    print_vec3("Qm.transform(v3a)", v3_qm);
    
    matrix4x4 M = T * S * R;
    vector3 v3_m = M.transform(v3a);
    print_vec3("M.transform(v3a)", v3_m);
    
    log("=== Extended Math test DONE ===");
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
GET https://docs.perception.cx/perception/angel-script/extended-math-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/file-system.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/file-system.md).

# File System

**API Folder Location** : C:\Users\\"UserName"\Documents\My Games\\

Filesystem API that allows scripts to read, write, and manage files **only inside the main scripting directory**.

Scripts **cannot** access, modify, create, or query files **outside** this directory.\
All paths must be **relative** and are automatically sandboxed for safety.

***

### Overview

The filesystem API provides the following capabilities:

* Create files
* Create directories
* Read files
* Check if a file exists
* List files or directories
* Delete files
* Delete directories

All functions are available as **global AngelScript functions**.

***

### Path Rules

To ensure safety and consistency:

#### ✔ Paths must be relative

Absolute paths such as:

```
/folder/file.txt
C:\temp\log.txt
```

are not allowed.

#### ✔ Parent-directory traversal is not allowed

Paths cannot contain:

```
..
```

#### ✔ Scripts cannot escape the main scripting directory

Every operation is automatically constrained to the script directory.

***

### Global Functions

#### `bool create_file(const string &in path, const string &in data = "")`

Creates or overwrites a file at the given relative path.

* **path** — relative file path under the main scripting directory
* **data** — optional file contents (defaults to empty)

```cpp
bool ok = create_file("data/info.txt", "Hello World!");
```

***

#### `bool create_directory(const string &in path)`

Creates a directory (non-recursive).

```cpp
bool ok = create_directory("data/logs");
```

***

#### `bool read_file(const string &in path, string &out data)`

Reads a file and returns its contents through an output parameter.

* Returns `true` on success, `false` if the file does not exist or could not be read.

```cpp
string text;
bool ok = read_file("data/info.txt", text);
if (ok)
{
    log("File contents: " + text);
}
```

***

#### `bool does_file_exist(const string &in path)`

Checks if a file exists.

```cpp
if (does_file_exist("data/info.txt"))
{
    log("File exists");
}
```

***

#### \`bool query\_directory(const string \&in path,

bool include\_dirs,\
bool include\_files,\
const array\<string> \&in extensions,\
array\<string> \&out entries)\`

Lists the contents of a directory.

**Parameters**

* `path` — relative directory path under the main scripting directory
* `include_dirs` — if `true`, include subdirectories in the results
* `include_files` — if `true`, include files in the results
* `extensions` — list of file extensions to include; pass an empty array for no filter
* `entries` — output array that will be filled with names (no directory prefix)

**Example**

```cpp
array<string> entries;
array<string> noFilter; // empty

bool ok = query_directory("data", true, true, noFilter, entries);
if (ok)
{
    for (uint i = 0; i < entries.length(); ++i)
    {
        log("Entry: " + entries[i]);
    }
}
```

**Filtered example**

```cpp
array<string> exts = { ".json" };
array<string> jsonFiles;

bool ok = query_directory("data", false, true, exts, jsonFiles);
if (ok)
{
    for (uint i = 0; i < jsonFiles.length(); ++i)
    {
        log("JSON: " + jsonFiles[i]);
    }
}
```

***

#### `bool delete_file(const string &in path)`

Deletes a file.

```cpp
bool ok = delete_file("data/old.txt");
```

***

#### `bool delete_directory(const string &in path)`

Deletes a directory.\
Depending on configuration, the directory may need to be empty.

```cpp
bool ok = delete_directory("data/temp");
```

***

#### `bool write_file_binary(const string &in path, const array<uint8> &in data)`

Writes raw bytes to a file (creates or overwrites).

* `path` — relative file path under the main scripting directory
* `data` — raw bytes to write

Returns `true` on success, `false` on failure.

***

#### `bool read_file_binary(const string &in path, array<uint8> &out data)`

Reads a file as raw bytes.

* `path` — relative file path under the main scripting directory
* `data` (out) — filled with file bytes on success

Returns `true` on success, `false` if the file does not exist or could not be read.

***

#### `bool append_file_binary(const string &in path, const array<uint8> &in data)`

Appends raw bytes to the end of a file.

* `path` — relative file path under the main scripting directory
* `data` — raw bytes to append

Returns `true` on success, `false` on failure.

***

#### `uint64 get_file_size(const string &in path)`

Returns the file size in bytes.

* `path` — relative file path under the main scripting directory

Returns the size in bytes. (If you want to document a failure value, pick one consistent rule like “returns 0 on missing file” and note it here.)

***

### Example Test Script

A simple AngelScript example that exercises all functions:

```cpp
int main()
{
    log("=== AS FS TEST START ===");

    // 1) Create a directory
    bool ok = create_directory("fs_tests");
    log("create_directory: " + string(ok ? "true" : "false"));

    // 2) Create a file
    ok = create_file("fs_tests/test.txt", "Hello from AngelScript FS API!\n");
    log("create_file: " + string(ok ? "true" : "false"));

    // 3) Read it back
    string data;
    ok = read_file("fs_tests/test.txt", data);
    log("read_file: " + string(ok ? "true" : "false"));
    if (ok)
        log("data = " + data);

    // 4) Check existence
    bool exists = does_file_exist("fs_tests/test.txt");
    log("does_file_exist: " + string(exists ? "true" : "false"));

    // 5) Query directory
    array<string> entries;
    array<string> noFilter;
    ok = query_directory("fs_tests", true, true, noFilter, entries);
    log("query_directory: " + string(ok ? "true" : "false"));
    if (ok)
    {
        for (uint i = 0; i < entries.length(); ++i)
            log("entry: " + entries[i]);
    }

    // 6) Delete file + directory
    ok = delete_file("fs_tests/test.txt");
    log("delete_file: " + string(ok ? "true" : "false"));

    ok = delete_directory("fs_tests");
    log("delete_directory: " + string(ok ? "true" : "false"));

    log("=== AS FS TEST END ===");
    return 1; // keep script loaded
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/file-system.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/gui-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/gui-api.md).

# GUI API

This page documents the **AngelScript GUI API** used to build and interact with the Perception.cx UI.

> ❗ All GUI types are **owned** and cleaned up by the engine.\
> You never `delete` or free them from AngelScript.

***

### Overview

```cpp
 /* This gives you position and size of the main GUI window */
void get_gui_position(float &out x, float &out y)
void get_gui_size(float &out w, float &out h)
```

Typical usage flow:

1. Create a **subtab** under one of the fixed top-level tabs.
2. Create a **panel** inside that subtab.
3. Add UI elements (checkboxes, keybinds, sliders, inputs, color pickers, lists, multi/single-select, buttons) to that panel.
4. Read/update values in your `main()` or `on_frame()` loop.
5. Optionally, attach a **callback** to a button.

Example:

```cpp
subtab_t st = create_subtab(0, "My Script");
if (!st.is_valid())
{
    log("[GUI] failed to create subtab");
    return -1;
}

panel_t p = st.add_panel("Main Panel", false); // false = large panel

checkbox_t cb = p.add_checkbox("Enable Feature", false);
slider_double_t dist = p.add_slider_double("Distance", "m", 100.0, 0.0, 500.0, 1.0);

// Each frame:
void on_frame(int cb_index, int data_index)
{
    bool enabled = cb.get();
    double d = dist.get();
    // ... use enabled + d ...
}
```

***

### Subtabs & Panels

#### `subtab_t`

A `subtab_t` represents a subtab under one of the fixed top-level tabs.

**Create**

```cpp
subtab_t create_subtab(int parent_tab, const string &in name);
```

* `parent_tab`: 0–(FIXED\_TAB\_COUNT-1) – which main tab to attach to.
* `name`: label shown in the UI subtab bar.

**Methods**

```cpp
panel_t add_panel(const string &in name, bool is_small);
bool is_valid() const;
void subtab_t::set_active(bool active);
void panel_t::set_active(bool active);
```

* `add_panel` – creates a new panel inside this subtab.
  * `is_small = true` → small panel layout; `false` → normal/large.
* `is_valid()` – `true` if the handle is non-null. Only needed for error-checking in `main()`.

#### `panel_t`

Represents a panel inside a subtab.\
All other UI elements are added **to a panel**.

You don’t manually free panels; they’re destroyed when the owning subtab is destroyed (usually when the script unloads).

***

### Checkbox

#### Create

```cpp
checkbox_t panel_t::add_checkbox(
    const string &in name,
    bool initial,
    bool draw_title = true,
    bool find_protect = false,
    bool draw_just_label = false
);
```

* `name`: label.
* `initial`: initial on/off state.
* `draw_title`: whether to render the title text.
* `find_protect`: if `true`, protects the element from naive find/replace patterns (internal anti-scan behavior).
* `draw_just_label`: When enabled, the checkbox is non-interactive and functions purely as a label. This is useful when you only want to attach a color picker or keybind without toggle behavior.

> ❗ Design rule:
>
> * A checkbox can act as a **parent** for either:
>   * up to **two color pickers**, or
>   * up to **two keybinds** or
>   * one **colorpicker +** one **keybind**
> * Color pickers / keybind must be added **immediately after** the checkbox on the panel.

#### Methods

```cpp
bool checkbox_t::get() const;
void checkbox_t::set(bool v);
void checkbox_t::set_active(bool active);
```

Example:

```cpp
checkbox_t cb = p.add_checkbox("Enable ESP", false);
cb.set(true);
bool enabled = cb.get();
```

***

### Keybind

Keybinds let you bind a virtual-key and mode to a checkbox-controlled feature.

#### Create

```cpp
keybind_t panel_t::add_keybind(
    const string &in name,
    int key,
    const string &in mode,
    bool draw_title = true,
    bool find_protect = false
);
```

* **Must** appear right after its parent checkbox.
* `key`: a Win32 virtual-key code (e.g. `0x2E` for Delete, `0x2C` for PrintScreen).
* `mode`: `"off"`, `"on"`, `"single"`, `"toggle"`, or `"always_on"`.

#### Methods

```cpp
void keybind_t::get(int &out key, string &out mode) const;
void keybind_t::set(int key, const string &in mode);
void keybind_t::set_active(bool active);
bool keybind_t::is_pressed() const
```

Example:

```cpp
checkbox_t cb = p.add_checkbox("Aimbot", false);
keybind_t kb = p.add_keybind("Aimbot Hotkey", 0x2E, "toggle");

int k; string m;
kb.get(k, m); // -> 0x2E, "toggle"

kb.set(0x2C, "single");
kb.get(k, m); // -> 0x2C, "single"
```

***

### Color Picker

Color pickers store RGBA as **0–255 floats**.

#### Create

```cpp
color_picker_t panel_t::add_color(
    const string &in name,
    const array<float> &in rgba,
    bool find_protect = false
);
```

* Must follow a checkbox or keybind within that chain (according to your UI layout rules).
* `rgba` – `array<float>` of size 4: `{R, G, B, A}`, each in \[0–255].

#### Methods

```cpp
void color_picker_t::get(array<float> &out rgba) const;
void color_picker_t::set(const array<float> &in rgba);
void color_picker_t::set_active(bool active);
```

Example:

```cpp
checkbox_t cb = p.add_checkbox("Chams", true);

array<float> rgba = {255.0f, 0.0f, 0.0f, 255.0f};
color_picker_t col = p.add_color("Enemy Color", rgba);

// read back
array<float> out = array<float>(4);
col.get(out); // out[0..3] now contain 0–255

// change
array<float> new_rgba = {77.0f, 204.0f, 26.0f, 255.0f};
col.set(new_rgba);
```

***

### Sliders

#### Double slider

```cpp
slider_double_t panel_t::add_slider_double(
    const string &in name,
    const string &in postfix,
    double value,
    double minv,
    double maxv,
    double step,
    bool draw_title = true,
    bool find_protect = false
);
```

#### Methods

```cpp
double slider_double_t::get() const;
void   slider_double_t::set(double v);
void   slider_double_t::set_active(bool active);
```

Example:

```cpp
slider_double_t dist = p.add_slider_double("Distance", "m", 150.0, 0.0, 500.0, 1.0);
double d0 = dist.get();
dist.set(275.0);
double d1 = dist.get();
```

#### Int slider

```cpp
slider_int_t panel_t::add_slider_int(
    const string &in name,
    const string &in postfix,
    int value,
    int minv,
    int maxv,
    int step,
    bool draw_title = true,
    bool find_protect = false
);
```

#### Methods

```cpp
int  slider_int_t::get() const;
void slider_int_t::set(int v);
void slider_int_t::set_active(bool active);
```

***

### Input Text Box

```cpp
input_t panel_t::add_input(
    const string &in name,
    const string &in initial,
    bool draw_title = true,
    bool find_protect = false
);

string input_t::get() const;
void   input_t::set(const string &in v);
```

Example:

```cpp
input_t user = p.add_input("Username", "DefaultUser");
string s0 = user.get();
user.set("AS_User");
string s1 = user.get();
```

***

### List

Lists are 2-column rows (`info1`, `info2`).

#### Create

```cpp
list_t panel_t::add_list(
    const string &in name,
    const array<dictionary@> &in members,
    bool draw_title = true,
    bool find_protect = false
);
```

Each `dictionary` is expected to have:

* `"info1"` – string
* `"info2"` – string

#### Methods

<pre class="language-cpp"><code class="lang-cpp">int list_t::get() const;
int  list_t::get_count() const;
void list_t::clear();
void list_t::append(const string &#x26;in info1, const string &#x26;in info2);
void list_t::set_active(bool active);
<strong>void list_t::remove(int index) const;
</strong>void list_t::highlight(int index) const;
void list_t::remove_highlight(int index) const;
void list_t::hide(int index) const;
void list_t::show(int index) const;
</code></pre>

Example:

```cpp
array<dictionary@> members;
dictionary@ d0 = dictionary();
d0.set("info1", "Row0-Col0");
d0.set("info2", "Row0-Col1");
members.insertLast(d0);

dictionary@ d1 = dictionary();
d1.set("info1", "Row1-Col0");
d1.set("info2", "Row1-Col1");
members.insertLast(d1);

list_t lst = p.add_list("Test List", members);
int c0 = lst.get_count();
lst.append("Extra", "Info");
int c1 = lst.get_count();
```

***

### Multi-Select

A multi-select lets you toggle multiple options.

#### Create

```cpp
multi_select_t panel_t::add_multi_select(
    const string &in name,
    const array<dictionary@> &in options,
    bool is_expandable,
    bool draw_title = true,
    bool find_protect = false
);
```

Each `dictionary` in `options` should contain:

* `"label"` – string
* `"selected"` – bool (optional; defaults to false)

#### Methods

```cpp
void multi_select_t::get(array<bool> &out states) const;
void multi_select_t::set(int index, bool state);
void multi_select_t::set_active(bool active);
```

Example:

```cpp
array<dictionary@> mopts;

dictionary@ m0 = dictionary();
m0.set("label", "A");
m0.set("selected", true);
mopts.insertLast(m0);

dictionary@ m1 = dictionary();
m1.set("label", "B");
m1.set("selected", false);
mopts.insertLast(m1);

multi_select_t ms = p.add_multi_select("Modes", mopts, true);

array<bool> states;
ms.get(states); // states.length=2, [true,false]

ms.set(1, true);
ms.get(states); // [true,true]
```

***

### Single-Select

Single-select is a dropdown/radio list with a single active index.

#### Create

```cpp
single_select_t panel_t::add_single_select(
    const string &in name,
    const array<string> &in options,
    int initial_index,
    bool is_expandable,
    bool draw_title = true,
    bool find_protect = false
);
```

#### Methods

```cpp
int  single_select_t::get() const;
void single_select_t::set(int index);
void single_select_t::set_active(bool active);
```

Example:

```cpp
array<string> sopts = { "One", "Two", "Three" };
single_select_t ss = p.add_single_select("Select One", sopts, 1, true);

int idx0 = ss.get(); // 1
ss.set(2);
int idx1 = ss.get(); // 2
```

***

### Buttons & Callbacks

Buttons are clickable UI elements with an AngelScript callback.

#### Funcdef

```cpp
funcdef void button_callback_t();
```

#### Create

```cpp
button_t panel_t::add_button(
    const string &in name,
    button_callback_t@ cb,
    bool find_protect = false
);
```

* `cb` is a function with signature `void f()`.

#### Methods

```cpp
void button_t::set_active(bool active);
```

#### Example

```cpp
int g_hits = 0;

void OnTestButton()
{
    g_hits++;
    Print("[GUI] Test button clicked " + g_hits + " times");
}

int main()
{
    subtab_t st = create_subtab(0, "Button Demo");
    if (!st.is_valid()) return -1;

    panel_t p = st.add_panel("Main", false);
    button_t btn = p.add_button("Click Me", @OnTestButton);

    return 1;
}
```

When you click the button in the UI, `OnTestButton` will be executed.

***

## `bool gui_active()`

Checks if the gui is currently visible or not

***

### Finding Existing Elements (`find_*`)

If your script needs to **attach** to UI created elsewhere (or from config), use the `find_*` helpers.

Each `find_*` searches by:

* `tab` – top-level tab index (0..FIXED\_TAB\_COUNT-1)
* `subtab` – subtab name (string)
* `panel` – panel name(string)
* `name` – element label (string)
* element type (encoded in the function name)

#### Signatures

```cpp
checkbox_t      find_checkbox(int tab, const string &in subtab, const string &in panel, const string &in name);
slider_double_t find_slider_double(int tab, const string &in subtab, const string &in panel, const string &in name);
slider_int_t    find_slider_int(int tab, const string &in subtab, const string &in panel, const string &in name);
input_t         find_input(int tab, const string &in subtab, const string &in panel, const string &in name);
multi_select_t  find_multi_select(int tab, const string &in subtab, const string &in panel, const string &in name);
single_select_t find_single_select(int tab, const string &in subtab, const string &in panel, const string &in name);
keybind_t       find_keybind(int tab, const string &in subtab, const string &in panel, const string &in name);
button_t        find_button(int tab, const string &in subtab, const string &in panel, const string &in name);
color_picker_t  find_color(int tab, const string &in subtab, const string &in panel, const string &in name);
list_t          find_list(int tab, const string &in subtab, const string &in panel, const string &in name);
```

These return handle `0` if no element is found.

Example:

```cpp
void on_frame()
{
    checkbox_t cb = find_checkbox(0, "AS GUI Test", "Panel Name", "Color Feature");
    if (cb != 0)
    {
        bool v = cb.get();
        // use v ...
    }

    slider_double_t sld = find_slider_double(0, "AS GUI Test", "Panel Name", "Distance Slider");
    if (sld != 0)
    {
        double d = sld.get();
        // ...
    }
}
```

> ❗ Internally, `find_*` marks elements as "referenced" for cleanup when the script unloads.\
> You don’t need (and must not try) to free them manually.

***

### Config Helpers

These are global functions for saving/loading the UI configuration (all tabs, subtabs, elements).

```cpp
string construct_config();
void   apply_config(const string &in cfg);
```

* `construct_config()` – builds a serialized config string of the current UI state.
* `apply_config(cfg)` – applies a serialized config string.

Example:

```cpp
void save_ui()
{
    string cfg = construct_config();
    // write cfg to file or elsewhere
}

void load_ui(const string &in cfg)
{
    apply_config(cfg);
}
```

***

### Name Prefixing for Elements (`##prefix_`)

Multiple UI elements with the **same visible name** are supporte&#x64;**,** but the **configuration system cannot uniquely identify them** unless you explicitly assign a prefix.

The `##prefix_` syntax allows you to attach an **internal unique ID** to an element while keeping the **visible label unchanged**.

***

#### ✔ What Prefixing Does

* The part **after** `##prefox_` is the **visible label** shown in the UI and the rest is Unique ID.
* Prefixing is **optional**, but required if you want your elements to save/load uniquely in configs.
* *find\_ functions completely ignore the prefix*\* and search only by the visible label.

***

#### ✔ Example

```cpp
// Both show "Player Name" on screen
p.add_input("##elem1_Player Name", "Alex");
p.add_input("##elem2_Player Name", "Alex");
```

Both inputs look identical to the user, but internally:

* Internal IDs: `elem1_Player Name`, `elem2_Player Name`
* Visible name: `Player Name`
* Config system will save/load each one correctly.

***

### Behavior Summary

| System / Functionality      | Prefix Used?                    | Notes                                                        |
| --------------------------- | ------------------------------- | ------------------------------------------------------------ |
| **UI Rendering**            | ❌ No — prefix hidden            | Only the text after `##` is shown.                           |
| **Internal ID / Config**    | ✅ Yes — full prefixed name used | Required for unique config entries.                          |
| *find\_ API*\*              | ❌ No — prefix ignored           | Searches only by visible name.                               |
| **Duplicate visible names** | ✔ Allowed, even without prefix  | But: config will **not** differentiate them unless prefixed. |

***

### ⚠ Important Notes

#### 1. Duplicate names *without* prefix

These **work in the UI**, but the configuration system will treat them as the **same element**, causing:

* overwritten values
* incorrect load order
* mismatched element states

#### 2. Duplicate names *with* prefix

These behave perfectly:

* visible name is the same
* internal ID is unique
* config system saves & loads correctly
* find\_\* still searches by visible name only

#### 3. find\_\* and duplicates

Because find\_\* searches by visible name, if you have two labels both named `"Player Name"`, then:

```cpp
auto inp = find_input(0, "Tab", "Panel", "Player Name");
```

…it will always return the **first** one created, regardless of prefixes.

***

### When Should You Use Prefixing?

Use `##prefix_` whenever:

* You create multiple repeated UI blocks (e.g. per-player, per-item, per-weapon).
* You have identical element names inside the same panel or subtab.
* You want your configuration to properly remember each element’s value.

***

### Quick Example

```cpp
panel_t p = st.add_panel("Players", false);

// These two will look identical to the user
p.add_slider_double("##p1_Speed", 0.0, 100.0, 50.0);
p.add_slider_double("##p2_Speed", 0.0, 100.0, 60.0);

// Without prefixes, the config system would conflict them
// With prefixes, each one saves/loads separately
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/gui-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/input-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/input-api.md).

# Input API

The Input API provides full access to mouse, keyboard, and scroll states from AngelScript.\
All functions are **safe** — no pointers or raw memory are exposed to scripts.

***

### 📍 Mouse

#### Get Mouse Position

```cpp
void get_mouse_pos(float &out x, float &out y)
```

Returns the current mouse position **within the viewport**.

***

#### Get Mouse Position Relative To Desktop

```cpp
void get_mouse_pos_desktop(float &out x, float &out y)
```

Returns the absolute mouse position in **desktop coordinates** (OS-space).

***

#### Get Mouse Movement Delta

```cpp
void get_mouse_delta(float &out dx, float &out dy)
```

Returns the **delta movement** of the mouse since the last frame (viewport space).

***

#### Get Mouse Movement Delta Relative To Desktop

```cpp
void get_mouse_delta_desktop(float &out dx, float &out dy)
```

Returns the **desktop-space delta** of mouse movement since the last frame.

***

#### Was Mouse Movement Received

```cpp
bool mouse_movement_received()
```

Returns `true` if any mouse movement has been received during this frame.

***

#### Get Scroll Delta

```cpp
float get_scroll_delta()
```

Returns the scroll wheel delta value for the current frame.

***

#### Is Hovered Over Region

```cpp
bool is_hovered(float x, float y, float w, float h)
```

Returns `true` if the mouse is hovering over a given rectangular region.

* `(x, y)` — Top-left corner of the region.
* `(w, h)` — Width and height of the region.

***

### ⌨️ Keyboard

Keyboard functions use **virtual key (VK)** codes (standard Windows-style, e.g., `0x41` = A).

***

#### Key State Queries

Each of the following functions takes an `int vk` (the virtual key code):

```cpp
bool key_down(int vk)
bool key_raw_down(int vk)
bool key_fired(int vk)
bool key_toggle(int vk)
bool key_singlepress(int vk)
bool key_prev_down(int vk)
```

| Function          | Description                                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------------------- |
| `key_down`        | Returns `true` if the key is currently held down.                                                         |
| `key_raw_down`    | Returns raw (unfiltered) down state.                                                                      |
| `key_fired`       | Returns `true` if the key transitioned from up→down this frame (WinProc like input for input boxes, etc). |
| `key_toggle`      | Returns toggle state (for keys like CapsLock).                                                            |
| `key_singlepress` | True only once per press event (useful for UI).                                                           |
| `key_prev_down`   | Returns `true` if the key was down in the previous frame.                                                 |

***

#### Get Key State

```cpp
void get_key_state(int vk,
    bool &out raw_down, bool &out down,
    bool &out fired, bool &out toggle,
    bool &out singlepress, bool &out prev_down)
```

Fetches **all key state flags at once** for the specified key.

***

#### Get Keys Down

```cpp
void get_keys_down(array<int> &out indices)
```

Fills an array with the **virtual key codes** of all keys currently held down.

Example:

```cpp
array<int> pressed;
get_keys_down(pressed);

for (uint i = 0; i < pressed.length(); ++i)
{
    print("Key down: " + get_key_name(pressed[i]) + "\n");
}
```

***

### 🔡 Text Input

#### Get Latest Key Input

```cpp
string get_recent_key_input()
```

Returns a string containing the most recently typed characters since the last frame.\
Use this for text fields or console input.

***

#### Get Key Name By VK

```cpp
string get_key_name(int vk)
```

Returns a **human-readable name** for the specified virtual key code.\
Example: `get_key_name(0x41)` → `"A"`

***

### 🧠 Notes

* All keyboard queries use the Windows-style **VK codes** (`0x01` = LMB, `0x41` = A, `0x1B` = ESC, etc.).
* Mouse functions operate in **viewport space** unless the “desktop” variant is used.
* Functions are designed to be **safe and lightweight** — they only read internal copies of state.
* You can safely call any of these from UI, game logic, or render scripts.

***

#### 🧩 Example Usage

```cpp
void update_ui()
{
    float mx, my;
    get_mouse_pos(mx, my);

    if (is_hovered(100,100,200,80))
        draw_rect_filled(100,100,200,80, 50,120,255,180, 6.0f, RR_TOP_LEFT|RR_TOP_RIGHT);

    if (key_fired(0x1B)) // ESC key
        print("Escape pressed!\n");

    string input = get_recent_key_input();
    if (input.length() > 0)
        draw_text("Typed: " + input, mx + 10, my + 10,
                  255,255,255,255, get_font18(), TE_NONE, 0,0,0,0, 0.0f, true);
}
```

***

#### Version


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/input-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/intrinsics.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/intrinsics.md).

# Intrinsics

The **Intrinsics API** provides direct CPU intrinsic bindings for **faithful reproduction of pointer decryption and obfuscation logic** (bit rotations, bit scans, and a subset of SSE integer operations).

### Important Notes

* All SSE 128-bit operations use `array<uint8>` **length = 16**.
* Outputs are written to `&out result` arrays.
* For `mm_extract_*`, lane `index` must be in range (ex: `mm_extract_epi64` → `0..1`, `mm_extract_epi32` → `0..3`, `mm_extract_epi16` → `0..7`, `mm_extract_epi8` → `0..15`).
* For `mm_shuffle_epi8` (pshufb): mask high bit (`0x80`) zeros the output byte (hardware behavior).

***

### Bit Rotation

```cpp
uint8  rol8 (uint8  value, int count)
uint8  ror8 (uint8  value, int count)
uint16 rol16(uint16 value, int count)
uint16 ror16(uint16 value, int count)
uint32 rol32(uint32 value, int count)
uint32 ror32(uint32 value, int count)
uint64 rol64(uint64 value, int count)
uint64 ror64(uint64 value, int count)
```

Rotates bits left/right by `count` (wrap-around).

***

### Byte Swap

```cpp
uint16 bswap16(uint16 value)
uint32 bswap32(uint32 value)
uint64 bswap64(uint64 value)
```

Swaps endianness of the value.

***

### Bit Manipulation

```cpp
int popcnt32(uint32 value)
int popcnt64(uint64 value)

int lzcnt32(uint32 value)
int lzcnt64(uint64 value)

int tzcnt32(uint32 value)
int tzcnt64(uint64 value)
```

* `popcnt*` — population count (# of set bits)
* `lzcnt*` — leading zero count
* `tzcnt*` — trailing zero count

***

### SSE Logical Operations (128-bit)

All operands are 16-byte arrays.

```cpp
void mm_xor_si128    (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_or_si128     (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_and_si128    (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_andnot_si128 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
```

* `mm_andnot_si128(a, b)` behaves like `(~a) & b`.

***

### SSE Shift Operations

```cpp
void mm_slli_epi16 (const array<uint8> &in a, int imm8, array<uint8> &out result)
void mm_srli_epi16 (const array<uint8> &in a, int imm8, array<uint8> &out result)

void mm_slli_epi32 (const array<uint8> &in a, int imm8, array<uint8> &out result)
void mm_srli_epi32 (const array<uint8> &in a, int imm8, array<uint8> &out result)

void mm_slli_epi64 (const array<uint8> &in a, int imm8, array<uint8> &out result)
void mm_srli_epi64 (const array<uint8> &in a, int imm8, array<uint8> &out result)

// byte shifts (whole 128-bit register)
void mm_slli_si128 (const array<uint8> &in a, int imm8, array<uint8> &out result) // shift left by bytes
void mm_srli_si128 (const array<uint8> &in a, int imm8, array<uint8> &out result) // shift right by bytes
```

***

### SSE Shuffle Operations

```cpp
void mm_shuffle_epi8      (const array<uint8> &in a, const array<uint8> &in mask, array<uint8> &out result) // pshufb
void mm_shuffle_epi32     (const array<uint8> &in a, int imm8, array<uint8> &out result)                    // pshufd
void mm_shufflehi_epi16   (const array<uint8> &in a, int imm8, array<uint8> &out result)                    // pshufhw
void mm_shufflelo_epi16   (const array<uint8> &in a, int imm8, array<uint8> &out result)                    // pshuflw
```

***

### SSE Unpack Operations

```cpp
void mm_unpackhi_epi8  (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_unpackhi_epi16 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_unpackhi_epi32 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_unpackhi_epi64 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)

void mm_unpacklo_epi8  (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_unpacklo_epi16 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_unpacklo_epi32 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_unpacklo_epi64 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
```

***

### SSE Arithmetic

```cpp
void mm_add_epi8  (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_add_epi16 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_add_epi32 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_add_epi64 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)

void mm_sub_epi8  (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_sub_epi16 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_sub_epi32 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_sub_epi64 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)

void mm_mullo_epi16(const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_mullo_epi32(const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
```

***

### SSE Set / Broadcast

```cpp
void mm_set_epi64x (int64 e1, int64 e0, array<uint8> &out result)
void mm_set_epi32  (int32 e3, int32 e2, int32 e1, int32 e0, array<uint8> &out result)

void mm_set1_epi64x(int64 a, array<uint8> &out result) // broadcast qword
void mm_set1_epi32 (int32 a, array<uint8> &out result) // broadcast dword
void mm_set1_epi16 (int16 a, array<uint8> &out result)
void mm_set1_epi8  (int8  a, array<uint8> &out result)

void mm_setzero_si128(array<uint8> &out result)

void broadcast_qword(uint64 value, array<uint8> &out result)
void broadcast_dword(uint32 value, array<uint8> &out result)
```

**Lane ordering note (matches your tests):**\
`mm_set_epi32(e3,e2,e1,e0)` → `mm_extract_epi32(result, 0) == e0`, ..., index 3 == `e3`.

***

### SSE Extract

```cpp
int64 mm_extract_epi64(const array<uint8> &in a, int index)
int32 mm_extract_epi32(const array<uint8> &in a, int index)
int32 mm_extract_epi16(const array<uint8> &in a, int index)
int32 mm_extract_epi8 (const array<uint8> &in a, int index)
```

***

### SSE Compare

```cpp
void mm_cmpeq_epi8 (const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_cmpeq_epi16(const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
void mm_cmpeq_epi32(const array<uint8> &in a, const array<uint8> &in b, array<uint8> &out result)
```

Outputs per lane are `0xFF..FF` for equal, `0` for not equal (hardware behavior).

***

### Full Test Example

```cpp
// SSE Intrinsics API Test Script
// Tests all bit manipulation and SSE operations for correctness

int g_tests_passed = 0;
int g_tests_failed = 0;

void test_assert(bool condition, const string &in name)
{
    if (condition) {
        g_tests_passed++;
        log_console("[PASS] " + name);
    } else {
        g_tests_failed++;
        log_console("[FAIL] " + name);
    }
}

void test_assert_eq_u64(uint64 expected, uint64 actual, const string &in name)
{
    if (expected == actual) {
        g_tests_passed++;
        log_console("[PASS] " + name);
    } else {
        g_tests_failed++;
        log_console("[FAIL] " + name + " - expected: " + formatInt(expected, "H") + " got: " + formatInt(actual, "H"));
    }
}

void test_assert_eq_i64(int64 expected, int64 actual, const string &in name)
{
    if (expected == actual) {
        g_tests_passed++;
        log_console("[PASS] " + name);
    } else {
        g_tests_failed++;
        log_console("[FAIL] " + name + " - expected: " + expected + " got: " + actual);
    }
}

void test_assert_array_eq(const array<uint8> &in expected, const array<uint8> &in actual, const string &in name)
{
    if (expected.length() != actual.length()) {
        g_tests_failed++;
        log_console("[FAIL] " + name + " - length mismatch");
        return;
    }
    for (uint i = 0; i < expected.length(); i++) {
        if (expected[i] != actual[i]) {
            g_tests_failed++;
            log_console("[FAIL] " + name + " - mismatch at index " + i);
            return;
        }
    }
    g_tests_passed++;
    log_console("[PASS] " + name);
}

// ============================================================================
// Bit Rotation Tests
// ============================================================================
void test_bit_rotation()
{
    log_console("\n=== Bit Rotation Tests ===");
    
    // ROL8
    test_assert_eq_u64(0x81, rol8(0xC0, 1), "rol8(0xC0, 1) == 0x81");
    test_assert_eq_u64(0x0F, rol8(0xF0, 4), "rol8(0xF0, 4) == 0x0F");
    
    // ROR8
    test_assert_eq_u64(0x60, ror8(0xC0, 1), "ror8(0xC0, 1) == 0x60");
    test_assert_eq_u64(0x0F, ror8(0xF0, 4), "ror8(0xF0, 4) == 0x0F");
    
    // ROL16
    test_assert_eq_u64(0x0002, rol16(0x0001, 1), "rol16(0x0001, 1) == 0x0002");
    test_assert_eq_u64(0x8001, rol16(0xC000, 1), "rol16(0xC000, 1) == 0x8001");
    
    // ROR16
    test_assert_eq_u64(0x8000, ror16(0x0001, 1), "ror16(0x0001, 1) == 0x8000");
    test_assert_eq_u64(0x00FF, ror16(0xFF00, 8), "ror16(0xFF00, 8) == 0x00FF");
    
    // ROL32
    test_assert_eq_u64(0x00000002, rol32(0x00000001, 1), "rol32(0x1, 1) == 0x2");
    test_assert_eq_u64(0x80000001, rol32(0xC0000000, 1), "rol32(0xC0000000, 1) == 0x80000001");
    test_assert_eq_u64(0xDEADBEEF, rol32(ror32(0xDEADBEEF, 13), 13), "rol32(ror32(x, 13), 13) == x");
    
    // ROR32
    test_assert_eq_u64(0x80000000, ror32(0x00000001, 1), "ror32(0x1, 1) == 0x80000000");
    test_assert_eq_u64(0x0000FFFF, ror32(0xFFFF0000, 16), "ror32(0xFFFF0000, 16) == 0x0000FFFF");
    
    // ROL64
    test_assert_eq_u64(0x0000000000000002, rol64(0x0000000000000001, 1), "rol64(0x1, 1) == 0x2");
    test_assert_eq_u64(0xDEADBEEFCAFEBABE, rol64(ror64(0xDEADBEEFCAFEBABE, 27), 27), "rol64(ror64(x, 27), 27) == x");
    
    // ROR64
    test_assert_eq_u64(0x8000000000000000, ror64(0x0000000000000001, 1), "ror64(0x1, 1) == 0x8000000000000000");
}

// ============================================================================
// Byte Swap Tests
// ============================================================================
void test_byte_swap()
{
    log_console("\n=== Byte Swap Tests ===");
    
    test_assert_eq_u64(0x3412, bswap16(0x1234), "bswap16(0x1234) == 0x3412");
    test_assert_eq_u64(0x78563412, bswap32(0x12345678), "bswap32(0x12345678) == 0x78563412");
    test_assert_eq_u64(0xEFCDAB8967452301, bswap64(0x0123456789ABCDEF), "bswap64(0x0123456789ABCDEF)");
    
    // Double swap should return original
    test_assert_eq_u64(0x1234, bswap16(bswap16(0x1234)), "bswap16(bswap16(x)) == x");
    test_assert_eq_u64(0xDEADBEEF, bswap32(bswap32(0xDEADBEEF)), "bswap32(bswap32(x)) == x");
}

// ============================================================================
// Bit Manipulation Tests
// ============================================================================
void test_bit_manipulation()
{
    log_console("\n=== Bit Manipulation Tests ===");
    
    // POPCNT
    test_assert_eq_i64(0, popcnt32(0x00000000), "popcnt32(0) == 0");
    test_assert_eq_i64(1, popcnt32(0x00000001), "popcnt32(1) == 1");
    test_assert_eq_i64(32, popcnt32(0xFFFFFFFF), "popcnt32(0xFFFFFFFF) == 32");
    test_assert_eq_i64(16, popcnt32(0xAAAAAAAA), "popcnt32(0xAAAAAAAA) == 16");
    test_assert_eq_i64(64, popcnt64(0xFFFFFFFFFFFFFFFF), "popcnt64(0xFFFFFFFFFFFFFFFF) == 64");
    
    // LZCNT
    test_assert_eq_i64(32, lzcnt32(0x00000000), "lzcnt32(0) == 32");
    test_assert_eq_i64(31, lzcnt32(0x00000001), "lzcnt32(1) == 31");
    test_assert_eq_i64(0, lzcnt32(0x80000000), "lzcnt32(0x80000000) == 0");
    test_assert_eq_i64(0, lzcnt64(0x8000000000000000), "lzcnt64(0x8000000000000000) == 0");
    
    // TZCNT
    test_assert_eq_i64(32, tzcnt32(0x00000000), "tzcnt32(0) == 32");
    test_assert_eq_i64(0, tzcnt32(0x00000001), "tzcnt32(1) == 0");
    test_assert_eq_i64(31, tzcnt32(0x80000000), "tzcnt32(0x80000000) == 31");
    test_assert_eq_i64(4, tzcnt32(0x00000010), "tzcnt32(0x10) == 4");
}

// ============================================================================
// SSE Logical Tests
// ============================================================================
void test_sse_logical()
{
    log_console("\n=== SSE Logical Tests ===");
    
    array<uint8> a, b, result, expected;
    
    // Setup test vectors
    mm_set1_epi8(0xFF, a);  // All 1s
    mm_set1_epi8(0x00, b);  // All 0s
    
    // XOR
    mm_xor_si128(a, a, result);
    mm_setzero_si128(expected);
    test_assert_array_eq(expected, result, "mm_xor_si128(a, a) == 0");
    
    mm_xor_si128(a, b, result);
    test_assert_array_eq(a, result, "mm_xor_si128(0xFF, 0x00) == 0xFF");
    
    // OR
    mm_or_si128(a, b, result);
    test_assert_array_eq(a, result, "mm_or_si128(0xFF, 0x00) == 0xFF");
    
    // AND
    mm_and_si128(a, b, result);
    test_assert_array_eq(b, result, "mm_and_si128(0xFF, 0x00) == 0x00");
    
    // ANDNOT
    mm_andnot_si128(a, a, result);
    test_assert_array_eq(b, result, "mm_andnot_si128(0xFF, 0xFF) == 0x00");
}

// ============================================================================
// SSE Shift Tests
// ============================================================================
void test_sse_shift()
{
    log_console("\n=== SSE Shift Tests ===");
    
    array<uint8> a, result;
    
    // Test mm_slli_epi64
    mm_set_epi64x(0x0000000000000001, 0x0000000000000001, a);
    mm_slli_epi64(a, 1, result);
    test_assert_eq_i64(2, mm_extract_epi64(result, 0), "mm_slli_epi64 shift left by 1");
    test_assert_eq_i64(2, mm_extract_epi64(result, 1), "mm_slli_epi64 shift left by 1 (high)");
    
    // Test mm_srli_epi64
    mm_set_epi64x(0x8000000000000000, 0x8000000000000000, a);
    mm_srli_epi64(a, 1, result);
    test_assert_eq_i64(0x4000000000000000, mm_extract_epi64(result, 0), "mm_srli_epi64 shift right by 1");
    
    // Test mm_slli_epi32
    mm_set_epi32(1, 1, 1, 1, a);
    mm_slli_epi32(a, 4, result);
    test_assert_eq_i64(16, mm_extract_epi32(result, 0), "mm_slli_epi32 shift left by 4");
    
    // Test mm_srli_epi32
    mm_set_epi32(16, 16, 16, 16, a);
    mm_srli_epi32(a, 4, result);
    test_assert_eq_i64(1, mm_extract_epi32(result, 0), "mm_srli_epi32 shift right by 4");
    
    // Test byte shift (si128)
    mm_set_epi64x(0x0102030405060708, 0x090A0B0C0D0E0F10, a);
    mm_slli_si128(a, 1, result);
    test_assert_eq_i64(0, mm_extract_epi8(result, 0), "mm_slli_si128 byte 0 is 0");
    
    mm_srli_si128(a, 1, result);
    test_assert_eq_i64(0, mm_extract_epi8(result, 15), "mm_srli_si128 byte 15 is 0");
}

// ============================================================================
// SSE Unpack Tests
// ============================================================================
void test_sse_unpack()
{
    log_console("\n=== SSE Unpack Tests ===");
    
    array<uint8> a, b, result;
    
    // Test unpack low epi32
    mm_set_epi32(7, 6, 5, 4, a);
    mm_set_epi32(3, 2, 1, 0, b);
    
    mm_unpacklo_epi32(a, b, result);
    test_assert_eq_i64(4, mm_extract_epi32(result, 0), "mm_unpacklo_epi32 [0]");
    test_assert_eq_i64(0, mm_extract_epi32(result, 1), "mm_unpacklo_epi32 [1]");
    test_assert_eq_i64(5, mm_extract_epi32(result, 2), "mm_unpacklo_epi32 [2]");
    test_assert_eq_i64(1, mm_extract_epi32(result, 3), "mm_unpacklo_epi32 [3]");
    
    mm_unpackhi_epi32(a, b, result);
    test_assert_eq_i64(6, mm_extract_epi32(result, 0), "mm_unpackhi_epi32 [0]");
    test_assert_eq_i64(2, mm_extract_epi32(result, 1), "mm_unpackhi_epi32 [1]");
    test_assert_eq_i64(7, mm_extract_epi32(result, 2), "mm_unpackhi_epi32 [2]");
    test_assert_eq_i64(3, mm_extract_epi32(result, 3), "mm_unpackhi_epi32 [3]");
}

// ============================================================================
// SSE Shuffle Tests 
// ============================================================================
void test_sse_shuffle()
{
    log_console("\n=== SSE Shuffle Tests ===");
    
    array<uint8> a, mask, result;
    
    // Test mm_shuffle_epi32 (pshufd)
    mm_set_epi32(3, 2, 1, 0, a);
    
    // _MM_SHUFFLE(0,1,2,3) = 0x1B - reverse order
    mm_shuffle_epi32(a, 0x1B, result);
    test_assert_eq_i64(3, mm_extract_epi32(result, 0), "mm_shuffle_epi32 reverse [0]");
    test_assert_eq_i64(2, mm_extract_epi32(result, 1), "mm_shuffle_epi32 reverse [1]");
    test_assert_eq_i64(1, mm_extract_epi32(result, 2), "mm_shuffle_epi32 reverse [2]");
    test_assert_eq_i64(0, mm_extract_epi32(result, 3), "mm_shuffle_epi32 reverse [3]");
    
    // Broadcast element 0 to all lanes: _MM_SHUFFLE(0,0,0,0) = 0x00
    mm_shuffle_epi32(a, 0x00, result);
    test_assert_eq_i64(0, mm_extract_epi32(result, 0), "mm_shuffle_epi32 broadcast [0]");
    test_assert_eq_i64(0, mm_extract_epi32(result, 1), "mm_shuffle_epi32 broadcast [1]");
    test_assert_eq_i64(0, mm_extract_epi32(result, 2), "mm_shuffle_epi32 broadcast [2]");
    test_assert_eq_i64(0, mm_extract_epi32(result, 3), "mm_shuffle_epi32 broadcast [3]");
    
    // Test mm_shuffle_epi8 (pshufb) - identity shuffle
    // FIX: Clear arrays first and build fresh 16-byte arrays
    array<uint8> src(16), identity_mask(16);
    for (uint i = 0; i < 16; i++) {
        src[i] = uint8(i * 10);
        identity_mask[i] = uint8(i);
    }
    mm_shuffle_epi8(src, identity_mask, result);
    test_assert_array_eq(src, result, "mm_shuffle_epi8 identity");
    
    // Test mm_shuffle_epi8 with high bit set (zero)
    array<uint8> all_ff(16), high_bit_mask(16);
    for (uint i = 0; i < 16; i++) {
        all_ff[i] = 0xFF;
        high_bit_mask[i] = 0x80; // High bit set = zero output
    }
    mm_shuffle_epi8(all_ff, high_bit_mask, result);
    array<uint8> zeros;
    mm_setzero_si128(zeros);
    test_assert_array_eq(zeros, result, "mm_shuffle_epi8 all zeros with high bit");
}

// ============================================================================
// SSE Arithmetic Tests - FIXED
// ============================================================================
void test_sse_arithmetic()
{
    log_console("\n=== SSE Arithmetic Tests ===");
    
    array<uint8> a, b, result;
    
    // Test add epi32
    // mm_set_epi32(e3, e2, e1, e0) -> [0]=e0, [1]=e1, [2]=e2, [3]=e3
    mm_set_epi32(4, 3, 2, 1, a);  // [0]=1, [1]=2, [2]=3, [3]=4
    mm_set_epi32(1, 1, 1, 1, b);  // [0]=1, [1]=1, [2]=1, [3]=1
    mm_add_epi32(a, b, result);
    test_assert_eq_i64(2, mm_extract_epi32(result, 0), "mm_add_epi32 [0]");  // 1+1=2
    test_assert_eq_i64(3, mm_extract_epi32(result, 1), "mm_add_epi32 [1]");  // 2+1=3
    test_assert_eq_i64(4, mm_extract_epi32(result, 2), "mm_add_epi32 [2]");  // 3+1=4
    test_assert_eq_i64(5, mm_extract_epi32(result, 3), "mm_add_epi32 [3]");  // 4+1=5
    
    // Test sub epi32
    mm_sub_epi32(a, b, result);
    test_assert_eq_i64(0, mm_extract_epi32(result, 0), "mm_sub_epi32 [0]");  // 1-1=0
    test_assert_eq_i64(1, mm_extract_epi32(result, 1), "mm_sub_epi32 [1]");  // 2-1=1 (FIXED expectation)
    test_assert_eq_i64(2, mm_extract_epi32(result, 2), "mm_sub_epi32 [2]");  // 3-1=2
    test_assert_eq_i64(3, mm_extract_epi32(result, 3), "mm_sub_epi32 [3]");  // 4-1=3
    
    // Test add epi64
    mm_set_epi64x(100, 200, a);
    mm_set_epi64x(1, 2, b);
    mm_add_epi64(a, b, result);
    test_assert_eq_i64(202, mm_extract_epi64(result, 0), "mm_add_epi64 [0]");
    test_assert_eq_i64(101, mm_extract_epi64(result, 1), "mm_add_epi64 [1]");
    
    // Test multiply epi32
    mm_set_epi32(4, 3, 2, 1, a);
    mm_set_epi32(10, 10, 10, 10, b);
    mm_mullo_epi32(a, b, result);
    test_assert_eq_i64(10, mm_extract_epi32(result, 0), "mm_mullo_epi32 [0]");
    test_assert_eq_i64(20, mm_extract_epi32(result, 1), "mm_mullo_epi32 [1]");
    test_assert_eq_i64(30, mm_extract_epi32(result, 2), "mm_mullo_epi32 [2]");
    test_assert_eq_i64(40, mm_extract_epi32(result, 3), "mm_mullo_epi32 [3]");
}
// ============================================================================
// SSE Set/Extract Tests
// ============================================================================
void test_sse_set_extract()
{
    log_console("\n=== SSE Set/Extract Tests ===");
    
    array<uint8> a;
    
    // Test set and extract epi64
    mm_set_epi64x(0xDEADBEEFCAFEBABE, 0x123456789ABCDEF0, a);
    test_assert_eq_i64(0x123456789ABCDEF0, mm_extract_epi64(a, 0), "mm_set/extract_epi64 [0]");
    test_assert_eq_i64(0xDEADBEEFCAFEBABE, mm_extract_epi64(a, 1), "mm_set/extract_epi64 [1]");
    
    // Test set1 (broadcast)
    mm_set1_epi32(42, a);
    test_assert_eq_i64(42, mm_extract_epi32(a, 0), "mm_set1_epi32 [0]");
    test_assert_eq_i64(42, mm_extract_epi32(a, 1), "mm_set1_epi32 [1]");
    test_assert_eq_i64(42, mm_extract_epi32(a, 2), "mm_set1_epi32 [2]");
    test_assert_eq_i64(42, mm_extract_epi32(a, 3), "mm_set1_epi32 [3]");
    
    // Test setzero
    mm_setzero_si128(a);
    test_assert_eq_i64(0, mm_extract_epi64(a, 0), "mm_setzero [0]");
    test_assert_eq_i64(0, mm_extract_epi64(a, 1), "mm_setzero [1]");
    
    // Test broadcast helpers
    broadcast_qword(0xCAFEBABE, a);
    test_assert_eq_i64(0xCAFEBABE, mm_extract_epi64(a, 0), "broadcast_qword [0]");
    test_assert_eq_i64(0xCAFEBABE, mm_extract_epi64(a, 1), "broadcast_qword [1]");
}

// ============================================================================
// SSE Compare Tests
// ============================================================================
void test_sse_compare()
{
    log_console("\n=== SSE Compare Tests ===");
    
    array<uint8> a, b, result;
    
    mm_set_epi32(4, 3, 2, 1, a);
    mm_set_epi32(4, 0, 2, 0, b);
    
    mm_cmpeq_epi32(a, b, result);
    test_assert_eq_i64(0, mm_extract_epi32(result, 0), "mm_cmpeq_epi32 1!=0");
    test_assert_eq_i64(-1, mm_extract_epi32(result, 1), "mm_cmpeq_epi32 2==2 -> 0xFFFFFFFF");
    test_assert_eq_i64(0, mm_extract_epi32(result, 2), "mm_cmpeq_epi32 3!=0");
    test_assert_eq_i64(-1, mm_extract_epi32(result, 3), "mm_cmpeq_epi32 4==4 -> 0xFFFFFFFF");
}

// ============================================================================
// Real-world Pointer Decryption Test
// ============================================================================
void test_pointer_decryption_simulation()
{
    log_console("\n=== Pointer Decryption Simulation ===");
    
    // Simulate a simple XOR + ROL pointer decryption
    uint64 encrypted = 0xDEADBEEFCAFEBABE;
    uint64 key = 0x1234567890ABCDEF;
    int rotation = 17;
    
    // Encrypt: ROL then XOR
    uint64 temp = rol64(encrypted, rotation);
    uint64 decrypted_test = temp ^ key;
    
    // Decrypt: XOR then ROR
    temp = decrypted_test ^ key;
    uint64 recovered = ror64(temp, rotation);
    
    test_assert_eq_u64(encrypted, recovered, "ROL/XOR encrypt-decrypt cycle");
    
    // More complex: using SSE for parallel operations
    array<uint8> data, xor_key, result;
    
    mm_set_epi64x(0x1111111111111111, 0x2222222222222222, data);
    mm_set_epi64x(0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF, xor_key);
    
    mm_xor_si128(data, xor_key, result);
    test_assert_eq_i64(~0x2222222222222222, mm_extract_epi64(result, 0), "SSE XOR decryption [0]");
    test_assert_eq_i64(~0x1111111111111111, mm_extract_epi64(result, 1), "SSE XOR decryption [1]");
}

// ============================================================================
// Main Entry Point
// ============================================================================
int main()
{
    log_console("========================================");
    log_console("  SSE Intrinsics API Test Suite");
    log_console("========================================");
    
    test_bit_rotation();
    test_byte_swap();
    test_bit_manipulation();
    test_sse_logical();
    test_sse_shift();
    test_sse_shuffle();
    test_sse_unpack();
    test_sse_arithmetic();
    test_sse_set_extract();
    test_sse_compare();
    test_pointer_decryption_simulation();
    
    log_console("\n========================================");
    log_console("  Test Results");
    log_console("========================================");
    log_console("Passed: " + g_tests_passed);
    log_console("Failed: " + g_tests_failed);
    
    if (g_tests_failed == 0) {
        log("All SSE Intrinsics tests PASSED!");
    } else {
        log_error("Some tests FAILED - check console for details");
    }
    
    return 0;
}

```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/intrinsics.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/json-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/json-api.md).

# Json API

The AngelScript JSON API provides robust parsing and encoding of JSON directly into native AngelScript structures.\
JSON objects map to **dictionary** objects, using standard AngelScript types.

This API mirrors the Lua JSON API and is designed to behave identically where possible.

***

### Overview

Available functions:

| Function                             | Description                               |
| ------------------------------------ | ----------------------------------------- |
| `json_parse(text, result, error)`    | Parse JSON text into a `dictionary`       |
| `json_decode(text, result, error)`   | Alias of `json_parse`                     |
| `json_stringify(value, json, error)` | Convert a `dictionary` into a JSON string |
| `json_encode(value, json, error)`    | Alias of `json_stringify`                 |

All functions return **true on success** and **false on failure**, with detailed error messages.

***

### JSON → Dictionary

#### `bool json_parse(const string &in text, dictionary &out result, string &out error)`

#### `bool json_decode(const string &in text, dictionary &out result, string &out error)`

Parses a JSON string and converts it into a nested AngelScript `dictionary`.

#### Parameters

| Name     | Type         | Description                                 |
| -------- | ------------ | ------------------------------------------- |
| `text`   | `string`     | JSON text to parse                          |
| `result` | `dictionary` | Output dictionary filled with parsed values |
| `error`  | `string`     | Error message if the function fails         |

#### JSON → AngelScript Type Mapping

| JSON                 | AngelScript                       |
| -------------------- | --------------------------------- |
| Object `{}`          | `dictionary` (recursively nested) |
| String `"text"`      | `string`                          |
| Number `123`, `4.5`  | `double`                          |
| Boolean `true/false` | `double` (`1.0`/`0.0`)            |
| null                 | *field omitted*                   |
| Array `[...]`        | *(currently skipped)*             |

#### Example

```cpp
dictionary d;
string err;

bool ok = json_parse("{\"a\":1, \"b\":\"hello\"}", d, err);
if (!ok)
{
    log_error("JSON parse failed: " + err);
    return;
}

double a;
string b;

d.get("a", a);    // 1.0
d.get("b", b);    // "hello"
```

***

### Dictionary → JSON

#### `bool json_stringify(const dictionary &in value, string &out json, string &out error)`

#### `bool json_encode(const dictionary &in value, string &out json, string &out error)`

Converts a dictionary (and any nested dictionaries) into valid JSON text.

#### Parameters

| Name    | Type         | Description                         |
| ------- | ------------ | ----------------------------------- |
| `value` | `dictionary` | The object to convert into JSON     |
| `json`  | `string`     | Output JSON text                    |
| `error` | `string`     | Error message if the function fails |

#### AngelScript → JSON Type Mapping

| AngelScript        | JSON        |
| ------------------ | ----------- |
| `double`           | number      |
| `string`           | string      |
| `bool`             | boolean     |
| `dictionary@`      | JSON object |
| `null dictionary@` | `null`      |
| *(any other type)* | error       |

#### Example

```cpp
dictionary d;
d.set("name", "Player1");
d.set("score", 120.0);
d.set("alive", true);

string json;
string err;

if (!json_stringify(d, json, err))
{
    log_error("Stringify failed: " + err);
}
else
{
    log("JSON: " + json);
}
```

Output:

```cpp
{"name":"Player1","score":120,"alive":true}
```

***

### Nesting Example

JSON objects automatically map to nested dictionaries:

```cpp
string text = """
{
    "player": {
        "name": "Alice",
        "pos": { "x": 10, "y": 20 }
    }
}
""";

dictionary root;
string err;

json_parse(text, root, err);

dictionary@ player;
root.get("player", @player);

string name;
dictionary@ pos;
double px, py;

player.get("name", name);
player.get("pos", @pos);
pos.get("x", px);
pos.get("y", py);
```

***

### Null Behavior

JSON `null` becomes **nonexistent key**:

```cpp
{"a":1,"b":null,"c":2}
```

Becomes:

```cpp
d.exists("a") == true
d.exists("b") == false
d.exists("c") == true
```

***

### Unsupported Types

The AngelScript dictionary can technically store any type, but the JSON stringifier only supports:

* `double`
* `string`
* `bool`
* `dictionary@`

Anything else causes:

```cpp
json_stringify: unsupported value type in dictionary
```

***

### Arrays

JSON arrays (`[ ... ]`) are **currently skipped**.\
If you need them, support can be added using `array<T>` or `CScriptArray`.

***

### Full Roundtrip Example

```cpp
dictionary d;
d.set("value", 123.0);
d.set("name", "Test");
d.set("ok", true);

dictionary inner;
inner.set("x", 10.0);
inner.set("y", 20.0);
d.set("pos", @inner);

string json, err;
json_stringify(d, json, err);

// parse it back
dictionary back;
json_parse(json, back, err);
```

***

### Full API Test

```cpp
void DumpDict(const string &in label, dictionary &in d)
{
    log(label);
    
    array<string>@ keys = d.getKeys();
    for (uint i = 0; i < keys.length(); i++)
    {
        string k = keys[i];
        // Try double first
        double dv;
        string sv;
        bool gotDouble = d.get(k, dv);
        bool gotString = d.get(k, sv);
        
        string vStr;
        if (gotDouble)
        vStr = "double " + k + " = " + dv;
        else if (gotString)
        vStr = "string " + k + " = \"" + sv + "\"";
        else
        vStr = "key " + k + " (unsupported type in dump)";
        
        log("  " + vStr);
    }
}

void TestBasicParse()
{
    log("[1] Basic json_parse / json_decode");
    
    const string jsonText = """
    {
        "number": 123,
        "float":  3.14,
        "bool_true": true,
        "bool_false": false,
        "text": "hello",
        "object": { "x": 10, "y": 20 }
    }
    """;
    
    dictionary d;
    string err;
    
    if (!json_parse(jsonText, d, err))
    {
        log_error("  [FAIL] json_parse failed: " + err);
        return;
    }
    log("  [ OK ] json_parse succeeded");
    DumpDict("  Dump of parsed dictionary:", d);
    
    // Basic checks
    double num = 0;
    double flt = 0;
    string txt;
    
    if (d.get("number", num) && num == 123)
    log("  [ OK ] number == 123");
    else
    log_error("  [FAIL] number != 123");
    
    if (d.get("float", flt) && flt > 3.13 && flt < 3.15)
    log("  [ OK ] float ~= 3.14");
    else
    log_error("  [FAIL] float ~= 3.14");
    
    if (d.get("text", txt) && txt == "hello")
    log("  [ OK ] text == \"hello\"");
    else
    log_error("  [FAIL] text != \"hello\"");
    
    // bools are stored as doubles (1.0 / 0.0)
    double bt = 0, bf = 1;
    d.get("bool_true", bt);
    d.get("bool_false", bf);
    if (bt == 1.0 && bf == 0.0)
    log("  [ OK ] bool_true/false mapped to 1.0/0.0");
    else
    log_error("  [FAIL] bool mapping incorrect");
    
    // Test alias json_decode
    dictionary d2;
    string err2;
    if (json_decode("{\"a\":1,\"b\":2}", d2, err2))
    log("  [ OK ] json_decode succeeded");
    else
    log_error("  [FAIL] json_decode failed: " + err2);
}

void TestInvalidParse()
{
    log("\n[2] Invalid JSON parse test");
    
    dictionary d;
    string err;
    
    const string badJson = "{ invalid json !!! }";
    bool ok = json_parse(badJson, d, err);
    if (!ok)
    {
        log("  [ OK ] json_parse returned false for invalid JSON");
        log("        error: " + err);
    }
    else
    {
        log_error("  [FAIL] json_parse unexpectedly succeeded on invalid JSON");
    }
}

void TestStringifyRoundtrip()
{
    log("\n[3] json_stringify / json_encode roundtrip");
    
    dictionary d;
    d.set("hello", "world");
    d.set("num", 42.0);          // numbers are stored as double
    d.set("float", 1.5);
    d.set("flag_bool", true);    // bool (script side)
    d.set("flag_num", 1.0);      // numeric boolean
    
    // nested object
    dictionary nested;
    nested.set("x", 10.0);
    nested.set("y", 20.0);
    d.set("nested", @nested);
    
    DumpDict("  Original dictionary:", d);
    
    string json;
    string err;
    
    if (!json_stringify(d, json, err))
    {
        log_error("  [FAIL] json_stringify failed: " + err);
        return;
    }
    
    log("  [ OK ] json_stringify succeeded");
    log("  JSON: " + json);
    
    // Roundtrip: parse back
    dictionary back;
    string err2;
    if (!json_parse(json, back, err2))
    {
        log_error("  [FAIL] parse(stringify(...)) failed: " + err2);
        return;
    }
    
    log("  [ OK ] parse(stringify(...)) succeeded");
    DumpDict("  Decoded dictionary:", back);
    
    // Test alias json_encode
    string json2, err3;
    if (json_encode(d, json2, err3))
    log("  [ OK ] json_encode succeeded: " + json2);
    else
    log_error("  [FAIL] json_encode failed: " + err3);
}

void TestNullAndArrays()
{
    log("\n[4] Null and array handling note");
    
    const string txt = """
    {
        "a": 1,
        "b": null,
        "c": [1,2,3]
    }
    """;
    
    dictionary d;
    string err;
    
    if (!json_parse(txt, d, err))
    {
        log_error("  [FAIL] parse failed: " + err);
        return;
    }
    
    DumpDict("  Parsed dictionary:", d);
    
    // "b" is null -> omitted
    double a = 0;
    bool hasB = d.exists("b");
    d.get("a", a);
    
    if (a == 1.0 && !hasB)
    log("  [ OK ] null field skipped, 'a' present");
    else
    log_error("  [FAIL] null or 'a' handling incorrect");
    
    // "c" is an array -> currently skipped
    if (!d.exists("c"))
    log("  [ OK ] array key 'c' skipped as expected");
    else
    log_error("  [FAIL] array key 'c' unexpectedly present");
}

int main()
{
    log("=== JSON API Test Begin (AngelScript) ===");
    
    TestBasicParse();
    TestInvalidParse();
    TestStringifyRoundtrip();
    TestNullAndArrays();
    
    log("=== JSON API Test End ===");
    return 0;
}

```

***

### Summary of Functions

| Function                             | Description                |
| ------------------------------------ | -------------------------- |
| `json_parse(text, result, error)`    | Parse JSON into dictionary |
| `json_decode(text, result, error)`   | Alias of parse             |
| `json_stringify(value, json, error)` | Convert dictionary to JSON |
| `json_encode(value, json, error)`    | Alias of stringify         |


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/json-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/life-cycle.md`

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

---

## Source: `docs/perception/angelscript/mutex-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/mutex-api.md).

# Mutex API

The Mutex API provides lightweight thread synchronization inside AngelScript.\
Mutex objects are native engine primitives exposed as `mutex_t` handles.\
They support:

* **Exclusive locks (writers)**
* **Shared locks (readers)**
* **Non-blocking try-lock operations**
* **Automatic cleanup on script shutdown**

Mutexes are created by `create_mutex()` and manually released using `destroy()`

***

### 🔑 Creating Mutexes

#### Create

```cpp
mutex_t create_mutex();
```

Creates a new mutex and registers it with the current AngelScript context.

Example:

```cpp
mutex_t m = create_mutex();
```

#### Destroy

```cpp
void mutex_t::destroy();
```

Frees the underlying native mutex.

> **Note:** If the script forgets to call `destroy()`, the PCX engine frees all remaining mutexes when the script context unloads.

Example:

```cpp
m.destroy();
```

***

### 🔐 Exclusive Lock (Writer Lock)

Use these when only one thread should modify shared state.

#### Lock (blocking)

```cpp
void mutex_t::lock();
```

Blocks until exclusive ownership is acquired.

#### Try Lock (non-blocking)

```cpp
bool mutex_t::try_lock();
```

Returns `true` if the lock is acquired immediately, `false` otherwise.

#### Unlock

```cpp
void mutex_t::unlock();
```

Releases the exclusive lock.

***

### 📖 Shared Lock (Reader Lock)

Shared locks allow **multiple readers**, but automatically block if an exclusive writer holds the lock.

#### Lock Shared (blocking)

```cpp
void mutex_t::lock_shared();
```

Blocks until a shared lock is available.

#### Try Lock Shared (non-blocking)

```cpp
bool mutex_t::try_lock_shared();
```

Returns immediately with `true` on success.

#### Unlock Shared

```cpp
void mutex_t::unlock_shared();
```

Releases the shared lock.

***

### 🧩 Usage Example

```cpp
mutex_t g_mtx = create_mutex();

int sharedValue = 0;

void writer_thread(int callback_id, int data_index)
{
    g_mtx.lock();
    log("[writer] acquired exclusive lock");
    
    sharedValue += 10;
    
    g_mtx.unlock();
    log("[writer] released lock");
}

void reader_thread(int callback_id, int data_index)
{
    if (g_mtx.try_lock_shared())
    {
        log("[reader] acquired shared lock");
        int v = sharedValue;  // safe read
        g_mtx.unlock_shared();
        log("[reader] released shared lock");
    }
    else
    {
        log("[reader] shared lock unavailable");
    }
}

int main()
{
    
    register_callback(writer_thread, 1, 0);
    register_callback(reader_thread, 1, 0);
    return 1;
}

void on_unload()
{
    log("unloaded");
    // Optional: manual cleanup
    g_mtx.destroy();
}

```

***

### 🗑 Automatic Cleanup

Even if a script forgets:

```cpp
mutex_t m = create_mutex();
// ... never calls m.destroy()
```

PCX will:

* Free each `mtx_t` safely
* Avoid leaks and invalid handles

***

### Avoid Deadlocks!

* You must avoid deadlocks
* If an exception happens and the active thread had a lock, It will cause a deadlock
* Use the following try & catch logic to avoid it.

```cpp
mutex_t g_example_mutex;

// A safe function that guarantees the mutex is always unlocked.
void do_work_safe(bool should_throw)
{
    log("Attempting to lock the mutex...");
    g_example_mutex.lock();
    log("Mutex locked.");

    try
    {
        if (should_throw)
        {
            log("An error occurred! Throwing an exception...");
            throw("Error");
        }
    }
    catch
    {
        log("Caught an exception, but the unlock call will still be reached.");
    }

    // This code is now guaranteed to run, preventing a deadlock.
    g_example_mutex.unlock();
    log("Mutex unlocked.");
}

void main()
{
    g_example_mutex = create_mutex();

    // 1. Call the function and make it throw an exception.
    //    The function will catch its own exception and unlock the mutex.
    do_work_safe(true);
    
    // 2. Call it again. This will now succeed because the mutex was released.
    log("Calling the function again. This will work correctly.");
    do_work_safe(false);

    log("Program finished successfully.");
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/mutex-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/net-api.md`

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

---

## Source: `docs/perception/angelscript/overview.md`

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

---

## Source: `docs/perception/angelscript/proc-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/proc-api.md).

# Proc API

The Proc API lets AngelScript access and edit memory of external processes using a lightweight handle type `proc_t`.

***

#### 🔑 Process Handles

***

**Referencing Processes**

```cpp
proc_t ref_process(uint pid)
proc_t ref_process(const string &in name)
```

* `pid` – Windows process ID.
* `name` – Executable name (`"notepad.exe"`, `"cs2.exe"`, etc).

Returns a `proc_t` handle, or `0` if the process could not be opened.

***

**Releasing Handles**

```cpp
void proc_t::deref()
```

Decrements the internal reference and clears the handle.\
After calling `deref()`, the handle becomes invalid (further calls are no-ops).

You must also call `deref()` if `proc_t::alive()` returns `false`.

***

#### 🧬 Process Info

```cpp
uint64 proc_t::base_address() const
uint64 proc_t::peb()          const
uint   proc_t::pid()          const
bool   proc_t::alive()        const
```

* `base_address()` – Image base (module base) of the process.
* `peb()` – Address of the process' PEB.
* `pid()` – Process ID.
* `alive()` – Determines whether the process is currently alive and running.

***

#### Address Validity

```cpp
bool   proc_t::is_valid_address(uint64 address)     const
```

Check if an address is mapped inside target process.

***

#### 📖 Scalar Reads

All addresses are **virtual addresses** in the target process.

**Unsigned Integers**

```cpp
uint8  proc_t::ru8 (uint64 addr) const
uint16 proc_t::ru16(uint64 addr) const
uint32 proc_t::ru32(uint64 addr) const
uint64 proc_t::ru64(uint64 addr) const
```

Reads unsigned integer values at `addr`.

***

**Signed Integers**

```cpp
int8  proc_t::r8 (uint64 addr) const
int16 proc_t::r16(uint64 addr) const
int32 proc_t::r32(uint64 addr) const
int64 proc_t::r64(uint64 addr) const
```

Reads signed integer values at `addr`.

***

**Floating-Point**

```cpp
float  proc_t::rf32(uint64 addr) const
double proc_t::rf64(uint64 addr) const
```

Reads `float` / `double` from `addr`.

***

#### ✏️ Scalar Writes

**Unsigned Integers**

```cpp
bool proc_t::wu8 (uint64 addr, uint8  v)
bool proc_t::wu16(uint64 addr, uint16 v)
bool proc_t::wu32(uint64 addr, uint32 v)
bool proc_t::wu64(uint64 addr, uint64 v)
```

Writes unsigned integer values.\
Returns `true` on success.

***

**Signed Integers**

```cpp
bool proc_t::w8 (uint64 addr, int8  v)
bool proc_t::w16(uint64 addr, int16 v)
bool proc_t::w32(uint64 addr, int32 v)
bool proc_t::w64(uint64 addr, int64 v)
```

Writes signed integer values.

***

**Floating-Point**

```cpp
bool proc_t::wf32(uint64 addr, float  v)
bool proc_t::wf64(uint64 addr, double v)
```

Writes `float` / `double`.

***

#### 🔤 Strings

All string helpers assume **null-terminated** memory on the remote side (for reads) and write a terminating null when writing.

**Reading Strings**

```cpp
string proc_t::rs (uint64 addr, int max_chars) const
string proc_t::rws(uint64 addr, int max_chars) const
```

* `rs` – Reads an ANSI/UTF-8 style string from `addr`.
* `rws` – Reads a UTF-16 wide string, converts to UTF-8 `string`.

`max_chars` is a hard cap to avoid walking off invalid memory.

***

**Writing Strings**

```cpp
bool proc_t::ws (uint64 addr, const string &in text)
bool proc_t::wws(uint64 addr, const string &in text)
```

* `ws` – Writes `text` as ANSI/UTF-8 bytes plus trailing `\0`.
* `wws` – Converts `text` to UTF-16 and writes wide string plus trailing `L'\0'`.

Returns `true` on success.

***

#### 📦 Raw Memory (byte arrays)

Uses `array<uint8>` for bulk reads/writes.

```cpp
void proc_t::rvm(uint64 addr, uint size, array<uint8> &out out_buf)
bool proc_t::wvm(uint64 addr, const array<uint8> &in in_buf)
```

* `rvm` – Reads `size` bytes starting at `addr` into `out_buf`.\
  `out_buf` is resized to `size`.
* `wvm` – Writes bytes from `in_buf` to `addr`.\
  Returns `true` if all bytes were written.

***

#### 🧮 SIMD Helpers

Convenience wrappers around 16/32/64-byte vectors (`__m128/__m256/__m512`).\
All data is exposed as raw bytes.

```cpp
void proc_t::r128(uint64 addr, array<uint8> &out out16) const
void proc_t::r256(uint64 addr, array<uint8> &out out32) const
void proc_t::r512(uint64 addr, array<uint8> &out out64) const

bool proc_t::w128(uint64 addr, const array<uint8> &in in16)
bool proc_t::w256(uint64 addr, const array<uint8> &in in32)
bool proc_t::w512(uint64 addr, const array<uint8> &in in64)
```

* `r128`/`r256`/`r512` – Read 16/32/64 bytes into the output array (array is resized).
* `w128`/`w256`/`w512` – Write 16/32/64 bytes from the input array.\
  Returns `false` if the array is too small or the write fails.

***

#### Thread Environment Blocks (TEB)

**`array<uint64>@ proc_t::get_all_tebs() const`**

Returns a list of **TEB (Thread Environment Block) addresses** for all threads currently discovered in the target process.

**Signature**

```
array<uint64>@ proc_t::get_all_tebs() const
```

**Returns**

* `array<uint64>` — `{ teb1, teb2, ... }`
  * Each entry is a **virtual address** of a TEB in the target process.
  * Returns null if no threads are found or enumeration fails.

***

#### 📦 Modules & Pattern Scans

**Module Lookup**

```cpp
bool proc_t::get_module(
    const string &in name,
    uint64 &out module_base,
    uint64 &out module_size
)
```

Looks up a module by name (e.g. `"notepad.exe"`, `"client.dll"`):

* On success:
  * `module_base` – Base address of the module.
  * `module_size` – Size in bytes.
  * Returns `true`.
* Returns `false` if the module is not found.

***

**Code Pattern Search**

```cpp
uint64 proc_t::find_code_pattern(
    uint64 search_start,
    uint64 search_size,
    const string &in signature
)

void proc_t::find_all_code_patterns(
    uint64 search_start,
    uint64 search_size,
    const string &in signature,
    array<uint64> &out result
)
```

Scans `[search_start, search_start + search_size)` for a textual pattern:

* `signature` – Pattern string, e.g. `"48 8B ?? ?? ?? 89"`\
  (exact format is the same as used internally by your pattern scanner).
* `find_code_pattern` returns the **address of the first match**, or `0` if not found.
* `find_all_code_patterns` populates `result` with **all** matching addresses.

***

#### 🔍 Example: Scanning Notepad

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (p.pid() == 0)
    {
        log("Failed to reference notepad.exe");
        return 0;
    }

    uint64 base = p.base_address();
    log("PID  = " + p.pid());
    log("Base = 0x" + formatUInt(base, "0H", 16));

    // Read the first two bytes ("MZ")
    uint8 b0 = p.ru8(base);
    uint8 b1 = p.ru8(base + 1);
    log("Header Bytes: "
        + formatUInt(b0, "0H", 2) + " "
        + formatUInt(b1, "0H", 2));

    // Dump first 16 bytes
    array<uint8> bytes;
    p.rvm(base, 16, bytes);

    string dump;
    for (uint i = 0; i < bytes.length(); i++)
    {
        if (i > 0) dump += " ";
        dump += formatUInt(bytes[i], "0H", 2);
    }
    log("DOS Header (16 bytes): " + dump);

    // Find module + pattern "4D 5A" (MZ signature)
    uint64 modBase, modSize;
    if (p.get_module("notepad.exe", modBase, modSize))
    {
        log("Module Base = 0x" + formatUInt(modBase, "0H", 16));
        log("Module Size = 0x" + formatUInt(modSize, "0H", 16));

        uint64 addr = p.find_code_pattern(modBase, modSize, "4D 5A");
        log("Pattern '4D 5A' found at 0x" + formatUInt(addr, "0H", 16));
    }
    else
    {
        log("Module not found");
    }

    p.deref();
    return 0;
}
```

***

### Process Struct Helpers

These helpers let you describe a C-style structure in a `dictionary` and read it.

***

#### 📦 Struct Descriptor (common concept)

A **struct descriptor** is a `dictionary` where each entry:

* Key = field name (string)
* Value = another `dictionary` with:
  * `"offset"` – byte offset from struct base (int64)
  * `"type"` – field type string (`"u16"`, `"i32"`, `"f32"`, etc.)
  * *(optional)* `"max_chars"` for string fields

Example:

```cpp
dictionary PLAYER_DESC;

void init_player_desc()
{
    dictionary@ health = { {"offset", int64(0x10)}, {"type", "i32"} };
    dictionary@ armor  = { {"offset", int64(0x14)}, {"type", "i32"} };
    dictionary@ pos_x  = { {"offset", int64(0x30)}, {"type", "f32"} };
    dictionary@ pos_y  = { {"offset", int64(0x34)}, {"type", "f32"} };
    dictionary@ pos_z  = { {"offset", int64(0x38)}, {"type", "f32"} };

    PLAYER_DESC.set("health", @health);
    PLAYER_DESC.set("armor",  @armor);
    PLAYER_DESC.set("pos_x",  @pos_x);
    PLAYER_DESC.set("pos_y",  @pos_y);
    PLAYER_DESC.set("pos_z",  @pos_z);
}
```

**Supported field types**

| Type        | Size | Meaning                  |
| ----------- | ---- | ------------------------ |
| `"u8"`      | 1    | unsigned 8-bit           |
| `"u16"`     | 2    | unsigned 16-bit          |
| `"u32"`     | 4    | unsigned 32-bit          |
| `"u64"`     | 8    | unsigned 64-bit          |
| `"i8"`      | 1    | signed 8-bit             |
| `"i16"`     | 2    | signed 16-bit            |
| `"i32"`     | 4    | signed 32-bit            |
| `"i64"`     | 8    | signed 64-bit            |
| `"f32"`     | 4    | 32-bit float             |
| `"f64"`     | 8    | 64-bit double            |
| `"string"`  | var  | UTF-8 C-string in target |
| `"wstring"` | var  | UTF-16 string → UTF-8    |

For `"string"` / `"wstring"`, you can add `"max_chars"` to limit how many characters are read (default \~256, clamped to 1..8192).

***

#### 📘 `bool proc_t::read_struct(uint64 addr, dictionary &out result, const dictionary &in desc)`

Reads **one** structure instance from the target process into an existing `dictionary`.

**Signature**

```cpp
bool read_struct(uint64 addr,
                 dictionary &out result,
                 const dictionary &in desc) const
```

**Parameters**

* `addr`\
  Absolute address of the struct in the remote process.
* `result`\
  Dictionary that will be **filled** with the decoded fields.\
  (Existing contents are cleared before filling.)
* `desc`\
  Struct descriptor `dictionary` described above.

**Return**

* `true` on success
* `false` on failure (invalid process handle, invalid descriptor, etc.)

**Stored value types**

To keep things simple (and consistent with your JSON API):

* All integer fields are stored as **`int64`**
* All float fields are stored as **`double`**
* String fields are stored as script **`string`**

So you can safely read with:

```cpp
int64  i;   result.get("field", i);
double d;   result.get("field", d);
string s;   result.get("field", s);
```

You can also read into `uint64` etc. – the dictionary will convert as needed.

***

**Example – Read one player struct**

```cpp
void example_read_player()
{
    init_player_desc();

    proc_t p = ref_process("somegame.exe");

    uint64 base, size;
    p.get_module("somegame.exe", base, size);

    dictionary player;
    if (!p.read_struct(base + 0x123456, player, PLAYER_DESC))
    {
        log("read_struct failed");
        return;
    }

    int64 health;
    player.get("health", health);

    log("Health = " + health);
}
```

***

#### 📘 `bool proc_t::read_struct_array(uint64 base, uint count, uint size, array<dictionary>@ &out result, const dictionary &in desc)`

Reads an **array** of structures into an `array<dictionary>`.

**Signature**

```cpp
bool read_struct_array(uint64 base,
                       uint count,
                       uint size,
                       array<dictionary>@ &out result,
                       const dictionary &in desc) const
```

**Parameters**

* `base`\
  Address of the **first** element.
* `count`\
  Number of elements to read.
* `size`\
  Size in bytes of each element in the array (`sizeof(struct)`).
* `result`\
  `array<dictionary>` that will be resized to `count`.\
  Each element will be filled with that struct's data. If an element is `null` internally, it is created.
* `desc`\
  Same struct descriptor as for `read_struct`.

**Return**

* `true` on success
* `false` if the process is invalid, `count`/`size` is 0, etc.

**Example – Player list**

```cpp
void example_read_players()
{
    init_player_desc();

    proc_t p = ref_process("somegame.exe");

    uint64 base = 0x20000000;
    uint   count = 32;
    uint   structSize = 0x140;

    array<dictionary> players;
    if (!p.read_struct_array(base, count, structSize, players, PLAYER_DESC))
    {
        log("read_struct_array failed");
        return;
    }

    for (uint i = 0; i < players.length(); i++)
    {
        dictionary@ pl = players[i];

        int64  hp   = 0;
        double px   = 0.0;
        pl.get("health", hp);
        pl.get("pos_x", px);

        log("Player " + i + " hp=" + hp + " pos_x=" + px);
    }
}
```

***

### 🧪 Full Example Script – Read `IMAGE_DOS_HEADER` from notepad.exe

This is a complete AngelScript file you can drop into your environment.\
It:

1. Builds a DOS header descriptor
2. Uses `proc_t.read_struct` to read it from `notepad.exe`
3. Prints all key fields and the computed NT header address

```cpp
dictionary DOS_HEADER;

string to_hex16(uint v)
{
    const string HEX = "0123456789ABCDEF";
    string hex16 = "0000";
    for (int i = 0; i < 4; i++)
    {
        uint nibble = (v >> ((3 - i) * 4)) & 0xF;
        hex16[i] = HEX[nibble];
    }
    return hex16;
}

string to_hex32(uint v)
{
    const string HEX = "0123456789ABCDEF";
    string hex32 = "00000000";
    for (int i = 0; i < 8; i++)
    {
        uint nibble = (v >> ((7 - i) * 4)) & 0xF;
        hex32[i] = HEX[nibble];
    }
    return hex32;
}

void init_dos_descriptor()
{
    dictionary@ e_magic    = { {"offset", int64(0x00)}, {"type", "u16"} };
    dictionary@ e_cblp     = { {"offset", int64(0x02)}, {"type", "u16"} };
    dictionary@ e_cp       = { {"offset", int64(0x04)}, {"type", "u16"} };
    dictionary@ e_crlc     = { {"offset", int64(0x06)}, {"type", "u16"} };
    dictionary@ e_cparhdr  = { {"offset", int64(0x08)}, {"type", "u16"} };
    dictionary@ e_minalloc = { {"offset", int64(0x0A)}, {"type", "u16"} };
    dictionary@ e_maxalloc = { {"offset", int64(0x0C)}, {"type", "u16"} };
    dictionary@ e_ss       = { {"offset", int64(0x0E)}, {"type", "u16"} };
    dictionary@ e_sp       = { {"offset", int64(0x10)}, {"type", "u16"} };
    dictionary@ e_csum     = { {"offset", int64(0x12)}, {"type", "u16"} };
    dictionary@ e_ip       = { {"offset", int64(0x14)}, {"type", "u16"} };
    dictionary@ e_cs       = { {"offset", int64(0x16)}, {"type", "u16"} };
    dictionary@ e_lfarlc   = { {"offset", int64(0x18)}, {"type", "u16"} };
    dictionary@ e_ovno     = { {"offset", int64(0x1A)}, {"type", "u16"} };

    dictionary@ e_lfanew   = { {"offset", int64(0x3C)}, {"type", "u32"} };

    DOS_HEADER.set("e_magic",    @e_magic);
    DOS_HEADER.set("e_cblp",     @e_cblp);
    DOS_HEADER.set("e_cp",       @e_cp);
    DOS_HEADER.set("e_crlc",     @e_crlc);
    DOS_HEADER.set("e_cparhdr",  @e_cparhdr);
    DOS_HEADER.set("e_minalloc", @e_minalloc);
    DOS_HEADER.set("e_maxalloc", @e_maxalloc);
    DOS_HEADER.set("e_ss",       @e_ss);
    DOS_HEADER.set("e_sp",       @e_sp);
    DOS_HEADER.set("e_csum",     @e_csum);
    DOS_HEADER.set("e_ip",       @e_ip);
    DOS_HEADER.set("e_cs",       @e_cs);
    DOS_HEADER.set("e_lfarlc",   @e_lfarlc);
    DOS_HEADER.set("e_ovno",     @e_ovno);
    DOS_HEADER.set("e_lfanew",   @e_lfanew);
}

void dump_dos_header(dictionary@ dos, uint64 base)
{
    uint64 e_magic64    = 0;
    uint64 e_cblp64     = 0;
    uint64 e_cp64       = 0;
    uint64 e_crlc64     = 0;
    uint64 e_cparhdr64  = 0;
    uint64 e_minalloc64 = 0;
    uint64 e_maxalloc64 = 0;
    uint64 e_ss64       = 0;
    uint64 e_sp64       = 0;
    uint64 e_csum64     = 0;
    uint64 e_ip64       = 0;
    uint64 e_cs64       = 0;
    uint64 e_lfarlc64   = 0;
    uint64 e_ovno64     = 0;
    uint64 e_lfanew64   = 0;

    dos.get("e_magic",    e_magic64);
    dos.get("e_cblp",     e_cblp64);
    dos.get("e_cp",       e_cp64);
    dos.get("e_crlc",     e_crlc64);
    dos.get("e_cparhdr",  e_cparhdr64);
    dos.get("e_minalloc", e_minalloc64);
    dos.get("e_maxalloc", e_maxalloc64);
    dos.get("e_ss",       e_ss64);
    dos.get("e_sp",       e_sp64);
    dos.get("e_csum",     e_csum64);
    dos.get("e_ip",       e_ip64);
    dos.get("e_cs",       e_cs64);
    dos.get("e_lfarlc",   e_lfarlc64);
    dos.get("e_ovno",     e_ovno64);
    dos.get("e_lfanew",   e_lfanew64);

    log("[AS] ==== IMAGE_DOS_HEADER dump ====");
    log("[AS] base      = 0x" + to_hex32(uint(base & 0xFFFFFFFF)));
    log("[AS] e_magic   = 0x" + to_hex16(uint(e_magic64   & 0xFFFF)));
    log("[AS] e_cblp    = 0x" + to_hex16(uint(e_cblp64    & 0xFFFF)));
    log("[AS] e_cp      = 0x" + to_hex16(uint(e_cp64      & 0xFFFF)));
    log("[AS] e_crlc    = 0x" + to_hex16(uint(e_crlc64    & 0xFFFF)));
    log("[AS] e_cparhdr = 0x" + to_hex16(uint(e_cparhdr64 & 0xFFFF)));
    log("[AS] e_minalloc= 0x" + to_hex16(uint(e_minalloc64& 0xFFFF)));
    log("[AS] e_maxalloc= 0x" + to_hex16(uint(e_maxalloc64& 0xFFFF)));
    log("[AS] e_ss      = 0x" + to_hex16(uint(e_ss64      & 0xFFFF)));
    log("[AS] e_sp      = 0x" + to_hex16(uint(e_sp64      & 0xFFFF)));
    log("[AS] e_csum    = 0x" + to_hex16(uint(e_csum64    & 0xFFFF)));
    log("[AS] e_ip      = 0x" + to_hex16(uint(e_ip64      & 0xFFFF)));
    log("[AS] e_cs      = 0x" + to_hex16(uint(e_cs64      & 0xFFFF)));
    log("[AS] e_lfarlc  = 0x" + to_hex16(uint(e_lfarlc64  & 0xFFFF)));
    log("[AS] e_ovno    = 0x" + to_hex16(uint(e_ovno64    & 0xFFFF)));
    log("[AS] e_lfanew  = 0x" + to_hex32(uint(e_lfanew64  & 0xFFFFFFFF)));

    if ((e_magic64 & 0xFFFF) == 0x5A4D)
    log("[AS] DOS magic OK ('MZ')");
    else
    log("[AS] DOS magic INVALID (expected 0x5A4D)");

    uint64 nt_addr = base + (e_lfanew64 & 0xFFFFFFFF);
    log("[AS] NT header at: 0x" + to_hex32(uint(nt_addr & 0xFFFFFFFF)));
}

void test_dos_header()
{
    init_dos_descriptor();

    proc_t p = ref_process("notepad.exe");
    if (!p.alive())
    {
        log("[AS] notepad.exe not found");
        return;
    }

    uint64 base = p.base_address();

    dictionary dos;
    if (!p.read_struct(base, dos, DOS_HEADER))
    {
        log("[AS] read_struct failed");
        return;
    }

    dump_dos_header(@dos, base);
}

int main()
{
    test_dos_header();
    return 1;
}
```

***

#### Virtual Memory Allocation

These functions let you allocate and manage RWX memory inside the target process.\
They are intended for advanced use; you are fully responsible for tracking and freeing any allocations you create.

**:red\_circle: Important Memory Management Notes (MUST READ!)**

These points are critical for using `alloc_vm` safely:

* **Control Flow Guard**\
  If the target process has Control Flow Guard (CFG) enabled and you intend to execute code from this region, CFG may block all jumps and calls into the allocated memory.\
  To avoid this, CFG must be fully disabled for the target process.\
  Be aware that disabling CFG reduces the security of the device.
* **Allocations are not automatically freed.**\
  Every allocation you create must be manually released using `free_vm()`. If you lose track of an allocation, the memory will remain reserved until the target process exits.
* **Allocations persist for the lifetime of the target process.**\
  Memory created with `alloc_vm` is automatically released only when the **target process** itself closes.
* **Closing the Perception overlay will clear all allocations.**\
  When the overlay is closed, Perception will clean up every RWX allocation for *all* processes currently referenced.\
  If you need an allocation to stay alive, **do not close the overlay** while that memory is being used.
* **Repeated unfreed allocations can exhaust physical memory.**\
  If you repeatedly allocate memory without freeing it, these leaks will accumulate and can eventually **consume all available physical RAM**, potentially degrading system performance or causing instability. If you are writing an injector make sure your inject frees the memory.
* **If you are writing an injector, you must free allocated memory.**\
  Any injector, loader, or external tool that allocates memory through `alloc_vm` is responsible for freeing it once the memory is no longer needed.\
  Failing to do so will leave permanent physical memory leaks until the target process exits.

**Functions**

```cpp
uint64 proc_t::alloc_vm(uint size)
bool   proc_t::free_vm(uint64 address)
```

**`uint64 proc_t::alloc_vm(uint size)`**

Allocates a block of **read–write–execute (RWX)** memory in the target process and returns its base address.

* **Parameters**
  * `size` — Size of the allocation in bytes.
* **Returns**
  * Base address of the allocated region on success.
  * `0` on failure.

**Notes**

* The allocated region is **not associated with any module** and is **not discoverable** through higher-level helpers (e.g. module lookup, pattern scan helpers, etc.).\
  You must store and manage the returned address yourself.
* The memory is RWX. If the target process uses **Control Flow Guard (CFG)** and you intend to execute from this region, CFG may block jumps/calls into it unless the target process allows it.

***

**`bool proc_t::free_vm(uint64 address)`**

Frees a region previously allocated with `alloc_vm`.

* **Parameters**
  * `address` — Base address previously returned by `alloc_vm`.
* **Returns**
  * `true` if the region was successfully freed.
  * `false` if the address is invalid or the free fails.

***

**🔗 Export Lookup – `get_proc_address`**

```cpp
uint64 proc_t::get_proc_address(
    uint64        module_base,
    const string &in export_name
)
```

Resolves the address of an **exported symbol** inside a module in the target process.

* `module_base`\
  Base address of the module **inside the target process**.\
  Typically obtained from:
  * `proc_t::base_address()`, or
  * `proc_t::get_module("module_name.dll", base, size)`.
* `export_name`\
  Name of the exported function or symbol, e.g. `"Sleep"`, `"CreateFileW"`.

**Returns**

* Absolute **virtual address** of the exported symbol in the target process.
* `0` if the export is not found or the arguments are invalid.

**Notes**

* This walks the module's **export table** only – it does *not* search imports or runtime-resolved addresses.
* The address is directly usable for:
  * Call stubs / shellcode in the remote process.
  * Manual thunking (e.g. "jmp \[resolved\_addr]" from your injected code).
* You are responsible for ensuring the returned address is valid / executable before calling into it.

**Example**

```cpp
proc_t p = ref_process("notepad.exe");

uint64 kbase, ksize;
if (p.get_module("KERNEL32.DLL", kbase, ksize))
{
    uint64 addrSleep = p.get_proc_address(kbase, "Sleep");
    log("Sleep @ 0x" + formatUInt(addrSleep, "0H", 16));
}
```

***

**🧷 Import Table (IAT) Slot Lookup – `get_import_rdata_address`**

```cpp
uint64 proc_t::get_import_rdata_address(
    uint64        module_base,
    const string &in import_name
)
```

Resolves the **address of the import table entry** (IAT slot) for a given imported function inside a module.

This does **not** return the function's address directly – it returns the address of the **pointer stored in `.rdata` / IAT**. That pointer can then be read or patched (for IAT hooks, trampolines, etc.).

* `module_base`\
  Base address of the module whose **imports you want to inspect/patch** (usually the main EXE or a specific DLL), obtained from `base_address()` or `get_module(...)`.
* `import_name`\
  Name of the imported function as it appears in the import table, e.g. `"Sleep"`, `"MessageBoxW"`.

**Returns**

* Address of the **IAT entry** (pointer-sized slot) for the requested import.
* `0` if the import cannot be found or the arguments are invalid.

**How to use**

* Read current target of the import:

  ```cpp
  uint64 slot_addr = p.get_import_rdata_address(modBase, "Sleep");
  uint64 current_fn = p.ru64(slot_addr); // current function pointer
  ```
* Install a basic IAT hook (patch the pointer):

  ```cpp
  uint64 slot_addr = p.get_import_rdata_address(modBase, "Sleep");
  if (slot_addr != 0)
  {
      // 'stub_remote' is an RWX address you allocated in the target
      p.wu64(slot_addr, stub_remote);
  }
  ```

**Notes**

* This only sees imports that are present in the module's **static import table**.
* Imports resolved manually at runtime (e.g. via `GetProcAddress` into custom memory) will **not** show up here.
* Ideal for:
  * Classic **IAT hooks** (redirecting calls to your own stub).
  * Finding the call site used by a module to invoke a given API, so your shellcode can jump through the same IAT entry.

***

**Pointer Array Helpers**

**`array<uint64>@ proc_t::read_pointer_array(uint64 base, uint count, int offset_delta) const`**

Reads an array of 64-bit pointers from the target process.

This is a convenience helper for common layouts like:

* pointer lists (`T**`, vtable arrays, entity pointer arrays)
* "pointer + fixed offset" patterns

**Parameters**

* `base` — Address of the first pointer (each element is `uint64`, so step = 8 bytes).
* `count` — Number of pointers to read.
* `offset_delta` — Value added to **each** pointer after reading (can be negative).

**Return**

* Returns `array<uint64>@` containing `count` elements.
* Returns `null` if `base` is invalid, `count` is 0, or the process handle is invalid.

**Example**

```cpp
proc_t p = ref_process("cs2.exe");
if (!p.alive())
{
    log_error("process not found");
    return 0;
}

uint64 list_base = 0x12345678; // address of first uint64 pointer
uint count = 64;

// Example: read pointer array and add +0x10 to each pointer
array<uint64>@ ptrs = p.read_pointer_array(list_base, count, 0x10);
if (ptrs is null)
{
    log_error("read_pointer_array failed");
    return 0;
}

for (uint i = 0; i < ptrs.length(); ++i)
{
    uint64 addr = ptrs[i];
    if (addr == 0) continue;

    // ... use addr ...
}
```

***

### Virtual Memory Analysis

These APIs allow querying and iterating virtual memory regions.

***

#### `bool proc_t::virtual_query(uint64 address, uint64 &out region_start, uint64 &out region_size, uint &out protection, bool &out heap_likely) const`

Queries the memory region that contains `address`.

**Parameters**

* `address` — Any virtual address inside the target region.
* `region_start` — Region start address (output).
* `region_size` — Region size in bytes (output).
* `protection` — Region protection flags (output).
* `heap_likely` — True if the region is likely heap/alloc-like (output).

**Returns**

* `true` on success
* `false` if the address is not mapped or cannot be queried

***

#### `array<dictionary@>@ proc_t::get_vad_snapshot(bool heap_likely_only = false) const`

Builds a snapshot of virtual memory regions and **returns** it as an array of dictionary handles.

* When `heap_likely_only == true`, only heap-like regions are returned.
* When `heap_likely_only == false`, all regions are returned.

**Returns**

* `array<dictionary@>@` — array of dictionaries, one per region. Returns `null` on failure.

**Dictionary field types**

Each dictionary entry stores fields as `int64` (matching the same convention as `read_struct`). You must use `int64` in your `.get()` calls:

| Key             | Stored Type | Description                               |
| --------------- | ----------- | ----------------------------------------- |
| `"start"`       | `int64`     | Region start address                      |
| `"size"`        | `int64`     | Region size in bytes                      |
| `"end"`         | `int64`     | Region end address                        |
| `"protection"`  | `int64`     | Protection flags                          |
| `"heap_likely"` | `int64`     | `1` if region is heap-like, `0` otherwise |

**Example**

```cpp
void enumerate_regions(proc_t p, bool heap_only)
{
    array<dictionary@>@ vad = p.get_vad_snapshot(heap_only);
    if (vad is null)
    {
        log("get_vad_snapshot failed");
        return;
    }

    log("Regions: " + vad.length());

    for (uint i = 0; i < vad.length(); i++)
    {
        dictionary@ d = vad[i];

        int64 rStart = 0;
        int64 rSize  = 0;
        int64 rEnd   = 0;
        int64 prot   = 0;
        int64 heap   = 0;

        d.get("start",       rStart);
        d.get("size",        rSize);
        d.get("end",         rEnd);
        d.get("protection",  prot);
        d.get("heap_likely", heap);

        log("Region[" + i + "] start=0x" + formatUInt(uint64(rStart), "0H", 16)
            + " size=0x" + formatUInt(uint64(rSize), "0H", 16)
            + " heap=" + (heap != 0));
    }
}
```

***

### Memory Scan Helpers

All scan functions **return** `array<uint64>@` containing matching addresses. Returns `null` on failure (invalid process handle, etc.).

All scan functions accept a `heap_only` parameter (default `false`). When `true`, only heap-like memory regions are scanned.

***

#### `array<uint64>@ proc_t::scan_u32(uint value, bool heap_only = false) const`

Scans for a 32-bit unsigned value.

```cpp
array<uint64>@ results = p.scan_u32(12345, false);
```

***

#### `array<uint64>@ proc_t::scan_u64(uint64 value, bool heap_only = false) const`

Scans for a 64-bit unsigned value.

```cpp
array<uint64>@ results = p.scan_u64(0xDEADBEEF, false);
```

***

#### `array<uint64>@ proc_t::scan_float(float value, bool heap_only = false) const`

Scans for a 32-bit floating-point value.

```cpp
array<uint64>@ results = p.scan_float(100.0f, true);
```

***

#### `array<uint64>@ proc_t::scan_double(double value, bool heap_only = false) const`

Scans for a 64-bit floating-point value.

```cpp
array<uint64>@ results = p.scan_double(3.14159, false);
```

***

#### `array<uint64>@ proc_t::scan_string(const string &in text, bool heap_only = false) const`

Scans for a UTF-8 / ANSI byte string in memory.

```cpp
array<uint64>@ results = p.scan_string("player_name", true);
```

***

#### `array<uint64>@ proc_t::scan_wstring(const string &in text, bool heap_only = false) const`

Scans for a UTF-16 (wide) string in memory. The input is a regular `string` which is internally converted to UTF-16 before scanning.

```cpp
array<uint64>@ results = p.scan_wstring("Notepad", false);
```

***

#### `array<uint64>@ proc_t::scan_pointer(uint64 target, bool heap_only = false) const`

Scans for all locations in memory that contain a pointer to `target`.

```cpp
uint64 vtable_addr = 0x7FF612340000;
array<uint64>@ refs = p.scan_pointer(vtable_addr, false);
if (refs !is null)
{
    for (uint i = 0; i < refs.length(); i++)
        log("Reference at 0x" + formatUInt(refs[i], "0H", 16));
}
```

***

#### 🔍 Full Scan Example

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (!p.alive())
    {
        log("Process not found");
        return 0;
    }
    
    // Scan for a known health value
    array<uint64>@ hits = p.scan_u32(100, true);
    if (hits is null || hits.length() == 0)
    {
        log("No matches found");
        p.deref();
        return 0;
    }

    log("Found " + hits.length() + " matches for value 100:");
    uint n = hits.length() < 10 ? hits.length() : 10;
    for (uint i = 0; i < n; i++)
    {
        log("  [" + i + "] 0x" + formatUInt(hits[i], "0H", 16));
    }

    // Scan for a float position
    array<uint64>@ float_hits = p.scan_float(128.5f, true);
    if (float_hits !is null)
        log("Float matches: " + float_hits.length());

    // Scan for a string
    array<uint64>@ str_hits = p.scan_string("notepad", false);
    if (str_hits !is null)
        log("String matches: " + str_hits.length());

    p.deref();
    return 0;
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/proc-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/render-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/render-api.md).

# Render API

**📐 Constants**

```cpp
const uint8 RR_TOP_LEFT
const uint8 RR_TOP_RIGHT
const uint8 RR_BOTTOM_LEFT
const uint8 RR_BOTTOM_RIGHT
```

> Rectangle-corner rounding flags (bitmask).

```cpp
const int TE_NONE
const int TE_OUTLINE
const int TE_SHADOW
const int TE_GLOW
```

> Text rendering effects.

***

**🎨 Viewport**

```cpp
void get_view(float &out w, float &out h)
float get_view_scale()
double get_fps()
```

* `get_view` — Returns the current viewport width/height in pixels.
* `get_view_scale` — Returns the viewport reference scale (for DPI scaling, etc).
* `get_fps()` — Returns current frames per second.

***

**📏 Basic Shapes**

**Rectangle**

```cpp
void draw_rect(float x,float y,float w,float h,
               uint8 r,uint8 g,uint8 b,uint8 a,
               float thickness, float rounding, uint8 rounding_flags)
```

Draws an **outlined rectangle**.

**Filled Rectangle**

```cpp
void draw_rect_filled(float x,float y,float w,float h,
                      uint8 r,uint8 g,uint8 b,uint8 a,
                      float rounding, uint8 rounding_flags)
```

Draws a **filled rectangle**.

**Line**

```cpp
void draw_line(float x1,float y1,float x2,float y2,
               uint8 r,uint8 g,uint8 b,uint8 a, float thickness)
```

Draws a line between `(x1,y1)` and `(x2,y2)`.

**Arc**

```cpp
void draw_arc(float cx, float cy, float rx, float ry,
              float start_angle_deg, float sweep_angle_deg,
              uint8 r, uint8 g, uint8 b, uint8 a,
              float thickness, bool filled)
```

Draws an arc or pie-slice centered at `(cx, cy)`.

**Circle**

```cpp
void draw_circle(float cx,float cy,float radius,
                 uint8 r,uint8 g,uint8 b,uint8 a,
                 float thickness, bool filled)
```

**Triangle**

```cpp
void draw_triangle(float ax,float ay,float bx,float by,float cx,float cy,
                   uint8 r,uint8 g,uint8 b,uint8 a,
                   float thickness, bool filled)
```

**Polygon**

```cpp
void draw_polygon(const array<float> &in xy_pairs, uint count_pairs,
                  uint8 r,uint8 g,uint8 b,uint8 a,
                  float thickness, bool filled)
```

* `xy_pairs` — `[x0, y0, x1, y1, …]`
* `count_pairs` — optional; set `0` to use full array length.

**Four Corner Gradient**

```cpp
void draw_four_corner_gradient(float x,float y,float w,float h,
    uint8 tlr,uint8 tlg,uint8 tlb,uint8 tla,
    uint8 trr,uint8 trg,uint8 trb,uint8 tra,
    uint8 blr,uint8 blg,uint8 blb,uint8 bla,
    uint8 brr,uint8 brg,uint8 brb,uint8 bra,
    float rounding)
```

Draws a gradient rectangle with individual RGBA colors for each corner.

***

**🖼️ Bitmaps**

```cpp
uint64 create_bitmap(const array<uint8> &in data)
void   draw_bitmap(uint64 bmp, float x,float y,float w,float h,
                   uint8 r,uint8 g,uint8 b,uint8 a, bool rounded)
```

* `create_bitmap` — Creates a bitmap from raw RGBA or compressed bytes. Returns an **encrypted handle** (`uint64`) used for drawing.
* `draw_bitmap` — Draws the bitmap tinted with color `(r,g,b,a)`.

***

**🔤 Fonts & Text**

```cpp
uint64 create_font(const string &in path, float size, bool antialias, 
bool load_color, array<uint> @glyph_ranges = null)
//load color should only be used for fonts that require texture coloring (e.g. emojis)

/* Automatically resolves font paths within the API directory
   (e.g., verdana_custom.ttf or fonts/verdana_custom.ttf).
   The API may also fall back to searching system font locations.
   If a system font shares the same name, it may be loaded instead.
   Use unique font names to avoid naming conflicts. */

uint64 create_font_mem(const string &in label, float size, const array<uint8> &in buf, 
 bool antialias, bool load_color, array<uint> @glyph_ranges = null)

uint64 get_font18() // default font of size 18
uint64 get_font20() // default font of size 20
uint64 get_font24() // default font of size 24
uint64 get_font28() // default font of size 28

// Using custom glyph ranges
array<uint> ranges = {
    0x0020, 0x00FF,   // Basic Latin + Latin-1 Supplement
    0x0400, 0x04FF,   // Cyrillic
    0
};
uint64 font2 = create_font("Arial", 16.0f, true, false, ranges);
```

**Text Drawing**

```cpp
void draw_text(const string &in text, float x,float y,
               uint8 r,uint8 g,uint8 b,uint8 a,
               uint64 font, int effect,
               uint8 er,uint8 eg,uint8 eb,uint8 ea,
               float effect_amount)
```

* `effect` — One of `TE_NONE`, `TE_OUTLINE`, `TE_SHADOW`, `TE_GLOW`.
* `effect_color` — `(er,eg,eb,ea)`.
* `effect_amount` — Intensity scalar.

**Text Metrics**

```cpp
void get_text_size(uint64 font, const string &in text, int maxw, int maxh,
                   float &out w, float &out h)
int get_char_advance(uint64 font, uint wchar32)
```

> Measure text dimensions or a single character's advance width.

***

**✂️ Clipping**

```cpp
void clip_push(float x,float y,float w,float h)
void clip_pop()
```

***

**Example**

```cpp
void draw_ui()
{
    float vw, vh; get_view(vw, vh);
    float cx = vw * 0.5f, cy = vh * 0.5f;

    uint64 font = get_font20();

    draw_rect_filled(cx - 100, cy - 50, 200, 100,
                     40, 40, 40, 255, 8.0f, RR_TOP_LEFT|RR_TOP_RIGHT);

    draw_text("Hello World", cx - 60, cy - 10,
              255,255,255,255, font, TE_SHADOW,
              0,0,0,180, 1.0f);
}
```

***

**🔺 Custom Draw (Shaders & Direct GPU Access)**

The custom draw API gives scripts direct access to the D3D11 GPU pipeline — custom HLSL shaders, vertex buffers, textures, render targets, and all primitive topologies. Custom draw commands respect draw order with all other render functions.

**Constants**

**Topology**

```cpp
const int TOPO_TRIANGLE_LIST    // Default. 3 vertices per triangle.
const int TOPO_TRIANGLE_STRIP   // Shared edges. N vertices = N-2 triangles.
const int TOPO_LINE_LIST        // 2 vertices per line segment.
const int TOPO_LINE_STRIP       // Connected line segments.
const int TOPO_POINT_LIST       // Individual points.
```

**Blend Factors**

```cpp
const int BLEND_ZERO
const int BLEND_ONE
const int BLEND_SRC_ALPHA
const int BLEND_INV_SRC_ALPHA
const int BLEND_DEST_ALPHA
const int BLEND_INV_DEST_ALPHA
const int BLEND_SRC_COLOR
const int BLEND_INV_SRC_COLOR
const int BLEND_DEST_COLOR
const int BLEND_INV_DEST_COLOR
```

**Blend Operations**

```cpp
const int BLEND_OP_ADD
const int BLEND_OP_SUBTRACT
const int BLEND_OP_REV_SUBTRACT
const int BLEND_OP_MIN
const int BLEND_OP_MAX
```

**Vertex Layout Element Types**

```cpp
const int ELEM_FLOAT1       // 4 bytes
const int ELEM_FLOAT2       // 8 bytes
const int ELEM_FLOAT3       // 12 bytes
const int ELEM_FLOAT4       // 16 bytes
const int ELEM_BYTE4_UNORM  // 4 bytes (normalized 0-1)
const int ELEM_UINT1        // 4 bytes
```

**Texture Filter Modes**

```cpp
const int FILTER_POINT
const int FILTER_LINEAR
const int FILTER_ANISOTROPIC
```

**Texture Address Modes**

```cpp
const int ADDRESS_WRAP
const int ADDRESS_CLAMP
const int ADDRESS_MIRROR
const int ADDRESS_BORDER
```

**Shaders**

```cpp
uint64 create_shader(const string &in vs_source, const string &in ps_source,
                     const string &in layout)
void   destroy_shader(uint64 shader)
```

Creates a compiled shader from HLSL source strings. The `layout` parameter is a format string describing the vertex input layout:

```
"POSITION:0:FLOAT2, COLOR:0:FLOAT4"
"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2"
"POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2"
```

Format: `SEMANTIC:semantic_index:TYPE` separated by commas. Supported types: `FLOAT1`, `FLOAT2`, `FLOAT3`, `FLOAT4`, `BYTE4`, `UINT1`.

Returns `0` on compilation failure. Shader entry point must be `main` for both VS and PS.

**Vertex Buffers**

```cpp
uint64 create_vertex_buffer(uint stride, uint max_vertices, bool dynamic)
void   destroy_vertex_buffer(uint64 vb)
```

* `stride` — Bytes per vertex (must match shader layout).
* `max_vertices` — Maximum number of vertices the buffer can hold.
* `dynamic` — `true` for per-frame updates (typical), `false` for static geometry.

**Constant Buffers**

```cpp
uint64 create_constant_buffer(uint size)
void   destroy_constant_buffer(uint64 cb)
```

Size is automatically aligned to 16 bytes. Bound to both VS and PS at the specified slot.

**Blend States**

```cpp
uint64 create_blend_state(int src, int dst, int op,
                          int src_alpha, int dst_alpha, int op_alpha)
void   destroy_blend_state(uint64 bs)
```

For premultiplied alpha (recommended for overlay rendering):

```cpp
uint64 blend = create_blend_state(BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                   BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

For standard alpha blending:

```cpp
uint64 blend = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                   BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

**Samplers**

```cpp
uint64 create_sampler(int filter, int address_u, int address_v)
void   destroy_sampler(uint64 s)
```

Controls how textures are sampled. `FILTER_LINEAR` for smooth scaling, `FILTER_POINT` for pixel-perfect rendering.

**Textures**

```cpp
uint64 create_texture(uint width, uint height, const array<uint8> &in rgba_data)
void   destroy_texture(uint64 tex)
```

Creates a texture from raw RGBA pixel data. The `rgba_data` array must be exactly `width * height * 4` bytes.

**Render Targets**

```cpp
uint64 create_render_target(uint width, uint height)
void   destroy_render_target(uint64 rt)
```

Creates an offscreen render target for multi-pass rendering. Pass `0` for width/height to match the viewport size.

**Drawing**

```cpp
void custom_draw(uint64 shader, uint64 vb,
                 const array<uint8> &in vertex_data, uint vertex_count,
                 int topology,
                 uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
                 uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

The main draw call. Submits custom geometry to the GPU using the specified shader and resources.

* `shader` — Required. Handle from `create_shader`.
* `vb` — Required. Handle from `create_vertex_buffer`.
* `vertex_data` — Raw vertex bytes packed into `array<uint8>`. Must match the shader's layout stride.
* `vertex_count` — Number of vertices to draw.
* `topology` — One of the `TOPO_*` constants.
* `blend` — Blend state handle, or `0` for default blending.
* `sampler` — Sampler handle, or `0` for no sampler.
* `texture` — Texture handle, or `0` for no texture.
* `tex_slot` — Texture/sampler register slot (usually `0`).
* `cb` — Constant buffer handle, or `0` for no constants.
* `cb_data` — Raw constant data as `array<uint8>`, or `null` if no constants.
* `cb_slot` — Constant buffer register slot (usually `0`).

> Custom draw commands respect draw order with all other render functions. If you call `draw_rect_filled`, then `custom_draw`, then `draw_text`, they render in exactly that order.

**Render Target Control**

```cpp
void custom_set_render_target(uint64 rt)
void custom_reset_render_target()
void custom_bind_rt_as_texture(uint64 rt, int slot)
void custom_restore_state()
```

* `custom_set_render_target` — Redirects subsequent `custom_draw` calls to an offscreen render target.
* `custom_reset_render_target` — Switches back to the main backbuffer.
* `custom_bind_rt_as_texture` — Binds a render target's contents as a texture for sampling in a shader.
* `custom_restore_state` — Resets the D3D11 pipeline state. Call after render target operations to ensure normal rendering continues correctly.

**Packing Vertex Data**

Since `custom_draw` takes raw bytes, you need to pack floats into `array<uint8>`. Use `fpToIEEE` to convert floats:

```cpp
void pack_float(array<uint8> &b, int offset, float val)
{
    uint bits = fpToIEEE(val);
    b[offset]     = uint8(bits & 0xFF);
    b[offset + 1] = uint8((bits >> 8) & 0xFF);
    b[offset + 2] = uint8((bits >> 16) & 0xFF);
    b[offset + 3] = uint8((bits >> 24) & 0xFF);
}
```

**Resource Cleanup**

All custom draw resources are automatically destroyed when a script is unloaded. You can also destroy them manually:

```cpp
destroy_shader(shader);
destroy_vertex_buffer(vb);
destroy_constant_buffer(cb);
destroy_blend_state(blend);
destroy_sampler(sampler);
destroy_texture(tex);
destroy_render_target(rt);
destroy_index_buffer(ib);
destroy_depth_stencil_state(ds);
destroy_rasterizer_state(rs);
destroy_compute_shader(cs);
destroy_structured_buffer(sb);
destroy_mesh(mesh);
destroy_depth_buffer(db);
```

***

**🔢 Index Buffers & Indexed Drawing**

```cpp
uint64 create_index_buffer(uint max_indices, bool use_32bit, bool dynamic)
void   destroy_index_buffer(uint64 ib)
```

* `max_indices` — Maximum number of indices the buffer can hold.
* `use_32bit` — `true` for 32-bit indices (`uint`), `false` for 16-bit (`uint16`). Use 32-bit for meshes with more than 65535 vertices.
* `dynamic` — `true` for per-frame updates, `false` for static geometry.

```cpp
void custom_draw_indexed(uint64 shader, uint64 vb,
    const array<uint8> &in vertex_data, uint vertex_count,
    uint64 ib, const array<uint8> &in index_data, uint index_count,
    int topology,
    uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
    uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

Same as `custom_draw` but uses an index buffer to avoid duplicating shared vertices. Useful for cubes, grids, and any geometry with shared edges.

***

**🧊 Depth/Stencil State**

```cpp
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func)
void   destroy_depth_stencil_state(uint64 ds)
void   custom_set_depth_stencil_state(uint64 ds)
```

**Depth Comparison Constants**

```cpp
const int CMP_NEVER
const int CMP_LESS           // Standard 3D depth testing
const int CMP_EQUAL
const int CMP_LESS_EQUAL
const int CMP_GREATER
const int CMP_NOT_EQUAL
const int CMP_GREATER_EQUAL
const int CMP_ALWAYS         // Disable depth test (still writes if depth_write=true)
```

* `depth_enable` — Enable depth testing.
* `depth_write` — Write to depth buffer on pass.
* `compare_func` — One of the `CMP_*` constants.
* `custom_set_depth_stencil_state(0)` — Resets to default (no depth testing).

For solid 3D rendering, use `create_depth_stencil_state(true, true, CMP_LESS)`.

***

**🔳 Rasterizer State**

```cpp
uint64 create_rasterizer_state(int cull_mode, int fill_mode, bool scissor_enable)
void   destroy_rasterizer_state(uint64 rs)
void   custom_set_rasterizer_state(uint64 rs)
```

**Cull/Fill Constants**

```cpp
const int CULL_NONE          // Render both sides
const int CULL_FRONT
const int CULL_BACK          // Default — cull back-facing triangles

const int FILL_SOLID         // Default
const int FILL_WIREFRAME
```

* `scissor_enable` — Typically `true`. Required for clipping to work.
* `custom_set_rasterizer_state(0)` — Resets to default.

For 3D meshes where you want to see all faces (pyramids, etc), use `CULL_NONE`.

***

**📺 Viewport & Texture Binding**

```cpp
void custom_set_viewport(float x, float y, float w, float h)
void custom_reset_viewport()
void custom_bind_texture(uint64 texture, uint64 sampler, int slot)
```

* `custom_set_viewport` — Restricts rendering to a sub-region of the screen. Use before `draw_mesh` or `custom_draw` to confine 3D rendering to a panel.
* `custom_reset_viewport` — Restores the full viewport.
* `custom_bind_texture` — Binds a texture + sampler to a slot, persisting across subsequent draw calls. Pass `0` for texture to bind the backbuffer capture result.

***

**💻 Compute Shaders**

```cpp
uint64 create_compute_shader(const string &in cs_source)
void   destroy_compute_shader(uint64 cs)
void   dispatch_compute(uint64 cs, uint x, uint y, uint z)
```

Creates and dispatches a compute shader (cs\_5\_0). Entry point must be `main`. Thread group counts `(x, y, z)` are passed to `Dispatch()`.

Compute shaders are dispatched as state-only commands — no geometry is drawn. Use structured buffers for CS input/output.

**Bind Stage Constants**

```cpp
const int STAGE_VS   // Vertex shader (0)
const int STAGE_PS   // Pixel shader (1)
const int STAGE_CS   // Compute shader (2)
```

***

**📊 Structured Buffers**

```cpp
uint64 create_structured_buffer(uint element_size, uint element_count, bool cpu_write, bool gpu_write)
void   destroy_structured_buffer(uint64 sb)
void   update_structured_buffer(uint64 sb, const array<uint8> &in data)
void   bind_structured_buffer(uint64 sb, int slot, int stage)
```

* `element_size` — Size of each element in bytes (typically 16 for `float4`).
* `element_count` — Number of elements.
* `cpu_write` — `true` to allow CPU updates via `update_structured_buffer`. Creates SRV only.
* `gpu_write` — `true` to allow GPU writes from compute shaders. Creates both SRV and UAV.
* `bind_structured_buffer` — Binds the buffer to a shader stage. CS stage with `gpu_write` binds as UAV, otherwise SRV. Use `STAGE_VS`, `STAGE_PS`, or `STAGE_CS`.

**Example: GPU particle buffer**

```cpp
// Create: 16 bytes per particle (float4), 1024 particles, GPU-writable
uint64 sb = create_structured_buffer(16, 1024, false, true);

// In compute shader: bind as UAV for writing
bind_structured_buffer(sb, 0, STAGE_CS);
dispatch_compute(cs, 16, 1, 1);  // 16 groups × 64 threads = 1024 particles

// In pixel shader: bind as SRV for reading
bind_structured_buffer(sb, 0, STAGE_PS);
```

***

**📷 Backbuffer Capture**

```cpp
void capture_backbuffer(int slot)
```

Captures the current backbuffer contents to a staging texture and binds it as a shader resource at the specified slot. Use with a custom pixel shader to create post-processing effects like bloom, blur, color grading, or screen-space reflections.

```cpp
capture_backbuffer(0);
custom_bind_texture(0, sampler, 0);  // texture=0 uses the captured backbuffer
custom_draw(post_fx_shader, vb, fullscreen_quad, 6, TOPO_TRIANGLE_LIST, ...);
```

***

**🖼️ Texture Loading**

```cpp
uint64 load_texture_mem(const array<uint8> &in data)
uint64 load_texture(const string &in path)
void   get_texture_info(uint64 tex, float &out w, float &out h)
```

* `load_texture_mem` — Decodes PNG, JPG, BMP, TGA, or GIF from a byte array. Returns a texture handle (same type as `create_texture`).
* `load_texture` — Loads an image file from disk. Tries the script directory first, then the absolute path.
* `get_texture_info` — Returns the texture dimensions.
* Destroy with `destroy_texture(handle)`.

***

**🏔️ Mesh Loading (OBJ)**

```cpp
uint64 load_mesh_mem(const array<uint8> &in data)
uint64 load_mesh(const string &in path)
void   get_mesh_info(uint64 mesh, float &out vert_count, float &out index_count,
                     float &out min_x, float &out min_y, float &out min_z,
                     float &out max_x, float &out max_y, float &out max_z)
void   destroy_mesh(uint64 mesh)
```

Parses Wavefront OBJ format with support for positions (`v`), normals (`vn`), texture coordinates (`vt`), faces with 3+ vertices (auto-triangulated), and negative indices.

**Fixed vertex layout:** `POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2` — 32 bytes per vertex. Shaders used with loaded meshes must match this layout.

* `get_mesh_info` — Returns vertex/index counts and the axis-aligned bounding box.
* `load_mesh` — Loads from disk, tries script directory first.

***

**🔺 Drawing Meshes**

```cpp
void draw_mesh(uint64 mesh, uint64 shader, int topology,
               uint64 blend, uint64 sampler, uint64 texture, int tex_slot,
               uint64 cb, const array<uint8> @cb_data, int cb_slot)
```

Convenience draw call for loaded or procedural meshes. Binds the mesh's internal vertex/index buffers and calls `DrawIndexed` in one step. Pass `0` for optional handles (sampler, texture, cb). The shader layout must match the mesh's vertex format.

**Example: render a lit OBJ mesh**

```cpp
// Create mesh and shader
uint64 mesh = load_mesh("model.obj");
uint64 shader = create_shader(vs_3d, ps_lit,
    "POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2");
uint64 cb_mvp = create_constant_buffer(64);

// Each frame: build MVP matrix, draw
custom_set_viewport(x, y, w, h);
custom_set_rasterizer_state(rs_nocull);
custom_set_depth_stencil_state(ds_off);
draw_mesh(mesh, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb_mvp, mvp_data, 0);
custom_reset_viewport();
custom_set_rasterizer_state(0);
custom_set_depth_stencil_state(0);
custom_restore_state();
```

***

**🌊 Depth Buffers & 3D Rendering**

```cpp
uint64 create_depth_buffer(uint width, uint height)
void   destroy_depth_buffer(uint64 db)
void   custom_set_render_target_ext(uint64 rt, uint64 depth_buffer)
void   custom_clear_render_target(uint64 rt, float r, float g, float b, float a)
void   custom_clear_depth_buffer(uint64 db)
```

* `create_depth_buffer` — Creates a D24S8 depth/stencil buffer. Pass `0, 0` to match viewport size.
* `custom_set_render_target_ext` — Binds a render target with an optional depth buffer for proper 3D occlusion. Auto-clears both, sets viewport and scissor to RT dimensions. Pass `0` for depth buffer to use color-only (same behavior as `custom_set_render_target`).
* `custom_clear_render_target` — Clears a render target to a specific color without re-binding it.
* `custom_clear_depth_buffer` — Clears depth to 1.0 and stencil to 0.

**Example: solid 3D scene with depth**

```cpp
uint64 rt = create_render_target(400, 300);
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);

// Render pass
custom_set_render_target_ext(rt, db);
custom_clear_render_target(rt, 0, 0, 0, 1);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs_nocull);
draw_mesh(mesh1, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb, mvp1_data, 0);
draw_mesh(mesh2, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, cb, mvp2_data, 0);
custom_reset_render_target();
custom_set_rasterizer_state(0);
custom_set_depth_stencil_state(0);

// Blit result to screen
custom_bind_rt_as_texture(rt, 0);
custom_draw(blit_shader, vb, quad, 6, TOPO_TRIANGLE_LIST, blend, sampler, 0, 0, cb, screen_cb, 0);
custom_restore_state();
```

***

**🎛️ Multi-CB Binding**

```cpp
void custom_bind_constant_buffer(uint64 cb, const array<uint8> &in data, int slot, int stage)
```

Binds a constant buffer to a specific register slot and shader stage, independently of draw calls. This persists across subsequent draws until changed. Use `STAGE_VS`, `STAGE_PS`, or `STAGE_CS`.

This enables multi-buffer shader setups where camera data lives on `b0`, material properties on `b1`, and lighting on `b2`:

```cpp
custom_bind_constant_buffer(cb_camera, camera_data, 0, STAGE_VS);   // b0 in VS
custom_bind_constant_buffer(cb_material, mat_data, 1, STAGE_PS);    // b1 in PS
custom_bind_constant_buffer(cb_light, light_data, 2, STAGE_PS);     // b2 in PS
draw_mesh(mesh, shader, TOPO_TRIANGLE_LIST, blend, 0, 0, 0, 0, null, 0);
```

Note: when using `custom_bind_constant_buffer` for the MVP, pass `0` for the `cb` parameter of `draw_mesh` to avoid it overwriting your manually bound buffers.

***

**🧱 Procedural Mesh**

```cpp
uint64 create_mesh_raw(const array<uint8> &in vertex_data, uint vertex_count, uint stride,
                       const array<uint8> &in index_data, uint index_count, bool use_32bit)
float  get_mesh_stride(uint64 mesh)
```

* `create_mesh_raw` — Builds a mesh from raw vertex and index byte arrays with any vertex layout. The shader must match the stride. Use for procedural terrain, generated geometry, or particle quads.
* `get_mesh_stride` — Returns the vertex stride in bytes (32 for OBJ-loaded meshes).
* Destroy with `destroy_mesh(handle)`.

The vertex data can use any layout — it's not restricted to the OBJ format's position+normal+uv.

***

**🎨 Dynamic Texture Update**

```cpp
void custom_update_texture(uint64 tex, uint x, uint y, uint w, uint h,
                           const array<uint8> &in rgba_data)
```

Performs a partial update of an existing texture. The `rgba_data` must be exactly `w * h * 4` bytes. Use for dynamic sprite sheets, minimaps, procedural atlases, or any per-frame texture content.

```cpp
// Update an 8x8 region at position (10, 10)
array<uint8> pixels(8 * 8 * 4);
// ... fill pixels ...
custom_update_texture(tex, 10, 10, 8, 8, pixels);
```

***

**🌌 Example: Nebula Shader**

```cpp
string vs_src =
"cbuffer cb : register(b0) { float2 screen; float time; float pad; };\n"
"struct vi { float2 pos : POSITION; float2 uv : TEXCOORD0; };\n"
"struct vo { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; float time : TEXCOORD1; float2 res : TEXCOORD2; };\n"
"vo main(vi i) {\n"
"    vo o;\n"
"    o.pos = float4(i.pos.x / screen.x * 2.0 - 1.0,\n"
"                   1.0 - i.pos.y / screen.y * 2.0, 0.0, 1.0);\n"
"    o.uv = i.uv;\n"
"    o.time = time;\n"
"    o.res = screen;\n"
"    return o;\n"
"}\n";

string ps_src =
"struct vo { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; float time : TEXCOORD1; float2 res : TEXCOORD2; };\n"
"\n"
"float hash(float2 p) {\n"
"    float3 p3 = frac(float3(p.xyx) * 0.1031);\n"
"    p3 += dot(p3, p3.yzx + 33.33);\n"
"    return frac((p3.x + p3.y) * p3.z);\n"
"}\n"
"\n"
"float noise(float2 p) {\n"
"    float2 i = floor(p);\n"
"    float2 f = frac(p);\n"
"    f = f * f * (3.0 - 2.0 * f);\n"
"    float a = hash(i);\n"
"    float b = hash(i + float2(1.0, 0.0));\n"
"    float c = hash(i + float2(0.0, 1.0));\n"
"    float d = hash(i + float2(1.0, 1.0));\n"
"    return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);\n"
"}\n"
"\n"
"float fbm(float2 p) {\n"
"    float v = 0.0;\n"
"    float a = 0.5;\n"
"    float2x2 rot = float2x2(0.8, 0.6, -0.6, 0.8);\n"
"    for (int i = 0; i < 5; i++) {\n"
"        v += a * noise(p);\n"
"        p = mul(rot, p) * 2.0;\n"
"        a *= 0.5;\n"
"    }\n"
"    return v;\n"
"}\n"
"\n"
"float4 main(vo i) : SV_TARGET {\n"
"    float2 uv = i.uv;\n"
"    float t = i.time * 0.25;\n"
"\n"
"    float2 p = uv * 3.0;\n"
"    float f1 = fbm(p + float2(t * 0.7, t * 0.4));\n"
"    float f2 = fbm(p + float2(f1 * 1.5 + t * 0.1, f1 * 1.2 - t * 0.2));\n"
"    float f3 = fbm(p + float2(f2 * 1.8 - t * 0.3, f2 * 0.9 + t * 0.5));\n"
"\n"
"    float3 c1 = float3(0.02, 0.01, 0.08);\n"
"    float3 c2 = float3(0.08, 0.3, 0.7);\n"
"    float3 c3 = float3(0.5, 0.08, 0.75);\n"
"    float3 c4 = float3(0.0, 0.7, 0.5);\n"
"\n"
"    float3 col = c1;\n"
"    col = lerp(col, c2, smoothstep(0.0, 0.6, f1));\n"
"    col = lerp(col, c3, smoothstep(0.2, 0.8, f2));\n"
"    col = lerp(col, c4, smoothstep(0.3, 0.7, f3 * f1));\n"
"\n"
"    col += float3(0.3, 0.15, 0.5) * pow(f3, 3.0) * 1.2;\n"
"\n"
"    float vignette = 1.0 - length((uv - 0.5) * 1.4);\n"
"    vignette = smoothstep(0.0, 0.7, vignette);\n"
"    col *= vignette;\n"
"\n"
"    float edge = smoothstep(0.0, 0.06, uv.x) * smoothstep(0.0, 0.06, uv.y)\n"
"               * smoothstep(0.0, 0.06, 1.0 - uv.x) * smoothstep(0.0, 0.06, 1.0 - uv.y);\n"
"\n"
"    float alpha = saturate(length(col) * 1.2) * edge * 0.9;\n"
"    return float4(col * alpha, alpha);\n"
"}\n";

uint64 g_shader = 0;
uint64 g_vb = 0;
uint64 g_cb = 0;
uint64 g_blend = 0;
int g_cb_id = 0;
float g_time = 0.0f;

void pack_float(array<uint8> &buf, int offset, float val)
{
    uint bits = fpToIEEE(val);
    buf[offset + 0] = uint8(bits & 0xFF);
    buf[offset + 1] = uint8((bits >> 8) & 0xFF);
    buf[offset + 2] = uint8((bits >> 16) & 0xFF);
    buf[offset + 3] = uint8((bits >> 24) & 0xFF);
}

void pack_quad(array<uint8> &buf, int offset,
    float x0, float y0, float x1, float y1)
{
    int o = offset;
    pack_float(buf, o,    x0); pack_float(buf, o+4,  y0);
    pack_float(buf, o+8,  0.0f); pack_float(buf, o+12, 0.0f); o += 16;
    pack_float(buf, o,    x1); pack_float(buf, o+4,  y0);
    pack_float(buf, o+8,  1.0f); pack_float(buf, o+12, 0.0f); o += 16;
    pack_float(buf, o,    x0); pack_float(buf, o+4,  y1);
    pack_float(buf, o+8,  0.0f); pack_float(buf, o+12, 1.0f); o += 16;
    pack_float(buf, o,    x1); pack_float(buf, o+4,  y0);
    pack_float(buf, o+8,  1.0f); pack_float(buf, o+12, 0.0f); o += 16;
    pack_float(buf, o,    x1); pack_float(buf, o+4,  y1);
    pack_float(buf, o+8,  1.0f); pack_float(buf, o+12, 1.0f); o += 16;
    pack_float(buf, o,    x0); pack_float(buf, o+4,  y1);
    pack_float(buf, o+8,  0.0f); pack_float(buf, o+12, 1.0f);
}

void on_frame(int cb_id, int data)
{
    double fps = get_fps();
    if (fps > 0.0)
        g_time += float(1.0 / fps);

    float sw, sh;
    get_view(sw, sh);

    float panel_w = 440.0f;
    float panel_h = 270.0f;
    float panel_x = (sw - panel_w) * 0.5f;
    float panel_y = (sh - panel_h) * 0.5f - 60.0f;

    draw_rect_filled(panel_x - 2, panel_y - 2, panel_w + 4, panel_h + 4,
        120, 80, 200, 35, 12.0f,
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT);

    array<uint8> verts(6 * 16);
    pack_quad(verts, 0, panel_x, panel_y, panel_x + panel_w, panel_y + panel_h);

    array<uint8> cb_data(16);
    pack_float(cb_data, 0,  sw);
    pack_float(cb_data, 4,  sh);
    pack_float(cb_data, 8,  g_time);
    pack_float(cb_data, 12, 0.0f);

    custom_draw(g_shader, g_vb, verts, 6, TOPO_TRIANGLE_LIST,
        g_blend, 0, 0, 0,
        g_cb, cb_data, 0);

    draw_rect(panel_x - 1, panel_y - 1, panel_w + 2, panel_h + 2,
        255, 255, 255, 25, 1.0f, 12.0f,
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT);

    uint64 font = get_font18();
    float tw, th;

    string title = "Perception.cx";
    get_text_size(font, title, -1, -1, tw, th);
    draw_text(title, panel_x + (panel_w - tw) * 0.5f, panel_y + panel_h + 12,
        200, 180, 255, 190, font, TE_NONE, 0, 0, 0, 0, 0.0f);

    string info = "FPS: " + formatFloat(fps, "", 0, 1);
    get_text_size(font, info, -1, -1, tw, th);
    draw_text(info, panel_x + (panel_w - tw) * 0.5f, panel_y + panel_h + 32,
        140, 140, 140, 130, font, TE_NONE, 0, 0, 0, 0, 0.0f);
}

int main()
{
    g_shader = create_shader(vs_src, ps_src, "POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");

    if (g_shader == 0)
    {
        log_error("shader compilation failed");
        return -1;
    }

    g_vb    = create_vertex_buffer(16, 64, true);
    g_cb    = create_constant_buffer(16);
    g_blend = create_blend_state(BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);

    if (g_vb == 0 || g_cb == 0 || g_blend == 0)
    {
        log_error("resource creation failed");
        return -1;
    }

    log("custom shader test loaded");
    g_cb_id = register_callback(@on_frame, 1, 0);
    return 1;
}

void on_unload()
{
    if (g_cb_id > 0)
        unregister_callback(g_cb_id);

    if (g_shader != 0) destroy_shader(g_shader);
    if (g_vb != 0)     destroy_vertex_buffer(g_vb);
    if (g_cb != 0)     destroy_constant_buffer(g_cb);
    if (g_blend != 0)  destroy_blend_state(g_blend);

    log("custom shader test unloaded");
}
```

***

**🧪 Example: Full API Test**

```cpp
string vs_uv =
"cbuffer cb:register(b0){float2 screen;float time;float pad;};\n"
"struct vi{float2 pos:POSITION;float2 uv:TEXCOORD0;};\n"
"struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
"vo main(vi i){vo o;\n"
"  o.pos=float4(i.pos.x/screen.x*2-1,1-i.pos.y/screen.y*2,0,1);\n"
"  o.uv=i.uv;o.time=time;return o;}\n";

string ps_nebula =
"struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
"float hash(float2 p){float3 p3=frac(float3(p.xyx)*0.1031);p3+=dot(p3,p3.yzx+33.33);return frac((p3.x+p3.y)*p3.z);}\n"
"float noise(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);\n"
"  return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+float2(1,1)),f.x),f.y);}\n"
"float fbm(float2 p){float v=0,a=0.5;float2x2 r={0.8,0.6,-0.6,0.8};\n"
"  for(int i=0;i<5;i++){v+=a*noise(p);p=mul(r,p)*2;a*=0.5;}return v;}\n"
"float4 main(vo i):SV_TARGET{\n"
"  float t=i.time*0.25;float2 p=i.uv*3;\n"
"  float f1=fbm(p+float2(t*0.7,t*0.4));\n"
"  float f2=fbm(p+float2(f1*1.5+t*0.1,f1*1.2-t*0.2));\n"
"  float f3=fbm(p+float2(f2*1.8-t*0.3,f2*0.9+t*0.5));\n"
"  float3 c=float3(0.02,0.01,0.08);\n"
"  c=lerp(c,float3(0.08,0.3,0.7),smoothstep(0,0.6,f1));\n"
"  c=lerp(c,float3(0.5,0.08,0.75),smoothstep(0.2,0.8,f2));\n"
"  c=lerp(c,float3(0,0.7,0.5),smoothstep(0.3,0.7,f3*f1));\n"
"  c+=float3(0.3,0.15,0.5)*pow(f3,3)*1.2;\n"
"  float v=smoothstep(0,0.7,1-length((i.uv-0.5)*1.4));\n"
"  float e=smoothstep(0,0.05,i.uv.x)*smoothstep(0,0.05,i.uv.y)*smoothstep(0,0.05,1-i.uv.x)*smoothstep(0,0.05,1-i.uv.y);\n"
"  float a=saturate(length(c)*1.2)*v*e*0.92;\n"
"  return float4(c*a,a);}\n";

string ps_tex =
"Texture2D tex0:register(t0);SamplerState samp0:register(s0);\n"
"struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
"float4 main(vo i):SV_TARGET{float4 c=tex0.Sample(samp0,i.uv);return float4(c.rgb*c.a,c.a);}\n";

string vs_col =
"cbuffer cb:register(b0){float2 screen;float time;float pad;};\n"
"struct vi{float2 pos:POSITION;float4 col:COLOR;};\n"
"struct vo{float4 pos:SV_POSITION;float4 col:COLOR;};\n"
"vo main(vi i){vo o;o.pos=float4(i.pos.x/screen.x*2-1,1-i.pos.y/screen.y*2,0,1);o.col=i.col;return o;}\n";

string ps_col =
"struct vo{float4 pos:SV_POSITION;float4 col:COLOR;};\n"
"float4 main(vo i):SV_TARGET{return float4(i.col.rgb*i.col.a,i.col.a);}\n";

uint64 g_sh_nebula=0, g_sh_tex=0, g_sh_col=0;
uint64 g_vb_uv=0, g_vb_col=0, g_cb=0, g_blend=0;
uint64 g_samp_linear=0, g_samp_point=0;
uint64 g_texture=0, g_rt=0;
int g_cb_id=0;
float g_time=0;

void pf(array<uint8> &b,int o,float v){uint bits=fpToIEEE(v);b[o]=uint8(bits&0xFF);b[o+1]=uint8((bits>>8)&0xFF);b[o+2]=uint8((bits>>16)&0xFF);b[o+3]=uint8((bits>>24)&0xFF);}

int vu(array<uint8> &b,int o,float x,float y,float u,float v){pf(b,o,x);pf(b,o+4,y);pf(b,o+8,u);pf(b,o+12,v);return o+16;}
int vc(array<uint8> &b,int o,float x,float y,float r,float g,float bl,float a){pf(b,o,x);pf(b,o+4,y);pf(b,o+8,r);pf(b,o+12,g);pf(b,o+16,bl);pf(b,o+20,a);return o+24;}

int qu(array<uint8> &b,int o,float x0,float y0,float x1,float y1){
    o=vu(b,o,x0,y0,0,0);o=vu(b,o,x1,y0,1,0);o=vu(b,o,x0,y1,0,1);
    o=vu(b,o,x1,y0,1,0);o=vu(b,o,x1,y1,1,1);o=vu(b,o,x0,y1,0,1);return o;}

array<uint8> mcb(float sw,float sh){array<uint8> c(16);pf(c,0,sw);pf(c,4,sh);pf(c,8,g_time);pf(c,12,0);return c;}

void label(uint64 font,float cx,float y,const string &in text,uint8 a=180){
    float tw,th; get_text_size(font,text,-1,-1,tw,th);
    draw_text(text,cx-tw*0.5f,y,190,175,235,a,font,TE_NONE,0,0,0,0,0);
}

void sublabel(uint64 font,float cx,float y,const string &in text){
    float tw,th; get_text_size(font,text,-1,-1,tw,th);
    draw_text(text,cx-tw*0.5f,y,140,135,160,140,font,TE_NONE,0,0,0,0,0);
}

void border(float x,float y,float w,float h,float r=6){
    draw_rect(x-1,y-1,w+2,h+2,255,255,255,25,1,r,RR_TOP_LEFT|RR_TOP_RIGHT|RR_BOTTOM_LEFT|RR_BOTTOM_RIGHT);
}

void on_frame(int cb_id,int data)
{
    double fps=get_fps();
    if(fps>0) g_time+=float(1.0/fps);

    float sw,sh; get_view(sw,sh);
    array<uint8> cb_data=mcb(sw,sh);
    uint64 font=get_font18();

    float total_w=780, total_h=340;
    float ox=(sw-total_w)*0.5f;
    float oy=(sh-total_h)*0.5f;
    float row1_y=oy+30;
    float gap=15;

    // title
    draw_rect_filled(ox-10,oy-10,total_w+20,total_h+20,20,15,35,140,12,
        RR_TOP_LEFT|RR_TOP_RIGHT|RR_BOTTOM_LEFT|RR_BOTTOM_RIGHT);
    border(ox-10,oy-10,total_w+20,total_h+20,12);
    label(font,ox+total_w*0.5f,oy+2,"Perception.cx  -  Custom Draw API Test",220);

    float p1x=ox, p1y=row1_y, p1w=300, p1h=200;
    {
        custom_set_render_target(g_rt);

        array<uint8> rt_cb(16);
        pf(rt_cb,0,320);pf(rt_cb,4,200);pf(rt_cb,8,g_time);pf(rt_cb,12,0);

        array<uint8> rv(6*16);int o=0;
        o=qu(rv,o,0,0,320,200);

        custom_draw(g_sh_nebula,g_vb_uv,rv,6,TOPO_TRIANGLE_LIST,g_blend,0,0,0,g_cb,rt_cb,0);
        custom_reset_render_target();

        custom_bind_rt_as_texture(g_rt,0);
        array<uint8> sv(6*16);o=0;
        o=qu(sv,o,p1x,p1y,p1x+p1w,p1y+p1h);
        custom_draw(g_sh_tex,g_vb_uv,sv,6,TOPO_TRIANGLE_LIST,g_blend,g_samp_linear,0,0,g_cb,cb_data,0);
        custom_restore_state();

        border(p1x,p1y,p1w,p1h);
        label(font,p1x+p1w*0.5f,p1y+p1h+6,"Render Target -> Blit");
        sublabel(font,p1x+p1w*0.5f,p1y+p1h+24,"set_rt / reset_rt / bind_rt / restore");
    }

    float p2x=p1x+p1w+gap, p2y=row1_y, p2w=150, p2h=200;
    {
        float half=p2w*0.5f;

        array<uint8> lv(6*16);int o=0;
        o=qu(lv,o,p2x,p2y,p2x+half,p2y+p2h);
        custom_draw(g_sh_tex,g_vb_uv,lv,6,TOPO_TRIANGLE_LIST,g_blend,g_samp_linear,g_texture,0,g_cb,cb_data,0);

        array<uint8> rv(6*16);o=0;
        o=qu(rv,o,p2x+half,p2y,p2x+p2w,p2y+p2h);
        custom_draw(g_sh_tex,g_vb_uv,rv,6,TOPO_TRIANGLE_LIST,g_blend,g_samp_point,g_texture,0,g_cb,cb_data,0);

        border(p2x,p2y,p2w,p2h,0);
        draw_line(p2x+half,p2y,p2x+half,p2y+p2h,255,255,255,40,1);

        label(font,p2x+p2w*0.5f,p2y+p2h+6,"LINEAR | POINT");
        sublabel(font,p2x+p2w*0.5f,p2y+p2h+24,"texture + sampler");
    }
    
    float p3x=p2x+p2w+gap, p3y=row1_y, p3w=300, p3h=200;
    {
        draw_rect_filled(p3x,p3y,p3w,p3h,15,12,30,100,6,
            RR_TOP_LEFT|RR_TOP_RIGHT|RR_BOTTOM_LEFT|RR_BOTTOM_RIGHT);
        border(p3x,p3y,p3w,p3h);

        float sec=p3h/5.0f;
        float ty=p3y;
        float draw_x=p3x+p3w*0.45f;
        float draw_w=p3w*0.48f;

        // TRIANGLE_LIST
        {
            array<uint8> v(3*24);int o=0;
            float cx=draw_x+draw_w*0.5f;
            o=vc(v,o,cx,ty+6,1,0.2f,0.2f,1);
            o=vc(v,o,cx+16,ty+sec-6,0.2f,1,0.2f,1);
            o=vc(v,o,cx-16,ty+sec-6,0.2f,0.2f,1,1);
            custom_draw(g_sh_col,g_vb_col,v,3,TOPO_TRIANGLE_LIST,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("TRIANGLE_LIST",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
            ty+=sec;
        }

        // TRIANGLE_STRIP
        {
            array<uint8> v(4*24);int o=0;
            float lx=draw_x+draw_w*0.3f;
            o=vc(v,o,lx,ty+6,1,0.6f,0,1);
            o=vc(v,o,lx+30,ty+6,1,0.9f,0.2f,1);
            o=vc(v,o,lx+8,ty+sec-6,0.9f,1,0.3f,1);
            o=vc(v,o,lx+38,ty+sec-6,1,1,0.5f,1);
            custom_draw(g_sh_col,g_vb_col,v,4,TOPO_TRIANGLE_STRIP,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("TRIANGLE_STRIP",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
            ty+=sec;
        }

        // LINE_LIST
        {
            array<uint8> v(4*24);int o=0;
            float lx=draw_x+draw_w*0.2f;
            o=vc(v,o,lx,ty+8,0,1,1,1);
            o=vc(v,o,lx+draw_w*0.5f,ty+sec-8,0,1,1,1);
            o=vc(v,o,lx+15,ty+8,1,0,1,1);
            o=vc(v,o,lx+draw_w*0.5f+15,ty+sec-8,1,0,1,1);
            custom_draw(g_sh_col,g_vb_col,v,4,TOPO_LINE_LIST,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("LINE_LIST",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
            ty+=sec;
        }

        // LINE_STRIP (animated)
        {
            array<uint8> v(8*24);int o=0;
            for(int i=0;i<8;i++){
                float f=float(i)/7.0f;
                float lx=draw_x+draw_w*0.15f+f*draw_w*0.7f;
                float ly=ty+sec*0.5f+sin(g_time*3+f*6.28f)*12;
                o=vc(v,o,lx,ly,f,1-f,0.5f,1);
            }
            custom_draw(g_sh_col,g_vb_col,v,8,TOPO_LINE_STRIP,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("LINE_STRIP",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
            ty+=sec;
        }

        // POINT_LIST
        {
            array<uint8> v(12*24);int o=0;
            for(int i=0;i<12;i++){
                float f=float(i)/11.0f;
                float px=draw_x+draw_w*0.15f+f*draw_w*0.7f;
                float py=ty+sec*0.5f+sin(f*6.28f*2+g_time)*6;
                o=vc(v,o,px,py,1,1,1,0.9f);
            }
            custom_draw(g_sh_col,g_vb_col,v,12,TOPO_POINT_LIST,g_blend,0,0,0,g_cb,cb_data,0);
            draw_text("POINT_LIST",p3x+8,ty+sec*0.5f-7,130,130,130,160,font,TE_NONE,0,0,0,0,0);
        }

        label(font,p3x+p3w*0.5f,p3y+p3h+6,"All Topologies");
        sublabel(font,p3x+p3w*0.5f,p3y+p3h+24,"5 primitive types + per-vertex color");
    }
    
    string s="FPS: "+formatFloat(fps,"",0,1)+"   |   3 shaders   2 VBs   1 CB   1 blend   2 samplers   1 texture   1 RT   5 topologies";
    sublabel(font,ox+total_w*0.5f,oy+total_h-12,s);
}

array<uint8> make_checker(uint sz,uint tile){
    array<uint8> d(sz*sz*4);
    for(uint y=0;y<sz;y++){
        for(uint x=0;x<sz;x++){
            uint i=(y*sz+x)*4;
            bool w=(((x/tile)+(y/tile))%2)==0;
            d[i]=w?230:30;d[i+1]=w?220:30;d[i+2]=w?250:70;d[i+3]=255;
        }
    }
    return d;
}

int main()
{
    g_sh_nebula=create_shader(vs_uv,ps_nebula,"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");
    g_sh_tex=create_shader(vs_uv,ps_tex,"POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");
    g_sh_col=create_shader(vs_col,ps_col,"POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    if(g_sh_nebula==0||g_sh_tex==0||g_sh_col==0){log_error("shader fail");return 1;}

    g_vb_uv=create_vertex_buffer(16,128,true);
    g_vb_col=create_vertex_buffer(24,128,true);
    if(g_vb_uv==0||g_vb_col==0){log_error("vb fail");return 1;}

    g_cb=create_constant_buffer(16);
    if(g_cb==0){log_error("cb fail");return 1;}

    g_blend=create_blend_state(BLEND_ONE,BLEND_INV_SRC_ALPHA,BLEND_OP_ADD,BLEND_ONE,BLEND_INV_SRC_ALPHA,BLEND_OP_ADD);
    if(g_blend==0){log_error("blend fail");return 1;}

    g_samp_linear=create_sampler(FILTER_LINEAR,ADDRESS_CLAMP,ADDRESS_CLAMP);
    g_samp_point=create_sampler(FILTER_POINT,ADDRESS_WRAP,ADDRESS_WRAP);
    if(g_samp_linear==0||g_samp_point==0){log_error("sampler fail");return 1;}

    array<uint8> checker=make_checker(8,2);
    g_texture=create_texture(8,8,checker);
    if(g_texture==0){log_error("texture fail");return 1;}

    g_rt=create_render_target(320,200);
    if(g_rt==0){log_error("rt fail");return 1;}

    log("custom draw test loaded — all resources created");
    g_cb_id=register_callback(@on_frame,1,0);
    return 1;
}

void on_unload()
{
    if(g_cb_id>0) unregister_callback(g_cb_id);
    if(g_sh_nebula!=0) destroy_shader(g_sh_nebula);
    if(g_sh_tex!=0) destroy_shader(g_sh_tex);
    if(g_sh_col!=0) destroy_shader(g_sh_col);
    if(g_vb_uv!=0) destroy_vertex_buffer(g_vb_uv);
    if(g_vb_col!=0) destroy_vertex_buffer(g_vb_col);
    if(g_cb!=0) destroy_constant_buffer(g_cb);
    if(g_blend!=0) destroy_blend_state(g_blend);
    if(g_samp_linear!=0) destroy_sampler(g_samp_linear);
    if(g_samp_point!=0) destroy_sampler(g_samp_point);
    if(g_texture!=0) destroy_texture(g_texture);
    if(g_rt!=0) destroy_render_target(g_rt);
    log("custom draw test unloaded");
}
```

***

**🧪 Example: Full API Test 2 — Advanced (3D, Compute, Mesh Loading)**

```cpp
uint64 g_sh_2d, g_sh_mat, g_sh_sb, g_sh_bb, g_sh_mesh_tex;
uint64 g_cs;
uint64 g_vb, g_cb_scr, g_cb_mvp, g_cb_mat;
uint64 g_blend, g_samp_lin, g_samp_pt;
uint64 g_rt, g_db, g_ds_on, g_ds_off, g_rs_nc;
uint64 g_mesh_pyr, g_mesh_quad;
uint64 g_tex_loaded, g_tex_dyn;
uint64 g_sb_gpu, g_sb_params;
int g_cb_id = 0;
float g_time = 0;
bool g_ok = false;

void wf(array<uint8> &buf, uint off, float val) {
    if (val == 0.0f) { buf[off]=0; buf[off+1]=0; buf[off+2]=0; buf[off+3]=0; return; }
    int s = 0;
    float v = val;
    if (v < 0.0f) { s = 1; v = -v; }
    int e = 127;
    while (v >= 2.0f && e < 254) { v /= 2.0f; e++; }
    while (v < 1.0f && e > 1) { v *= 2.0f; e--; }
    v -= 1.0f;
    uint m = uint(v * 8388608.0f);
    uint bits = uint(s) << 31 | uint(e) << 23 | (m & 0x7FFFFF);
    buf[off]   = uint8(bits & 0xFF);
    buf[off+1] = uint8((bits >> 8) & 0xFF);
    buf[off+2] = uint8((bits >> 16) & 0xFF);
    buf[off+3] = uint8((bits >> 24) & 0xFF);
}

float rf(const array<uint8> &buf, uint off) {
    uint bits = uint(buf[off]) | (uint(buf[off+1]) << 8) | (uint(buf[off+2]) << 16) | (uint(buf[off+3]) << 24);
    if (bits == 0) return 0.0f;
    int s = int((bits >> 31) & 1);
    int e = int((bits >> 23) & 0xFF) - 127;
    float val = 1.0f + float(bits & 0x7FFFFF) / 8388608.0f;
    if (e > 0) { for (int i = 0; i < e; i++) val *= 2.0f; }
    else if (e < 0) { for (int i = 0; i < -e; i++) val /= 2.0f; }
    return s != 0 ? -val : val;
}

array<uint8> fb(float a, float b, float c, float d) {
    array<uint8> r(16, 0);
    wf(r, 0, a); wf(r, 4, b); wf(r, 8, c); wf(r, 12, d);
    return r;
}

array<uint8> mat4_persp(float fov, float asp, float zn, float zf) {
    float f = cos(fov * 0.5f) / sin(fov * 0.5f);
    float r = zn - zf;
    array<uint8> m(64, 0);
    wf(m, 0, f / asp); wf(m, 20, f);
    wf(m, 40, (zf + zn) / r); wf(m, 44, -1);
    wf(m, 56, (2 * zf * zn) / r);
    return m;
}

array<uint8> mat4_roty(float a) {
    float c = cos(a), s = sin(a);
    array<uint8> m(64, 0);
    wf(m, 0, c); wf(m, 8, s); wf(m, 20, 1);
    wf(m, 32, -s); wf(m, 40, c);
    wf(m, 60, 1);
    return m;
}

array<uint8> mat4_rotx(float a) {
    float c = cos(a), s = sin(a);
    array<uint8> m(64, 0);
    wf(m, 0, 1); wf(m, 20, c); wf(m, 24, -s);
    wf(m, 36, s); wf(m, 40, c);
    wf(m, 60, 1);
    return m;
}

array<uint8> mat4_trans(float tx, float ty, float tz) {
    array<uint8> m(64, 0);
    wf(m, 0, 1); wf(m, 20, 1); wf(m, 40, 1);
    wf(m, 48, tx); wf(m, 52, ty); wf(m, 56, tz); wf(m, 60, 1);
    return m;
}

array<uint8> mat4_mul(const array<uint8> &a, const array<uint8> &b) {
    array<float> fa(16), fb2(16);
    for (uint i = 0; i < 16; i++) { fa[i] = rf(a, i * 4); fb2[i] = rf(b, i * 4); }
    array<uint8> r(64, 0);
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++) {
            float s = 0;
            for (int k = 0; k < 4; k++) s += fa[i * 4 + k] * fb2[k * 4 + j];
            wf(r, uint((i * 4 + j) * 4), s);
        }
    return r;
}

void quad_verts(array<uint8> &buf, uint off, float x0, float y0, float x1, float y1) {
    wf(buf, off,      x0); wf(buf, off + 4,  y0); wf(buf, off + 8,  0); wf(buf, off + 12, 0);
    wf(buf, off + 16, x1); wf(buf, off + 20, y0); wf(buf, off + 24, 1); wf(buf, off + 28, 0);
    wf(buf, off + 32, x1); wf(buf, off + 36, y1); wf(buf, off + 40, 1); wf(buf, off + 44, 1);
    wf(buf, off + 48, x0); wf(buf, off + 52, y0); wf(buf, off + 56, 0); wf(buf, off + 60, 0);
    wf(buf, off + 64, x1); wf(buf, off + 68, y1); wf(buf, off + 72, 1); wf(buf, off + 76, 1);
    wf(buf, off + 80, x0); wf(buf, off + 84, y1); wf(buf, off + 88, 0); wf(buf, off + 92, 1);
}

string g_vs_2d =
    "cbuffer cb:register(b0){float2 screen;float time;float pad;};\n"
    "struct vi{float2 pos:POSITION;float2 uv:TEXCOORD0;};\n"
    "struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
    "vo main(vi i){vo o;o.pos=float4(i.pos.x/screen.x*2-1,-(i.pos.y/screen.y*2-1),0,1);o.uv=i.uv;o.time=time;return o;}\n";

string g_ps_tex =
    "Texture2D tex0:register(t0);SamplerState samp0:register(s0);\n"
    "struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{return tex0.Sample(samp0,i.uv);}\n";

string g_vs_mesh =
    "cbuffer cb:register(b0){float4x4 mvp;};\n"
    "struct vi{float3 pos:POSITION;float3 norm:NORMAL;float2 uv:TEXCOORD0;};\n"
    "struct vo{float4 pos:SV_POSITION;float3 norm:TEXCOORD0;float2 uv:TEXCOORD1;};\n"
    "vo main(vi i){vo o;o.pos=mul(mvp,float4(i.pos,1));o.norm=i.norm;o.uv=i.uv;return o;}\n";

string g_ps_mat =
    "cbuffer cb_mat:register(b1){float4 mat_color;};\n"
    "struct vo{float4 pos:SV_POSITION;float3 norm:TEXCOORD0;float2 uv:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  float3 L=normalize(float3(0.4,0.8,0.6));\n"
    "  float ndl=saturate(dot(normalize(i.norm),L));\n"
    "  float3 col=mat_color.rgb*(ndl*0.7+0.3);\n"
    "  return float4(col,mat_color.a);}\n";

string g_ps_lit =
    "struct vo{float4 pos:SV_POSITION;float3 norm:TEXCOORD0;float2 uv:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  float3 L=normalize(float3(0.5,1.0,0.3));\n"
    "  float ndl=saturate(dot(normalize(i.norm),L));\n"
    "  return float4(float3(0.2,0.6,1.0)*ndl+float3(0.05,0.05,0.1),1);}\n";

string g_ps_mesh_tex =
    "Texture2D tex0:register(t0);SamplerState samp0:register(s0);\n"
    "struct vo{float4 pos:SV_POSITION;float3 norm:TEXCOORD0;float2 uv:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  float3 L=normalize(float3(0.5,1.0,0.3));\n"
    "  float ndl=saturate(dot(normalize(i.norm),L));\n"
    "  float4 tc=tex0.Sample(samp0,i.uv);\n"
    "  return float4(tc.rgb*(ndl*0.8+0.2),1);}\n";

string g_ps_sb_vis =
    "StructuredBuffer<float4> colors:register(t0);\n"
    "struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  uint x=clamp(uint(i.uv.x*16),0,15);\n"
    "  uint y=clamp(uint(i.uv.y*16),0,15);\n"
    "  return float4(colors[y*16+x].rgb,1);}\n";

string g_cs_src =
    "StructuredBuffer<float4> params:register(t1);\n"
    "RWStructuredBuffer<float4> buf:register(u0);\n"
    "[numthreads(16,16,1)] void main(uint3 id:SV_DispatchThreadID){\n"
    "  uint idx=id.y*16+id.x;\n"
    "  float t=params[0].x;\n"
    "  float u=id.x/15.0,v=id.y/15.0;\n"
    "  float r=0.5+0.5*sin(t*2+u*6.28);\n"
    "  float g=0.5+0.5*sin(t*1.5+v*6.28);\n"
    "  float b=0.5+0.5*cos(t+(u+v)*3.14);\n"
    "  buf[idx]=float4(r,g,b,1);}\n";

string g_ps_bb =
    "Texture2D tex0:register(t0);SamplerState samp0:register(s0);\n"
    "struct vo{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float time:TEXCOORD1;};\n"
    "float4 main(vo i):SV_TARGET{\n"
    "  float4 c=tex0.Sample(samp0,i.uv);\n"
    "  float3 inv=1.0-c.rgb;\n"
    "  float br=max(max(c.r,c.g),c.b);\n"
    "  return float4(br>0.01?inv:float3(0.12,0.12,0.18),1);}\n";

string g_obj =
    "v 0 0.8 0\nv -0.6 -0.5 0.6\nv 0.6 -0.5 0.6\nv 0.6 -0.5 -0.6\nv -0.6 -0.5 -0.6\n"
    "vn 0 0.447 0.894\nvn 0.894 0.447 0\nvn 0 0.447 -0.894\nvn -0.894 0.447 0\nvn 0 -1 0\n"
    "vt 0.5 1\nvt 0 0\nvt 1 0\n"
    "f 1/1/1 2/2/1 3/3/1\nf 1/1/2 3/2/2 4/3/2\nf 1/1/3 4/2/3 5/3/3\nf 1/1/4 5/2/4 2/3/4\n"
    "f 2/2/5 5/3/5 4/2/5\nf 2/2/5 4/2/5 3/3/5\n";

uint64 g_sh_lit;

void label(float x, float y, string text, uint8 r, uint8 g, uint8 b) {
    draw_text(text, x, y, r, g, b, 255, get_font18(), 0, 0, 0, 0, 0, 0.0f);
}

void border(float x, float y, float w, float h, uint8 r, uint8 g, uint8 b) {
    draw_rect(x - 2, y - 2, w + 4, h + 4, r, g, b, 255, 2, 0.0f, 0);
}

void render_cb(int callback_id, int data_index) {
    if (!g_ok) {
        draw_text("INIT FAILED", 100, 100, 255, 80, 80, 255, get_font24(), 0, 0, 0, 0, 0, 0.0f);
        return;
    }

    g_time += 0.016f;
    float sw = 0, sh = 0;
    get_view(sw, sh);
    array<uint8> cb_scr = fb(sw, sh, g_time, 0);

    float total_w = 740, total_h = 620;
    float ox = (sw - total_w) * 0.5f;
    float oy = (sh - total_h) * 0.5f;
    float gap = 14;
    float lbl_h = 22;

    draw_rect_filled(ox - 16, oy - 40, total_w + 32, total_h + 56, 10, 10, 18, 220, 6.0f, 0);
    draw_text("PCX Draw API - All 26 New Functions", ox, oy - 28, 200, 220, 255, 255, get_font20(), 0, 0, 0, 0, 0, 0.0f);

    // ===== ROW 1 =====
    float r1y = oy + 4;

    // A: Compute Shader + Structured Buffer
    float aw = 230, ah = 150;
    float ax = ox, ay = r1y + lbl_h;
    label(ax + 4, r1y, "A: Compute Shader + SB", 0, 255, 0);
    border(ax, ay, aw, ah, 0, 255, 0);

    array<uint8> params_data = fb(g_time, 0, 0, 0);
    update_structured_buffer(g_sb_params, params_data);
    bind_structured_buffer(g_sb_params, 1, STAGE_CS);
    bind_structured_buffer(g_sb_gpu, 0, STAGE_CS);
    dispatch_compute(g_cs, 1, 1, 1);
    bind_structured_buffer(g_sb_gpu, 0, STAGE_PS);
    array<uint8> va(96, 0);
    quad_verts(va, 0, ax, ay, ax + aw, ay + ah);
    custom_draw(g_sh_sb, g_vb, va, 6, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, g_cb_scr, cb_scr, 0);
    custom_restore_state();

    // B: Depth Buffer + draw_mesh into RT
    float bw = total_w - aw - gap, bh = ah + lbl_h;
    float bx = ax + aw + gap, by = r1y + lbl_h;
    label(bx + 4, r1y, "B: Depth Buffer + Multi-CB", 255, 160, 0);
    border(bx, by, bw, ah, 255, 160, 0);

    custom_set_render_target_ext(g_rt, g_db);
    custom_clear_render_target(g_rt, 0.04f, 0.04f, 0.08f, 1.0f);
    custom_clear_depth_buffer(g_db);
    custom_set_rasterizer_state(g_rs_nc);
    custom_set_depth_stencil_state(g_ds_on);

    array<uint8> proj = mat4_persp(1.0f, 256.0f / 180.0f, 0.1f, 100.0f);
    array<uint8> rxm = mat4_rotx(0.4f);

    array<uint8> ry1 = mat4_roty(g_time * 0.9f);
    array<uint8> t1 = mat4_trans(-0.5f, 0, -3.5f);
    array<uint8> tmp1 = mat4_mul(ry1, rxm);
    array<uint8> tmp2 = mat4_mul(tmp1, t1);
    array<uint8> mvp1 = mat4_mul(tmp2, proj);
    array<uint8> mat_blue = fb(0.2f, 0.4f, 1.0f, 1.0f);
    custom_bind_constant_buffer(g_cb_mat, mat_blue, 1, STAGE_PS);
    draw_mesh(g_mesh_pyr, g_sh_mat, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, g_cb_mvp, mvp1, 0);

    array<uint8> ry2 = mat4_roty(g_time * 0.9f + 0.6f);
    array<uint8> t2 = mat4_trans(0.5f, 0, -2.5f);
    array<uint8> tmp3 = mat4_mul(ry2, rxm);
    array<uint8> tmp4 = mat4_mul(tmp3, t2);
    array<uint8> mvp2 = mat4_mul(tmp4, proj);
    array<uint8> mat_red = fb(1.0f, 0.25f, 0.15f, 1.0f);
    custom_bind_constant_buffer(g_cb_mat, mat_red, 1, STAGE_PS);
    draw_mesh(g_mesh_pyr, g_sh_mat, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, g_cb_mvp, mvp2, 0);

    custom_reset_render_target();
    custom_set_rasterizer_state(0);
    custom_set_depth_stencil_state(0);
    custom_bind_rt_as_texture(g_rt, 0);
    array<uint8> vb2(96, 0);
    quad_verts(vb2, 0, bx, by, bx + bw, by + ah);
    custom_draw(g_sh_2d, g_vb, vb2, 6, TOPO_TRIANGLE_LIST, g_blend, g_samp_lin, 0, 0, g_cb_scr, cb_scr, 0);
    custom_restore_state();

    // ===== ROW 2 =====
    float r2y = ay + ah + gap;

    // C: Loaded Texture
    float cw = 160, ch = 120;
    float cx2 = ox, cy = r2y + lbl_h;
    label(cx2 + 4, r2y, "C: Texture Load", 255, 0, 255);
    border(cx2, cy, cw, ch, 255, 0, 255);
    custom_bind_texture(g_tex_loaded, g_samp_pt, 0);
    array<uint8> vc(96, 0);
    quad_verts(vc, 0, cx2, cy, cx2 + cw, cy + ch);
    custom_draw(g_sh_2d, g_vb, vc, 6, TOPO_TRIANGLE_LIST, g_blend, g_samp_pt, g_tex_loaded, 0, g_cb_scr, cb_scr, 0);
    custom_restore_state();

    // D: Lit Mesh
    float dw = 190, dh = 120;
    float dx2 = cx2 + cw + gap, dy = r2y + lbl_h;
    label(dx2 + 4, r2y, "D: Lit Mesh", 255, 50, 50);
    border(dx2, dy, dw, dh, 255, 50, 50);
    {
        array<uint8> projd = mat4_persp(1.0f, dw / dh, 0.1f, 100.0f);
        array<uint8> ryd = mat4_roty(g_time * 1.2f);
        array<uint8> rxd = mat4_rotx(0.3f);
        array<uint8> td = mat4_trans(0, 0, -3.0f);
        array<uint8> t1d = mat4_mul(ryd, rxd);
        array<uint8> t2d = mat4_mul(t1d, td);
        array<uint8> mvpd = mat4_mul(t2d, projd);

        custom_set_viewport(dx2, dy, dw, dh);
        custom_set_rasterizer_state(g_rs_nc);
        custom_set_depth_stencil_state(g_ds_off);
        draw_mesh(g_mesh_pyr, g_sh_lit, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, g_cb_mvp, mvpd, 0);
        custom_reset_viewport();
        custom_set_rasterizer_state(0);
        custom_set_depth_stencil_state(0);
        custom_restore_state();
    }

    // E: Textured Mesh
    float ew = total_w - cw - dw - gap * 2, eh = 120;
    float ex = dx2 + dw + gap, ey = r2y + lbl_h;
    label(ex + 4, r2y, "E: Textured Mesh", 255, 255, 255);
    border(ex, ey, ew, eh, 255, 255, 255);
    {
        array<uint8> proje = mat4_persp(1.0f, ew / eh, 0.1f, 100.0f);
        array<uint8> rye = mat4_roty(-g_time * 0.8f);
        array<uint8> rxe = mat4_rotx(0.5f);
        array<uint8> te = mat4_trans(0, 0, -3.0f);
        array<uint8> t1e = mat4_mul(rye, rxe);
        array<uint8> t2e = mat4_mul(t1e, te);
        array<uint8> mvpe = mat4_mul(t2e, proje);

        custom_set_viewport(ex, ey, ew, eh);
        custom_set_rasterizer_state(g_rs_nc);
        custom_set_depth_stencil_state(g_ds_off);
        draw_mesh(g_mesh_pyr, g_sh_mesh_tex, TOPO_TRIANGLE_LIST, g_blend, g_samp_lin, g_tex_loaded, 0, g_cb_mvp, mvpe, 0);
        custom_reset_viewport();
        custom_set_rasterizer_state(0);
        custom_set_depth_stencil_state(0);
        custom_restore_state();
    }

    // ===== ROW 3 =====
    float r3y = cy + ch + gap;

    // F: Dynamic Texture
    float fw = 200, fh = 120;
    float fx = ox, fy = r3y + lbl_h;
    label(fx + 4, r3y, "F: Dynamic Texture", 0, 200, 180);
    border(fx, fy, fw, fh, 0, 200, 180);
    {
        array<uint8> clear_px(32 * 32 * 4);
        for (uint i = 0; i < clear_px.length(); i += 4) {
            clear_px[i] = 25; clear_px[i+1] = 25; clear_px[i+2] = 45; clear_px[i+3] = 255;
        }
        custom_update_texture(g_tex_dyn, 0, 0, 32, 32, clear_px);

        int blk_x = int(g_time * 6) % 24;
        int blk_y = int(g_time * 4) % 24;
        array<uint8> block(8 * 8 * 4);
        for (int py = 0; py < 8; py++)
            for (int px = 0; px < 8; px++) {
                uint idx = uint((py * 8 + px) * 4);
                block[idx]     = uint8(255.0f * (0.5f + 0.5f * sin(g_time * 3.0f)));
                block[idx + 1] = uint8(255.0f * (0.5f + 0.5f * sin(g_time * 3.0f + 2.0f)));
                block[idx + 2] = 255;
                block[idx + 3] = 255;
            }
        custom_update_texture(g_tex_dyn, uint(blk_x), uint(blk_y), 8, 8, block);

        custom_bind_texture(g_tex_dyn, g_samp_pt, 0);
        array<uint8> vf(96, 0);
        quad_verts(vf, 0, fx, fy, fx + fw, fy + fh);
        custom_draw(g_sh_2d, g_vb, vf, 6, TOPO_TRIANGLE_LIST, g_blend, g_samp_pt, g_tex_dyn, 0, g_cb_scr, cb_scr, 0);
        custom_restore_state();
    }

    // G: Raw Mesh + Multi-CB
    float gw = 190, gh = 120;
    float gx = fx + fw + gap, gy = r3y + lbl_h;
    label(gx + 4, r3y, "G: Raw Mesh + Multi-CB", 100, 180, 255);
    border(gx, gy, gw, gh, 100, 180, 255);
    {
        float hue = g_time * 0.8f;
        array<uint8> mat_anim = fb(0.5f + 0.5f * sin(hue), 0.5f + 0.5f * sin(hue + 2.09f), 0.5f + 0.5f * sin(hue + 4.19f), 1.0f);
        array<uint8> projg = mat4_persp(1.0f, gw / gh, 0.1f, 100.0f);
        array<uint8> tg = mat4_trans(0, 0, -2.0f);
        array<uint8> mvpg = mat4_mul(tg, projg);

        custom_set_viewport(gx, gy, gw, gh);
        custom_set_rasterizer_state(g_rs_nc);
        custom_set_depth_stencil_state(g_ds_off);
        custom_bind_constant_buffer(g_cb_mvp, mvpg, 0, STAGE_VS);
        custom_bind_constant_buffer(g_cb_mat, mat_anim, 1, STAGE_PS);
        draw_mesh(g_mesh_quad, g_sh_mat, TOPO_TRIANGLE_LIST, g_blend, 0, 0, 0, 0, null, 0);
        custom_reset_viewport();
        custom_set_rasterizer_state(0);
        custom_set_depth_stencil_state(0);
        custom_restore_state();
    }

    // H: Backbuffer Capture
    float hw = total_w - fw - gw - gap * 2, hh = 120;
    float hx = gx + gw + gap, hy = r3y + lbl_h;
    label(hx + 4, r3y, "H: Backbuffer Capture", 0, 255, 255);
    border(hx, hy, hw, hh, 0, 255, 255);
    {
        capture_backbuffer(0);
        custom_bind_texture(0, g_samp_lin, 0);
        array<uint8> vh(96, 0);
        quad_verts(vh, 0, hx, hy, hx + hw, hy + hh);
        custom_draw(g_sh_bb, g_vb, vh, 6, TOPO_TRIANGLE_LIST, g_blend, g_samp_lin, 0, 0, g_cb_scr, cb_scr, 0);
        custom_restore_state();
    }

    // Status bar
    float sy = fy + fh + 12;
    draw_rect_filled(ox - 8, sy - 4, total_w + 16, 22, 20, 20, 35, 200, 4.0f, 0);
    string status = "mesh_pyr=" + (g_mesh_pyr != 0 ? "OK" : "FAIL")
        + "   mesh_quad=" + (g_mesh_quad != 0 ? "OK" : "FAIL")
        + "   tex=" + (g_tex_loaded != 0 ? "OK" : "FAIL")
        + "   depth=" + (g_db != 0 ? "OK" : "FAIL")
        + "   rt=" + (g_rt != 0 ? "OK" : "FAIL")
        + "   cs=" + (g_cs != 0 ? "OK" : "FAIL");
    draw_text(status, ox, sy, 140, 160, 200, 255, get_font18(), 0, 0, 0, 0, 0, 0.0f);
}

int main() {
    log("PCX Draw API Test - init");

    string ly_2d = "POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2";
    string ly_mesh = "POSITION:0:FLOAT3, NORMAL:0:FLOAT3, TEXCOORD:0:FLOAT2";

    g_sh_2d       = create_shader(g_vs_2d, g_ps_tex, ly_2d);
    g_sh_sb       = create_shader(g_vs_2d, g_ps_sb_vis, ly_2d);
    g_sh_bb       = create_shader(g_vs_2d, g_ps_bb, ly_2d);
    g_sh_mat      = create_shader(g_vs_mesh, g_ps_mat, ly_mesh);
    g_sh_lit      = create_shader(g_vs_mesh, g_ps_lit, ly_mesh);
    g_sh_mesh_tex = create_shader(g_vs_mesh, g_ps_mesh_tex, ly_mesh);
    g_cs          = create_compute_shader(g_cs_src);

    g_vb       = create_vertex_buffer(16, 128, true);
    g_cb_scr   = create_constant_buffer(16);
    g_cb_mvp   = create_constant_buffer(64);
    g_cb_mat   = create_constant_buffer(16);
    g_blend    = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD, BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
    g_samp_lin = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
    g_samp_pt  = create_sampler(FILTER_POINT, ADDRESS_CLAMP, ADDRESS_CLAMP);

    g_rt     = create_render_target(256, 180);
    g_db     = create_depth_buffer(256, 180);
    g_ds_on  = create_depth_stencil_state(true, true, CMP_LESS);
    g_ds_off = create_depth_stencil_state(false, false, CMP_ALWAYS);
    g_rs_nc  = create_rasterizer_state(CULL_NONE, FILL_SOLID, true);

    g_sb_gpu    = create_structured_buffer(16, 256, false, true);
    g_sb_params = create_structured_buffer(16, 1, true, false);

    array<uint8> obj_bytes(g_obj.length());
    for (uint i = 0; i < g_obj.length(); i++) obj_bytes[i] = uint8(g_obj[i]);
    g_mesh_pyr = load_mesh_mem(obj_bytes);
    if (g_mesh_pyr != 0) {
        float vc, ic, mnx, mny, mnz, mxx, mxy, mxz;
        get_mesh_info(g_mesh_pyr, vc, ic, mnx, mny, mnz, mxx, mxy, mxz);
        log("Mesh: " + int(vc) + " verts, " + int(ic) + " idx, bounds " + mnx + "," + mny + "," + mnz + " -> " + mxx + "," + mxy + "," + mxz);
    } else {
        log_error("load_mesh_mem FAILED");
    }

    array<uint8> tga(18 + 16 * 16 * 4, 0);
    tga[2] = 2; tga[12] = 16; tga[14] = 16; tga[16] = 32; tga[17] = 0x20;
    for (int y = 0; y < 16; y++)
        for (int x = 0; x < 16; x++) {
            uint i = 18 + uint((y * 16 + x) * 4);
            bool cross = (x == y) || (x == 15 - y);
            tga[i]     = uint8(x * 17);
            tga[i + 1] = cross ? 255 : uint8(y * 17);
            tga[i + 2] = uint8((15 - x) * 17);
            tga[i + 3] = 255;
        }
    g_tex_loaded = load_texture_mem(tga);
    if (g_tex_loaded != 0) {
        float tw, th;
        get_texture_info(g_tex_loaded, tw, th);
        log("Texture: " + int(tw) + "x" + int(th));
    }

    array<uint8> dyn_px(32 * 32 * 4);
    for (uint i = 0; i < dyn_px.length(); i += 4) {
        dyn_px[i] = 30; dyn_px[i+1] = 30; dyn_px[i+2] = 50; dyn_px[i+3] = 255;
    }
    g_tex_dyn = create_texture(32, 32, dyn_px);

    array<uint8> raw_vb(4 * 32, 0);
    wf(raw_vb,  0,-0.6f); wf(raw_vb,  4,-0.5f); wf(raw_vb,  8, 0); wf(raw_vb, 12, 0); wf(raw_vb, 16, 0); wf(raw_vb, 20, 1); wf(raw_vb, 24, 0); wf(raw_vb, 28, 1);
    wf(raw_vb, 32, 0.6f); wf(raw_vb, 36,-0.5f); wf(raw_vb, 40, 0); wf(raw_vb, 44, 0); wf(raw_vb, 48, 0); wf(raw_vb, 52, 1); wf(raw_vb, 56, 1); wf(raw_vb, 60, 1);
    wf(raw_vb, 64, 0.6f); wf(raw_vb, 68, 0.5f); wf(raw_vb, 72, 0); wf(raw_vb, 76, 0); wf(raw_vb, 80, 0); wf(raw_vb, 84, 1); wf(raw_vb, 88, 1); wf(raw_vb, 92, 0);
    wf(raw_vb, 96,-0.6f); wf(raw_vb,100, 0.5f); wf(raw_vb,104, 0); wf(raw_vb,108, 0); wf(raw_vb,112, 0); wf(raw_vb,116, 1); wf(raw_vb,120, 0); wf(raw_vb,124, 0);
    array<uint8> raw_ib(24, 0);
    raw_ib[0]=0; raw_ib[4]=1; raw_ib[8]=2; raw_ib[12]=0; raw_ib[16]=2; raw_ib[20]=3;
    g_mesh_quad = create_mesh_raw(raw_vb, 4, 32, raw_ib, 6, true);
    if (g_mesh_quad != 0) {
        float stride = get_mesh_stride(g_mesh_quad);
        log("Raw mesh: stride=" + int(stride));
    }

    g_ok = g_sh_2d != 0 && g_sh_mat != 0 && g_sh_lit != 0 && g_sh_sb != 0
        && g_sh_bb != 0 && g_sh_mesh_tex != 0 && g_cs != 0
        && g_vb != 0 && g_cb_scr != 0 && g_cb_mvp != 0 && g_cb_mat != 0
        && g_blend != 0 && g_samp_lin != 0 && g_samp_pt != 0
        && g_rt != 0 && g_db != 0 && g_ds_on != 0 && g_ds_off != 0 && g_rs_nc != 0
        && g_mesh_pyr != 0 && g_mesh_quad != 0
        && g_tex_loaded != 0 && g_tex_dyn != 0
        && g_sb_gpu != 0 && g_sb_params != 0;

    if (!g_ok) { log_error("INIT FAILED"); return 0; }

    log("All OK");
    g_cb_id = register_callback(@render_cb, 16, 0);
    return g_cb_id > 0 ? 1 : 0;
}

void on_unload() {
    if (g_cb_id > 0) unregister_callback(g_cb_id);
}

```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/render-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/sound-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/sound-api.md).

# Sound API

The Sound API lets AngelScript scripts load and play audio files with real-time volume and stereo panning control.

Sound files are loaded from relative paths resolved against your script directory (same as the File System API).

**Supported formats:** WAV (PCM 8/16-bit), MP3, AAC, WMA, FLAC — anything Windows Media Foundation can decode.

All audio is resampled to 44100 Hz stereo at load time. Up to 64 sounds can play simultaneously.

***

### Concepts

There are two handle types, both represented as `uint64`:

* **Sound handle** — a loaded audio resource returned by `load_sound`. Can be played multiple times simultaneously. Must be freed with `free_sound` when no longer needed.
* **Instance handle** — a single playing occurrence returned by `play_sound`. Used to stop, query, or adjust an active playback.

Both return `0` on failure. All functions are safe to call with `0` handles (they become no-ops).

***

### Loading & Freeing

**`uint64 load_sound(const string &in path)`**

Loads a sound file from a relative path.

* `path` — Relative path to the audio file (e.g. `"sounds/hit.wav"`, `"alert.mp3"`).

Returns a sound handle, or `0` if the file doesn't exist or decoding fails.

***

**`void free_sound(uint64 handle)`**

Frees a previously loaded sound resource. Any active instances using this sound are stopped automatically.

***

### Playback

**`uint64 play_sound(uint64 sound, float volume = 1.0, float pan = 0.0, bool loop = false)`**

Plays a loaded sound and returns an instance handle.

* `sound` — Sound handle from `load_sound`.
* `volume` — `0.0` (silent) to `1.0` (full). Clamped.
* `pan` — `-1.0` (full left) to `+1.0` (full right). `0.0` is center. Clamped.
* `loop` — If `true`, the sound repeats until explicitly stopped.

Returns an instance handle, or `0` if the sound handle is invalid or all 64 instance slots are in use.

***

**`void stop_sound(uint64 instance)`**

Stops a playing instance immediately.

***

**`void stop_all_sounds()`**

Stops every currently playing sound instance.

***

**`bool is_sound_playing(uint64 instance)`**

Returns `true` if the instance is still actively playing. Returns `false` if it finished, was stopped, or the handle is invalid.

***

### Live Adjustment

These functions modify a playing instance in real time. Changes take effect on the next mixer tick (\~20ms).

**`void set_sound_volume(uint64 instance, float volume)`**

Changes volume of a playing instance. `0.0` to `1.0`, clamped.

***

**`void set_sound_pan(uint64 instance, float pan)`**

Changes stereo panning of a playing instance. `-1.0` (left) to `+1.0` (right), clamped.

***

### Examples

#### Play a one-shot sound effect

```cpp
uint64 snd = 0;

int main()
{
    snd = load_sound("pop.mp3");
    if (snd == 0)
    {
        log("Failed to load sound");
        return 0;
    }

    play_sound(snd, 0.8f, 0.0f);
    return 1;
}

void on_unload()
{
    if (snd != 0)
        free_sound(snd);
}
```

***

#### Looping background music

```cpp
uint64 music = 0;
uint64 music_inst = 0;

int main()
{
    music = load_sound("ambient.ogg");
    if (music != 0)
        music_inst = play_sound(music, 0.5f, 0.0f, true);

    return 1;
}

void on_unload()
{
    if (music_inst != 0)
        stop_sound(music_inst);
    if (music != 0)
        free_sound(music);
}
```

***

#### Directional sound with panning

```cpp
void play_hit(uint64 snd, float target_x, float player_x, float max_range)
{
    float pan = (target_x - player_x) / max_range;
    if (pan < -1.0f) pan = -1.0f;
    if (pan >  1.0f) pan =  1.0f;

    play_sound(snd, 1.0f, pan);
}
```

***

#### Adjusting volume over time

```cpp
uint64 snd = 0;
uint64 inst = 0;
int cb = 0;
float vol = 1.0f;

void fade_out(int id, int data)
{
    if (inst == 0) return;

    vol -= 0.02f;
    if (vol <= 0.0f)
    {
        stop_sound(inst);
        inst = 0;
        return;
    }

    set_sound_volume(inst, vol);
}

int main()
{
    snd = load_sound("alert.wav");
    if (snd == 0) return 0;

    inst = play_sound(snd, 1.0f, 0.0f);
    cb = register_callback(@fade_out, 50, 0);
    return 1;
}

void on_unload()
{
    if (cb != 0) unregister_callback(cb);
    if (inst != 0) stop_sound(inst);
    if (snd != 0) free_sound(snd);
}
```

***

#### Multiple simultaneous sounds

```cpp
int main()
{
    uint64 snd = load_sound("hit.wav");
    if (snd == 0) return 0;

    play_sound(snd, 1.0f,  0.0f);
    play_sound(snd, 0.7f, -0.5f);
    play_sound(snd, 0.5f,  0.8f);

    return 1;
}
```

***

### Notes

* Sound data is fully decoded to PCM at load time. Loading is the expensive operation — `play_sound` is cheap.
* Instance handles point into a fixed pool of 64 slots. If all slots are in use, `play_sound` returns `0`.
* Calling `free_sound` automatically stops all instances that reference that sound.
* Sounds are automatically freed when your script is unloaded (leaked handles are cleaned up). You should still free sounds explicitly when possible.
* The `path` parameter follows the same validation rules as the File System API: relative paths only, no `..` segments, no `:` characters.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/sound-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/system-api-cpu-and-disassembly.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/system-api-cpu-and-disassembly.md).

# System API (CPU & Disassembly)

Low-level CPU information, high-precision timing, and full multi-instruction x64 disassembly using **Zydis**.

***

## 📌 Overview

The System API provides:

* **CPU Information**
* **High-Resolution Performance Timers**
* **x64 Instruction Disassembly** using **Zydis**
* Full operand breakdown: registers, memory operands, immediates, pointer operands, etc.

All functions are **global** inside AngelScript.

***

## 📘 Available Functions

### 🔧 CPU Information

| Function              | Returns                                 | Description              |
| --------------------- | --------------------------------------- | ------------------------ |
| `string cpu_vendor()` | `"AuthenticAMD"`, `"GenuineIntel"`      | CPU vendor ID            |
| `string cpu_brand()`  | `"AMD Ryzen 9 7900X 12-Core Processor"` | Human-readable CPU model |

***

### ⏱ Timing

| Function                 | Returns                             | Description                         |
| ------------------------ | ----------------------------------- | ----------------------------------- |
| `uint64 rdtsc()`         | Raw CPU timestamp counter           | Fast but CPU-frequency dependent    |
| `int64 perf_time()`      | High-resolution performance counter | Use with `perf_frequency()`         |
| `int64 perf_frequency()` | Ticks per second                    | For converting perf\_time → seconds |

#### 📌 Example (timing a loop)

```cpp
int64 freq = perf_frequency();
int64 t0   = perf_time();

for (uint i = 0; i < 1000000; i++) { }

int64 t1 = perf_time();
double dt_sec = double(t1 - t0) / double(freq);

log("Elapsed seconds: " + dt_sec);
```

***

## 🧩 Zydis Disassembly API

### Functions

| Function                                                                                                 | Returns              | Description                   |
| -------------------------------------------------------------------------------------------------------- | -------------------- | ----------------------------- |
| `void zydis_disasm(const array<uint8>& in bytes, array<dictionary@>& out out_insts)`                     | `array<dictionary@>` | Full decode starting at RIP=0 |
| `void zydis_disasm(const array<uint8>& in bytes, uint64 runtime_rip, array<dictionary@>& out out_insts)` | `array<dictionary@>` | Full decode with custom RIP   |

Both return a **list of instructions**, where each item is a **dictionary** with metadata and operand array.

***

## 🧱 Instruction Structure (`disasm_instruction_t`)

Each instruction dictionary contains:

| Key                       | Type                 | Description                 |
| ------------------------- | -------------------- | --------------------------- |
| `"runtime_address"`       | `int64`              | Instruction RIP             |
| `"length"`                | `int64`              | Size in bytes               |
| `"mnemonic"`              | `string`             | `"mov"`, `"push"`, `"lea"`  |
| `"text"`                  | `string`             | Full Intel disassembly text |
| `"operand_count"`         | `int64`              | Total operands              |
| `"operand_count_visible"` | `int64`              | Non-hidden operands         |
| `"operands"`              | `array<dictionary@>` | List of operand tables      |

***

## 🔍 Operand Structure (`operand_t`)

Each operand dictionary contains:

| Key            | Type     | Example                               | Notes         |
| -------------- | -------- | ------------------------------------- | ------------- |
| `"id"`         | `int64`  | `0`                                   | Operand index |
| `"type"`       | `string` | `"reg"` / `"mem"` / `"imm"` / `"ptr"` | Operand type  |
| `"visibility"` | `string` | `"explicit"` / `"hidden"`             |               |
| `"size"`       | `int64`  | `64`                                  | Bit size      |

#### Register operand

| Key          | Type     | Description                |
| ------------ | -------- | -------------------------- |
| `"reg_name"` | `string` | `"rax"`, `"rcx"`, `"xmm0"` |

#### Memory operand

| Key                      | Type          | Description                 |
| ------------------------ | ------------- | --------------------------- |
| `"mem_segment"`          | `string`      | `"ss"`                      |
| `"mem_base"`             | `string`      | `"rbp"`                     |
| `"mem_index"`            | `string`      | `"rax"` or ""               |
| `"mem_scale"`            | `int64`       | Scale (1,2,4,8)             |
| `"mem_has_displacement"` | `int64` (0/1) | Whether displacement exists |
| `"mem_displacement"`     | `int64`       | Signed displacement         |

#### Immediate operand

| Key                      | Type          | Description              |
| ------------------------ | ------------- | ------------------------ |
| `"imm_is_signed"`        | `int64` (0/1) | Signed flag              |
| `"imm_is_relative"`      | `int64` (0/1) | Is relative jump?        |
| `"imm_value"`            | `int64`       | Immediate value          |
| `"imm_absolute_address"` | `int64`       | Computed RIP + relOffset |

#### Pointer operand

| Key             | Type    | Description |
| --------------- | ------- | ----------- |
| `"ptr_segment"` | `int64` |             |
| `"ptr_offset"`  | `int64` |             |

***

## 🚀 AngelScript Example

This example shows **CPU info**, **timing**, and full **multi-instruction disassembly** — the same script you used for validation.

```cpp
int main()
{
    log("=== AS SYSTEM / ZYDIS FULL TEST START ===");

    // CPU info
    log("CPU Vendor: " + cpu_vendor());
    log("CPU Brand : " + cpu_brand());

    // Timing test
    int64 freq = perf_frequency();
    int64 t0   = perf_time();

    uint64 sum = 0;
    for (uint i = 0; i < 1000000; i++) sum += i;

    int64 t1 = perf_time();
    log("perf_frequency (ticks/sec): " + freq);
    log("perf_time delta seconds   : " + double(t1 - t0) / double(freq));

    log("RDTSC: " + rdtsc());

    // Example code to disassemble
    array<uint8> bytes = {
        0x55,                    // push rbp
        0x48, 0x89, 0xE5,        // mov rbp, rsp
        0x48, 0x83, 0xEC, 0x30   // sub rsp, 0x30
    };

    array<dictionary@> ins;
    zydis_disasm(bytes, 0x140000000, ins);

    log("=== ZYDIS TEST (HARDCODED BYTES) ===");
    for (uint i = 0; i < ins.length(); i++)
    {
        dictionary@ inst = ins[i];

        int64 addr; 
        inst.get("runtime_address", addr);

        string text;
        inst.get("text", text);

        log(formatInt(addr, "0x%X") + ": " + text);
    }

    log("=== AS SYSTEM / ZYDIS FULL TEST END ===");
    return 1;
}
```

***

## 🔥 Example Output

```cpp
=== AS SYSTEM / ZYDIS FULL TEST START ===
CPU Vendor: AuthenticAMD
CPU Brand : AMD Ryzen 9 7900X 12-Core Processor

perf_frequency (ticks/sec): 10000000
perf_time delta seconds : 0.0094
RDTSC: 161134003150540

=== ZYDIS TEST (HARDCODED BYTES) ===
0x140000000: push rbp
0x140000001: mov rbp, rsp
0x140000004: sub rsp, 0x30

=== AS SYSTEM / ZYDIS FULL TEST END ===
```

***

## 📅 Date & Time API

Provides local date/time information, including readable names, 12-hour formatting, and Unix timestamps.

### 🧭 Functions

#### **`dictionary@ get_datetime()`**

Returns a dictionary with the following keys:

| Key            | Type   | Description                    |
| -------------- | ------ | ------------------------------ |
| `"year"`       | int    | e.g. 2025                      |
| `"month"`      | int    | 1–12                           |
| `"day"`        | int    | 1–31                           |
| `"hour"`       | int    | 0–23                           |
| `"minute"`     | int    | 0–59                           |
| `"second"`     | int    | 0–59                           |
| `"msec"`       | int    | 0–999                          |
| `"day_name"`   | string | `"Monday"`, `"Tuesday"`, ...   |
| `"month_name"` | string | `"January"`, `"February"`, ... |
| `"hour12"`     | int    | 1–12                           |
| `"ampm"`       | string | `"AM"` or `"PM"`               |

***

#### **`uint64 get_timestamp()`**

Returns a **Unix timestamp** in **UTC**, measured in seconds since `1970-01-01`.

***

## 🧪 Example: Getting Time & Date

```cpp
int main()
{
    dictionary@ dt = get_datetime();
    
    int year, month, day, hour12, minute;
    string dayName, monthName, ampm;
    
    dt.get("year", year);
    dt.get("month", month);
    dt.get("day", day);
    dt.get("hour12", hour12);
    dt.get("minute", minute);
    dt.get("day_name", dayName);
    dt.get("month_name", monthName);
    dt.get("ampm", ampm);
    
    log("Today is: " + dayName + ", " + monthName + " " + day + ", " + year);
    log("Local Time: " +
    hour12 +
    ":" +
    (minute < 10 ? "0" + formatInt(minute) : formatInt(minute)) +
    " " + ampm);
    
    uint64 ts = get_timestamp();
    log("Unix Timestamp: " + ts);
    return 1;
}

```

***

#### Thread Priority

* `bool set_thread_to_highest_priority()` — Set current thread to highest priority.
* `bool set_thread_to_lowest_priority()` — Set current thread to lowest priority.
* `bool set_thread_to_normal_priority()` — Set current thread to normal priority.

**What this is useful for:**\
Use these helpers when you have a **callback (os thread)** that must stay responsive (e.g., high-frequency polling, tight timing loops, heavy disassembly / scan batches, or avoiding stutter in critical update logic). You can temporarily raise priority during a burst of work, then restore **normal** afterward to avoid starving other threads and the UI.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/system-api-cpu-and-disassembly.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/unicorn.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/unicorn.md).

# Unicorn

The Unicorn API exposes a lightweight CPU + memory emulation layer to AngelScript.\
It supports two modes:

* **Local emulation** (`uc_create`) — fully sandboxed memory you map/write yourself.
* **Process-backed emulation** (`uc_create_process`) — unmapped reads/fetches can be paged-in from a `proc_t` target, enabling “emulate code that reads target memory”.

***

#### Notes (Important)

* **Always** call `uc_close(handle)` when done.
* You should use **`uc_setup_stack`** for setting up stack.
* If you modify code bytes at the same address and re-run, call **`uc_flush_code(handle)`** (TB cache flush) or run the updated code at a different address.
* **Null pointer access, invalid instructions, and interrupts** are caught automatically — emulation stops and sets exception state. Check with `uc_get_last_exception(handle)` after `uc_start` returns.
* Memory addresses are Unicorn virtual addresses:
  * Low “sandbox” memory (e.g. `0x1000` / `0x2000`) is local/emulator-owned.
  * Real target VAs (user-mode addresses) are process-backed when running in process mode.

***

#### Constants

**Memory Protection Flags**

Copy

```cpp
const uint32 UC_PROT_READ
const uint32 UC_PROT_WRITE
const uint32 UC_PROT_EXEC
const uint32 UC_PROT_ALL
```

Use these with `uc_mem_map`.

***

**Register IDs (x86\_64)**

Register IDs are exposed as global `const int` values, for example:

Copy

```cpp
// General purpose registers
const int UC_X86_REG_RAX;
const int UC_X86_REG_RBX;
const int UC_X86_REG_RCX;
const int UC_X86_REG_RDX;
const int UC_X86_REG_RSI;
const int UC_X86_REG_RDI;
const int UC_X86_REG_RBP;
const int UC_X86_REG_RSP;

const int UC_X86_REG_R8;
const int UC_X86_REG_R9;
const int UC_X86_REG_R10;
const int UC_X86_REG_R11;
const int UC_X86_REG_R12;
const int UC_X86_REG_R13;
const int UC_X86_REG_R14;
const int UC_X86_REG_R15;

// Instruction pointer & flags
const int UC_X86_REG_RIP;
const int UC_X86_REG_EFLAGS;

// Segment registers
const int UC_X86_REG_CS;
const int UC_X86_REG_DS;
const int UC_X86_REG_ES;
const int UC_X86_REG_FS;
const int UC_X86_REG_GS;
const int UC_X86_REG_SS;

// Segment bases
const int UC_X86_REG_FS_BASE;
const int UC_X86_REG_GS_BASE;

// SIMD control
const int UC_X86_REG_MXCSR;

// XMM registers
const int UC_X86_REG_XMM0;
const int UC_X86_REG_XMM1;
const int UC_X86_REG_XMM2;
const int UC_X86_REG_XMM3;
const int UC_X86_REG_XMM4;
const int UC_X86_REG_XMM5;
const int UC_X86_REG_XMM6;
const int UC_X86_REG_XMM7;
const int UC_X86_REG_XMM8;
const int UC_X86_REG_XMM9;
const int UC_X86_REG_XMM10;
const int UC_X86_REG_XMM11;
const int UC_X86_REG_XMM12;
const int UC_X86_REG_XMM13;
const int UC_X86_REG_XMM14;
const int UC_X86_REG_XMM15;

// YMM registers
const int UC_X86_REG_YMM0;
const int UC_X86_REG_YMM1;
const int UC_X86_REG_YMM2;
const int UC_X86_REG_YMM3;
const int UC_X86_REG_YMM4;
const int UC_X86_REG_YMM5;
const int UC_X86_REG_YMM6;
const int UC_X86_REG_YMM7;
const int UC_X86_REG_YMM8;
const int UC_X86_REG_YMM9;
const int UC_X86_REG_YMM10;
const int UC_X86_REG_YMM11;
const int UC_X86_REG_YMM12;
const int UC_X86_REG_YMM13;
const int UC_X86_REG_YMM14;
const int UC_X86_REG_YMM15;

```

***

**Hook Types**

```cpp
const int UC_HOOK_CODE
const int UC_HOOK_MEM_UNMAPPED
```

* `UC_HOOK_CODE` — Hook every instruction executed.
* `UC_HOOK_MEM_UNMAPPED` — Hook unmapped memory access (read/write/fetch).

***

#### Engine Handles

**Create (Local)**

Copy

```cpp
uint64 uc_create()
```

Creates a new Unicorn context (local emulation). Returns a handle, or `0` on failure.

***

**Create (Process-backed)**

Copy

```cpp
uint64 uc_create_process(proc_t proc, bool allow_writes = true)
```

Creates a Unicorn context that can page-in unmapped reads/fetches from `proc`.\
Use `allow_writes=false` for safe read-only emulation.

A synthetic `TEB` is created with the real `PEB` address written at offset **0x60**. For correct and stable emulation, you should override the **FS** and **GS** base registers to point to a real TEB instance.

Returns a handle, or `0` on failure.

***

**Close**

Copy

```cpp
void uc_close(uint64 handle)
```

Destroys the Unicorn context and releases all internal resources.

***

#### Memory

**Map Memory**

Copy

```cpp
bool uc_mem_map(uint64 handle, uint64 addr, uint64 size, uint32 perms)
```

Maps a memory region in the emulator.

* `addr` must be page-aligned.
* `size` must be page-aligned (or a multiple of page size).

Returns `true` on success.

***

**Write Memory**

Copy

```cpp
bool uc_mem_write(uint64 handle, uint64 addr, const array<uint8> &in data)
```

Writes bytes into emulator memory at `addr`.

***

**Read Memory**

Copy

```cpp
bool uc_mem_read(uint64 handle, uint64 addr, uint32 size, array<uint8> &out data)
```

Reads bytes from emulator memory at `addr` into `data`.

In process-backed mode, this may succeed if the page was already paged-in (or if your integration supports paging-in for external reads).

***

#### Registers

**Write 64-bit Register**

Copy

```cpp
bool uc_reg_write64(uint64 handle, int reg, uint64 value)
```

***

**Read 64-bit Register**

Copy

```cpp
uint64 uc_reg_read64(uint64 handle, int reg)
```

***

**Write 128-bit Register (XMM)**

Copy

```cpp
bool uc_reg_write128(uint64 handle, int reg, const array<uint8> &in data)
```

`data` must be exactly 16 bytes.

***

**Read 128-bit Register (XMM)**

Copy

```cpp
bool uc_reg_read128(uint64 handle, int reg, array<uint8> &out data)
```

Returns exactly 16 bytes in `data`.

***

**Write 256-bit Register (YMM)**

Copy

```cpp
bool uc_reg_write256(uint64 handle, int reg, const array<uint8> &in data)
```

`data` must be exactly 32 bytes.

***

**Read 256-bit Register (YMM)**

Copy

```cpp
bool uc_reg_read256(uint64 handle, int reg, array<uint8> &out data)
```

Returns exactly 32 bytes in `data`.

***

#### Execution

**Setup Stack (Recommended)**

Copy

```cpp
bool uc_setup_stack(uint64 handle, uint64 stack_base, uint64 stack_size, uint64 stop_addr)
```

Maps a stack region, sets `RSP`, pushes a return address, and maps a STOP page.

Use this before running any code that can execute `ret`.

Returns `true` on success.

If `uc_setup_stack` is not used in process mode, the emulator may attempt to read stack memory from the remote process instead of the emulated address space.

***

**Start Emulation**

Copy

```cpp
int uc_start(uint64 handle, uint64 begin, uint64 end, uint64 timeout = 0, uint64 count = 0)
```

Starts emulation at `begin`.

* `end` — stop address (use a STOP page if your code returns)
* `timeout` — microseconds (0 = unlimited)
* `count` — instruction limit (0 = unlimited)

Returns `UC_ERR_OK` on success. [Error Codes](https://github.com/unicorn-engine/unicorn/blob/c24c9ebe773ce6fbecb0e39f68ffb23b7326b17f/include/unicorn/unicorn.h#L164)

***

**Flush Translated Code Cache**

Copy

```cpp
bool uc_flush_code(uint64 handle)
```

Flushes Unicorn’s internal translation cache (TB cache).\
Call this after modifying code bytes at an address you will execute again.

Returns `true` on success.

***

**Callback Signature**

```cpp
funcdef bool UcHookFn(uint64 uc, uint64 addr)
```

Hook callbacks receive:

* `uc` — Unicorn handle (same value as the `handle` you created)
* `addr` — address of the instruction or faulting memory access

Return value:

* `true` — continue emulation
* `false` — stop emulation (recommended to also call `uc_emu_stop`)

**Add Hook**

```cpp
bool uc_hook_add(uint64 handle, int type, UcHookFn@ cb)
```

Registers a hook callback on the Unicorn context.

* `handle` — Unicorn context handle
* `type` — hook type constant (`UC_HOOK_CODE`, `UC_HOOK_MEM_UNMAPPED`)
* `cb` — callback function handle

Returns `true` on success, `false` on failure.

**Stop Emulation (from hook)**

```cpp
void uc_emu_stop(uint64 handle)
```

Stops emulation immediately. Intended for use **inside hook callbacks** to halt execution cleanly.

***

#### Exception Handling

In process-backed mode, emulated code may branch to null pointers, execute invalid instructions, or trigger software interrupts. These are caught automatically and stop emulation cleanly instead of crashing or returning a cryptic error.

**What gets caught:**

* **Null pointer access** — any read, write, or fetch to an address below `0x10000` (the null page). Common when emulated code follows a branch like `if (!ptr) return;` but the pointer is actually null in the target process.
* **Invalid instructions** — bad opcodes that the CPU can't decode.
* **Software interrupts** — `INT3` breakpoints, `INT 0x2E` syscalls, and other INT instructions.

All three set the exception state and stop emulation. Your script can then check what happened.

**Get Last Exception Code**

```cpp
int uc_get_last_exception(uint64 handle)
```

Returns the NTSTATUS-style exception code from the last `uc_start` run:

| Code           | Meaning                                                  |
| -------------- | -------------------------------------------------------- |
| `0`            | Clean exit (no exception)                                |
| `0xC0000005`   | Access violation (null pointer or unmapped non-usermode) |
| `0xC000001D`   | Illegal instruction                                      |
| `0xC0000005+N` | Software interrupt N                                     |

The exception state is cleared at the start of each `uc_start` call.

**Get Exception Address**

```cpp
uint64 uc_get_exception_address(uint64 handle)
```

Returns the `RIP` (instruction pointer) where the exception occurred. Returns `0` if the last run completed cleanly.

***

**Notes (Hooks)**

* Hooks run during `uc_start(...)` execution.
* Keep hook callbacks lightweight (they can fire very frequently, especially `UC_HOOK_CODE`).
* If you stop execution from a hook, prefer:
  * `uc_emu_stop(handle)` and return `false` from the hook.

***

#### Examples

**Example 1 — Read Notepad ImageBaseAddress via PEB (GS:\[0x60])**

This example:

* References `notepad.exe`
* Creates a process-backed Unicorn context
* Reads `PEB->ImageBaseAddress` via:
  * `mov rax, gs:[0x60]` (PEB)
  * `mov rax, [rax+0x10]` (ImageBaseAddress)
  * `ret` (lands on STOP)

Copy

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (!p.alive()) { log_error("notepad not found"); return -1; }

    uint64 uc = uc_create_process(p, false);
    if (uc == 0) { log_error("uc_create_process failed"); p.deref(); return -1; }

    array<uint8> code = {
        0x65,0x48,0x8B,0x04,0x25,0x60,0x00,0x00,0x00, // mov rax, gs:[0x60]
        0x48,0x8B,0x40,0x10,                         // mov rax, [rax+0x10]
        0xC3                                          // ret
    };

    uint64 CODE  = 0x1000;
    uint64 STACK = 0x2000;
    uint64 STOP  = 0x4000;

    uc_mem_map(uc, CODE, 0x1000, UC_PROT_ALL);
    uc_mem_write(uc, CODE, code);

    uc_reg_write64(uc, UC_X86_REG_RIP, CODE);

    if (!uc_setup_stack(uc, STACK, 0x2000, STOP)) {
        log_error("uc_setup_stack failed");
        uc_close(uc); p.deref();
        return -1;
    }

    if (!uc_start(uc, CODE, STOP, 0, 0)) {
        log_error("uc_start failed");
        uc_close(uc); p.deref();
        return -1;
    }

    uint64 imageBase = uc_reg_read64(uc, UC_X86_REG_RAX);
    log("PEB->ImageBaseAddress: 0x" + formatInt(imageBase, "h"));

    uc_close(uc);
    p.deref();
    return 1;
}
```

***

**Example 2 — Patch Code In-Place + Flush Cache**

This example shows why `uc_flush_code` exists.\
We run two different code blobs at the same address:

* Run 1: `mov rax, gs:[0x60]; ret` (returns PEB)
* Patch code in place
* Flush translation cache
* Run 2: `mov rax, [abs64]; ret` (returns ImageBase)

Copy

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (!p.alive()) { log_error("notepad not found"); return -1; }

    uint64 uc = uc_create_process(p, false);
    if (uc == 0) { log_error("uc_create_process failed"); p.deref(); return -1; }

    uint64 CODE  = 0x1000;
    uint64 STACK = 0x2000;
    uint64 STOP  = 0x4000;

    uc_mem_map(uc, CODE, 0x1000, UC_PROT_ALL);

    // Run 1: get PEB in RAX
    array<uint8> get_peb = {
        0x65,0x48,0x8B,0x04,0x25,0x60,0x00,0x00,0x00, // mov rax, gs:[0x60]
        0xC3
    };

    uc_mem_write(uc, CODE, get_peb);
    uc_flush_code(uc);

    uc_reg_write64(uc, UC_X86_REG_RIP, CODE);
    uc_setup_stack(uc, STACK, 0x2000, STOP);

    if (!uc_start(uc, CODE, STOP, 0, 0)) {
        log_error("uc_start(get_peb) failed");
        uc_close(uc); p.deref();
        return -1;
    }

    uint64 peb = uc_reg_read64(uc, UC_X86_REG_RAX);
    log("PEB ptr = 0x" + formatInt(peb, "h"));

    // Read expected ImageBase from process-backed memory (optional)
    array<uint8> q;
    uc_mem_read(uc, peb + 0x10, 8, q);

    uint64 expected = 0;
    for (int i = 0; i < 8; i++)
        expected |= (uint64(q[i]) << (i * 8));

    // Run 2: mov rax, [abs (peb+0x10)]
    array<uint8> read_abs = {
        0x48,0xA1,
        0,0,0,0,0,0,0,0,
        0xC3
    };

    uint64 addr = peb + 0x10;
    for (int i = 0; i < 8; i++)
        read_abs[2 + i] = uint8((addr >> (i * 8)) & 0xFF);

    uc_mem_write(uc, CODE, read_abs);
    uc_flush_code(uc);

    uc_reg_write64(uc, UC_X86_REG_RIP, CODE);
    uc_setup_stack(uc, STACK, 0x2000, STOP);

    if (!uc_start(uc, CODE, STOP, 0, 0)) {
        log_error("uc_start(read_abs) failed");
        uc_close(uc); p.deref();
        return -1;
    }

    uint64 imageBase = uc_reg_read64(uc, UC_X86_REG_RAX);
    log("ImageBase = 0x" + formatInt(imageBase, "h"));
    log("Expected  = 0x" + formatInt(expected, "h"));

    uc_close(uc);
    p.deref();
    return 1;
}
```

***

**Example 3 — Local Sandbox Emulation (No Process)**

This runs a tiny code snippet in a fully local emulator memory map.

Copy

```cpp
int main()
{
    uint64 uc = uc_create();
    if (uc == 0) { log_error("uc_create failed"); return -1; }

    uint64 CODE  = 0x1000;
    uint64 STACK = 0x2000;
    uint64 STOP  = 0x4000;

    // mov rax, 0x12345678; ret
    array<uint8> code = {
        0x48,0xC7,0xC0,0x78,0x56,0x34,0x12,
        0xC3
    };

    uc_mem_map(uc, CODE, 0x1000, UC_PROT_ALL);
    uc_mem_write(uc, CODE, code);
    uc_reg_write64(uc, UC_X86_REG_RIP, CODE);

    if (!uc_setup_stack(uc, STACK, 0x2000, STOP)) {
        log_error("uc_setup_stack failed");
        uc_close(uc);
        return -1;
    }

    if (!uc_start(uc, CODE, STOP, 0, 0)) {
        log_error("uc_start failed");
        uc_close(uc);
        return -1;
    }

    uint64 rax = uc_reg_read64(uc, UC_X86_REG_RAX);
    log("RAX = 0x" + formatInt(rax, "h"));

    uc_close(uc);
    return 1;
}
```

***

**Example 4 — Handling Null Pointer Exceptions**

This example emulates a function that dereferences a null pointer. Instead of crashing, the emulator catches it and your script can handle it gracefully.

```cpp
int main()
{
    proc_t p = ref_process("notepad.exe");
    if (!p.alive()) { log_error("notepad not found"); return -1; }

    uint64 uc = uc_create_process(p, false);
    if (uc == 0) { log_error("uc_create_process failed"); p.deref(); return -1; }

    // mov rax, 0; mov rbx, [rax] — null pointer dereference
    array<uint8> code = {
        0x48,0x31,0xC0,             // xor rax, rax
        0x48,0x8B,0x18,             // mov rbx, [rax]  <-- null deref
        0xC3                        // ret (never reached)
    };

    uint64 CODE  = 0x1000;
    uint64 STACK = 0x2000;
    uint64 STOP  = 0x4000;

    uc_mem_map(uc, CODE, 0x1000, UC_PROT_ALL);
    uc_mem_write(uc, CODE, code);
    uc_setup_stack(uc, STACK, 0x2000, STOP);

    uc_start(uc, CODE, STOP, 0, 0);

    int exc = uc_get_last_exception(uc);
    if (exc != 0) {
        uint64 addr = uc_get_exception_address(uc);
        log_error("Exception 0x" + formatInt(exc, "h") + " at RIP 0x" + formatInt(addr, "h"));
    } else {
        uint64 rbx = uc_reg_read64(uc, UC_X86_REG_RBX);
        log("RBX = 0x" + formatInt(rbx, "h"));
    }

    uc_close(uc);
    p.deref();
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
GET https://docs.perception.cx/perception/angel-script/unicorn.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/utilities.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/utilities.md).

# Utilities

Low-level helpers for encoding/decoding binary data and text.

All functions treat `string` as a raw byte container, so they work fine with binary data (including `\0` bytes and non-UTF8).

#### Functions

```cpp
string util_base64_encode(const string &in data)
bool   util_base64_decode(const string &in text, string &out data, string &out error)

string util_hex_encode(const string &in data)
bool   util_hex_decode(const string &in text, string &out data, string &out error)

string util_url_encode(const string &in data)
string util_url_decode(const string &in data)
```

***

### Base64 helpers

#### `string util_base64_encode(const string &in data)`

Encodes arbitrary data as Base64 text.

* **Parameters**
  * `data` — Input bytes to encode (any string, including binary).
* **Returns**
  * Base64-encoded text using the standard alphabet `A–Z a–z 0–9 + /` with `=` padding.

**Example**

```cpp
string original = "hello";
string enc = util_base64_encode(original);
log("Base64 = " + enc);   // "aGVsbG8="
```

***

#### `bool util_base64_decode(const string &in text, string &out data, string &out error)`

Decodes a Base64 string back into raw bytes.

* **Parameters**
  * `text` — Base64 text to decode.
  * `data` (out) — Output decoded bytes on success.
  * `error` (out) — Error message when returning `false`.
* **Returns**
  * `true` on success, `false` on error.

**On success**

* `data` contains decoded bytes.
* `error` is empty.

**On failure**

* `data` is empty.
* `error` contains a human-readable message (e.g. `"Invalid base64 character"`).

**Example**

```cpp
string src = "aGVsbG8=";
string raw, err;

if (util_base64_decode(src, raw, err))
{
    log("decoded = " + raw);   // "hello"
}
else
{
    log_error("base64 decode failed: " + err);
}
```

**Error example**

```cpp
string bad = "aGVsbG8$";       // invalid char
string data, err;
bool ok = util_base64_decode(bad, data, err);
// ok  == false
// err == "Invalid base64 character"
```

***

### Hex helpers

#### `string util_hex_encode(const string &in data)`

Encodes binary data as uppercase hexadecimal text.

* **Parameters**
  * `data` — Raw bytes to encode.
* **Returns**
  * Hex string using `0–9 A–F`. Each byte becomes 2 characters.

**Example**

```cpp
string original = "hello";
string hex = util_hex_encode(original);
log("hex = " + hex);      // "68656C6C6F"
```

***

#### `bool util_hex_decode(const string &in text, string &out data, string &out error)`

Decodes a hex string back into raw bytes.

* **Parameters**

| Name  | Type           | Description                          |
| ----- | -------------- | ------------------------------------ |
| text  | `string`       | Hex text (must have even length)     |
| data  | `string` (out) | Output decoded bytes on success      |
| error | `string` (out) | Error message when returning `false` |

* **Returns**
  * `true` on success, `false` on error.

**On success**

* `data` contains decoded bytes.
* `error` is empty.

**On failure**

* `data` is empty.
* `error` contains a message.

**Example**

```cpp
string hex = "68656C6C6F";
string raw, err;

if (util_hex_decode(hex, raw, err))
{
    log("raw = " + raw);   // "hello"
}
else
{
    log_error("hex decode failed: " + err);
}
```

**Error examples**

```cpp
// 1) Odd length
string bad1  = "ABC";
string data1, err1;
bool ok1 = util_hex_decode(bad1, data1, err1);
// ok1  == false
// err1 == "Hex string length must be even"

// 2) Invalid characters
string bad2  = "GGGG";
string data2, err2;
bool ok2 = util_hex_decode(bad2, data2, err2);
// ok2  == false
// err2 == "Invalid hex character"
```

***

### URL helpers

These functions use standard URL percent-encoding:

* Unreserved characters stay as-is: `A–Z a–z 0–9 - _ . ~`
* Everything else becomes `%XX` (hex byte).

> **Note:** `util_url_decode` does **not** convert `+` to space. `+` is treated as a normal character.

#### `string util_url_encode(const string &in data)`

Percent-encodes a string for safe use in URLs (query params, etc).

* **Parameters**
  * `data` — Input string (can be binary, but typically text).
* **Returns**
  * URL-encoded string.

**Example**

```cpp
string original = "hello world! 100% ok?";
string enc = util_url_encode(original);
// Example: "hello%20world%21%20100%25%20ok%3F"

log("url encoded = " + enc);
```

***

#### `string util_url_decode(const string &in data)`

Decodes `%XX` sequences back into raw bytes.

* **Parameters**
  * `data` — URL-encoded string (e.g. `"hello%20world"`).
* **Returns**
  * Decoded string with `%XX` sequences converted to bytes.
  * Invalid `%` sequences are left as literal characters.

**Example**

```cpp
string url = "name=John%20Doe&msg=hello%21";
string decoded = util_url_decode(url);
// "name=John Doe&msg=hello!"

log("url decoded = " + decoded);
```

***

### Roundtrip examples

#### Base64 roundtrip

```cpp
string original = "The quick brown fox.";
string enc = util_base64_encode(original);
string dec, err;

if (util_base64_decode(enc, dec, err) && dec == original)
{
    log("Base64 roundtrip OK");
}
else
{
    log_error("Base64 roundtrip failed: " + err);
}
```

#### Hex roundtrip

```cpp
string original = "hello world!";
string hex = util_hex_encode(original);
string raw, err;

if (util_hex_decode(hex, raw, err) && raw == original)
{
    log("Hex roundtrip OK");
}
else
{
    log_error("Hex roundtrip failed: " + err);
}
```

#### URL roundtrip

```cpp
string original = "email=test@example.com&msg=hi there!";
string enc = util_url_encode(original);
string dec = util_url_decode(enc);

if (dec == original)
{
    log("URL roundtrip OK");
}
else
{
    log_error("URL roundtrip failed");
}
```

***

### Binary safety

All `util_*` functions operate on `string` as byte containers:

* You can safely encode/decode **binary** data.
* Data with `\0` bytes is preserved.
* Non-UTF8 content is preserved.

Useful for:

* Network packets
* Encryption keys
* Hash outputs
* Serialized structs / blobs

***

### hash\_set&#x20;

`hash_set` is a lightweight `unordered_set<uint64>` wrapper for fast membership tests (O(1) average).

#### Type

`hash_set`

#### Methods

**Core**

* `bool hash_set::contains(uint64 v) const`\
  Returns true if `v` exists in the set.
* `bool hash_set::insert(uint64 v)`\
  Inserts `v`. Returns true if it was newly inserted, false if it already existed.
* `bool hash_set::erase(uint64 v)`\
  Removes `v`. Returns true if an element was removed, false if it wasn’t present.
* `void hash_set::clear()`\
  Removes all elements.
* `uint hash_set::size() const`\
  Returns the number of elements.
* `bool hash_set::empty() const`\
  Returns true if the set is empty.

***

**Convenience**

* `void hash_set::set(uint64 v)`\
  Inserts `v` without returning a status.
* `bool hash_set::get(uint64 v, uint64 &out value)`\
  Checks if `v` exists and outputs the stored value.

***

**Iteration**

* `void hash_set::iter_begin()`\
  Resets the internal iterator to the start.
* `bool hash_set::iter_next(uint64 &out value)`\
  Retrieves the next value in the set.\
  Returns false when iteration is finished.

***

### hash\_map&#x20;

`hash_map` is a lightweight unordered map that associates `uint64` keys with any AngelScript type\
(primitives, strings, objects, and handles).

All operations run in O(1) average time.

#### Type

`hash_map`

#### Methods

**Construction**

* `hash_map@ hash_map()`\
  Factory constructor.

***

**Core**

* `void hash_map::set(uint64 key, ?&in value)`\
  Stores a value for the given key.
* `bool hash_map::get(uint64 key, ?&out value)`\
  Retrieves the value associated with `key`.\
  Returns true if found.
* `bool hash_map::contains(uint64 key)`\
  Returns true if the key exists.
* `bool hash_map::erase(uint64 key)`\
  Removes the entry for `key`.\
  Returns true if removed.
* `void hash_map::clear()`\
  Removes all entries.
* `uint hash_map::size()`\
  Returns the number of stored entries.
* `bool hash_map::empty()`\
  Returns true if the map is empty.

***

**Iteration**

* `void hash_map::iter_begin()`\
  Resets the internal iterator to the start.
* `bool hash_map::iter_next_key(uint64 &out key)`\
  Iterates over keys only.
* `bool hash_map::iter_next(uint64 &out key, ?&out value)`\
  Iterates over key-value pairs.

### Example (hash\_set & hash\_map)

```cpp
int main()
{
    log("hash_set + hash_map test: start");
    
    // ============================
    // hash_set tests
    // ============================
    
    hash_set s;
    
    // empty / size
    if (!s.empty()) { log_error("hash_set: expected empty() == true"); return 0; }
    if (s.size() != 0) { log_error("hash_set: expected size() == 0"); return 0; }
    
    // insert / set / contains
    if (!s.insert(0x100)) { log_error("hash_set: insert(0x100) should return true"); return 0; }
    s.set(0x200);
    
    if (!s.contains(0x100)) { log_error("hash_set: contains(0x100) failed"); return 0; }
    if (!s.contains(0x200)) { log_error("hash_set: contains(0x200) failed"); return 0; }
    if (s.contains(0x999)) { log_error("hash_set: contains(0x999) should be false"); return 0; }
    
    if (s.size() != 2) { log_error("hash_set: expected size() == 2"); return 0; }
    
    // get
    uint64 out_v = 0;
    if (!s.get(0x100, out_v) || out_v != 0x100)
    {
        log_error("hash_set: get(0x100) failed");
        return 0;
    }
    
    // erase
    if (!s.erase(0x100)) { log_error("hash_set: erase(0x100) should return true"); return 0; }
    if (s.erase(0x100))  { log_error("hash_set: erase(0x100) should return false"); return 0; }
    
    if (s.contains(0x100)) { log_error("hash_set: value still exists after erase"); return 0; }
    if (s.size() != 1) { log_error("hash_set: expected size() == 1 after erase"); return 0; }
    
    // iteration
    uint iter_count = 0;
    s.iter_begin();
    while (true)
    {
        uint64 v = 0;
        if (!s.iter_next(v))
        break;
        
        if (v != 0x200)
        {
            log_error("hash_set: unexpected value in iteration");
            return 0;
        }
        
        iter_count++;
    }
    
    if (iter_count != 1)
    {
        log_error("hash_set: iteration count mismatch");
        return 0;
    }
    
    // clear
    s.clear();
    if (!s.empty() || s.size() != 0)
    {
        log_error("hash_set: clear() failed");
        return 0;
    }
    
    // ============================
    // hash_map tests
    // ============================
    
    hash_map@ m = hash_map();
    if (m is null) { log_error("hash_map: factory returned null"); return 0; }
    
    // empty / size
    if (!m.empty()) { log_error("hash_map: expected empty() == true"); return 0; }
    if (m.size() != 0) { log_error("hash_map: expected size() == 0"); return 0; }
    
    int    vi = 42;
    double vd = 2.5;
    string vs = "test";
    
    // set
    m.set(1, vi);
    m.set(2, vd);
    m.set(3, vs);
    
    if (m.size() != 3) { log_error("hash_map: expected size() == 3"); return 0; }
    
    // contains
    if (!m.contains(1) || !m.contains(2) || !m.contains(3))
    {
        log_error("hash_map: contains failed");
        return 0;
    }
    
    if (m.contains(999))
    {
        log_error("hash_map: contains(999) should be false");
        return 0;
    }
    
    // get with correct types
    int out_i = 0;
    if (!m.get(1, out_i) || out_i != 42)
    {
        log_error("hash_map: get int failed");
        return 0;
    }
    
    double out_d = 0.0;
    if (!m.get(2, out_d) || out_d != 2.5)
    {
        log_error("hash_map: get double failed");
        return 0;
    }
    
    string out_s;
    if (!m.get(3, out_s) || out_s != "test")
    {
        log_error("hash_map: get string failed");
        return 0;
    }
    
    // type mismatch should fail
    string wrong;
    if (m.get(1, wrong))
    {
        log_error("hash_map: expected type mismatch to return false");
        return 0;
    }
    
    // iteration (keys only)
    uint key_count = 0;
    m.iter_begin();
    while (true)
    {
        uint64 k = 0;
        if (!m.iter_next_key(k))
        break;
        
        if (!m.contains(k))
        {
            log_error("hash_map: iter_next_key returned invalid key");
            return 0;
        }
        
        key_count++;
    }
    
    if (key_count != m.size())
    {
        log_error("hash_map: key iteration count mismatch");
        return 0;
    }
    
    // erase
    if (!m.erase(2)) { log_error("hash_map: erase(2) should return true"); return 0; }
    if (m.erase(2))  { log_error("hash_map: erase(2) should return false"); return 0; }
    
    if (m.contains(2))
    {
        log_error("hash_map: value still exists after erase");
        return 0;
    }
    
    if (m.size() != 2)
    {
        log_error("hash_map: expected size() == 2 after erase");
        return 0;
    }
    
    // clear
    m.clear();
    if (!m.empty() || m.size() != 0)
    {
        log_error("hash_map: clear() failed");
        return 0;
    }
    
    log("hash_set + hash_map test: OK");
    return 0;
}

```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/utilities.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/win-api.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/win-api.md).

# Win API

This API allows AngelScript scripts to interact with Windows:

* Find windows by title or class
* Read window titles, classes, positions, sizes
* Detect whether a window is foreground or active
* Read or write clipboard text
* Discover the thread & process IDs for a window
* Send messages (WM\_CHAR, WM\_KEYDOWN, WM\_KEYUP, etc.)
* Send global keyboard/mouse events (SendInput)

Handles (`hwnd`) are represented as **uint64** values.

***

## **Window Lookup**

#### `uint64 find_window(const string &in title)`

Finds a top-level window by its title.

Returns 0 if not found.

***

### Window Enumeration

#### &#x20;`array<WindowInfo>@ get_all_hwnds()`

Enumerates all top-level windows on the system and returns detailed information about each.

**Returns:** Handle to an array of `WindowInfo` objects, or `null` on failure.

#### WindowInfo Type

A value type containing window details:

| Property       | Type     | Description                             |
| -------------- | -------- | --------------------------------------- |
| `hwnd`         | `uint64` | Window handle                           |
| `pid`          | `uint`   | Process ID                              |
| `tid`          | `uint`   | Thread ID                               |
| `process_name` | `string` | Executable name (e.g., `"notepad.exe"`) |
| `title`        | `string` | Window title text                       |
| `class_name`   | `string` | Window class name                       |

**Example:**

```cpp
int main()
{
    array<WindowInfo>@ windows = get_all_hwnds();
    
    if (windows is null)
    {
        log("Failed to get windows list");
        return 0;
    }
    
    log("Found " + windows.length() + " windows\n");
    
    for (uint i = 0; i < windows.length(); i++)
    {
        WindowInfo w = windows[i];
        
        if (w.title.isEmpty())
           continue;
        
        log("=== Window " + (i + 1) + " ===");
        log("  HWND:         " + w.hwnd);
        log("  PID:          " + w.pid);
        log("  TID:          " + w.tid);
        log("  Process:      " + w.process_name);
        log("  Title:        " + w.title);
        log("  Class:        " + w.class_name);
        log("");
    }
    
    for (uint i = 0; i < windows.length(); i++)
    {
        if (windows[i].process_name == "notepad.exe")
        {
            log("Found Notepad! HWND: " + windows[i].hwnd);
            break;
        }
    }
      return 0;
}


```

***

#### `uint64 find_window(const string &in title, const string &in className)`

Finds a window by **title** and **class name**.

Pass empty string (`""`) to ignore a filter.

Returns 0 if not found.

***

## **Window Information**

#### `bool get_window_size(uint64 hwnd, int &out w, int &out h)`

Retrieves the window’s width and height (outer size).

Returns `false` if the window is invalid.

***

#### `bool get_window_rect(uint64 hwnd, int &out x, int &out y, int &out w, int &out h)`

Retrieves full window rect:

* `x, y` — top-left screen coordinates
* `w, h` — size in pixels

Returns `false` on failure.

***

#### `bool get_window_title(uint64 hwnd, string &out title)`

Gets the window’s title text (UTF-8).

* Returns `true` even for empty titles.
* Returns `false` only when the hwnd is invalid.

***

#### `bool get_window_class(uint64 hwnd, string &out cls)`

Gets the Win32 window class name.

Returns `false` if the window is invalid.

***

## **Foreground / Activity**

#### `bool set_foreground_window(uint64 hwnd)`

Attempts to bring the window to foreground.

***

#### `bool is_foreground_window(uint64 hwnd)`

Returns `true` if the given window is currently foreground.

***

#### `bool is_window_active(uint64 hwnd)`

Checks whether the window:

* is valid
* is visible
* is **not minimized**

This is a broader “is active” check.

***

## **Clipboard**

All clipboard strings are UTF-8.

#### `bool copy_to_clipboard(const string &in text)`

Copies text into the Windows clipboard.

***

#### `bool copy_from_clipboard(string &out text)`

Reads text from the Windows clipboard.

* Returns `true` if any text was successfully retrieved.
* Empty clipboard → empty string.

***

## **Thread & Process Info**

#### `bool get_window_thread_process_id(uint64 hwnd, uint &out tid, uint &out pid)`

Retrieves:

* `tid` — thread ID
* `pid` — process ID

Returns `false` if the hwnd is invalid.

***

## **Messaging**

#### `bool post_message(uint64 hwnd, uint msg, uint64 wparam, uint64 lparam)`

Posts a raw Win32 message to a window.

Examples:

* `post_message(hwnd, 0x0010, 0, 0)` → WM\_CLOSE
* `post_message(hwnd, 0x0100, VK_A, 0)` → WM\_KEYDOWN for ‘A’

Returns `false` if the hwnd is invalid.

***

## **Keyboard Input**

### Global keyboard (SendInput)

These functions simulate real keyboard events globally.

#### `void win_key_down(uint vk)`

Simulates a key-down.

#### `void win_key_up(uint vk)`

Simulates a key-up.

#### `void win_key_press(uint vk, uint delay_ms = 30)`

Press → delay → release.

* `delay_ms` clamped to `0..1000`.

***

### Window-targeted typing (PostMessage)

#### `bool send_char(uint64 hwnd, const string &in text)`

Sends a single character to a window using `WM_CHAR`.

* Only the **first UTF-16 code unit** is used.

***

#### `bool send_key(uint64 hwnd, uint vk)`

Sends:

* `WM_KEYDOWN`
* `WM_KEYUP`

…to a specific window.

***

## **Mouse Input**

Mouse input uses real global `SendInput` events.

#### `void mouse_move(int x, int y)`

Moves the mouse to absolute screen coordinates.

#### `void mouse_move_relative(int dx, int dy)`

Moves the mouse relative to the current cursor position.

***

#### `void mouse_left_click()`

Left button click.

#### `void mouse_right_click()`

Right button click.

#### `void mouse_middle_click()`

Middle button click.

Each sends DOWN → small wait → UP.

***

#### `void mouse_scroll(int amount)`

Scroll amount in “wheel notches”:

* positive → scroll up
* negative → scroll down

***

#### `void send_mouse_input(int64 dx, int64 dy, uint flags, uint mouse_data)`

Send input manually via raw input.

***

## **Util**

`int64 get_tickcount64()`

* GetTickCount64()

***

## **Examples**

### Find a window & print info

```cpp
string title;
string cls;

uint64 hwnd = find_window("Untitled - Notepad");

if (hwnd != 0)
{
    int x, y, w, h;
    get_window_rect(hwnd, x, y, w, h);

    get_window_title(hwnd, title);
    get_window_class(hwnd, cls);

    log("Title: " + title);
    log("Class: " + cls);
    log("Rect: " + x + "," + y + "  size " + w + "x" + h);
}
```

***

### Clipboard

```cpp
copy_to_clipboard("AngelScript clipboard test こんにちは 🌸");

string out;
copy_from_clipboard(out);

log("Clipboard: " + out);
```

***

### Global keyboard

<pre class="language-cpp"><code class="lang-cpp">// Type “HELLO”
win_key_press(0x48); // H
win_key_press(0x45); // E
win_key_press(0x4C); // L
win_key_press(0x4C); // L
<strong>win_key_press(0x4F); // O
</strong>
// Ctrl+V
win_key_down(0x11); // Ctrl
win_key_press(0x56); // V
win_key_up(0x11);
</code></pre>

***

### Send chars to a window

```cpp
uint64 hwnd = find_window("Untitled - Notepad");

set_foreground_window(hwnd);

send_char(hwnd, "H");
send_char(hwnd, "i");
send_char(hwnd, " ");
send_char(hwnd, "🌸");

send_key(hwnd, 0x0D); // Enter
```

***

### Mouse interaction

```cpp
mouse_move(100, 200);
mouse_left_click();

mouse_move_relative(50, 0);
mouse_right_click();

mouse_scroll(3);   // up
mouse_scroll(-3);  // down
```

## Full API Test

```cpp
const string TARGET_TITLE = "Untitled - Notepad"; // change as you like

void log_line(const string &in msg)
{
    log("[AS-WINAPI] " + msg);
}

void dump_window_info(uint64 hwnd)
{
    if (hwnd == 0)
    {
        log_line("HWND = 0");
        return;
    }
    
    log_line("HWND = 0x" + formatInt(int64(hwnd), "H"));
    
    string title, cls;
    if (get_window_title(hwnd, title))
    log_line("  title: " + title);
    else
    log_line("  title: <failed>");
    
    if (get_window_class(hwnd, cls))
    log_line("  class: " + cls);
    else
    log_line("  class: <failed>");
    
    int x, y, w, h;
    if (get_window_rect(hwnd, x, y, w, h))
    log_line("  rect:  x=" + x + " y=" + y + " w=" + w + " h=" + h);
    else
    log_line("  rect:  <failed>");
    
    uint tid, pid;
    if (get_window_thread_process_id(hwnd, tid, pid))
    log_line("  tid=" + tid + " pid=" + pid);
    else
    log_line("  tid/pid: <failed>");
}

uint64 get_target_hwnd()
{
    log_line("Target window title: " + TARGET_TITLE);
    
    uint64 hwnd = find_window(TARGET_TITLE);
    if (hwnd == 0)
    {
        log_line("Window not found.");
        return 0;
    }
    
    log_line("Found window.");
    dump_window_info(hwnd);
    
    bool fg = set_foreground_window(hwnd);
    log_line("set_foreground_window -> " + (fg ? "true" : "false"));
    
    return hwnd;
}

void test_mouse_basic()
{
    log_line("=== TEST: mouse movement & clicks ===");
    log_line("Move your eyes to where the cursor goes. :)");
    
    mouse_move(100, 100);
    mouse_left_click();
    log_line("  mouse_move(100,100) + left click");
    
    mouse_move_relative(80, 0);
    mouse_right_click();
    log_line("  mouse_move_relative(80,0) + right click");
    
    mouse_move_relative(0, 60);
    mouse_middle_click();
    log_line("  mouse_move_relative(0,60) + middle click");
    
    mouse_scroll(3);
    mouse_scroll(-3);
    log_line("  mouse_scroll(3) then mouse_scroll(-3)");
}

void test_clipboard()
{
    log_line("=== TEST: clipboard ===");
    
    string src = "Hello from AngelScript WinAPI! こんにちは 🌸";
    bool okSet = copy_to_clipboard(src);
    log_line("  copy_to_clipboard -> " + (okSet ? "true" : "false"));
    
    string got;
    bool okGet = copy_from_clipboard(got);
    log_line("  copy_from_clipboard -> " + (okGet ? "true" : "false"));
    log_line("  clipboard text: " + got);
}

void test_send_char_key(uint64 hwnd)
{
    log_line("=== TEST: send_char / send_key ===");
    
    if (hwnd == 0)
    {
        log_line("No hwnd, skipping send_char/send_key test.");
        return;
    }
    
    log_line("Make sure the target window has a focused text field.");
    
    // Send "Hi " + a flower
    bool ok1 = send_char(hwnd, "H");
    bool ok2 = send_char(hwnd, "i");
    bool ok3 = send_char(hwnd, " ");
    bool ok4 = send_char(hwnd, "🌸"); // first UTF-16 unit is used
    
    log_line("  send_char H -> " + (ok1 ? "true" : "false"));
    log_line("  send_char i -> " + (ok2 ? "true" : "false"));
    log_line("  send_char ' ' -> " + (ok3 ? "true" : "false"));
    log_line("  send_char 🌸 -> " + (ok4 ? "true" : "false"));
    
    // send Enter via WM_KEYDOWN/UP
    const uint VK_RETURN = 0x0D;
    bool okEnter = send_key(hwnd, VK_RETURN);
    log_line("  send_key(VK_RETURN) -> " + (okEnter ? "true" : "false"));
}

void test_global_keys()
{
    log_line("=== TEST: global key_press ===");
    log_line("Make sure some text field is focused if you want to see output.");
    
    // Type 'HELLO'
    const uint VK_H = 0x48;
    const uint VK_E = 0x45;
    const uint VK_L = 0x4C;
    const uint VK_O = 0x4F;
    
    win_key_press(VK_H, 40);
    win_key_press(VK_E, 40);
    win_key_press(VK_L, 40);
    win_key_press(VK_L, 40);
    win_key_press(VK_O, 40);
    
    // Ctrl+V (paste)
    const uint VK_CONTROL = 0x11;
    const uint VK_V       = 0x56;
    
    win_key_down(VK_CONTROL);
    win_key_press(VK_V, 30);
    win_key_up(VK_CONTROL);
    
    log_line("  typed HELLO and sent Ctrl+V");
}

int main()
{
    log_line("=== AS WinAPI Input Test START ===");
    
    uint64 hwnd = get_target_hwnd();
    
    test_mouse_basic();
    test_clipboard();
    test_global_keys();
    test_send_char_key(hwnd);
    
    log_line("=== AS WinAPI Input Test END ===");
    return 1; // keep script loaded if your host uses this
}


```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/win-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/perception/angelscript/zydis-encoder.md`

> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/zydis-encoder.md).

# Zydis Encoder

The **Zydis Encoder API** lets you **assemble instructions into raw machine code** at runtime. It’s designed for:

* Re-assembling disassembled code into **position-independent shellcode**
* Dynamically building/modifying shellcode for **Unicorn emulation**
* Inserting breakpoints (`int3`) or patching code on the fly

This encoder complements your Zydis disassembler by providing a structured way to **create `ZydisEncoderRequest` objects** and turn them into bytes.

***

### Concepts

#### Machine Mode

Most encoding depends on the active CPU mode:

* `MODE_LONG_64` (x86-64)
* `MODE_LONG_COMPAT_32`, `MODE_LONG_COMPAT_16`
* `MODE_LEGACY_32`, `MODE_LEGACY_16`
* `MODE_REAL_16`

Set the machine mode either:

* per-request (`ZydisEncoderRequest.set_machine_mode`)
* globally in a builder (`ZydisBuilder.set_machine_mode`)

***

### Enums

#### `ZYDIS_MACHINE_MODE`

* `MODE_LONG_64`
* `MODE_LONG_COMPAT_32`
* `MODE_LONG_COMPAT_16`
* `MODE_LEGACY_32`
* `MODE_LEGACY_16`
* `MODE_REAL_16`

#### `ZYDIS_BRANCH_TYPE`

Controls how a branch should be encoded.

* `BRANCH_NONE`
* `BRANCH_SHORT`
* `BRANCH_NEAR`
* `BRANCH_FAR`

#### `ZYDIS_BRANCH_WIDTH`

Controls displacement width for branch encoding.

* `WIDTH_NONE`
* `WIDTH_8`
* `WIDTH_16`
* `WIDTH_32`
* `WIDTH_64`

***

### Types

### `ZydisEncoderRequest` (value type)

A request describes a **single instruction** to be encoded.

#### Mnemonic & mode

* `void set_mnemonic(int mnemonic)`
* `int get_mnemonic()`
* `void set_machine_mode(int mode)`
* `int get_machine_mode()`

#### Operands

* `void set_operand_count(int count)`
* `int get_operand_count()`

#### Branch controls

* `void set_branch_type(int type)`
* `void set_branch_width(int width)`

#### Operand setters

* `void set_operand_reg(int index, int reg)`
* `void set_operand_imm(int index, int64 imm)`
* `void set_operand_mem(int index, int base, int idx, int scale, int64 disp, int size)`
* `void set_operand_ptr(int index, uint16 segment, uint32 offset)`

**Notes**

* Operand indexing is **0-based**.
* You must call `set_operand_count(n)` before setting operands.
* For memory operands, `base` and `idx` are register IDs (or `0` / none depending on your bindings), with:
  * `scale`: typically 1, 2, 4, 8
  * `disp`: signed displacement
  * `size`: operand size in bytes (e.g., `4` for dword, `8` for qword)

***

### `ZydisBuilder` (reference type)

A builder collects **instructions + raw bytes** and emits a single byte array.

#### Construction

* `ZydisBuilder@ ZydisBuilder()` — factory

#### Configuration

* `void set_machine_mode(int mode)`
* `void set_base_address(uint64 addr)`

#### Managing entries

* `void clear()`
* `void push(const ZydisEncoderRequest &in req)`
* `int get_instruction_count()`

#### Raw bytes helpers

* `void push_bytes(const array<uint8> &in bytes)`
* `void push_byte(uint8 b)`
* `void push_u16(uint16 value)` — little-endian
* `void push_u32(uint32 value)` — little-endian
* `void push_u64(uint64 value)` — little-endian

#### Convenience opcodes

* `void push_nop(int count = 1)`
* `void push_int3()`
* `void push_ret()`

#### Build output

* `bool build(array<uint8> &out bytes)`

**Notes**

* `set_base_address()` matters for **relative branches** and RIP-based calculations.
* `push_*` functions let you interleave **code and data** (useful for shellcode blobs).

***

### Global Functions

#### Encoding

* `bool zydis_encode(ZydisEncoderRequest &in req, array<uint8> &out bytes)`
* `bool zydis_encode_absolute(ZydisEncoderRequest &in req, uint64 runtime_address, array<uint8> &out bytes)`

Use `zydis_encode_absolute` when the instruction’s encoding depends on the actual runtime address (e.g., some branch forms / relative addressing decisions).

#### Utilities

* `bool zydis_nop_fill(array<uint8> &out bytes, uint32 length)`
* `bool zydis_decoded_to_request(const array<uint8> &in bytes, uint64 runtime_rip, ZydisEncoderRequest &out req)`

#### Mnemonic and register conversion

* `int zydis_mnemonic_from_string(const string &in name)`
* `string zydis_mnemonic_to_string(int mnemonic)`
* `int zydis_register_from_string(const string &in name)`
* `string zydis_register_to_string(int reg)`

***

## Full Test Example

```cpp
int main()
{
    test_basic_encoding();
    test_builder_api();
    test_raw_bytes();
    test_decode_to_request();
    test_nop_fill();
    test_memory_operands();
    test_branch_instructions();
    test_mixed_shellcode();
    log("All Zydis encoder tests completed!");
    return 0;
}

void test_basic_encoding()
{
    log("=== Testing basic instruction encoding ===");
    
    ZydisEncoderRequest req;
    req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    req.set_operand_count(2);
    req.set_operand_reg(0, zydis_register_from_string("rax"));
    req.set_operand_imm(1, 0x1234567890ABCDEF);
    
    array<uint8> bytes;
    if (zydis_encode(req, bytes))
    {
        log("mov rax, 0x1234567890ABCDEF encoded (" + bytes.length() + " bytes): " + bytes_to_hex(bytes));
        disasm_and_print(bytes, 0);
    }
    else
    {
        log_error("Failed to encode mov rax, imm64");
    }
    
    ZydisEncoderRequest req2;
    req2.set_mnemonic(zydis_mnemonic_from_string("xor"));
    req2.set_operand_count(2);
    req2.set_operand_reg(0, zydis_register_from_string("eax"));
    req2.set_operand_reg(1, zydis_register_from_string("eax"));
    
    array<uint8> bytes2;
    if (zydis_encode(req2, bytes2))
    {
        log("xor eax, eax encoded (" + bytes2.length() + " bytes): " + bytes_to_hex(bytes2));
        disasm_and_print(bytes2, 0);
    }
    else
    {
        log_error("Failed to encode xor eax, eax");
    }
    
    ZydisEncoderRequest req3;
    req3.set_mnemonic(zydis_mnemonic_from_string("inc"));
    req3.set_operand_count(1);
    req3.set_operand_reg(0, zydis_register_from_string("rcx"));
    
    array<uint8> bytes3;
    if (zydis_encode(req3, bytes3))
    {
        log("inc rcx encoded (" + bytes3.length() + " bytes): " + bytes_to_hex(bytes3));
        disasm_and_print(bytes3, 0);
    }
}

void test_builder_api()
{
    log("=== Testing ZydisBuilder API ===");
    
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140001000);
    builder.set_machine_mode(MODE_LONG_64);
    
    ZydisEncoderRequest mov_req;
    mov_req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    mov_req.set_operand_count(2);
    mov_req.set_operand_reg(0, zydis_register_from_string("rax"));
    mov_req.set_operand_imm(1, 0x42);
    builder.push(mov_req);
    
    ZydisEncoderRequest push_req;
    push_req.set_mnemonic(zydis_mnemonic_from_string("push"));
    push_req.set_operand_count(1);
    push_req.set_operand_reg(0, zydis_register_from_string("rax"));
    builder.push(push_req);
    
    ZydisEncoderRequest pop_req;
    pop_req.set_mnemonic(zydis_mnemonic_from_string("pop"));
    pop_req.set_operand_count(1);
    pop_req.set_operand_reg(0, zydis_register_from_string("rbx"));
    builder.push(pop_req);
    
    builder.push_nop(3);
    builder.push_int3();
    builder.push_ret();
    
    log("Instruction count: " + builder.get_instruction_count());
    
    array<uint8> shellcode;
    if (builder.build(shellcode))
    {
        log("Built shellcode (" + shellcode.length() + " bytes): " + bytes_to_hex(shellcode));
        disasm_and_print(shellcode, 0x140001000);
    }
    else
    {
        log_error("Failed to build shellcode");
    }
}

void test_raw_bytes()
{
    log("=== Testing raw bytes push ===");
    
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140002000);
    
    builder.push_byte(0xCC);
    
    builder.push_u16(0xBEEF);
    
    builder.push_u32(0xDEADBEEF);
    
    builder.push_u64(0xCAFEBABE12345678);
    
    array<uint8> raw_data = {0x90, 0x90, 0x48, 0x89, 0xC3};
    builder.push_bytes(raw_data);
    
    builder.push_ret();
    
    log("Entry count (mixed): " + builder.get_instruction_count());
    
    array<uint8> result;
    if (builder.build(result))
    {
        log("Mixed raw bytes result (" + result.length() + " bytes): " + bytes_to_hex(result));
        
        log("Breakdown:");
        log("  Byte 0 (CC): 0x" + format_hex_byte(result[0]));
        log("  U16 (BEEF): 0x" + format_hex_byte(result[1]) + format_hex_byte(result[2]));
        log("  U32 (DEADBEEF): 0x" + format_hex_byte(result[3]) + format_hex_byte(result[4]) + format_hex_byte(result[5]) + format_hex_byte(result[6]));
        log("  U64 starts at byte 7...");
    }
    else
    {
        log_error("Failed to build mixed raw bytes");
    }
}

void test_decode_to_request()
{
    log("=== Testing decode to request (re-encoding) ===");
    
    array<uint8> original = {0x48, 0x89, 0xC3};
    
    ZydisEncoderRequest req;
    if (zydis_decoded_to_request(original, 0x140001000, req))
    {
        log("Decoded mnemonic: " + zydis_mnemonic_to_string(req.get_mnemonic()));
        log("Operand count: " + req.get_operand_count());
        
        array<uint8> reencoded;
        if (zydis_encode(req, reencoded))
        {
            log("Original:   " + bytes_to_hex(original));
            log("Re-encoded: " + bytes_to_hex(reencoded));
            
            if (compare_arrays(original, reencoded))
            {
                log("SUCCESS: Re-encoding matches original!");
            }
            else
            {
                log("WARN: Re-encoding differs (may still be semantically equivalent)");
            }
        }
    }
    else
    {
        log_error("Failed to decode instruction");
    }
    
    array<uint8> lea_bytes = {0x48, 0x8D, 0x04, 0x8B};
    ZydisEncoderRequest lea_req;
    if (zydis_decoded_to_request(lea_bytes, 0, lea_req))
    {
        log("Decoded LEA mnemonic: " + zydis_mnemonic_to_string(lea_req.get_mnemonic()));
        array<uint8> lea_reenc;
        if (zydis_encode(lea_req, lea_reenc))
        {
            log("LEA original:   " + bytes_to_hex(lea_bytes));
            log("LEA re-encoded: " + bytes_to_hex(lea_reenc));
        }
    }
}

void test_nop_fill()
{
    log("=== Testing NOP fill ===");
    
    array<uint8> nops5;
    if (zydis_nop_fill(nops5, 5))
    {
        log("NOP sled (5 bytes): " + bytes_to_hex(nops5));
        disasm_and_print(nops5, 0);
    }
    
    array<uint8> nops15;
    if (zydis_nop_fill(nops15, 15))
    {
        log("NOP sled (15 bytes): " + bytes_to_hex(nops15));
        disasm_and_print(nops15, 0);
    }
    
    array<uint8> nops1;
    if (zydis_nop_fill(nops1, 1))
    {
        log("NOP sled (1 byte): " + bytes_to_hex(nops1));
    }
}

void test_memory_operands()
{
    log("=== Testing memory operands ===");
    
    ZydisEncoderRequest req;
    req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    req.set_operand_count(2);
    req.set_operand_reg(0, zydis_register_from_string("rax"));
    int rbx = zydis_register_from_string("rbx");
    int rcx = zydis_register_from_string("rcx");
    req.set_operand_mem(1, rbx, rcx, 8, 0x100, 8);
    
    array<uint8> bytes;
    if (zydis_encode(req, bytes))
    {
        log("mov rax, [rbx+rcx*8+0x100] (" + bytes.length() + " bytes): " + bytes_to_hex(bytes));
        disasm_and_print(bytes, 0);
    }
    
    ZydisEncoderRequest req2;
    req2.set_mnemonic(zydis_mnemonic_from_string("mov"));
    req2.set_operand_count(2);
    int rax = zydis_register_from_string("rax");
    int none = 0;
    req2.set_operand_mem(0, rax, none, 0, 0, 4);
    req2.set_operand_reg(1, zydis_register_from_string("edx"));
    
    array<uint8> bytes2;
    if (zydis_encode(req2, bytes2))
    {
        log("mov [rax], edx (" + bytes2.length() + " bytes): " + bytes_to_hex(bytes2));
        disasm_and_print(bytes2, 0);
    }
    
    ZydisEncoderRequest req3;
    req3.set_mnemonic(zydis_mnemonic_from_string("lea"));
    req3.set_operand_count(2);
    int rsp = zydis_register_from_string("rsp");
    req3.set_operand_reg(0, zydis_register_from_string("rax"));
    req3.set_operand_mem(1, rsp, none, 0, 0x20, 8);
    
    array<uint8> bytes3;
    if (zydis_encode(req3, bytes3))
    {
        log("lea rax, [rsp+0x20] (" + bytes3.length() + " bytes): " + bytes_to_hex(bytes3));
        disasm_and_print(bytes3, 0);
    }
}

void test_branch_instructions()
{
    log("=== Testing branch instructions ===");
    
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140001000);
    
    ZydisEncoderRequest jmp_req;
    jmp_req.set_mnemonic(zydis_mnemonic_from_string("jmp"));
    jmp_req.set_operand_count(1);
    jmp_req.set_operand_imm(0, 0x140001020);
    jmp_req.set_branch_type(BRANCH_NEAR);
    jmp_req.set_branch_width(WIDTH_32);
    builder.push(jmp_req);
    
    ZydisEncoderRequest call_req;
    call_req.set_mnemonic(zydis_mnemonic_from_string("call"));
    call_req.set_operand_count(1);
    call_req.set_operand_imm(0, 0x140002000);
    builder.push(call_req);
    
    ZydisEncoderRequest jz_req;
    jz_req.set_mnemonic(zydis_mnemonic_from_string("jz"));
    jz_req.set_operand_count(1);
    jz_req.set_operand_imm(0, 0x140001050);
    builder.push(jz_req);
    
    builder.push_ret();
    
    array<uint8> code;
    if (builder.build(code))
    {
        log("Branch code (" + code.length() + " bytes): " + bytes_to_hex(code));
        disasm_and_print(code, 0x140001000);
    }
}

void test_mixed_shellcode()
{
    log("=== Testing mixed shellcode (instructions + data) ===");
    
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140003000);
    
    ZydisEncoderRequest lea_req;
    lea_req.set_mnemonic(zydis_mnemonic_from_string("lea"));
    lea_req.set_operand_count(2);
    int rip = zydis_register_from_string("rip");
    int none = 0;
    lea_req.set_operand_reg(0, zydis_register_from_string("rcx"));
    lea_req.set_operand_mem(1, rip, none, 0, 0x20, 8);
    builder.push(lea_req);
    
    ZydisEncoderRequest mov_req;
    mov_req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    mov_req.set_operand_count(2);
    mov_req.set_operand_reg(0, zydis_register_from_string("rax"));
    mov_req.set_operand_imm(1, 0x0);
    builder.push(mov_req);
    
    builder.push_ret();
    
    builder.push_nop(5);
    
    builder.push_u64(0x6F6C6C6548);
    builder.push_byte(0x00);
    
    array<uint8> shellcode;
    if (builder.build(shellcode))
    {
        log("Mixed shellcode (" + shellcode.length() + " bytes): " + bytes_to_hex(shellcode));
        log("Disassembly of code portion:");
        disasm_and_print(shellcode, 0x140003000);
    }
}

string bytes_to_hex(const array<uint8> &in bytes)
{
    string result;
    for (uint i = 0; i < bytes.length(); i++)
    {
        if (i > 0) result += " ";
        result += format_hex_byte(bytes[i]);
    }
    return result;
}

string format_hex_byte(uint8 val)
{
    string chars = "0123456789ABCDEF";
    string hex;
    hex += chars[(val >> 4) & 0xF];
    hex += chars[val & 0xF];
    return hex;
}

bool compare_arrays(const array<uint8> &in a, const array<uint8> &in b)
{
    if (a.length() != b.length()) return false;
    for (uint i = 0; i < a.length(); i++)
    {
        if (a[i] != b[i]) return false;
    }
    return true;
}

void disasm_and_print(const array<uint8> &in bytes, uint64 rip)
{
    array<dictionary@> insts;
    zydis_disasm(bytes, rip, insts);
    for (uint i = 0; i < insts.length(); i++)
    {
        string text;
        insts[i].get("text", text);
        int64 addr;
        insts[i].get("runtime_address", addr);
        int64 len;
        insts[i].get("length", len);
        log("  0x" + formatInt(addr, "H") + " [" + len + "]: " + text);
    }
}
```

***

### Examples

### 1) Basic encoding

```cpp
void test_basic_encoding()
{
    ZydisEncoderRequest req;
    req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    req.set_operand_count(2);
    req.set_operand_reg(0, zydis_register_from_string("rax"));
    req.set_operand_imm(1, 0x1234567890ABCDEF);

    array<uint8> bytes;
    if (zydis_encode(req, bytes))
    {
        log("mov rax, imm64: " + bytes_to_hex(bytes));
        disasm_and_print(bytes, 0);
    }
    else
    {
        log_error("Failed to encode mov rax, imm64");
    }
}
```

***

### 2) Building shellcode with `ZydisBuilder`

```cpp
void test_builder_api()
{
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140001000);
    builder.set_machine_mode(MODE_LONG_64);

    ZydisEncoderRequest mov_req;
    mov_req.set_mnemonic(zydis_mnemonic_from_string("mov"));
    mov_req.set_operand_count(2);
    mov_req.set_operand_reg(0, zydis_register_from_string("rax"));
    mov_req.set_operand_imm(1, 0x42);
    builder.push(mov_req);

    builder.push_nop(3);
    builder.push_int3();
    builder.push_ret();

    array<uint8> shellcode;
    if (builder.build(shellcode))
    {
        log("Shellcode: " + bytes_to_hex(shellcode));
        disasm_and_print(shellcode, 0x140001000);
    }
}
```

***

### 3) Mixing instructions + data

```cpp
void test_mixed_shellcode()
{
    ZydisBuilder@ builder = ZydisBuilder();
    builder.set_base_address(0x140003000);
    builder.set_machine_mode(MODE_LONG_64);

    ZydisEncoderRequest lea_req;
    lea_req.set_mnemonic(zydis_mnemonic_from_string("lea"));
    lea_req.set_operand_count(2);
    lea_req.set_operand_reg(0, zydis_register_from_string("rcx"));
    lea_req.set_operand_mem(1, zydis_register_from_string("rip"), 0, 0, 0x20, 8);
    builder.push(lea_req);

    builder.push_ret();

    builder.push_nop(5);
    builder.push_u64(0x6F6C6C6548); // "Hello" (little endian-ish)
    builder.push_byte(0x00);

    array<uint8> blob;
    if (builder.build(blob))
    {
        log("Mixed blob: " + bytes_to_hex(blob));
        disasm_and_print(blob, 0x140003000);
    }
}
```

***

### 4) Decode → Request → Re-encode

```cpp
void test_decode_to_request()
{
    array<uint8> original = {0x48, 0x89, 0xC3}; // mov rbx, rax (example)

    ZydisEncoderRequest req;
    if (zydis_decoded_to_request(original, 0x140001000, req))
    {
        log("Decoded: " + zydis_mnemonic_to_string(req.get_mnemonic()));

        array<uint8> reencoded;
        if (zydis_encode(req, reencoded))
        {
            log("Original:   " + bytes_to_hex(original));
            log("Re-encoded: " + bytes_to_hex(reencoded));
        }
    }
}
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/zydis-encoder.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.

---

## Source: `docs/angelscript-lang/INDEX.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/ (Doxygen, AngelScript 2.38.0)
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# AngelScript core language reference

This directory holds a curated scrape of the **core AngelScript language reference** from the
official manual at <https://www.angelcode.com/angelscript/sdk/docs/manual/> (Doxygen, version
2.38.0). It documents the AngelScript scripting language itself — data types, expressions,
statements, functions, classes, handles, inheritance, funcdefs/delegates, enums, namespaces,
co-routines, and the standard script add-ons (string, array, dictionary, math). It is **not**
the PCX Perception.cx AngelScript API bindings, which live separately under
`docs/perception/angelscript/`.

AngelScript is licensed under the zlib/libpng license (see `license.md`). All pages here are
reproduced under that license with attribution to Andreas Jönsson / AngelCode. Each `.md` file
carries a provenance + license header identifying its source URL and fetch date.

## Files

| File | Source page | Topic |
| --- | --- | --- |
| `overview.md` | [doc_overview.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_overview.html) | AngelScript overview (engine, modules, contexts, language, memory) |
| `license.md` | [doc_license.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_license.html) | zlib/libpng license text |
| `datatypes.md` | [doc_datatypes.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes.html) | Data types (index of primitives, objects, handles, strings, auto) |
| `strings.md` | [doc_strings.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_strings.html) | Custom string type (registration, Unicode/ASCII, multiline/char literals) |
| `arrays.md` | [doc_arrays.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_arrays.html) | Custom array type (template types, specializations) |
| `dictionary.md` | [doc_datatypes_dictionary.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_dictionary.html) | dictionary type (script-side usage, operators, methods) |
| `expressions.md` | [doc_expressions.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html) | Expressions (assignment, math, logic, comparison, casts, anonymous objects) |
| `statements.md` | [doc_script_statements.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_statements.html) | Statements (if/switch, loops, foreach, break/continue, return, try-catch) |
| `functions.md` | [doc_script_func.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func.html) | Functions (declaration, parameter/return refs, overloading, defaults, anon) |
| `variables.md` | [doc_global_variable.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_variable.html) | Global variables (init order, lifetime) |
| `script-class.md` | [doc_script_class.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class.html) | Script classes (index: constructors, methods, inheritance, ops, accessors) |
| `script-class-props.md` | [doc_script_class_prop.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_prop.html) | Property accessors (virtual + indexed) |
| `inheritance.md` | [doc_script_class_inheritance.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_inheritance.html) | Inheritance and polymorphism (super, final, abstract, override, casts) |
| `handles.md` | [doc_script_handle.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_handle.html) | Object handles (usage, lifetimes, polymorphing, const handles) |
| `generics.md` | [doc_generic.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_generic.html) | The generic calling convention (embedding; template types are the script-side "generics") |
| `funcdef.md` | [doc_global_funcdef.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_funcdef.html) | Funcdefs (function signature definitions) |
| `delegate.md` | [doc_datatypes_funcptr.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_funcptr.html) | Function handles and delegates |
| `enums.md` | [doc_global_enums.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_enums.html) | Enums (named integer constants) |
| `namespaces.md` | [doc_global_namespace.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_namespace.html) | Namespaces and `using namespace` |
| `coroutines.md` | [doc_adv_coroutine.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_coroutine.html) | Co-routines (embedding-side; no standalone script coroutine page exists) |
| `addons-overview.md` | [doc_addon.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon.html) | Add-ons overview and script extensions index |
| `addon-strings.md` | [doc_addon_std_string.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html) | std::string add-on (scriptstdstring) |
| `addon-array.md` | [doc_addon_array.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_array.html) | array template object add-on (scriptarray) |
| `addon-dictionary.md` | [doc_addon_dict.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_dict.html) | dictionary object add-on (scriptdictionary) |
| `addon-math.md` | [doc_addon_math.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_math.html) | math functions add-on (scriptmath, complex type) |

## Requested filenames that do not exist on the server

The task brief named several pages whose exact URLs return HTTP 404 on the manual server. For
each, the table above used the real manual page covering the same topic:

| Requested (404) | Real page used |
| --- | --- |
| `doc_statements.html` | `doc_script_statements.html` |
| `doc_functions.html` | `doc_script_func.html` |
| `doc_variables.html` | `doc_global_variable.html` |
| `doc_inheritance.html` | `doc_script_class_inheritance.html` |
| `doc_handle.html` | `doc_script_handle.html` |
| `doc_funcdef.html` | `doc_global_funcdef.html` |
| `doc_delegate.html` | `doc_datatypes_funcptr.html` (covers delegates) |
| `doc_enum.html` | `doc_global_enums.html` |
| `doc_namespace.html` | `doc_global_namespace.html` |
| `doc_coroutine.html` | `doc_adv_coroutine.html` (embedding-side; no script coroutine page) |
| `doc_dictionary.html` | `doc_datatypes_dictionary.html` |
| `doc_addon_1.html` | `doc_addon.html` |
| `doc_addon_strings.html` | `doc_addon_std_string.html` |

## Not included (deferred)

The following manual pages were intentionally **not** scraped. They are either C++ embedding /
engine-registration material (out of scope for a script-writer language reference) or remaining
add-on / sample / good-practice pages. A future contributor can fetch them to extend coverage.

### C++ embedding / registration (engine-side, not the script language)

- [doc_register_api.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_api.html) — registering the API
- [doc_register_func.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_func.html)
- [doc_register_prop.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_prop.html)
- [doc_register_type.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_type.html)
- [doc_register_obj.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_obj.html)
- [doc_register_global.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_global.html)
- [doc_callbacks.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_callbacks.html)
- [doc_exceptions.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_exceptions.html)
- [doc_adv_*](https://www.angelcode.com/angelscript/sdk/docs/manual/) — all `doc_advanced_*` / `doc_adv_*` embedding pages (templates, access masks, concurrent scripts, custom options, etc.)
- [doc_module.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_module.html)
- [doc_call_script_func.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_call_script_func.html)
- [doc_debug.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_debug.html)
- [doc_memory.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_memory.html)
- [doc_gc.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_gc.html)

### Remaining script-side / reference pages not scraped

- [doc_datatypes_primitives.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_primitives.html) — primitives
- [doc_datatypes_obj.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_obj.html) — objects and handles
- [doc_datatypes_strings.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_strings.html) — string literals / heredoc
- [doc_datatypes_arrays.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_arrays.html) — array script usage
- [doc_datatypes_auto.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_auto.html) — auto declarations
- [doc_script_class_desc.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_desc.html), [doc_script_class_construct.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_construct.html), [doc_script_class_memberinit.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_memberinit.html), [doc_script_class_destruct.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_destruct.html), [doc_script_class_methods.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_methods.html), [doc_script_class_private.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_private.html), [doc_script_class_ops.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_ops.html) — class sub-topics
- [doc_script_func_decl.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_decl.html), [doc_script_func_ref.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_ref.html), [doc_script_func_retref.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_retref.html), [doc_script_func_overload.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_overload.html), [doc_script_func_defarg.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_defarg.html), [doc_script_anonfunc.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_anonfunc.html) — function sub-topics
- [doc_global_func.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_func.html), [doc_global_virtprop.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_virtprop.html), [doc_global_class.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_class.html), [doc_global_interface.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_interface.html), [doc_script_mixin.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_mixin.html), [doc_global_typedef.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_typedef.html), [doc_global_import.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_import.html)
- [doc_script_shared.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_shared.html) — shared script entities
- [doc_operator_precedence.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_operator_precedence.html) — operator precedence
- [doc_reserved_keywords.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_reserved_keywords.html) — reserved keywords/tokens
- [doc_script_bnf.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_bnf.html) — script language grammar
- [doc_script_stdlib.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_stdlib.html) — standard library index
- [doc_good_practice.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_good_practice.html) — good practices
- [doc_samples.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_samples.html) and [doc_samples_corout.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_samples_corout.html) — samples

### Remaining add-on pages not scraped

- [doc_addon_application.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_application.html) — application module add-ons
- [doc_addon_any.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_any.html) — any object
- [doc_addon_handle.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_handle.html) — ref object
- [doc_addon_weakref.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_weakref.html) — weakref object
- [doc_addon_file.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_file.html) — file object
- [doc_addon_filesystem.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_filesystem.html) — filesystem object
- [doc_addon_grid.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_grid.html) — grid template object
- [doc_addon_datetime.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_datetime.html) — datetime object
- [doc_addon_socket.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_socket.html) — socket object
- [doc_addon_helpers_try.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_helpers_try.html) — exception routines
- [doc_addon_ctxmgr.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_ctxmgr.html) — context manager (default co-routine impl)
- [doc_addon_autowrap.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_autowrap.html) — automatic wrapper functions

---

## Source: `docs/angelscript-lang/addon-array.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_array.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# array template object

**Path:** /sdk/add_on/scriptarray/

The `array` type is a [template object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_template.html) that allow the scripts to declare arrays of any type. Since it is a generic class it is not the most performatic due to the need to determine characteristics at runtime. For that reason it is recommended that the application registers a [template specialization](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_template.html#doc_adv_template_2) for the array types that are most commonly used.

The type is registered with `RegisterScriptArray(asIScriptEngine *engine, bool defaultArrayType)`. The second parameter should be set to true if you wish to allow the syntax form `type[]` to declare arrays.

Compile the add-on with the pre-processor define `AS_USE_STLNAMES=1` to register the methods with the same names as used by C++ STL where the methods have the same significance. Not all methods from STL is implemented in the add-on, but many of the most frequent once are so a port from script to C++ and vice versa might be easier if STL names are used.

Compile the add-on with the pre-processor define `AS_USE_ACCESSORS=1` to register `length` as a virtual property instead of the method `length()`.

Compile the add-on with the pre-processor define `AS_NO_IMPL_OPS_WITH_STRING_AND_PRIMITIVE=1` to disable the implicit operations with primitives that automatically formats the primitive values to strings.

## Public C++ interface

```cpp
class CScriptArray
{
public:
  // Set the memory functions that should be used by all CScriptArrays
  static void SetMemoryFunctions(asALLOCFUNC_t allocFunc, asFREEFUNC_t freeFunc);

  // Factory functions
  static CScriptArray *Create(asITypeInfo *arrayType);
  static CScriptArray *Create(asITypeInfo *arrayType, asUINT length);
  static CScriptArray *Create(asITypeInfo *arrayType, asUINT length, void *defaultValue);
  static CScriptArray *Create(asITypeInfo *arrayType, void *listBuffer);

  // Memory management
  void AddRef() const;
  void Release() const;

  // Type information
  asITypeInfo *GetArrayObjectType() const;
  int GetArrayTypeId() const;
  int GetElementTypeId() const;

  // Get the current size
  asUINT GetSize() const;

  // Returns true if the array is empty
  bool IsEmpty() const;

  // Pre-allocates memory for elements
  void Reserve(asUINT numElements);

  // Resize the array
  void Resize(asUINT numElements);

  // Get a pointer to an element. Returns 0 if out of bounds
  void *At(asUINT index);
  const void *At(asUINT index) const;

  // Set value of an element.
  // The value arg should be a pointer to the value that will be copied to the element.
  // Remember, if the array holds handles the value parameter should be the
  // address of the handle. The refCount of the object will also be incremented
  void SetValue(asUINT index, void *value);

  // Copy the contents of one array to another (only if the types are the same)
  CScriptArray &operator=(const CScriptArray&);

  // Compare two arrays
  bool operator==(const CScriptArray &) const;

  // Array manipulation
  void InsertAt(asUINT index, void *value);
  void RemoveAt(asUINT index);
  void InsertLast(void *value);
  void RemoveLast();

  void SortAsc();
  void SortAsc(asUINT startAt, asUINT count);
  void SortDesc();
  void SortDesc(asUINT startAt, asUINT count);
  void Sort(asUINT startAt, asUINT count, bool asc);
  void Sort(asIScriptFunction *less, asUINT startAt, asUINT count);
  void Reverse();

  int Find(void *value) const;
  int Find(asUINT startAt, void *value) const;
  int FindByRef(void *ref) const;
  int FindByRef(asUINT startAt, void *ref) const;

  // Returns the address of the inner buffer for direct manipulation
  void *GetBuffer();
};
```

## Public script interface

See also: [Arrays in the script language](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_arrays.html)

## C++ example

This function shows how a script array can be instantiated from the application and then passed to the script.

```cpp
// Registered with AngelScript as 'array<string> @CreateArrayOfString()'
CScriptArray *CreateArrayOfStrings()
{
  // If called from the script, there will always be an active
  // context, which can be used to obtain a pointer to the engine.
  asIScriptContext *ctx = asGetActiveContext();
  if( ctx )
  {
    asIScriptEngine* engine = ctx->GetEngine();

    // The script array needs to know its type to properly handle the elements.
    // Note that the object type should be cached to avoid performance issues
    // if the function is called frequently.
    asITypeInfo* t = engine->GetTypeInfoByDecl("array<string>");

    // Create an array with the initial size of 3 elements
    CScriptArray* arr = CScriptArray::Create(t, 3);

    for( asUINT i = 0; i < arr->GetSize(); i++ )
    {
      // Set the value of each element
      string val("test");
      arr->SetValue(i, &val);
    }

    // The ref count for the returned handle was already set in the array's constructor
    return arr;
  }
  return 0;
}
```

---

## Source: `docs/angelscript-lang/addon-dictionary.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_dict.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# dictionary object

**Path:** /sdk/add_on/scriptdictionary/

The dictionary object maps string values to values or objects of other types.

Register with `RegisterScriptDictionary(asIScriptEngine*)`.

Compile the add-on with the pre-processor define `AS_USE_STLNAMES=1` to register the methods with the same names as used by C++ STL where the methods have the same significance. Not all methods from STL is implemented in the add-on, but many of the most frequent once are so a port from script to C++ and vice versa might be easier if STL names are used.

## Public C++ interface

```cpp
typedef std::string dictKey;

class CScriptDictionary
{
public:
  // Factory functions
  static CScriptDictionary *Create(asIScriptEngine *engine);

  // Reference counting
  void AddRef() const;
  void Release() const;

  // Perform a shallow copy of the other dictionary
  CScriptDictionary &operator=(const CScriptDictionary &other);

  // Sets a key/value pair
  void Set(const dictKey &key, void *value, int typeId);
  void Set(const dictKey &key, asINT64 &value);
  void Set(const dictKey &key, double &value);

  // Gets the stored value. Returns false if the value isn't compatible with informed type
  bool Get(const dictKey &key, void *value, int typeId) const;
  bool Get(const dictKey &key, asINT64 &value) const;
  bool Get(const dictKey &key, double &value) const;

  // Index accessors. If the dictionary is not const it inserts the value if it doesn't already exist.
  // If the dictionary is const then a script exception is set if it doesn't exist and a null pointer is returned
  CScriptDictValue *operator[](const dictKey &key);
  const CScriptDictValue *operator[](const dictKey &key) const;

  // Returns the type id of the stored value, or negative if it doesn't exist
  int GetTypeId(const dictKey &key) const;

  // Returns true if the key is set
  bool Exists(const dictKey &key) const;

  // Returns true if the dictionary is empty
  bool IsEmpty() const;

  // Returns the number of keys in the dictionary
  asUINT GetSize() const;

  // Deletes the key
  bool Delete(const dictKey &key);

  // Deletes all keys
  void DeleteAll();

  // Get an array of all keys
  CScriptArray *GetKeys() const;

  // STL style iterator
  class CIterator
  {
  public:
    void operator++();    // Pre-increment
    void operator++(int);  // Post-increment
    bool operator==(const CIterator &other) const;
    bool operator!=(const CIterator &other) const;

    // Accessors
    const dictKey &GetKey() const;
    int GetTypeId() const;
    bool GetValue(asINT64 &value) const;
    bool GetValue(double &value) const;
    bool GetValue(void *value, int typeId) const;
    const void * GetAddressOfValue() const;
  };

  CIterator begin() const;
  CIterator end() const;
  CIterator find(const dictKey &key) const;
};
```

## Public script interface

See also: [Dictionaries in the script language](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_dictionary.html)

## Example usage from C++

Here's a skeleton for iterating over the entries in the dictionary. For brevity the code doesn't show how to interpret the values, for more information on that see `asETypeIdFlags` and `asIScriptEngine::GetTypeInfoById`.

```cpp
void iterateDictionary(CScriptDictionary *dict)
{
  // Iterate over each entry
  for (auto it : *dict)
  {
    // Determine the name of the key
    std::string keyName = it.GetKey();
    cout << "\"" << keyName << "\"" << " = ";

    // Get the type and address of the value
    int typeId = it.GetTypeId();
    const void *addressOfValue = it.GetAddressOfValue();

    // Cast the value to the correct C++ type according to the typeId and then print it
    ...
  }
}
```

---

## Source: `docs/angelscript-lang/addon-math.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_math.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# math functions

**Path:** /sdk/add_on/scriptmath/

This add-on registers the math functions from the standard C runtime library with the script engine. Use `RegisterScriptMath(asIScriptEngine*)` to perform the registration.

By defining the preprocessor word `AS_USE_FLOAT=0`, the functions will be registered to take and return doubles instead of floats.

The function `RegisterScriptMathComplex(asIScriptEngine*)` registers a type that represents a complex number, i.e. a number with real and imaginary parts.

## Public script interface

```angelscript
// Trigonometric functions
float cos(float rad);
float sin(float rad);
float tan(float rad);

// Inverse trigonometric functions
float acos(float val);
float asin(float val);
float atan(float val);
float atan2(float y, float x);

// Hyperbolic functions
float cosh(float rad);
float sinh(float rad);
float tanh(float rad);

// Logarithmic functions
float log(float val);
float log10(float val);

// Power to
float pow(float val, float exp);

// Square root
float sqrt(float val);

// Absolute value
float abs(float val);

// Ceil and floor functions
float ceil(float val);
float floor(float val);

// Returns the fraction
float fraction(float val);

// Approximate float comparison, to deal with numeric imprecision
bool closeTo(float a, float b, float epsilon = 0.00001f);
bool closeTo(double a, double b, double epsilon = 0.0000000001);

// Conversion between floating point and IEEE 754 representations
float  fpFromIEEE(uint raw);
double fpFromIEEE(uint64 raw);
uint   fpToIEEE(float fp);
uint64 fpToIEEE(double fp);
```

### Functions

**cos, sin, tan**
Calculates the trigonometric functions cosine, sine, and tangent. The input angle should be given in radian.

**acos, asin, atan**
Calculates the inverse of the trigonometric functions cosine, sine, and tangent. The returned angle is given in radian.

**atan2**
Calculates the inverse of the trigonometric function tangent. The input is the y and x proportions. The returned angle is given in radian.

**cosh, sinh, tanh**
Calculates the hyperbolic of the cosine, sine, and tangent. The input angle should be given in radian.

**log, log10**
Calculates the logarithm of the input value. log is the natural logarithm and log10 is the base-10 logarithm.

**pow**
Calculates the based raised to the power of exponent.

**sqrt**
Calculates the square root of the value.

**abs**
Returns the absolute value.

**ceil, floor**
ceil returns the closest integer number that is higher or equal to the input. Floor returns the closest integer number that is lower or equal to the input.

**fraction**
Returns the fraction of the number, i.e. what remains after taking away the integral number.

**closeTo**
Due to numerical errors with the binary representation of real numbers it is often difficult to do direct comparisons of two float values. The closeTo function will return true of the two values are almost equal, allowing for a small difference up to the size of the epsilon value.

**fpFromIEEE, fpToIEEE**
Translates the float to and from IEEE 754 representation. This can be used if one wishes to directly inspect or manipulate the floating point value in the binary representation.

### The complex type

```angelscript
// This type represents a complex number with real and imaginary parts
class complex
{
  // Constructors
  complex();
  complex(const complex &in);
  complex(float r);
  complex(float r, float i);

  // Equality operator
  bool opEquals(const complex &in) const;

  // Compound assignment operators
  complex &opAddAssign(const complex &in);
  complex &opSubAssign(const complex &in);
  complex &opMulAssign(const complex &in);
  complex &opDivAssign(const complex &in);

  // Math operators
  complex opAdd(const complex &in) const;
  complex opSub(const complex &in) const;
  complex opMul(const complex &in) const;
  complex opDiv(const complex &in) const;

  // Returns the absolute value (magnitude)
  float abs() const;

  // Swizzle operators
  complex get_ri() const;
  void set_ri(const complex &in);
  complex get_ir() const;
  void set_ir(const complex &in);

  // The real and imaginary parts
  float r;
  float i;
}
```

**complex**
The constructors allow for implicit construction, making a copy, implicit conversion from float, and explicit initialization from two float values.

**=, !=**
Compares two complex values.

**=, +=, -=, \*=, /=**
Assign and compound assignment of complex values.

**+, -, \*, /**
Math operators on complex values.

**abs**
Returns the absolute (magnitude) of the complex value.

**r, i**
Retrieves the real and imaginary part of the complex value.

**ri, ir**
Swizzle operators return a complex value with the ordering of the real and imaginary parts as indicated by the name.

---

## Source: `docs/angelscript-lang/addon-strings.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# string object

**Path:** /sdk/add_on/scriptstdstring/

This add-on registers the `std::string` type as-is with AngelScript. This gives perfect compatibility with C++ functions that use `std::string` in parameters or as return type.

A potential drawback is that the `std::string` type is a value type, thus may increase the number of copies taken when string values are being passed around in the script code. However, this is most likely only a problem for scripts that perform a lot of string operations.

Register the type with `RegisterStdString(asIScriptEngine*)`. Register the optional split method and global join function with `RegisterStdStringUtils(asIScriptEngine*)`. The optional functions require that the [array template object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_array.html) has been registered first.

Compile the add-on with the pre-processor define `AS_USE_STLNAMES=1` to register the methods with the same names as used by C++ STL where the methods have the same significance. Not all methods from STL is implemented in the add-on, but many of the most frequent ones are so a port from script to C++ and vice versa might be easier if STL names are used.

Compile the add-on with the pre-processor define `AS_USE_ACCESSORS=1` to register `length` as a virtual property instead of the method `length()`.

## Public C++ interface

Refer to the `std::string` implementation for your compiler.

## Public script interface

See also: [Strings in the script language](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_stdlib_string.html)

---

## Source: `docs/angelscript-lang/addons-overview.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Add-ons

This page gives a brief description of the add-ons that you'll find in the /sdk/add_on/ folder.

- [Application modules](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_application.html)
- [Script extensions](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_script.html)

## Script extensions

The script extensions add-ons provide types and functions usable directly from scripts:

- [string object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html) — see `addon-strings.md`
- [array template object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_array.html) — see `addon-array.md`
- [any object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_any.html)
- [ref object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_handle.html)
- [weakref object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_weakref.html)
- [dictionary object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_dict.html) — see `addon-dictionary.md`
- [file object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_file.html)
- [filesystem object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_filesystem.html)
- [math functions](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_math.html) — see `addon-math.md`
- [grid template object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_grid.html)
- [datetime object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_datetime.html)
- [socket object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_socket.html)
- [Exception routines](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_helpers_try.html)

---

## Source: `docs/angelscript-lang/arrays.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_arrays.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Custom array type

Like the [string type](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_strings.html), AngelScript doesn't have a built-in dynamic array type. Instead the application developers that wishes to allow dynamic arrays in the scripts should register this in the way that is best suited for the application. To save time a readily usable add-on is provided with a fully implemented [dynamic array type](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_array.html).

If you wish to create your own array type, you'll need to understand how [template types](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_template.html) work. A template type is a special form of registering a type that the engine can then use to instanciate the true types based on the desired sub-types. This allow a single type registration to cover all possible array types that the script may need, instead of the application having to register a specific type for each type of array.

Of course, a generic type like this will have a drawback in performance due to runtime checks to determine the actual type, so the application should consider registering [template specializations](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_template.html#doc_adv_template_2) of the most common array types. This will allow the best optimizations for those types, and will also permit better interaction with the application as the template specialization can better match the actual array types that the application uses.

---

## Source: `docs/angelscript-lang/coroutines.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_coroutine.html
     Fetched: 2026-06-20
     Note: The requested page doc_coroutine.html does not exist on the server (HTTP 404).
           AngelScript has no standalone script-side coroutine page; the manual covers
           co-routines on the embedding/advanced page doc_adv_coroutine.html, reproduced here.
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Co-routines

> **Note**
> Co-routines are an application-embedding feature, not a built-in script construct. This page describes how the host application implements co-routines; the [Context manager](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_ctxmgr.html) add-on provides a ready-made implementation.

Co-routines is a way to allow multiple execution paths in parallel, but without the hazards of pre-emptive scheduling in [multithreading](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_concurrent.html) where one thread can be suspended at any moment so another can resume. Because co-routines always voluntarily suspend themselves in favor of the next co-routine, there is no need to worry about atomic instructions and critical sections.

Co-routines are not natively built-into the AngelScript library, but it can easily be implemented from the application side. In fact, the [Context manager](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_ctxmgr.html) add-on already provides a default implementation for this.

To implement your own version of co-routines you will need a couple of pieces:

- The co-routine itself, which is just an instance of the `asIScriptContext` object. Each co-routine will have its own context object that holds the callstack of the co-routine.
- A function that will permit the script to create, or spawn, new co-routines. This function will need to be able to refer to starting function of the new co-routine. This reference can be done by name, or perhaps more elegantly with a [function pointer](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_funcptr.html). Once invoked this function will instanciate the new context, and prepare it with the starting function.
- A function that will permit a co-routine to yield control to the next co-routine. This function will simply suspend the current context so the next co-routine can be resumed.
- A simple control algorithm for the co-routines. This can just be a loop that will iterate over an array of co-routines, i.e. contexts, until all of them have finished executing. When a new co-routine is created it is simply appended to the array to be picked up when the current co-routine yields the control.

A simple implementation of the function that spawns a new co-routine may look like this:

```cpp
void CreateCoRoutine(string &func)
{
  asIScriptContext *ctx = asGetActiveContext();
  if( ctx )
  {
    asIScriptEngine *engine = ctx->GetEngine();
    string mod = ctx->GetFunction()->GetModuleName();

    // We need to find the function that will be created as the co-routine
    string decl = "void " + func + "()";
    asIScriptFunction *funcPtr = engine->GetModule(mod.c_str())->GetFunctionByDecl(decl.c_str());
    if( funcPtr == 0 )
    {
      // No function could be found, raise an exception
      ctx->SetException(("Function '" + decl + "' doesn't exist").c_str());
      return;
    }

    // Create a new context for the co-routine
    asIScriptContext *coctx = engine->CreateContext();
    coctx->Prepare(funcPtr);

    // Add the new co-routine context to the array of co-routines
    coroutines.push_back(coctx);
  }
}
```

The yield function is even simpler:

```cpp
void Yield()
{
  asIScriptContext *ctx = asGetActiveContext();
  if( ctx )
  {
    // Suspend the context so the next co-routine can be resumed
    ctx->Suspend();
  }
}
```

A basic control algorithm might look like this:

```cpp
std::vector<asIScriptContext *> coroutines;

void Execute()
{
  int n = 0;
  while( coroutines.size() > 0 )
  {
    // Resume the co-routine
    int r = coroutines[n]->Execute();
    if( r == asEXECUTION_SUSPENDED )
    {
      // Resume the next co-routine
      if( ++n == coroutines.size() )
        n = 0;
    }
    else
    {
      // The co-routine finished so let's remove it
      coroutines[n]->Release();
      coroutines.erase(n);
    }
  }
}
```

See also: [Context manager](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_ctxmgr.html), [Co-routines sample](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_samples_corout.html), [Concurrent scripts](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_concurrent.html)

---

## Source: `docs/angelscript-lang/datatypes.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Data types

Note that the host application may add types specific to that application, refer to the application's manual for more information.

- [Primitives](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_primitives.html)
- [Objects and handles](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_obj.html)
- [Function handles](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_funcptr.html)
- [Strings](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_strings.html)
- [Auto declarations](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_auto.html)

See also: [Standard library](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_stdlib.html)

---

## Source: `docs/angelscript-lang/delegate.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_funcptr.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Function handles and delegates

A function handle is a data type that can be dynamically set to point to a global function that has a matching function signature as that defined by the variable declaration. Function handles are commonly used for callbacks, i.e. where a piece of code must be able to call back to some code based on some conditions, but the code that needs to be called is not known at compile time.

To use function handles it is first necessary to [define the function signature](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_funcdef.html) that will be used at the global scope or as a member of a class. Once that is done the variables can be declared using that definition.

Here's an example that shows the syntax for using function handles

```angelscript
// Define a function signature for the function handle
funcdef bool CALLBACK(int, int);

// An example function that shows how to use this
void main()
{
  // Declare a function handle, and set it
  // to point to the myCompare function.
  CALLBACK @func = @myCompare;

  // The function handle can be compared with the 'is' operator
  if( func is null )
  {
    print("The function handle is null\n");
    return;
  }

  // Call the function through the handle, just as if it was a normal function
  if( func(1, 2) )
  {
    print("The function returned true\n");
  }
  else
  {
    print("The function returned false\n");
  }
}

// This function matches the CALLBACK definition, since it has
// the same return type and parameter types.
bool myCompare(int a, int b)
{
  return a > b;
}
```

## Delegates

It is also possible to take function handles to class methods, but in this case the class method must be bound to the object instance that will be used for the call. To do this binding is called creating a delegate, and is done by performing a construct call for the declared function definition passing the class method as the argument.

```angelscript
class A
{
  bool Cmp(int a, int b)
  {
     count++;
     return a > b;
  }
  int count = 0;
}

void main()
{
  A a;

  // Create the delegate for the A::Cmp class method
  CALLBACK @func = CALLBACK(a.Cmp);

  // Call the delegate normally as if it was a global function
  if( func(1,2) )
  {
    print("The function returned true\n");
  }
  else
  {
    print("The function returned false\n");
  }

  printf("The number of comparisons performed is "+a.count+"\n");
}
```

---

## Source: `docs/angelscript-lang/dictionary.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_dictionary.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# dictionary

> **Note**
> Dictionaries are only available in the scripts if the application [registers the support for them](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_dict.html). The syntax for using dictionaries may differ for the application you're working with so consult the application's manual for more details.

The dictionary stores key-value pairs, where the key is a string, and the value can be of any type. Key-value pairs can be added or removed dynamically, making the dictionary a good general purpose container object.

```angelscript
obj object;
obj @handle;

// Initialize with a list
dictionary dict = {{'one', 1}, {'object', object}, {'handle', @handle}};

// Examine and access the values through get or set methods ...
if( dict.exists('one') )
{
  // get returns true if the stored type is compatible with the requested type
  bool isValid = dict.get('handle', @handle);
  if( isValid )
  {
    dict.delete('object');
    dict.set('value', 1);
  }
}
```

Dictionary values can also be accessed or added by using the index operator.

```angelscript
// Read and modify an integer value
int val = int(dict['value']);
dict['value'] = val + 1;

// Read and modify a handle to an object instance
@handle = cast<obj>(dict['handle']);
if( handle is null )
  @dict['handle'] = object;
```

Dictionaries can also be created and initialized within expressions as [anonymous objects](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html#anonobj).

```angelscript
// Call a function that expects a dictionary as input and no other overloads
// In this case it is possible to inform the initialization list without explicitly giving the type
foo({{'a', 1},{'b', 2}});

// Call a function where there are multiple overloads expecting different
// In this case it is necessary to explicitly define the type of the initialization list
foo2(dictionary = {{'a', 1},{'b', 2}});
```

Dictionaries of dictionaries are created using [anonymous objects](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html#anonobj) as well.

```angelscript
dictionary d2 = {{'a', dictionary = {{'aa', 1}, {'ab', 2}}},
                 {'b', dictionary = {{'ba', 1}, {'bb', 2}}}};
```

The dictionary object supports [foreach loops](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_statements.html#while) to easily iterate over all contained elements.

```angelscript
dictionary dict = {{'a',1},{'b',2},{'c',3}};
int sum = 0;

// sum the values and clear the entries
foreach( auto value, auto key : dict ) // The key variable can be omitted if not needed
{
  sum += int(value);
  dict[key] = 0; // use the key to modify the current element in the dictionary
}
```

## Supporting dictionary object

The dictionary object is a [reference type](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_obj.html), so it's possible to use handles to the dictionary object when passing it around to avoid costly copies.

### Operators

**= assignment**
The assignment operator performs a shallow copy of the content.

**[] index operator**
The index operator takes a string for the key, and returns a reference to the [value](#supporting-dictionaryvalue-object). If the key/value pair doesn't exist it will be inserted with a null value.

### Methods

**`void set(const string &in key, ? &in value)`**
**`void set(const string &in key, int64 &in value)`**
**`void set(const string &in key, double &in value)`**
Sets a key/value pair in the dictionary. If the key already exists, the value will be changed.

**`bool get(const string &in key, ? &out value) const`**
**`bool get(const string &in key, int64 &out value) const`**
**`bool get(const string &in key, double &out value) const`**
Retrieves the value corresponding to the key. The methods return false if the key is not found, and in this case the value will maintain its default value based on the type.

**`array<string> @getKeys() const`**
This method returns an array with all of the existing keys in the dictionary. The order of the keys in the array is undefined.

**`bool exists(const string &in key) const`**
Returns true if the key exists in the dictionary.

**`bool delete(const string &in key)`**
Removes the key and the corresponding value from the dictionary. Returns false if the key wasn't found.

**`void deleteAll()`**
Removes all entries in the dictionary.

**`bool isEmpty() const`**
Returns true if the dictionary doesn't hold any entries.

**`uint getSize() const`**
Returns the number of keys in the dictionary.

## Supporting dictionaryValue object

The dictionaryValue type is how the [dictionary](#supporting-dictionary-object) object stores the values. When accessing the values through the dictionary index operator a reference to a dictionaryValue is returned.

The dictionaryValue type itself is a value type, i.e. no handles to it can be held, but it can hold handles to other objects as well as values of any type.

### Operators

**= assignment**
The value assignment operator should be used to copy a value into the dictionaryValue.

**@= handle assignment**
The handle assignment operator should be used to set the dictionaryValue to refer to an object instance.

**cast\<type\> cast operator**
The cast operator is used to dynamically cast the handle held in the dictionaryValue to the desired type. If the dictionaryValue doesn't hold a handle, or the handle is not compatible with the desired type, the cast operator will return a null handle.

**type() conversion operator**
The conversion operator is used to return a new value of the desired type. If no value conversion is found, an uninitialized value of the desired type is returned.

---

## Source: `docs/angelscript-lang/enums.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_enums.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Enums

Enums are a convenient way of registering a family of integer constants that may be used throughout the script as named literals instead of numeric constants. Using enums often help improve the readability of the code, as the named literal normally explains what the intention is without the reader having to look up what a numeric value means in the manual.

Even though enums list the valid values, you cannot rely on a variable of the enum type to only contain values from the declared list. Always have a default action in case the variable holds an unexpected value.

The enum values are declared by listing them in an enum statement. Unless a specific value is given for an enum constant it will take the value of the previous constant + 1. The first constant will receive the value 0, unless otherwise specified.

```angelscript
enum MyEnum
{
  eValue0,
  eValue2 = 2,
  eValue3,
  eValue200 = eValue2 * 100
}
```

---

## Source: `docs/angelscript-lang/expressions.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Expressions

- [Assignments](#assignments)
- [Function call](#function-call)
- [Math operators](#math-operators)
- [Bitwise operators](#bitwise-operators)
- [Compound assignments](#compound-assignments)
- [Logic operators](#logic-operators)
- [Equality comparison operators](#equality-comparison-operators)
- [Relational comparison operators](#relational-comparison-operators)
- [Identity comparison operators](#identity-comparison-operators)
- [Increment operators](#increment-operators)
- [Indexing operator](#indexing-operator)
- [Conditional expression](#conditional-expression)
- [Member access](#member-access)
- [Handle-of](#handle-of)
- [Parenthesis](#parenthesis)
- [Scope resolution](#scope-resolution)
- [Type conversions](#type-conversions)
- [Anonymous objects](#anonymous-objects)

## Assignments

```angelscript
lvalue = rvalue;
```

`lvalue` must be an expression that evaluates to a memory location where the expression value can be stored, e.g. a variable. An assignment evaluates to the same value and type of the data stored. The right hand expression is always computed before the left.

## Function call

```angelscript
func();
func(arg);
func(arg1, arg2);
lvalue = func();
```

Functions are called to perform an action, and possibly return a value that can be used in further operations. If a function takes more than one argument, the argument expressions are evaluated in the reverse order, i.e. the last argument is evaluated first.

Some functions are declared with output reference parameters to return multiple values. When calling such functions the output parameter must be given as an expression that can be assigned with the returned value. If the additional output value won't be used use the special argument 'void' to tell the compiler that.

```angelscript
// This function returns a value in the output parameter
void func(int &out outputValue)
{
  outputValue = 42;
}

// Call the function with a valid lvalue expression to receive the output value
int value;
func(value);

// Call the function with 'void' argument to ignore the output value
func(void);
```

Arguments can also be named and passed to a specific argument independent of the order the parameters were declared in. No positional arguments may follow any named arguments.

```angelscript
void func(int flagA = false, int flagB = false, int flagC = false) {}

// Call the function, setting only a subset of its parameters
func(flagC: true);
func(flagB: true, flagA: true);
```

For function templates it is necessary to explicitly inform the subtypes so the compiler can evaluate the correct function template instance to call.

```angelscript
templ<int,float>(arg1, arg2);
```

## Math operators

```angelscript
c = -(a + b);
```

| **operator** | **description** | **left hand** | **right hand** | **result** |
| --- | --- | --- | --- | --- |
| `+` | unary positive |  | *NUM* | *NUM* |
| `-` | unary negative |  | *NUM* | *NUM* |
| `+` | addition | *NUM* | *NUM* | *NUM* |
| `-` | subtraction | *NUM* | *NUM* | *NUM* |
| `*` | multiplication | *NUM* | *NUM* | *NUM* |
| `/` | division | *NUM* | *NUM* | *NUM* |
| `%` | modulos | *NUM* | *NUM* | *NUM* |
| `**` | exponent | *NUM* | *NUM* | *NUM* |

Plus and minus can be used as unary operators as well. NUM can be exchanged for any numeric type, e.g. `int` or `float`. Both terms of the dual operations will be implicitly converted to have the same type. The result is always the same type as the original terms. One exception is unary negative which is not available for `uint`.

## Bitwise operators

```angelscript
c = ~(a | b);
```

| **operator** | **description** | **left hand** | **right hand** | **result** |
| --- | --- | --- | --- | --- |
| `~` | bitwise complement |  | *NUM* | *NUM* |
| `&` | bitwise and | *NUM* | *NUM* | *NUM* |
| `|` | bitwise or | *NUM* | *NUM* | *NUM* |
| `^` | bitwise xor | *NUM* | *NUM* | *NUM* |
| `<<` | left shift | *NUM* | *NUM* | *NUM* |
| `>>` | right shift | *NUM* | *NUM* | *NUM* |
| `>>>` | arithmetic right shift | *NUM* | *NUM* | *NUM* |

All except `~` are dual operators.

Both operands will be converted to integers while keeping the sign of the original type before the operation. The resulting type will be the same as the left hand operand.

## Compound assignments

```angelscript
lvalue += rvalue;
lvalue = lvalue + rvalue;
```

A compound assignment is a combination of an operator followed by the assignment. The two expressions above means practically the same thing. Except that first one is more efficient in that the lvalue is only evaluated once, which can make a difference if the lvalue is complex expression in itself.

Available operators: `+= -= *= /= %= **= &= |= ^= <<= >>= >>>=`

## Logic operators

```angelscript
if( a and b or not c )
{
  // ... do something
}
```

| **operator** | **description** | **left hand** | **right hand** | **result** |
| --- | --- | --- | --- | --- |
| `not` | logical not |  | `bool` | `bool` |
| `and` | logical and | `bool` | `bool` | `bool` |
| `or` | logical or | `bool` | `bool` | `bool` |
| `xor` | logical exclusive or | `bool` | `bool` | `bool` |

Boolean operators only evaluate necessary terms. For example in expression `a and b`, `b` is only evaluated if `a` is `true`.

Each of the logic operators can be written as symbols as well, i.e. `||` for `or`, `&&` for `and`, `^^` for `xor`, and `!` for `not`.

## Equality comparison operators

```angelscript
if( a == b )
{
  // ... do something
}
```

The operators `==` and `!=` are used to compare two values to determine if they are equal or not equal, respectively. The result of this operation is always a boolean value.

## Relational comparison operators

```angelscript
if( a > b )
{
  // ... do something
}
```

The operators `<`, `>`, `<=`, and `>=` are used to compare two values to determine their relationship. The result is always a boolean value.

## Identity comparison operators

```angelscript
if( a is null )
{
  // ... do something
}
else if( a is b )
{
  // ... do something
}
```

The operators `is` and `!is` are used to compare the identity of two objects, i.e. to determine if the two are the same object or not. These operators are only valid for reference types as they compare the address of two objects. The result is always a boolean value.

## Increment operators

```angelscript
// The following means a = i; i = i + 1;
a = i++;

// The following means i = i - 1; b = i;
b = --i;
```

These operators can be placed either before or after an lvalue to increment/decrement its value either before or after the value is used in the expression. The value is always incremented or decremented with 1.

## Indexing operator

```angelscript
arr[i] = 1;
```

This operator is used to access an element contained within the object. Depending on the object type, the expression between the `[]` needs to be of different types.

## Conditional expression

```angelscript
choose ? a : b;
```

If the value of `choose` is `true` then the expression returns `a` otherwise it will return `b`.

Both `a` and `b` must be of the same type. If they are not, the compiler will attempt an implicit conversion by following the principle of least cost, i.e. the expression that will be converted is the one that cost less to convert. This cost is determined the same way as is done for [matching arguments in function calls](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_overload.html).

If the conversion doesn't work, or the conversion of either expression cost the same, then the compiler will give an error.

The conditional expression can be used as an lvalue, i.e. on the left value of an assignment expression, if both `a` and `b` are lvalues of the same type.

```angelscript
int a, b;
(expr ? a : b) = 42;
```

## Member access

```angelscript
object.property = 1;
object.method();
```

`object` must be an expression resulting in a data type that have members. `property` is the name of a member variable that can be read/set directly. `method` is the name of a member method that can be called on the object.

## Handle-of

```angelscript
// Make handle reference the object instance
@handle = @object;

// Clear the handle and release the object it references
@handle = null;
```

Object handles are references to an object. More than one handle can reference the same object, and only when no more handles reference an object is the object destroyed.

The members of the object that the handle references are accessed the same way through the handle as if accessed directly through the object variable, i.e. with `.` operator.

See also: [Object handles](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_handle.html)

## Parenthesis

```angelscript
a = c * (a + b);
if( (a or b) and c )
{
  // ... do something
}
```

Parenthesis are used to group expressions when the [operator precedence](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_operator_precedence.html) does not give the desired order of evaluation.

## Scope resolution

```angelscript
int value;
void function()
{
  int value;       // local variable overloads the global variable
  ::value = value; // use scope resolution operator to refer to the global variable
}
```

The scope resolution operator `::` can be used to access variables or functions from another scope when the name is overloaded by a local variable or function. Write the scope name on the left (or blank for the global scope) and the name of the variable/function on the right.

See also: [Namespaces](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_namespace.html)

## Type conversions

```angelscript
// implicitly convert the clss handle to a intf handle
intf @a = @clss();

// explicitly convert the intf handle to a clss handle
clss @b = cast<clss>(a);
```

Object handles can be converted to other object handles with the cast operator. If the cast is valid, i.e. the true object implements the class or interface being requested, the operator returns a valid handle. If the cast is not valid, the cast returns a null handle.

The above is called a reference cast, and only works for types that support object handles. In this case the handle still refers to the same object, it is just exposed through a different interface.

Types that do not support object handles can be converted with a value cast instead. In this case a new value is constructed, or in case of objects a new instance of the object is created.

```angelscript
// implicit value cast
int a = 1.0f;

// explicit value cast
float b = float(a)/2;
```

In most cases an explicit cast is not necessary for primitive types, however, as the compiler is usually able to do an implicit cast to the correct type.

## Anonymous objects

Anonymous objects, i.e. objects that are created without being declared as variables, can be instantiated in expressions by calling invoking the object's constructor as if it was a function. Both reference types and value types can be created like this.

```angelscript
// Call the function with a new object of the type MyClass
func(MyClass(1,2,3));
```

For types that support it, the anonymous objects can also be initialized with initialization lists.

```angelscript
// Call the function with a dictionary, explicitly informing the type of the initialization list
func(dictionary = {{'banana',1}, {'apple',2}, {'orange',3}});

// When there is only one possible type that support initialization lists it is possible
// to omit the type and let the compiler implicitly determine it based on the use
funcExpectsAnArrayOfInts({1,2,3,4});
```

If the desired type for the anonymous object is a template, it may be necessary to explicitly inform the template type;

```angelscript
funcExpectsAnArray(array<int> = {1,2,3,4});
```

---

## Source: `docs/angelscript-lang/funcdef.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_funcdef.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Funcdefs

Funcdefs are used to define a function signature that will be used to store pointers to functions with matching signatures. With this a function pointer can be created, which is able to store dynamic pointers that can be invoked at a later time as a normal function call.

```angelscript
// Define a function signature for the function pointer
funcdef bool CALLBACK(int, int);
```

See also: [Function handles](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_funcptr.html) for more information on how to use this.

---

## Source: `docs/angelscript-lang/functions.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Functions

Functions are declared globally, and consists of a signature where the types of the arguments and the return value is defined, and a body where the implementation is declared.

- [Function declaration](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_decl.html)
- [Parameter references](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_ref.html)
- [Return references](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_retref.html)
- [Function overloading](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_overload.html)
- [Default arguments](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_defarg.html)
- [Anonymous functions](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_anonfunc.html)

---

## Source: `docs/angelscript-lang/generics.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_generic.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# The generic calling convention

> **Note**
> This page describes the *generic calling convention* used when registering C++ functions with the engine — an application-embedding topic. AngelScript's script-side "generics" are [template types](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_template.html). This page is reproduced for completeness because the manual files it indexes are part of the core reference tree.

The generic calling convention is available for those situations where the application's native calling convention doesn't work, for example on platforms where support for native calling conventions haven't been added yet. You can detect if native calling conventions isn't supported on your target platform by calling the `asGetLibraryOptions` function and checking the returned string for "AS_MAX_PORTABILITY". If the identifier is in the returned string, then native calling conventions is not supported.

Functions implementing the generic calling conventions are always global functions (or static class methods), that take as parameter a pointer to an `asIScriptGeneric` interface and returns void.

```cpp
// The function has been registered with signature:
// MyIntf @func(int, float, MyIntf @+)

void MyGenericFunction(asIScriptGeneric *gen)
{
  // Extract the arguments
  int arg0 = gen->GetArgDWord(0);
  float arg1 = gen->GetArgFloat(1);
  asIScriptObject *arg2 = reinterpret_cast<asIScriptObject*>(gen->GetArgObject(2));

  // Call the real function
  asIScriptObject *ret = MyFunction(arg0, arg1, arg2);

  // Set the return value
  gen->SetReturnObject(ret);
}
```

Functions using the generic calling convention can be registered anywhere the script engine is expecting global functions or class methods (except where explicitly written otherwise).

Writing the functions for the generic calling convention requires extracting each argument from the AngelScript stack, and then manually giving the return value back. For that reason it may be desired to use the [automatic wrapper functions](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_autowrap.html) rather than writing the functions yourself.

## Extracting function arguments

To extract functions arguments from the generic interface you should call one of the GetArg methods that will return the value of the argument, or the `GetAddressOfArg` method. The GetAddressOfArg method returns a pointer to the actual value. The application should then cast this pointer to a pointer of the correct type so that the value can be read from the address.

If the function you're implementing represents a class method, the pointer to the object instance should be obtained with a call to `GetObject`.

For arguments that receive output references, i.e. &out, the GetAddressOfArg will give an address to a valid instance of the type. If the function does not want to return anything in these arguments it is not necessary to do anything.

The `asIScriptGeneric` interface treats the ref count the same way as in native calling conventions, i.e. the application function is responsible to releasing any handle received as a handle (or [register the function with +](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_obj_handle.html#doc_obj_handle_4)).

## Returning values

To return a value from the function one of the SetReturn methods can be called to pass the value to the generic interface. Returning primitive values is straight forward, but care must be taken when returning object types, either by value, reference, or as object handle. Depending on the type and the function used it may be necessary to increment the reference count, or even make a copy of the object first. Carefully read the instructions for `SetReturnAddress` and `SetReturnObject` to determine what needs to be done to get the expected result.

It is also possible to use the `GetAddressOfReturnLocation` method to obtain the address of the memory where the return value will be stored. The memory is not initialized, so you should use the placement new operator to initialize this memory with a call to the constructor. This also works for primitive types, which makes this ideal for template implementations, such as that in the [automatic wrapper functions](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_autowrap.html).

If the return type is a handle then the GetAddressOfReturnLocation will refer to a location holding a null pointer, so if the function is to return null it is not necessary to do anything. For primitives it will be an undefined value, so if the value is important it must be set. For objects of value types returned by value the function must initialize the return value at the location already preallocated by the calling function, unless an exception is set with `asIScriptContext::SetException`.

If the function is registered to return a +, then the script engine will [automatically increment the ref count](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_obj_handle.html#doc_obj_handle_4), just as is done for native calling conventions.

---

## Source: `docs/angelscript-lang/handles.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_handle.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Object handles

An object handle is a type that can hold a reference to an object. With object handles it is possible to declare more than one variables that refer to the same physical object.

Not all types allow object handles to be used. None of the primitive data types, bool, int, float, etc, can have object handles. Object types registered by the application may or may not allow object handles, depending on how they have been registered.

See also: [Object handles to the application](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_obj_handle.html)

## General usage

An object handle is declared by appending the @ symbol to the data type.

```angelscript
object@ obj_h;
```

This code declares the object handle obj and initializes it to null, i.e. it doesn't hold a reference to any object.

In expressions variables declared as object handles are used the exact same way as normal objects. But you should be aware that object handles are not guaranteed to actually reference an object, and if you try to access the contents of an object in a handle that is null an exception will be raised.

```angelscript
object obj;
object@ obj_h;
obj.Method();
obj_h.Method();
```

Operators like = or any other operator registered for the object type work on the actual object that the handle references. These will also throw an exception if the handle is empty.

```angelscript
object obj;
object@ obj_h;
obj_h = obj;
```

When you need to make an operation on the actual handle, you should prepend the expression with the @ symbol. Setting the object handle to point to an object is for example done like this:

```angelscript
object obj;
object@ obj_h;
@obj_h = @obj;
```

Note that the compiler can often implicitly determine that it is the handle of the object that is needed rather than the actual object itself. In these cases it is not necessary to explicitly prepend the expression with @.

An object handle can be compared against another object handle (of the same type) to verify if they are pointing to the same object or not. It can also be compared against null, which is a special keyword that represents an empty handle. This is done using the identity operator, is.

```angelscript
object@ obj_a, obj_b;
if( obj_a is obj_b ) {}
if( obj_a !is null ) {}
```

Observe, the == and != operators will do a value comparison on the objects referred to by the handles using the [opEquals](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_ops.html#doc_script_class_cmp_ops) or [opCmp](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_ops.html#doc_script_class_cmp_ops) operator overloads. Though, if the expressions are prepended with @ the operators will have the same function as is and !is.

## Object life times

An object's life time is normally for the duration of the scope the variable was declared in. But if a handle outside the scope is set to reference the object, the object will live on until all object handles are released.

```angelscript
object@ obj_h;
{
  object obj;
  @obj_h = @obj;

  // The object would normally die when the block ends,
  // but the handle is still holding a reference to it
}

// The object still lives on in obj_h ...
obj_h.Method();

// ... until the reference is explicitly released
// or the object handle goes out of scope
@obj_h = null;
```

## Object relations and polymorphing

Object handles can be used to write common code for related types, by means of inheritance or interfaces. This allows a handle to an interface to store references to all object types that implement that interface, similarly a handle to a base class can store references to all object types that derive from that class.

```angelscript
interface I {}
class A : I {}
class B : I {}

// Store reference in handle to interface
I @i1 = A();
I @i2 = B();

void function(I @i)
{
  // Functions implemented by the interface can be
  // called directly on the interface handle. But if
  // special treatment is need for a specific type, a
  // cast can be used to get a handle to the true type.
  A @a = cast<A>(i);
  if( a !is null )
  {
    // Access A's members directly
    ...
  }
  else
  {
    // The object referenced by i is not of type A
    ...
  }
}
```

## Const handles

Sometimes it is necessary to hold handles to objects that shouldn't be allowed to be modified. This is done by prefixing the type with 'const', e.g.

```angelscript
obj @a;                      // handle to modifiable object
const obj @b;                // handle to non-modifiable object
```

A handle to a non-modifiable object can refer to both modifiable objects and non-modifiable objects, but the script will not allow the object to be modified through that handle, nor allow the handle to be passed to another handle that would allow modifications.

This syntax is not to be confused with handles that are themselves read-only, i.e. the handle cannot be re-assigned to refer to a different object. Read-only handles like this are declared by adding the 'const' keyword as a suffix after the '@' symbol.

```angelscript
obj @ const c = obj();       // read-only handle to a modifiable object
const obj @ const d = obj(); // read-only handle to a non-modifiable object
```

A read-only handle can only be initialized when declared.

---

## Source: `docs/angelscript-lang/inheritance.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_inheritance.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Inheritance and polymorphism

AngelScript supports single inheritance, where a derived class inherits the properties and methods of its base class. Multiple inheritance is not supported, but polymorphism is supported by implementing [interfaces](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_interface.html), and code reuse is provided by including [mixin classes](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_mixin.html).

All the class methods are virtual, so it is not necessary to specify this manually. When a derived class overrides an implementation, it can extend the original implementation by specifically calling the base class' method using the scope resolution operator. When implementing the constructor for a derived class the constructor for the base class is called using the `super` keyword. If none of the base class' constructors is manually called, the compiler will automatically insert a call to the default constructor in the beginning. The base class' destructor will always be called after the derived class' destructor, so there is no need to manually do this.

```angelscript
// A derived class
class MyDerived : MyBase
{
  // The default constructor
  MyDerived()
  {
    // Calling the non-default constructor of the base class
    super(10);

    b = 0;
  }

  // Overloading a virtual method
  void DoSomething()
  {
    // Call the base class' implementation
    MyBase::DoSomething();

    // Do something more
    b = a;
  }

  int b;
}
```

A class that is derived from another can be implicitly cast to the base class. The same works for interfaces that are implemented by a class. The other direction requires an [explicit cast](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html#conversion), as it is not known at compile time if the cast is valid.

```angelscript
class A {}
class B : A {}
void Foo()
{
  A @handle_to_A;
  B @handle_to_B;

  @handle_to_A = A(); // OK
  @handle_to_A = B(); // OK. The reference will be implicitly cast to A@

  @handle_to_B = A(); // Not OK. This will give a compilation error
  @handle_to_B = B(); // OK

  @handle_to_A = handle_to_B; // OK. The reference will be implicitly cast to A@
  @handle_to_B = handle_to_A; // Not OK. This will give a compilation error

  @handle_to_B = cast<B>(handle_to_A); // OK. Though, the explicit cast will return null
                                       // if the object in handle_to_a is not really an
                                       // instance of B
}
```

## Extra control with final, abstract, and override

A class can be marked as 'final' to prevent the inheritance of it. This is an optional feature and mostly used in larger projects where there are many classes and it may be difficult to manually control the correct use of all classes. It is also possible to mark individual class methods of a class as 'final', in which case it is still possible to inherit from the class, but the finalled method cannot be overridden.

Another keyword that can be used to mark a class is 'abstract'. Abstract classes cannot be instantiated, but they can be derived from. Abstract classes are most frequently used when you want to create a family of classes by deriving from a common base class, but do not want the base class to be instantiated by itself. It is currently not possible to mark methods as abstract so all methods must have an implementation even for abstract classes.

```angelscript
// A final class that cannot be inherited from
final class MyFinal
{
  MyFinal() {}
  void Method() {}
}

// A class with individual methods finalled
class MyPartiallyFinal
{
  // A final method that cannot be overridden
  void Method1() final {}

  // Normal method that can still be overridden by derived class
  void Method2() {}
}

// An abstract class
abstract class MyAbstractBase {}
```

When deriving a class it is possible to tell the compiler that a method is meant to override a method in the inherited base class. When this is done and there is no matching method in the base class the compiler will emit an error, as it knows that something wasn't implemented quite the way it was meant. This is especially useful to catch errors in large projects where a base class might be modified, but the derived classes was forgotten.

```angelscript
class MyBase
{
  void Method() {}
  void Method(int) {}
}

class MyDerived : MyBase
{
  void Method() override {}      // OK. The method is overriding a method in the base class
  void Method(float) override {} // Not OK. The method isn't overriding a method in base class
}
```

---

## Source: `docs/angelscript-lang/license.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_license.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# License

## AngelCode Scripting Library

Copyright © 2003-2025 Andreas Jönsson

This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.

Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.

2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.

3. This notice may not be removed or altered from any source distribution.

---

## Source: `docs/angelscript-lang/namespaces.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_namespace.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Namespaces

Namespaces can be used to organize large projects in logical units that may be easier to remember. When using namespaces it is also not necessary to worry about using names for entities that may exist in a different part of the project under a different namespace.

```angelscript
namespace A
{
  // Entities in a namespace see each other normally.
  void function() { variable++; }
  int variable;
}

namespace B
{
  // Entities in different namespaces don't immediately see each other and
  // can reuse the same name without causing name conflicts. By using the
  // scoping operator the entity from the desired namespace can be explicitly
  // informed.
  void function() { A::function(); }
}
```

Observe that in order to refer to an entity from a different namespace the scoping operator must be used, unless it is a parent namespace in which case it is only necessary if the child namespace declare the same entity.

```angelscript
int var;
namespace Parent
{
  int var;
  namespace Child
  {
    int var;
    void func()
    {
      // Accessing variable in parent namespace requires
      // specifying the scope if an entity in a child namespace
      // uses the same name
      var = Parent::var;

      // To access variables in global scope the scoping
      // operator without any name should be used
      Parent::var = ::var;
    }
  }
}

void func()
{
  // Access variable in a nested namespace requires
  // fully qualified scope specifier
  int var = Parent::Child::var;
}
```

## Using namespace

In order to avoid having to always prefix symbols with their namespace it is also possible to use 'using namespace' to tell the compiler to also search for symbols in a specific namespace.

```angelscript
namespace test
{
  void func() {}
}
using namespace test;
void main()
{
  func(); // The function will be found within the test namespace
}
```

If 'using namespace' is used globally or within a namespace, the symbols from the given namespace will be visible throughout the entire enclosing namespace.

See also: [Statement 'using namespace'](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_statements.html#using_ns)

---

## Source: `docs/angelscript-lang/overview.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_overview.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Overview

AngelScript is structured around an [engine](https://www.angelcode.com/angelscript/sdk/docs/manual/classas_i_script_engine.html) where the application should [register](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_api.html) the [functions](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_func.html), [properties](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_prop.html), and even [types](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_type.html), that the scripts will be able to use. The scripts are then compiled into [modules](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_module.html), where the application may have one or more modules, depending on the need of the application. The application can also expose a different interface to each module through the use of [access profiles](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_access_mask.html). This is especially useful when the application works with multiple types of scripts, e.g. GUI, AI control, etc.

As the scripts are compiled into bytecode AngelScript also provides a virtual machine, also known as a [script context](https://www.angelcode.com/angelscript/sdk/docs/manual/classas_i_script_context.html), for [executing](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_call_script_func.html) the bytecode. The application can have any number of script context at the same time, though most applications will probably only need one. The contexts support [suspending](https://www.angelcode.com/angelscript/sdk/docs/manual/classas_i_script_context.html#ad4ac8be3586c46069b5870e40c86544a) the execution and then resuming it, so the application can easily implement features such as [concurrent scripts](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_concurrent.html) and [co-routines](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_coroutine.html). The script context also provides an interface for extracting run-time information, useful for [debugging](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_debug.html) scripts.

The [script language](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script.html) is based on the well known syntax of C++ and more modern languages such as Java, C#, and D. Anyone with some knowledge of those languages, or other script languages with similar syntax, such as Javascript and ActionScript, should feel right at home with AngelScript. Contrary to most script languages, AngelScript is a strongly typed language, which permits faster execution of the code and smoother interaction with the host application as there will be less need for runtime evaluation of the true type of values.

The [memory management](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_memory.html) in AngelScript is based on reference counting with an incremental [garbage collector](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_gc.html) for detecting and freeing objects with circular references. This provides for a controlled environment without application freezes as the garbage collector steps in to free up memory.

---

## Source: `docs/angelscript-lang/script-class-props.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_prop.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Property accessors

> **Note**
> The application can optionally [turn off support for property accessors](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_custom_options.html#doc_adv_custom_options_lang_mod), so you need to verify your application's manual to determine if this is supported for your application or not.

Many times when working with properties it is necessary to make sure specific logic is followed when accessing them. An example would be to always send a notification when a property is modified, or computing the value of the property from other properties. By implementing property accessor methods for the properties this can be implemented by the class itself, making it easier for the one who accesses the properties.

In AngelScript property accessors are declared with the following syntax:

```angelscript
class MyObj
{
  // A virtual property with accessors
  int prop
  {
    get const
    {
      // The actual value of the property could be stored
      // somewhere else, or even computed at access time.
      return realProp;
    }
    set
    {
      // The new value is stored in a hidden parameter appropriately called 'value'.
      realProp = value;
    }
  }

  // The actual value can be stored in a member or elsewhere.
  // It is actually possible to use the same name for the real property, if so is desired.
  private int realProp;
}
```

Behind the scene the compiler transforms this into two methods with the name of the property and the prefixes get_ and set_, and with the function decorator 'property'. The following generates the equivalent code, and is perfectly valid too:

```angelscript
class MyObj
{
  int get_prop() const property { return realProp; }
  void set_prop(int value) property { realProp = value; }
  private int realProp;
}
```

If you implement the property accessors by explicitly writing the two methods you must make sure the return type of the get accessor and the parameter type of the set accessor match, otherwise the compiler will not know which is the correct type to use.

For interfaces the first alternative is usually the preferred way of declaring the property accessors, as it gets quite short and easy to read.

```angelscript
interface IProp
{
  int prop { get const; set; }
}
```

You can also leave out either the get or set accessor. If you leave out the set accessor, then the property will be read-only. If you leave out the get accessor, then the property will be write-only.

Property accessors can also be implemented for global properties, which follows the same rules, except the functions are global.

When the property accessors have been declared it is possible to access them like ordinary properties, and the compiler will automatically expand the expressions to the appropriate function calls, either set_ or get_ depending on how the property is used in the expression.

```angelscript
void Func()
{
  MyObj obj;

  // Set the property value just like a normal property.
  // The compiler will convert this to a call to set_prop(10000).
  obj.prop = 10000;

  // Get the property value just a like a normal property.
  // The compiler will convert this to a call to get_prop().
  assert( obj.prop == 1000 );
}
```

Observe that as property accessors are actually a pair of methods rather than direct access to the value, some restrictions apply as to how they can be used in expressions that inspect and mutate in the same operation. Compound assignments can be used on property accessors if the owning object is a reference type, but not if the owning object is a value type. This is because the compiler must be able to guarantee that the object stays alive between the two calls to the get accessor and set accessor.

The increment and decrement operators are currently not supported.

In such cases the expression must be expanded so that the read and write operation are performed separately, e.g. the increment operator must be rewritten as follows:

```angelscript
a++;     // will not work if a is a virtual property
a += 1;  // this is OK, as long as the owner of the virtual
         // property is a reference type or the property is global
```

## Indexed property accessors

Property accessors can be used to emulate a single property or an array of properties accessed through the index operator. Property accessors for indexed access work the same way as ordinary property accessors, except that they take an index argument. The get accessor should take the index argument as the only argument, and the set accessor should take the index argument as the first argument, and the new value as the second argument.

```angelscript
string firstString;
string secondString;

// A global indexed get accessor
string get_stringArray(int idx) property
{
  switch( idx )
  {
  case 0: return firstString;
  case 1: return secondString;
  }
  return "";
}

// A global indexed set accessor
void set_stringArray(int idx, const string &in value) property
{
  switch( idx )
  {
  case 0: firstString = value; break;
  case 1: secondString = value; break;
  }
}

void main()
{
  // Setting the value of the indexed properties
  stringArray[0] = "Hello";
  stringArray[1] = "World";

  // Reading the value of the indexed properties
  print(StringArray[0] + " " + stringArray[1] + "\n");
}
```

Compound assignments currently doesn't work for indexed properties.

---

## Source: `docs/angelscript-lang/script-class.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Script classes

Script classes are declared globally and provides an easy way of grouping properties and methods into logical units. The syntax for classes is similar to C++ and Java.

- [Script class overview](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_desc.html)
- [Class constructors](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_construct.html)
- [Initialization of class members](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_memberinit.html)
- [Class destructor](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_destruct.html)
- [Class methods](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_methods.html)
- [Inheritance and polymorphism](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_inheritance.html)
- [Protected and private class members](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_private.html)
- [Operator overloads](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_ops.html)
- [Property accessors](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_prop.html)

---

## Source: `docs/angelscript-lang/statements.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_statements.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Statements

- [Variable declarations](#variable-declarations)
- [Expression statement](#expression-statement)
- [Conditions: if / if-else / switch-case](#conditions-if--if-else--switch-case)
- [Loops: while / do-while / for / foreach](#loops-while--do-while--for--foreach)
- [Loop control: break / continue](#loop-control-break--continue)
- [Return statement](#return-statement)
- [Statement blocks](#statement-blocks)
- [Try-catch blocks](#try-catch-blocks)
- [Using namespace](#using-namespace)

## Variable declarations

```angelscript
int var = 0, var2 = 10;
object@ handle, handle2;
const float pi = 3.141592f;
object obj(23), obj2 = object(23);
array<int> arr, arr2 = {1,2,3};
```

Variables must be declared before they are used within the statement block, or any sub blocks. When the code exits the statement block where the variable was declared the variable is no longer valid.

A variable can be declared with or without an initial expression. If it is declared with an initial expression it, the expression must evaluate to a type compatible with the variable type.

Any number of variables can be declared on the same line separated with commas, where all variables then get the same type.

Variables can be declared as `const`. In these cases the value of the variable cannot be changed after initialization.

Variables of primitive types that are declared without an initial value, will have a random value. Variables of complex types, such as handles and object are initialized with a default value. For handles this is `null`, for objects this is what is defined by the object's default constructor.

See also: [Auto declarations](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_auto.html)

## Expression statement

```angelscript
a = b;  // a variable assignment
func(); // a function call
```

Any [expression](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html) may be placed alone on a line as a statement. This will normally be used for variable assignments or function calls that don't return any value of importance.

All expression statements must end with a `;`.

## Conditions: if / if-else / switch-case

```angelscript
if( condition )
{
  // Do something if condition is true
}

if( value < 10 )
{
  // Do something if value is less than 10
}
else
{
  // Do something else if value is greater than or equal to 10
}
```

If statements are used to decide whether to execute a part of the logic or not depending on a certain condition. The conditional expression must always evaluate to `true` or `false`.

It's possible to chain several `if-else` statements, in which case each condition will be evaluated sequencially until one is found to be `true`.

```angelscript
switch( value )
{
case 0:
  // Do something if value equals 0, then leave
  break;

case 2:
case constant_value:
  // This will be executed if value equals 2 or the constant_value
  break;

default:
  // This will be executed if value doesn't equal any of the cases
}
```

If you have an integer (signed or unsigned) expression that have many different outcomes that should lead to different code, a switch case is often the best choice for implementing the condition. It is much faster than a series of ifs, especially if all of the case values are close in numbers.

Each case should be terminated with a break statement unless you want the code to continue with the next case.

The case value can be a constant variable that was initialized with a constant expression. If the constant variable was initialized with an expression that cannot be determined at compile time it cannot be used in the case values.

## Loops: while / do-while / for / foreach

```angelscript
// Loop, where the condition is checked before the logic is executed
int i = 0;
while( i < 10 )
{
  // Do something
  i++;
}

// Loop, where the logic is executed before the condition is checked
int j = 0;
do
{
  // Do something
  j++;
} while( j < 10 );
```

For both `while` and `do-while` the expression that determines if the loop should continue must evaluate to either true or false. If it evaluates to true, the loop continues, otherwise it stops and the code will continue with the next statement immediately following the loop.

```angelscript
// More compact loop, where condition is checked before the logic is executed
for( int n = 0; n < 10; n++ )
{
  // Do something
}
```

The `for` loop is a more compact form of a `while` loop. The first part of the statement (until the first `;`) is executed only once, before the loop starts. Here it is possible to declare a variable that will be visible only within the loop statement. The second part is the condition that must be satisfied for the loop to be executed. A blank expression here will always evaluate to true. The last part is executed after the logic within the loop, e.g. used to increment an iteration variable.

Multiple variables can be declared in the `for` loop, separated by `,`. Likewise, multiple increment expressions can be used in the last part by separating them with `,`.

```angelscript
// A foreach loop iterates over each element in a container object
dictionary dict = {...};
int count = 0;
int sum = 0;
foreach( auto val, auto key : dict )
{
   count++;
   sum += int(val);
   dict[key] = 0;
}
double average = double(sum)/count;
```

A `foreach` is a special kind of loop for container objects, where the loop will iterate over each element in the container.

The type and number of values that can be used for the container depends on the type of the container. Each container type that supports `foreach` loops will have a set of methods to allow the compiler to build the logic for iterating over the elements.

If the container is modified while still within the `foreach` loop, e.g. an element is removed or added, the behavior is undefined.

See also: [Foreach loop operators](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_ops.html#doc_script_class_foreach_ops)

## Loop control: break / continue

```angelscript
for(;;) // endless loop
{
  // Do something

  // End the loop when condition is true
  if( condition )
    break;
}
```

`break` terminates the smallest enclosing loop statement or switch statement.

```angelscript
for(int n = 0; n < 10; n++ )
{
  if( n == 5 )
    continue;

  // Do something for all values from 0 to 9, except for the value 5
}
```

`continue` jumps to the next iteration of the smallest enclosing loop statement.

## Return statement

```angelscript
float valueOfPI()
{
  return 3.141592f; // return a value
}
```

Any function with a return type other than `void` must be finished with a `return` statement where expression evaluates to the same data type as the function return type. Functions declared as `void` can have `return` statements without any expression to terminate early.

## Statement blocks

```angelscript
{
  int a;
  float b;

  {
    float a; // Override the declaration of the outer variable
             // but only within the scope of this block.

    // variables from outer blocks are still visible
    b = a;
  }

  // a now refers to the integer variable again
}
```

A statement block is a collection of statements. Each statement block has its own scope of visibility, so variables declared within a statement block are not visible outside the block.

## Try-catch blocks

```angelscript
{
  try
  {
    DoSomethingThatMightThrowException();

    // This is not executed if an exception was thrown
  }
  catch
  {
    // This is executed if an exception was thrown
  }
 }
```

A try-catch block can be used if you're executing some code that might throw an exception and you want to catch that exception and continue with the exception rather than just abort the script.

Exceptions can occur for various reasons, some examples include, accessing null pointers in uninitialized handles, division by zero, or exceptions raised from application registered functions. In some cases exceptions are intentionally raised by the script to interrupt some execution.

See also: [Exception handling](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_stdlib_exception.html)

## Using namespace

It is possible to declare 'using namespace' within a statement block. When this is done, all subsequent statements within that block will also search for symbols in the given namespace.

```angelscript
namespace test
{
  void func() {}
}
void main()
{
  test::func(); // This call must explicitly inform the namespace
  {
    using namespace test;
    func(); // This call will implicitly search the namespace
  }
  test::func(); // This is after the statement block and must again explicitly inform the namespace
}
```

See also: [Global 'using namespace'](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_namespace.html#doc_global_using_ns)

---

## Source: `docs/angelscript-lang/strings.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_strings.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Custom string type

Almost all applications have some need to manipulate text strings in one way or another. However most applications have very different needs, and also different ways of representing their string types. For that reason, AngelScript doesn't come with its own built-in string type that the application would be forced to adapt to, instead AngelScript allows the application to [register its own string type](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_api.html).

This article presents the options for customizing the script language to the application's needs with regards to strings. If you do not want, or do not need to have AngelScript use your own string type, then I suggest you use the standard add-on for [std::string registration](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html).

## Registering the custom string type

To make the script language support strings, the string type must first be [registered as type](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_type.html) with the engine. The application is free to use any valid type name, not necessarily 'string', though it is probably the most commonly used name. The custom string type can also be either value type or a reference type at the preference of the application developer.

Once the string type is registered, the application must also provide a string factory to allow the scripts to use literal string constants. The string factory must implement the `asIStringFactory` interface, and be registered with the `asIScriptEngine::RegisterStringFactory` method.

The string factory must implement all 3 methods of the `asIStringFactory` interface. The `GetStringConstant` method receives the raw string data by the compiler and should return a pointer to the custom string object that represents that string. The `ReleaseStringConstant` is called when the engine no longer needs the string constant, e.g. when discarding a module. The `GetRawStringData` is called by the engine when the raw string data is needed, e.g. when saving bytecode or when requesting a copy of a string constant.

Although not necessary, the application should preferably implement caching of the string constants, so that if two calls to GetStringConstant with the same raw string data is received the string factory returns the address of the same string instance in both calls. This will reduce the amount of memory needed to store the string constants, especially when scripts use the same string constants in many places. Remember, when using caching, the ReleaseStringConstant must only free the string object when the last call for that same object is done.

See also: [The standard string add-on](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html)

## Unicode vs ASCII

Is your application using Unicode or plain ASCII for the text? If you use Unicode, then you'll want to encode the scripts in UTF-8, which the AngelScript compiler supports natively. By default AngelScript expects the scripts to have been encoded in UTF-8, but should you prefer ASCII you can turn this off by setting the engine property `asEP_SCRIPT_SCANNER` to 0 right after creating the engine.

```cpp
// Set engine to use ASCII scanner for script code
engine->SetEngineProperty(asEP_SCRIPT_SCANNER, 0);
```

> `asEP_SCRIPT_SCANNER` — Select scanning method: 0 - ASCII, 1 - UTF8. Default: 1 (UTF8).

If you do use Unicode, then you'll also want to choose the desired encoding for the string literals, either UTF-8 or UTF-16. By default the string literals in AngelScript are encoded with UTF-8, but if your application is better prepared for UTF-16 then you'll want to change this by setting the engine property `asEP_STRING_ENCODING` to 1 before compiling your scripts.

```cpp
// Set engine to use UTF-16 encoding for string literals
engine->SetEngineProperty(asEP_STRING_ENCODING, 1);
```

> `asEP_STRING_ENCODING` — Select string encoding for literals: 0 - UTF8/ASCII, 1 - UTF16. Default: 0 (UTF8)

Observe that the string factory called by the engine to create new strings gives the size of the string data in bytes even for UTF-16 encoded strings, so you'll need to divide the size by two to get the number of characters in the string.

## Multiline string literals

There is also a couple of options that affect the script language itself a bit. If you like the convenience of allowing string literals to span multiple lines of code, then you can turn this on by setting the engine property `asEP_ALLOW_MULTILINE_STRINGS` to true. Without this the compiler will give an error if it encounters a line break before the end of the string.

```cpp
// Set engine to allow string literals with line breaks
engine->SetEngineProperty(asEP_ALLOW_MULTILINE_STRINGS, true);
```

> `asEP_ALLOW_MULTILINE_STRINGS` — Allow linebreaks in string constants. Default: false.

Observe that the line ending encoding of the source file will not be modified by the script compiler, so depending on how the file has been saved, you may get strings using different line endings.

The [heredoc strings](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_strings.html) are not affected by this setting, as they are designed to support multiline text sections.

## Character literals

By default AngelScript doesn't have character literals as C and C++ does. A string literal can be written with double quotes or single quotes and still have the same meaning. This makes it convenient to embed scripts in XML files or C/C++ source files where double quotes would otherwise end the script code.

If you want to have single quoted literals mean a single character literal instead of a string, then you can do so by setting the engine property `asEP_USE_CHARACTER_LITERALS` to true. The compiler will then convert single quoted literals to an integer number representing the first character.

```cpp
// Set engine to use character literals
engine->SetEngineProperty(asEP_USE_CHARACTER_LITERALS, true);
```

> `asEP_USE_CHARACTER_LITERALS` — Interpret single quoted strings as character literals. Default: false.

Observe that the `asEP_SCRIPT_SCANNER` property has great importance in this case, as an ASCII character can only represent values between 0 and 255, whereas a Unicode character can represent values between 0 and 1,114,111.

---

## Source: `docs/angelscript-lang/variables.md`

<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_variable.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Variables

Global variables may be declared in the scripts, which will then be shared between all contexts accessing the script module.

Variables declared globally like this are accessible from all functions. The value of the variables are initialized at compile time and any changes are maintained between calls. If a global variable holds a memory resource, e.g. a string, its memory is released when the module is discarded or the script engine is reset.

```angelscript
int MyValue = 0;
const uint Flag1 = 0x01;
```

Variables of primitive types are initialized before variables of non-primitive types. This allows class constructors to access other global variables already with their correct initial value. The exception is if the other global variable also is of a non-primitive type, in which case there is no guarantee which variable is initialized first, which may lead to null-pointer exceptions being thrown during initialization.

Be careful with calling functions that may access global variables from within the initialization expression of global variables. While the compiler tries to initialize the global variables in the order they are needed, there is no guarantee that it will always succeed. Should a function access a global variable that has not yet been initialized you will get unpredictable behaviour or a null-pointer exception.

---

## Source: `.claude/skills/pcx-angelscript-discipline/SKILL.md`

---
name: pcx-angelscript-discipline
description: >
  Behavioral and syntactic rules for writing .as scripts on Perception.cx.
  Prevents Enma-reflex errors in the AngelScript API surface — method names,
  parameter shapes, and constants differ between the two languages. Always
  active when editing .as files.
license: MIT
---

# AngelScript Discipline for Perception.cx

Behavioral and syntactic rules for writing `.as` scripts on Perception.cx. The companion skill to `game-cheat-guidelines` (which is Enma-flavored): same domain, different language, different gotchas. AngelScript on PCX has its own type system, lifecycle conventions, and API surface; the AI defaults to Enma idioms when editing `.as` files and produces code that does not compile.

**Always active when editing `.as` files.** These rules apply every time you write or edit a Perception.cx AngelScript script.

**Prerequisite:** `game-hacking-pcx` skill for the full doc index. **Read the relevant `docs/perception/angelscript/<file>.md` before writing any API call** — the AngelScript surface is not the Enma surface, and method names, parameter shapes, and constants differ.

---

## Trigger

`.as` file open, AngelScript syntax visible (`&in` references, `@` handles, `register_callback`, `on_tick`), user mentions AngelScript / `proc_t` / PCX scripting in AS context, any code referencing `docs/perception/angelscript/`.

---

## 1. AngelScript Is Not Enma — Don't Paste Enma APIs

**The PCX AngelScript API has different function names, different parameter shapes, and different idioms than the Enma API. They look similar; they are not interchangeable.**

The most common bug in AI-written `.as` scripts is pasting Enma API calls verbatim. The script doesn't compile, or worse, compiles to something that looks right and behaves wrong because AngelScript happens to have a same-named function with a different signature.

| Enma | AngelScript |
|---|---|
| `register_routine(cast<int64>(on_render), 0)` | `register_callback(on_tick, 16, 0)` |
| `int64 main()` | `int main()` |
| `void on_render(int64 data)` | `void on_tick(int id, int data_index)` |
| `println(...)` | `log(...)` |
| `color(r,g,b,a)` then `draw_rect(pos, size, color, ...)` | `draw_rect_filled(x, y, w, h, r, g, b, a, rounding, corner_flags)` |
| `get_view_width()` / `get_view_height()` | `get_view(vw, vh)` — out-param into two floats |
| `create_section("X")` returning `int64` | `create_section("X")` — same name, but check the AS gui-api doc for return type |

```cpp
// WRONG — Enma idioms in an .as file
int64 main() {
    color c = color(255, 0, 0, 255);
    draw_rect(vec2(10, 10), vec2(100, 100), c, 1.0, 4.0, 15);
    register_routine(cast<int64>(on_render), 0);
    return 1;
}

// RIGHT — AngelScript syntax, AS API, AS lifecycle
int main() {
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_tick(int id, int data_index) {
    draw_rect_filled(10.0f, 10.0f, 100.0f, 100.0f,
                     255, 0, 0, 255, 4.0f, RR_ALL);
}
```

**Why:** AngelScript is a separately registered host language with its own bindings. The Enma and AS APIs cover overlapping domains but the function signatures, type registrations, and constants are independent. Always confirm the call in `docs/perception/angelscript/<area>-api.md` before writing it.

---

## 2. Handles vs Values — Know Which You're Holding

**AngelScript distinguishes reference handles (`Type@`) from value types. PCX types use both, and the rule for each is in the doc.**

A handle is `Type@` — a reference-counted pointer. Assignment with `=` copies the handle; assignment with `@=` rebinds it. Method calls on a null handle throw. Value types use `=` for deep copy; you cannot have a "null" value.

```cpp
// Handle syntax — explicit @, null-checkable, ref-counted
proc_t@ p = ref_process("game.exe");      // ref_process returns a handle
if (p is null) { log("process not found"); return 0; }
if (!p.alive()) { p.deref(); return 0; }   // also deref when alive returns false

// Value syntax — vec3, color tuples, math types are typically values
Vector3 pos(1.0f, 2.0f, 3.0f);             // direct construction, no @
Vector3 copy = pos;                         // deep copy
```

The PCX docs are explicit about which types are handle-only, value-only, or both — *check the API page for each type you instantiate*. `proc_t` is documented as a handle; never declare it without `@` and never skip `is null` after `ref_process`.

```cpp
// WRONG — proc_t without handle syntax; may compile depending on registration
//         but ref_process returns a handle, and you lose the null-check pattern
proc_t p = ref_process("game.exe");
uint64 base = p.base_address();   // throws if process didn't open

// RIGHT
proc_t@ p = ref_process("game.exe");
if (p is null || !p.alive()) { return 0; }
uint64 base = p.base_address();
```

**Why:** A null handle dereference is a runtime exception that kills your script. Value-vs-handle confusion is the #1 source of `.as` crashes on PCX. The doc for each type tells you which one it is; check it once, write the right syntax forever.

---

## 3. Always `deref()` When You're Done — Even on Failure

**`proc_t` is reference-counted. You MUST call `deref()` to release it. The docs are explicit: even if `alive()` returns false, deref the handle.**

This is unique to AngelScript on PCX. The Enma equivalent (`ref_process` returning a `proc_t` value) is RAII-managed; the AngelScript version is not. A script that leaks `proc_t` handles will accumulate them across reloads.

```cpp
// WRONG — early return without deref leaks the handle
int main() {
    proc_t@ p = ref_process("game.exe");
    if (p is null) return 0;
    if (!p.alive()) return 0;            // LEAK — never derefed
    // ... do work ...
    p.deref();
    return 0;
}

// RIGHT — single exit path, or deref on every exit
int main() {
    proc_t@ p = ref_process("game.exe");
    if (p is null) return 0;
    if (!p.alive()) { p.deref(); return 0; }
    // ... do work ...
    p.deref();
    return 0;
}

// BETTER — for persistent scripts, store the handle globally and deref in on_unload
proc_t@ g_proc = null;

int main() {
    @g_proc = ref_process("game.exe");
    if (g_proc is null || !g_proc.alive()) { return 0; }
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload() {
    if (g_proc !is null) {
        g_proc.deref();
        @g_proc = null;
    }
}
```

Note the `@=` operator for rebinding handle assignments (`@g_proc = ...`); plain `=` between handles invokes the value-copy path on most PCX types and will not compile.

**Why:** Leaked handles keep the underlying process reference alive past script unload. Across many script reloads in an editing session, this accumulates resource pressure and can prevent re-attach to the target. The deref pattern is cheap; making it a habit costs you nothing and saves a class of bug.

---

## 4. `float` Is `float32` — Use `f` Suffixes; `double` Promotes Silently

**AngelScript uses `float` for 32-bit and `double` for 64-bit. Literal `1.5` is `double`. Render APIs and vertex math expect `float`. Use `1.5f` literals.**

This mirrors C/C++. The AS compiler will silently promote `float` to `double` when mixed in arithmetic, then narrow the result back at the call boundary — a path that can lose precision in tight render loops. Be explicit.

```cpp
// WRONG — double literals everywhere
float vw, vh; get_view(vw, vh);
float cx = vw * 0.5;                      // promotes vw to double, narrows result
draw_rect_filled(cx - 100, cy - 50, 200, 100,
                 40, 40, 40, 255, 8.0, RR_ALL);  // 8.0 is double → 8.0f conversion

// RIGHT — f suffix on every float literal that feeds a float API
float vw, vh; get_view(vw, vh);
float cx = vw * 0.5f;
draw_rect_filled(cx - 100.0f, cy - 50.0f, 200.0f, 100.0f,
                 40, 40, 40, 255, 8.0f, RR_ALL);
```

Color components are integers (0-255) in the PCX AS draw API — no `f` suffix on those. Rounding, dimensions, positions are floats — `f` suffix.

**Why:** AS's implicit promotion does the right thing for correctness but pays in a constant stream of `cvtss2sd` / `cvtsd2ss` around every literal. In a render path hit at 144 Hz, that's measurable. The `f` suffix is also a clarity signal — when you read the code later, you can tell what's a pixel coordinate (`100.0f`) and what's a count or flag (`100`).

---

## 5. Out Parameters Use `&out` — Not `out`, Not Pointers

**AngelScript out parameters are reference parameters declared `&out` (write-only) or `&inout` (read-write). `&in` is read-only by reference. These are *part of the declaration*, not call-site syntax.**

```cpp
// Declaring an out-param function
void get_view(float &out width, float &out height);
bool world_to_screen(const Vector3 &in world, Vector2 &out screen);

// Calling it — just pass the variables, no `&` at call site
float vw, vh;
get_view(vw, vh);                          // AS handles the reference

Vector2 screen;
if (world_to_screen(player_pos, screen)) {
    draw_circle_filled(screen.x, screen.y, 4.0f, 255, 0, 0, 255);
}
```

Three common mistakes:

- Declaring `out` without `&` — compile error, AS requires the reference qualifier
- Trying to write to `&in` — read-only, compile error
- Using `&inout` when you only write — silently legal but confusing; prefer `&out` when you mean "I will write this"

```cpp
// WRONG — bare `out` is C# syntax, not AS
void get_view(out float width, out float height);

// WRONG — & at call site is C++ syntax
get_view(&vw, &vh);

// RIGHT — & at declaration, plain variable at call
void get_view(float &out width, float &out height);
get_view(vw, vh);
```

**Why:** AS's reference syntax is its own — neither C++ nor C#. Mixing them gives confusing errors. Pin the rule once: `&in` / `&out` / `&inout` go on the parameter declaration; the call site is plain.

---

## 6. `array<T>` Is the Container, Not `T[]`

**AngelScript's standard array is `array<T>`, registered as part of the array add-on (per `docs/perception/angelscript/overview.md`). Do not use `T[]` — that is Enma syntax.**

```cpp
// WRONG — Enma syntax
uint64[] entities;
entities.push(0x12345);

// RIGHT — AngelScript syntax
array<uint64> entities;
entities.insertLast(0x12345);              // not push — check array docs for full API
uint count = entities.length();             // length() returns uint
for (uint i = 0; i < count; i++) {
    log("ent " + i + " = 0x" + formatInt(entities[i], "X", 16));
}
```

The AS array methods are `insertLast`, `removeLast`, `insertAt`, `removeAt`, `length`, `resize`, `sortAsc`, `sortDesc`, `find` — not the Enma `push`/`pop`/`contains`/`slice` set. The signatures and return types come from the AS standard library and are documented in the AngelScript reference (search "array" in the AS docs); read it once when you need a method you haven't used.

**Why:** `T[]` is a compile error in PCX AS. Even if you remember `array<T>`, defaulting to Enma method names (`push`, `pop`) will fail. The script-helper exception messages are clear, but the time wasted on a 30-second lookup adds up across an editing session.

---

## 7. Use `dictionary` for Maps, Not `map<K,V>`

**`dictionary` is AS's string-keyed map. There is no generic `map<K,V>` in the registered surface (per `docs/perception/angelscript/overview.md`).**

```cpp
// WRONG — Enma map syntax
map<string, int32> counts;
counts.set("a", 1);
int32 v = counts.get("a");

// RIGHT — AS dictionary
dictionary counts;
counts["a"] = 1;
int v;
if (counts.get("a", v)) {                  // get returns bool; out-param the value
    log("a = " + v);
}
```

Dictionary keys are always `string`. Values are `any`-typed (stored as `?` boxed values); reading them requires the typed `get(key, out_value)` form to unbox correctly. If you need a non-string key, encode it as a string (`formatInt(addr, "X")` for addresses) or use parallel arrays.

**Why:** AS's type system doesn't carry through generic K/V parameters in the same way Enma's does. The boxed-`any` pattern via `dictionary` is the idiomatic substitute. Mis-typing the `get` form is the common error — always use the two-arg form with a typed output variable.

---

## 8. Render API Takes Raw RGBA Ints, Not `color` Structs

**The PCX AS render API is positional-args-style: pass red, green, blue, alpha as separate `uint8`-range integers (0-255). There is no `color` value type to wrap them in the way Enma does.**

```cpp
// WRONG — Enma-style color struct
color c(255, 100, 50, 200);
draw_rect_filled(10, 10, 100, 100, c, 4.0f, RR_ALL);

// RIGHT — raw rgba ints inline
draw_rect_filled(10.0f, 10.0f, 100.0f, 100.0f,
                 255, 100, 50, 200, 4.0f, RR_ALL);

// For text — same pattern with optional shadow color
uint64 font = get_font20();
draw_text("HUD", 10.0f, 10.0f,
          255, 255, 255, 255,                // fg rgba
          font, TE_SHADOW,
          0, 0, 0, 180,                       // shadow rgba
          1.0f, true);                        // shadow dist, centered
```

This means colors don't carry through assignments cleanly. If you need named colors, define them as four constants each:

```cpp
const uint8 FG_R = 255, FG_G = 200, FG_B = 50, FG_A = 255;
const uint8 BG_R =   0, BG_G =   0, BG_B =  0, BG_A = 180;

void on_tick(int id, int data_index) {
    draw_rect_filled(10.0f, 10.0f, 200.0f, 50.0f, BG_R, BG_G, BG_B, BG_A, 4.0f, RR_ALL);
    draw_text("HUD", 20.0f, 25.0f, FG_R, FG_G, FG_B, FG_A,
              get_font20(), TE_NONE, 0,0,0,0, 0.0f, false);
}
```

**Why:** The AS render API is wide-call-shaped intentionally — the marshaling cost to host C++ for a `color` struct would dominate the call. Accepting integers directly maps to a single C function call with stack arguments. Embrace the verbosity; it pays in performance and clarity.

---

## 9. `register_callback` — Two-Argument Callback Signature, Interval in Milliseconds

**Callbacks registered with `register_callback(fn, interval_ms, data_index)` are invoked with `void on_X(int id, int data_index)`. The id is the callback id from `register_callback`; data_index is the third arg you passed at registration, so one function can serve many registrations.**

```cpp
// Two callbacks, same function, different data_index — common pattern for
// running the same logic against multiple targets
int g_cb_fast = 0;
int g_cb_slow = 0;

int main() {
    g_cb_fast = register_callback(on_tick, 8,   0);  // ~120 Hz, data 0
    g_cb_slow = register_callback(on_tick, 100, 1);  // 10 Hz,   data 1
    return 1;
}

void on_tick(int id, int data_index) {
    if (data_index == 0) {
        // hot path — runs every 8 ms
        render_overlay();
    } else if (data_index == 1) {
        // cold path — runs every 100 ms
        refresh_entity_cache();
    }
}

void on_unload() {
    unregister_callback(g_cb_fast);
    unregister_callback(g_cb_slow);
}
```

The interval is in milliseconds and is a *minimum gap*, not a deadline — if your callback runs 12 ms and you asked for 8 ms, the next call is in 12 ms, not -4 ms backed up. Use `100`–`200` for cold-path entity refresh, `8`–`16` for render-frequency updates.

**Why:** Mis-binding the callback signature is a silent failure — the engine looks up the function by name+arity, and if your signature is wrong it either fails to register or registers a different function. `unregister_callback` in `on_unload` is mandatory for clean reloads; an un-unregistered callback survives the script unload and fires against a freed context, which crashes.

---

## 10. Hot Reload Boundaries — Globals Reset, Game State Doesn't

**AS scripts on PCX reload by tearing down the whole script context — globals reset, callbacks are released, the dictionary heap is rebuilt. The game process is untouched. Design your data flow around this.**

What survives a reload:
- The game process and its memory (you re-attach via `ref_process`)
- File-system state (if you persisted config to disk)
- The PCX engine and its GUI state

What does NOT survive a reload:
- Global variables (reset to declaration default)
- Registered callbacks (cleared; you must `register_callback` again in `main`)
- Cached pattern-scan results (re-resolve in `main` or first callback)
- Dictionary entries holding values (rebuilt from disk if you persist them)
- GUI section state (per-section configuration; the GUI API will re-create sections, but their widget states are reinitialized to your defaults)

```cpp
// Typical hot-reload-safe persistent script structure:
proc_t@ g_proc = null;
uint64  g_entity_list = 0;
int     g_cb = 0;

int main() {
    // Re-attach on every load
    @g_proc = ref_process("game.exe");
    if (g_proc is null || !g_proc.alive()) { return 0; }

    // Re-resolve sigs on every load (cheap relative to runtime cost of running)
    uint64 base = g_proc.base_address();
    uint64 size = g_proc.module_size("game.exe");
    uint64 hit  = g_proc.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0) { g_proc.deref(); return 0; }
    g_entity_list = resolve_rip(g_proc, hit, 3, 7);

    // Load config from disk if you persist it
    load_config();

    g_cb = register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload() {
    unregister_callback(g_cb);
    save_config();
    if (g_proc !is null) { g_proc.deref(); @g_proc = null; }
}
```

**Why:** A script that assumes globals survive a reload will read stale or zero data on its first callback after reload — your overlay draws nothing, or worse, against a freed process handle. Treat `main()` as the authoritative initializer that runs from scratch every time.

---

## Summary

| # | Rule | One-liner |
|---|---|---|
| 1 | AS is not Enma | Look up every API in `docs/perception/angelscript/` before pasting |
| 2 | Handles vs values | `proc_t@` not `proc_t`; null-check with `is null` |
| 3 | Always deref | Even when alive() is false; in `on_unload` for persistent scripts |
| 4 | `float` literals get `f` | `8.0f` not `8.0` — render APIs are float-typed |
| 5 | `&out` at declaration | Call site is plain variable, no `&` |
| 6 | `array<T>` not `T[]` | Methods are `insertLast` / `removeLast` / `length` |
| 7 | `dictionary` for maps | String keys only; `get(key, out_var)` two-arg form |
| 8 | Raw RGBA ints | No `color` struct; pass `r, g, b, a` separately |
| 9 | `register_callback` | Signature `void on_X(int id, int data_index)`; deregister in `on_unload` |
| 10 | Hot-reload safety | Re-attach, re-resolve, re-register every `main()` |

**The 12 game-cheat-guidelines rules still apply** — this skill is the *AngelScript-flavored* version of those discipline rules. Address types are `uint64`, null-check every read, separate update from render, sigs over hardcodes, one feature per file, minimize writes, validate against the live binary. Read `skill://game-cheat-guidelines` for the full discipline.

**Cross-references:** `skill://game-cheat-guidelines` (the 12 rules; Enma-flavored examples but principles apply), `skill://game-hacking-pcx` (doc router), `docs/perception/angelscript/overview.md` (registered modules and addons), `docs/perception/angelscript/proc-api.md`, `docs/perception/angelscript/render-api.md`, `docs/perception/angelscript/life-cycle.md`, `docs/perception/angelscript/gui-api.md`.

---

## Source: `.claude/skills/game-cheat-guidelines/SKILL.md`

---
name: game-cheat-guidelines
description: >
  Behavioral rules for writing Perception.cx scripts in Enma, AngelScript, and
  C++ for authorized reverse engineering, analysis, overlay rendering, and
  research. Derived from Karpathy principles: memory reading, visualization,
  hooking, render pipelines, and RE workflows. Always active — these rules
  apply every time you write or edit Perception.cx script code. Authorized use
  only — analyze software you own or are permitted to test.
license: MIT
---

# Perception.cx Script Development Guidelines

Behavioral rules for writing Perception.cx scripts in Enma, AngelScript, and C++. Derived from the Karpathy principles and rewritten for the domain: memory reading, visualization, overlay rendering, hooking, and reverse-engineering workflows on the Perception.cx platform. These rules originated in game-overlay development and apply equally to authorized reverse engineering, security research, and analysis — analyze only software you own or are authorized to test.

**Always active.** These rules apply every time you write or edit Perception.cx script code. They are not suggestions.

**Prerequisite:** The `game-hacking-pcx` skill MUST be loaded alongside this one. It contains the full doc index (33,580 lines across 99 files) for Enma, AngelScript, and all Perception.cx APIs. **Read the relevant doc before writing any API call** — see `skill://game-hacking-pcx` for the complete file-by-file index.

---

## 1. Know the Target Before You Touch Memory

**Never read or write a single byte until you know what you're reading.**

Before implementing any feature:
- State the game, engine, and binary you're targeting. Name the module.
- Identify whether offsets come from a sig scan, a hardcoded offset table, or the r5sdk/community SDK. Say which.
- If an offset is hardcoded, flag it: hardcoded offsets break on game updates. Prefer pattern scans.
- If the struct layout comes from a reversed SDK, cite the header file. If you guessed it, say "UNVERIFIED" and mark the offset.
- If you don't know the field size, read it as `ru64` and inspect — never assume `int32` vs `float32` without evidence.

```
Before: "Read player health at base+0x43E0"
After:  "r5sdk/src/game/server/player.h defines m_iHealth at 0x43E0 (int32).
         Sig for entity list: 48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ?? 8B 81
         Last verified: Season 21 patch 1.98"
```

**Why:** A wrong offset doesn't crash your script — it reads garbage silently. You'll spend an hour debugging ESP that draws at (0, 0) because the position field moved 8 bytes. Ground every offset.

---

## 2. Addresses Are `uint64`, Always

**One type for addresses. No exceptions. No `int64` addresses.**

- Every variable holding a memory address is `uint64`. Period.
- `proc.base_address()` returns `uint64`. Module bases are `uint64`. Pointer chain intermediates are `uint64`.
- If you must pass an address to a function taking `int64`, use `cast<int64>(addr)` at the call site, not at storage.
- Pattern scan results are `uint64`. Entity list pointers are `uint64`. VTable slots are `uint64`.

```cpp
// WRONG
int64 base = p.base_address();
int64 entity = p.r64(base + 0x1234);  // sign-extends high addresses, subtle corruption

// RIGHT
uint64 base = p.base_address();
uint64 entity = p.ru64(base + 0x1234);
```

**Why:** `int64` and `uint64` are implicitly convertible in Enma but sign-extend differently in pointer arithmetic. Kernel addresses and high-usermode addresses (Windows `0x7FF...`) turn negative in `int64`, breaking comparisons and offset math. One type, zero bugs.

---

## 3. Validate Before You Chain

**Every pointer in a chain can be null. Check it or crash.**

- After every `ru64` that produces a pointer, check for 0 before dereferencing.
- After `ref_process()`, check `.alive()` immediately.
- After `find_code_pattern()`, check for 0 — a missed sig means the offset table is stale.
- After `get_module_base()`, check for 0 — the module might not be loaded yet.
- `is_valid_address()` exists. Use it when chasing unknown pointer chains.

```cpp
// WRONG — entity_list could be 0 after a patch
uint64 entity_list = p.ru64(base + ENTITY_LIST_OFFSET);
uint64 entity = p.ru64(entity_list + i * 0x8);  // reads from address 0x0 + i*8 = garbage

// RIGHT
uint64 entity_list = p.ru64(base + ENTITY_LIST_OFFSET);
if (entity_list == 0) return;
uint64 entity = p.ru64(entity_list + i * 0x8);
if (entity == 0) continue;
```

**Why:** Failed reads return 0 silently in Perception. A null pointer in a chain doesn't crash — it reads from address `0 + offset`, which returns more zeros or garbage. Your ESP draws nothing or draws at (0,0) and you don't know why. Validate every link.

---

## 4. Separate Scan from Render

**Pattern scans and heavy reads happen once or on interval. Rendering happens every frame.**

Structure every script as:
1. **`main()`** — setup: process attach, pattern scans, resolve base addresses. Run once.
2. **Update routine** — read entity data, build display list. Runs on interval or every frame, but does NO drawing.
3. **Render routine** — draws from the cached display list. Runs every frame. Does NO memory reads.

```cpp
// Global state
proc_t g_proc;
uint64 g_entity_list;
vec3[] g_positions;

void on_update(int64 data) {
    // Read game state — separated from render
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 0x8);
        if (ent == 0) continue;
        g_positions[i] = g_proc.read_vec3_fl32(ent + POS_OFFSET);
    }
}

void on_render(int64 data) {
    // Draw from cache — no proc reads here
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        draw_circle(world_to_screen(g_positions[i]), 5.0, g_color_enemy, 1.0, true);
    }
}
```

**Why:** Mixing reads and draws makes every frame dependent on read latency. If the target process lags or a page is swapped out, your overlay stutters. Separating them means the render path is pure compute — smooth even when reads are slow. It also makes the code testable: you can verify reads independently from draw correctness.

---

## 5. Pattern Scans Over Hardcoded Offsets

**Sigs survive patches. Hardcoded offsets don't.**

- For any address that isn't a direct struct field offset from a known base, use `find_code_pattern`.
- The sig should be wide enough to be unique but not so wide it spans an instruction that changes per-build.
- Wildcard (`??`) the bytes that contain relocatable values: RIP-relative displacements, jump targets, immediate addresses.
- Store the sig as a named constant, not inline. Document what it finds.

```cpp
// Sig for CEntityList global pointer — LEA RCX, [rip+????]
// Wildcards on the 4-byte RIP displacement
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";

uint64 resolve_entity_list(proc_t& p, uint64 base, uint64 size) {
    uint64 hit = p.find_code_pattern(base, size, SIG_ENTITY_LIST);
    if (hit == 0) return 0;
    // Resolve RIP-relative: read 4-byte displacement at hit+3, add to hit+7
    int32 disp = p.r32(hit + 3);
    return hit + 7 + cast<uint64>(disp);
}
```

**Why:** Every game update shuffles code and data. A hardcoded offset `0x25AB3F0` is dead on the next patch. A sig for the instruction that loads that pointer survives unless the compiler changes the instruction pattern — which is rare. Name your sigs, document what instruction they match, and resolve RIP-relative displacements correctly (4 bytes, signed, added to the *end* of the instruction).

---

## 6. One Feature, One File

**Each feature lives in its own file. No god scripts.**

- ESP in `esp.em`. Aimbot in `aim.em`. Radar in `radar.em`. Config/GUI in `menu.em`.
- Shared state (process handle, entity cache, config values) goes in a `globals.em` module and is imported.
- If two features need the same data, extract it into a shared update routine — don't duplicate reads.

```
project/
├── globals.em      # proc_t, entity cache, config state
├── offsets.em      # all sigs and resolved addresses
├── esp.em          # render routine for boxes/names/health
├── aim.em          # aimbot logic + smoothing
├── menu.em         # GUI sidebar widgets
└── main.em         # main() — setup, register routines
```

**Why:** A 2000-line monolith means every edit risks breaking unrelated features. Separate files let you reload one feature without touching others (Perception supports hot reload). It also makes it trivial to disable a feature: just don't register its routine.

---

## 7. Construct Every Frame, Cache Nothing Graphical

**Colors, vec2 positions, and font handles from `get_font*()` are cheap. Construct them fresh.**

- `color(r, g, b, a)` is a 4-byte stack struct. Creating it costs nothing.
- `vec2(x, y)` is two floats. Creating it costs nothing.
- `get_font20()` returns a cached handle — calling it every frame is fine.
- Never cache a `color` or `vec2` in a global to "avoid allocation" — there is no allocation. Enma drops them at scope exit.

```cpp
// WRONG — premature "optimization" that adds global state for nothing
color g_white;
color g_red;
int64 g_font;

int64 main() {
    g_white = color(255, 255, 255, 255);
    g_red = color(255, 0, 0, 255);
    g_font = get_font20();
    // ...
}

// RIGHT — construct in the render function, zero overhead
void on_render(int64 data) {
    color white = color(255, 255, 255, 255);
    color red = color(255, 0, 0, 255);
    draw_text("ESP", vec2(10.0, 10.0), white, get_font20(), 0, color(0,0,0,0), 0.0);
}
```

**Why:** Enma's `[[packed]]` structs are stack-allocated value types. A `color` is 4 bytes on the stack — cheaper than a global load. Caching render primitives adds mutable global state that makes reasoning about the render path harder, for literally zero performance gain.

---

## 8. Float Literals Need the `f` Suffix

**`0.2` is `float64`. `0.2f` is `float32`. The GPU and the game don't agree on which you meant.**

- All `vec2`/`vec3`/`vec4` constructors that feed vertex buffers need `float32` — use `f` suffix.
- Screen coordinates from `get_view_width()`/`get_view_height()` return `float64` — that's fine for draw calls.
- `read_vec3_fl32` returns `float64` fields (promoted) — arithmetic is `float64`, no suffix needed.
- When writing back to game memory with `wf32()`, the value is narrowed — make sure your math didn't accumulate `float64` precision you'll silently lose.

```cpp
// Custom vertex buffer data — must be float32
float32 x = 10.0f;
float32 y = 20.0f;

// Draw calls accept float64 — no suffix needed
draw_line(vec2(10.0, 20.0), vec2(100.0, 200.0), white, 1.0);
```

---

## 9. Prefer Reads Over Writes

**Reads are non-invasive. Writes alter the target's state and are inherently riskier.**

- Analysis, visualization, entity inspection, distance display — all read-only. Prefer these.
- If you must write (patching for research on a target you own or are authorized to test, modifying your own single-player session), write the minimum bytes needed and know exactly why.
- Never `wvm` a large buffer when `wu32` or `wf32` on a single field suffices.
- After a research write, verify it took effect with a read-back; some targets revert unexpected patches.
- Gate all writes behind `write_memory` permission checks — Perception enforces this; respect it in your design too.

```cpp
// WRONG — nop-patching 16 bytes when you only need one field
array<uint8> nops = {0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90,0x90};
p.wvm(recoil_addr, nops);

// RIGHT — write the single float you actually mean to change, minimal footprint
p.wf32(recoil_spread_addr, 0.0f);
```

**Why:** Every memory write mutates the target's state — a read is observation, a write is intervention. For analysis and overlay work you almost never need to write, and when you do, a minimal, deliberate write is easier to reason about and roll back than a large patch. Treat writes as a last resort, not a default.

---

## 10. World-to-Screen Is Math, Not Magic

**Implement W2S correctly once. Never approximate it.**

The formula depends on the engine's view matrix layout. For Source Engine (Apex, CS2, TF2):

```cpp
// Source Engine uses a 4x3 view matrix (3 rows of 4 floats = 48 bytes)
// Row 0: right.x, right.y, right.z, right.w
// Row 1: up.x,    up.y,    up.z,    up.w
// Row 2: fwd.x,   fwd.y,   fwd.z,   fwd.w

bool world_to_screen(vec3 world, out vec2 screen, float64 matrix_addr) {
    // Read 12 floats from the view matrix
    float64 w = m[3]*world.x + m[7]*world.y + m[11]*world.z + m[15]; // not present in 4x3 — check engine
    if (w < 0.001) return false;  // behind camera

    float64 inv_w = 1.0 / w;
    float64 nx = (m[0]*world.x + m[4]*world.y + m[8]*world.z + m[12]) * inv_w;
    float64 ny = (m[1]*world.x + m[5]*world.y + m[9]*world.z + m[13]) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2(
        (vw * 0.5) + (nx * vw * 0.5),
        (vh * 0.5) - (ny * vh * 0.5)
    );
    return true;
}
```

**Rules:**
- Always check `w > 0` (or a small epsilon) — behind-camera points produce mirrored coordinates.
- Read the matrix from the game's actual view matrix address, not a reconstructed one.
- Match the matrix layout to the engine. Source uses column-major 4x4, Unreal uses row-major, Unity uses column-major with flipped Z.
- Implement it once in a shared module. Every feature imports it.

---

## 11. GUI State Is Config, Not Code

**Every tunable goes through the GUI API. No magic constants buried in logic.**

- Bind every threshold, color, toggle, and hotkey to a GUI widget in a sidebar section.
- Use `section_checkbox` for feature toggles, `section_slider_float` for distances/smoothing, `section_keybind` for hotkeys.
- Read widget state at the top of each routine, then branch on it. Don't mix widget reads deep inside nested loops.
- Persist config to a file via the filesystem API. Load it in `main()`.

```cpp
bool g_esp_enabled;
float64 g_esp_distance;
color g_esp_color;

void setup_gui() {
    int64 sec = create_section("ESP");
    section_checkbox(sec, "Enable ESP", g_esp_enabled);
    section_slider_float(sec, "Max Distance", g_esp_distance, 0.0, 5000.0);
    // color picker, keybind, etc.
}
```

**Why:** Hardcoded thresholds mean recompiling to tweak. The overlay is your debugger — every value you might change during a session should be adjustable live. This also means someone else can use your script without reading the source.

---

## 12. Verify With the Binary, Not With Your Memory

**The IDB, the sig, and the live read must agree. If they don't, trust the live read.**

When something doesn't work:
1. Check the sig still hits in the current binary: `find_code_pattern` returns 0? Offset table is stale.
2. `struct_dump` the entity at the base you have — verify the field layout visually.
3. Cross-reference against the r5sdk headers or IDA's type info, but remember the SDK may be from an older season.
4. If the live read shows a valid-looking float where you expected an int, the struct changed. Update your types.
5. Never assume your cached offset table is correct after a game update. Re-scan everything.

```
Debugging checklist:
1. Is the process alive?           → p.alive()
2. Is the module loaded?           → get_module_base() != 0
3. Does the sig still hit?         → find_code_pattern() != 0
4. Is the pointer chain valid?     → check every link for 0
5. Does the field contain what     → struct_dump() or read + print
   you expect?
```

---

## Summary

| # | Rule | One-liner |
|---|------|-----------|
| 1 | Know the target | Ground every offset in evidence |
| 2 | `uint64` addresses | One type, zero sign bugs |
| 3 | Validate chains | Every pointer can be null |
| 4 | Separate scan/render | Reads and draws don't mix |
| 5 | Sigs over hardcodes | Survive patches |
| 6 | One feature, one file | No god scripts |
| 7 | Construct every frame | Colors and vecs are free |
| 8 | `f` suffix for float32 | The GPU cares |
| 9 | Prefer reads over writes | Reads are non-invasive |
| 10 | W2S once, correctly | Math, not magic |
| 11 | GUI for all tunables | No magic constants |
| 12 | Verify with the binary | Trust live reads over memory |

---

## Source: `.claude/skills/game-hacking-pcx/SKILL.md`

---
name: game-hacking-pcx
description: >
  Mandatory doc router for all PCX scripting sessions. Triggers on any game
  hacking, Enma, AngelScript, or Perception.cx work. Provides the full doc
  index (43,000+ lines across 139 files) and enforces reading the relevant
  documentation before writing any API call. Load alongside
  game-cheat-guidelines on every PCX session.
license: MIT
---

# Game Hacking & Scripting — Perception.cx / Enma / AngelScript / C++

## Trigger
Game hacking, game cheats, memory reading/writing, ESP, aimbot, pattern scanning, vtable hooking,
process manipulation, Enma scripting, AngelScript scripting, Perception.cx, PCX, render overlays,
any `.em` or `.as` game script work, or any mention of the Perception platform.

## MANDATORY: Read Before Writing Code

**You MUST read the relevant docs from `docs/` before writing ANY Enma, AngelScript,
or PCX API code.** Do not write from memory. The docs are the source of truth.

### When writing Enma (.em) code — read these:

**Language (always read `llms-language.md` first — it's the complete single-page reference):**
| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Complete language ref** | `docs/enma/llms-language.md` | 2861 | Every type, operator, control flow, struct, class, template, coroutine, exception, heap, FFI, annotation, module, addon |
| Complete SDK ref | `docs/enma/llms-sdk.md` | 832 | Embedding API, type registration, native functions, hot reload |

**Language guide (granular pages if you need detail beyond the single-page ref):**
| Doc | Path | Lines |
|-----|------|-------|
| Basics (types, vars, operators, control flow) | `docs/enma/lang-basics.md` | 267 |
| Functions (params, defaults, refs, out, variadic, lambdas) | `docs/enma/lang-functions.md` | 247 |
| Pointers (heap, address-of, member access, null) | `docs/enma/lang-pointers.md` | 357 |
| Structs & Classes (value/ref types, inheritance, vtable, interfaces, mixins) | `docs/enma/lang-structs-and-classes.md` | 912 |
| Templates (generics, monomorphization) | `docs/enma/lang-templates.md` | 173 |
| Advanced (delegates, namespaces, coroutines, exceptions, smart ptrs, FFI) | `docs/enma/lang-advanced.md` | 562 |
| Annotations (packed, align, reflect, serialize, export, dll, custom) | `docs/enma/lang-annotations.md` | 209 |
| Modules (import, .emb, multi-module linking) | `docs/enma/lang-modules.md` | 100 |
| Preprocessor (#define, #ifdef, #include, #pragma) | `docs/enma/lang-pre-processor.md` | 77 |
| Semantics & Limits (guarantees, compile-time rejects, what doesn't exist) | `docs/enma/lang-semantics-and-limits.md` | 181 |

**Addons (standard library — read the addon doc before using its types):**
| Addon | Path | Lines | Key types/functions |
|-------|------|-------|---------------------|
| Core | `docs/enma/addon-core.md` | 42 | `println`, `print` |
| Strings | `docs/enma/addon-strings.md` | 165 | `format`, `to_int`, `split`, `replace`, `substr` |
| Arrays | `docs/enma/addon-arrays.md` | 119 | `push`, `pop`, `sort`, `contains`, `slice`, `for-each` |
| Maps | `docs/enma/addon-maps.md` | 200 | `map<K,V>`, `get`, `set`, `contains`, `imap<V>` |
| Math | `docs/enma/addon-math.md` | 137 | `sin`, `cos`, `atan2`, `sqrt`, `clamp`, `lerp`, `random` |
| SIMD | `docs/enma/addon-simd.md` | 128 | SSE2 `f32x4`, `i32x4` vector ops |
| Vectors | `docs/enma/addon-vec.md` | 135 | `vec2`, `vec3`, `vec4` math types |
| 3D Math | `docs/enma/addon-math3d.md` | 182 | `quat`, `mat4` rotation/transform |
| Variant | `docs/enma/addon-variant.md` | 130 | Type-erased value container |
| Atomic | `docs/enma/addon-atomic.md` | 94 | `aint32`, `aint64` atomic ops |
| Bits | `docs/enma/addon-bits.md` | 117 | `popcount`, `clz`, `ctz`, `bswap`, `rotl` |
| Time | `docs/enma/addon-time.md` | 95 | `time_ms()`, `time_us()`, ISO 8601, `sleep` |
| Regex | `docs/enma/addon-regex.md` | 61 | `match`, `find`, `replace`, `split`, capture groups |
| File | `docs/enma/addon-file.md` | 125 | Sandboxed file I/O (permission-gated) |
| Thread | `docs/enma/addon-thread.md` | 120 | `mutex`, `lock_guard`, `condition_variable` |
| Hash Set | `docs/enma/addon-hash_set.md` | 89 | `hash_set<T>` |
| Sorted Map | `docs/enma/addon-sorted_map.md` | 89 | `sorted_map<K,V>` ordered iteration |
| List | `docs/enma/addon-list.md` | 192 | Double-ended O(1) push/pop |
| JSON | `docs/enma/addon-json.md` | 108 | `json_parse`, `json_stringify`, `json_value` navigation |

**SDK (C++ embedding — read when building host-side or custom addons):**
| Doc | Path | Lines |
|-----|------|-------|
| Quick Start | `docs/enma/sdk-quick-start.md` | 126 |
| Engine Lifecycle | `docs/enma/sdk-engine-lifecycle.md` | 166 |
| Compilation | `docs/enma/sdk-compilation.md` | 65 |
| Execution | `docs/enma/sdk-execution.md` | 103 |
| Calling Functions | `docs/enma/sdk-calling-functions.md` | 82 |
| Globals | `docs/enma/sdk-globals.md` | 79 |
| Type Registration | `docs/enma/sdk-type-registration.md` | 862 |
| Native Functions | `docs/enma/sdk-native-functions.md` | 446 |
| Hot Reload | `docs/enma/sdk-hot-reload.md` | 64 |
| Serialization & Linking | `docs/enma/sdk-serialization-and-linking.md` | 97 |
| Introspection | `docs/enma/sdk-introspection.md` | 317 |
| Lifecycle & RAII | `docs/enma/sdk-lifecycle.md` | 227 |
| Debug & Heap | `docs/enma/sdk-debug-and-gc.md` | 202 |
| Error Handling | `docs/enma/sdk-error-handling.md` | 116 |
| Safety | `docs/enma/sdk-safety.md` | 121 |
| Custom Addons | `docs/enma/sdk-custom-addons.md` | 576 |
| API Reference | `docs/enma/sdk-api-reference.md` | 411 |

### When writing PCX Enma API code — read the relevant API doc:

| API | Path | Lines | Use for |
|-----|------|-------|---------|
| **Proc API** | `docs/perception/proc-api.md` | 294 | Memory read/write, modules, pattern scan, VAD, pointer arrays, vec/quat/mat reads |
| **Render API** | `docs/perception/render-api.md` | 264 | 2D drawing (text, lines, circles, rects), fonts, shaders, vertex/index buffers, compute |
| **GUI API** | `docs/perception/gui-api.md` | 455 | Sidebar sections, checkboxes, sliders, buttons, text inputs, color pickers, keybinds |
| **Input API** | `docs/perception/input-api.md` | 126 | Mouse + keyboard state polling |
| **CPU API** | `docs/perception/cpu-api.md` | 92 | CPU ID, timing, datetime, bitcasts, thread priority |
| **Zydis API** | `docs/perception/zydis-api.md` | 133 | x86-64 assembler/disassembler |
| **Unicorn API** | `docs/perception/unicorn-api.md` | 151 | x86-64 CPU emulation |
| **Net API** | `docs/perception/net-api.md` | 200 | HTTP, WebSocket, raw UDP |
| **Win API** | `docs/perception/win-api.md` | 120 | Window enum, clipboard, keyboard/mouse send |
| **Filesystem API** | `docs/perception/filesystem-api.md` | 162 | Sandboxed file I/O |
| **Sound API** | `docs/perception/sound-api.md` | 90 | WAV/OGG playback |
| **Lifecycle** | `docs/perception/lifecycle-and-routines.md` | 134 | main(), routines, unload, exceptions |
| **MCP API** | `docs/perception/mcp-api.md` | 268 | AI agent JSON-RPC surface |

### When writing core AngelScript (.as) code — read the language manual:

| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Language Index** | `docs/angelscript-lang/INDEX.md` | - | Overview of the core language, data types, statements, etc. |
| Datatypes | `docs/angelscript-lang/datatypes.md` | 17 | Landing page for primitives, objects, and handles |
| Handles | `docs/angelscript-lang/handles.md` | - | Core AngelScript `@` object handles and memory management |
| Script Classes | `docs/angelscript-lang/script-class.md` | - | User-defined classes, members, and methods |
| Expressions | `docs/angelscript-lang/expressions.md` | - | Math, logic, assignments, and operator precedence |
| Statements | `docs/angelscript-lang/statements.md` | - | If, switch, loops, try/catch |

### When writing PCX AngelScript (.as) code — read these:

| API | Path | Lines |
|-----|------|-------|
| Overview | `docs/perception/angelscript/overview.md` | 68 |
| Life Cycle | `docs/perception/angelscript/life-cycle.md` | 128 |
| Engine | `docs/perception/angelscript/engine.md` | 178 |
| Atomic Types | `docs/perception/angelscript/atomic-types.md` | 185 |
| Proc API | `docs/perception/angelscript/proc-api.md` | 1156 |
| Render API | `docs/perception/angelscript/render-api.md` | 1829 |
| GUI API | `docs/perception/angelscript/gui-api.md` | 718 |
| Input API | `docs/perception/angelscript/input-api.md` | 226 |
| System/CPU/Disasm | `docs/perception/angelscript/system-api-cpu-and-disassembly.md` | 304 |
| Net API | `docs/perception/angelscript/net-api.md` | 379 |
| File System | `docs/perception/angelscript/file-system.md` | 298 |
| Extended Math | `docs/perception/angelscript/extended-math-api.md` | 580 |
| Win API | `docs/perception/angelscript/win-api.md` | 594 |
| JSON API | `docs/perception/angelscript/json-api.md` | 479 |
| Unicorn | `docs/perception/angelscript/unicorn.md` | 702 |
| Zydis Encoder | `docs/perception/angelscript/zydis-encoder.md` | 703 |
| Intrinsics | `docs/perception/angelscript/intrinsics.md` | 661 |
| Mutex API | `docs/perception/angelscript/mutex-api.md` | 248 |
| Utilities | `docs/perception/angelscript/utilities.md` | 607 |
| Sound API | `docs/perception/angelscript/sound-api.md` | 250 |
| Bit Reinterpret | `docs/perception/angelscript/bit-reinterpret-helpers.md` | 167 |
| Engine Specific | `docs/perception/angelscript/engine-specific-api.md` | 195 |
| CS2 Extended | `docs/perception/angelscript/cs2-extended-api.md` | 165 |

### PCX IDE & Extensions:

| Doc | Path | Lines |
|-----|------|-------|
| Perception IDE | `docs/perception/ide.md` | 585 |
| Extensions API | `docs/perception/extensions-api.md` | 371 |
| Analyzer | `docs/perception/analyzer.md` | 370 |

### When writing core Lua (.lua) code — read the language manual:

| Doc | Path | Lines | Content |
|-----|------|-------|---------|
| **Reference Manual** | `docs/lua-lang/manual-5.4.md` | 6056 | Full, authoritative Lua 5.4 reference manual |
| Welcome & Readme | `docs/lua-lang/readme-5.4.md` | 150 | Lua 5.4 readme and changes |

### PCX Lua (.lua) scripting:

| API | Path | Lines |
|-----|------|-------|
| Overview | `docs/perception/lua/overview.md` | 59 |
| All APIs | `docs/perception/lua/*.md` | 5779 total |

## How To Use These Docs

1. **Before writing Enma code**: `read docs/enma/llms-language.md` (the single-page complete ref)
2. **Before calling a PCX API**: `read docs/perception/<api-name>.md`
3. **Before writing AngelScript**: `read docs/perception/angelscript/<api-name>.md`
4. **If unsure about a type, function, or parameter**: read the doc, don't guess
5. **If the doc says a function is "gated"**: it requires a permission flag — mention this to the user

## Critical Enma Rules (from the docs)

- **Addresses are `uint64`**, never `int64` — sign-extension breaks high addresses
- **`float32` literals need `f` suffix**: `0.2f` not `0.2`
- **Implicit conversion: `int→float` OK, `float→int` COMPILE ERROR** — use `cast<int32>(f)`
- **`signed↔unsigned` is COMPILE ERROR** — use `cast<uint64>(signed_val)`
- **`color` and `vec2` are value types** — 4-byte and 8-byte stack structs, construct every frame
- **Handles from `create_*`/`load_*` are encrypted `int64`** — pass back, don't inspect
- **`main()` returns `> 0` to stay loaded, `<= 0` to unload**
- **Routines registered via `register_routine(cast<int64>(fn), data)`**
- **`proc_t` released on scope exit** (RAII) — no leak if you use stack variables
- **Failed reads return 0**, not exceptions — validate pointers
- **Pattern sigs**: hex bytes, `??` wildcard, e.g. `"48 8B 05 ?? ?? ?? ?? 48 85 C0"`
- **`import "vec"; import "color";`** — modules must be imported to use their types
- **`string` interpolation**: `f"value={x}"` — use `format()` for hex: `format("0x{x}", addr)`
- **No garbage collector** — deterministic RAII, destructors run at scope exit

## LSP Servers (built, ready to use)

- **Enma LSP**: `lsp/enma-lsp/server/dist/server.js`
- **AngelScript+PCX LSP**: `lsp/angel-lsp-pcx/server/out/server.js`

## RE Tools & Knowledge

- **Plugins & FLIRT sigs**: `knowledge/re-plugins-and-tools.md` — 6 IDA plugins, 4 Ghidra extensions, 51 FLIRT sigs, diffing, ret-sync
- **Anti-cheat architecture**: `knowledge/anti-cheat-architecture.md` — EAC/BE/Vanguard/GG detection matrix
- **Kernel RE tools**: `knowledge/kernel-re-tools.md` — WinDbg, HyperDbg, Volatility, PCILeech, IRPMon
- **AC driver patterns**: `signatures/anti-cheat/common-ac-patterns.md` — driver ID, callback sigs, integrity check patterns
- **Deobfuscation**: `skill://deobfuscation` — VM/CFF/packer reversal methodology (Themida, VMProtect, OLLVM)
- **Obfuscation taxonomy**: `knowledge/obfuscation-taxonomy.md` — protector architecture and weaknesses
- **Deobfuscation tools**: `knowledge/deobfuscation-tools.md` — NoVmp, Triton, Miasm, D-810, ScyllaHide, FLOSS
- **Protector patterns**: `signatures/obfuscation/protector-patterns.md` — VMP/Themida/OLLVM section names, dispatcher patterns, anti-debug
- r5sdk: `sdks/r5sdk/` (2438 reversed headers for Apex Legends)
- IDA IDB: `idb/r5apex_dx12_dump.i64` (28936 functions, FLIRT+types)
- Ghidra: `ghidra-projects/r5apex/`
- radare2, Ghidra, semgrep MCP servers all available

---

## Source: `knowledge/pcx-api-cheatsheet.md`

# Perception.cx Enma API Quick Reference

All natives are auto-registered. No import needed (except `import "vec"; import "color";` for those types).

## Proc API — Process Memory

```cpp
proc_t p = ref_process("game.exe");       // by name
proc_t p = ref_process(1234);              // by PID
bool alive = p.alive();
uint64 base = p.base_address();
uint64 peb  = p.peb();
uint32 pid  = p.pid();
bool valid  = p.is_valid_address(addr);
```

### Read Primitives
```cpp
uint8/16/32/64  p.ru8/ru16/ru32/ru64(uint64 addr);
int8/16/32/64   p.r8/r16/r32/r64(uint64 addr);
float32         p.rf32(uint64 addr);
float64         p.rf64(uint64 addr);
string          p.rs(uint64 addr, int32 max_chars);    // ASCII
string          p.rws(uint64 addr, int32 max_chars);   // UTF-16→UTF-8
array<uint8>    p.rvm(uint64 addr, uint64 size);       // bulk
```

### Write Primitives (gated: `write_memory`)
```cpp
bool p.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
bool p.w8/w16/w32/w64(uint64 addr, intN v);
bool p.wf32(uint64 addr, float32 v);
bool p.wf64(uint64 addr, float64 v);
bool p.wvm(uint64 addr, array<uint8> bytes);
```

### Typed Reads (vec/quat/mat)
```cpp
vec2 p.read_vec2_fl32(uint64 addr);     // also: _fl64 variant
vec3 p.read_vec3_fl32(uint64 addr);
vec4 p.read_vec4_fl32(uint64 addr);
quat p.read_quat_fl32(uint64 addr);
mat4 p.read_mat4_fl32(uint64 addr);
// write variants: p.write_vec3_fl32(addr, v), etc. (gated)
```

### Modules
```cpp
uint64                base = p.get_module_base("module.dll");
uint64                size = p.get_module_size("module.dll");
array<module_info_t>  mods = p.get_module_list();
uint64                exp  = p.get_proc_address(base, "ExportName");
uint64                imp  = p.get_import_rdata_address(base, "ImportName");
// module_info_t: .name(), .base(), .size()
```

### Pattern Scanning
```cpp
uint64 hit = p.find_code_pattern(start, size, "48 8B 05 ?? ?? ?? ?? 48 85 C0");
array<uint64> hits = p.find_all_code_patterns(start, size, sig);
```

### Memory Scanning
```cpp
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
array<uint64> p.scan_u64(value, heap_only);
array<uint64> p.scan_u32(value, heap_only);
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
```

### VAD / Virtual Query
```cpp
vad_region_t r = p.virtual_query(addr);       // .start(), .size(), .protection()
array<vad_region_t> snap = p.get_vad_snapshot(heap_only);
```

### VM Alloc/Free (gated: `virtual_memory_operations`)
```cpp
uint64 page = p.alloc_vm(4096);
bool ok = p.free_vm(page);
```

## Render API — 2D Drawing

```cpp
import "vec";
import "color";

// Primitives
draw_line(vec2 a, vec2 b, color c, float64 thickness);
draw_rect(vec2 pos, vec2 size, color c, float64 thickness, float64 rounding, uint8 flags);
draw_rect_filled(vec2 pos, vec2 size, color c, float64 rounding, uint8 flags);
draw_circle(vec2 center, float64 radius, color c, float64 thickness, bool filled);
draw_arc(vec2 center, vec2 radii, float64 start, float64 sweep, color c, float64 thick, bool filled);
draw_triangle(vec2 a, vec2 b, vec2 c, color col, float64 thickness, bool filled);
draw_text(string text, vec2 pos, color c, int64 font, int32 effect, color effect_c, float64 effect_amt);
draw_bitmap(int64 bmp, vec2 pos, vec2 size, color tint, bool rounded);

// effect: 0=none, 1=shadow, 2=outline
// rounding_flags: bitmask, 15=all corners

// Fonts
int64 get_font18(); int64 get_font20(); int64 get_font24(); int64 get_font28();
int64 create_font(string path, float64 size, bool aa, bool color, array ranges);
float64 get_text_width(int64 font, string text, int32 maxw, int32 maxh);
float64 get_text_height(int64 font, string text, int32 maxw, int32 maxh);

// Viewport
float64 get_view_width();  float64 get_view_height();
float64 get_view_scale();  float64 get_fps();

// Clipping
clip_push(vec2 pos, vec2 size); clip_pop();

// Shaders (layout: "POSITION:0:FLOAT2, COLOR:0:FLOAT4")
int64 create_shader(string vs, string ps, string layout);
int64 create_compute_shader(string cs);

// Buffers
int64 create_vertex_buffer(uint32 stride, uint32 max, bool dynamic);
int64 create_index_buffer(uint32 max, bool use32, bool dynamic);
int64 create_constant_buffer(uint32 size);
```

## GUI API — Sidebar Widgets

```cpp
int64 sec = create_section("Section Name");
section_checkbox(sec, "Label", bool_ref);
section_slider_float(sec, "Label", float_ref, min, max);
section_slider_int(sec, "Label", int_ref, min, max);
section_button(sec, "Label", callback_fn);
section_text_input(sec, "Label", string_ref);
section_keybind(sec, "Label", key_ref);
section_color_picker(sec, "Label", color_ref);
section_dropdown(sec, "Label", index_ref, items_array);
section_label(sec, "Text");
section_separator(sec);
```

## Input API

```cpp
bool key_down       (int64 vk);      // host-debounced down state
bool key_raw_down   (int64 vk);      // OS-level pressed state
bool key_fired      (int64 vk);      // up->down this frame (one-shot)
bool key_toggle     (int64 vk);      // caps-lock-style toggle
bool key_singlepress(int64 vk);      // fired but suppressed if modifiers held
bool key_prev_down  (int64 vk);      // down state from previous frame

key_state_t  get_key_state(int64 vk); // atomic snapshot of all 6 flags
array<int32> get_keys_down();         // virtual-key codes currently pressed
string       get_recent_key_input();  // buffered text input (UTF-8)
string       get_key_name(int64 vk);  // localized key name (e.g. "F1")

vec2 get_mouse_pos();                 // render-window pixels
vec2 get_mouse_pos_desktop();         // desktop pixels (full screen)
vec2 get_mouse_delta();               // raw movement this frame
vec2 get_mouse_delta_desktop();       // desktop-space delta this frame
bool mouse_movement_received();       // any movement this frame
bool is_hovered(vec2 pos, vec2 size); // mouse inside rect
float64 get_scroll_delta();           // wheel ticks; positive = up
```

## CPU API

```cpp
string get_cpu_vendor();
float64 time_ms();     // monotonic milliseconds
float64 time_us();     // monotonic microseconds
int32 get_datetime_year/month/day/hour/minute/second();
```

## Zydis API — x86-64 Disassembler/Assembler

```cpp
zydis_insn_t insn = zydis_decode(bytes_array, addr);
// insn.mnemonic, insn.length, insn.operands[]
array<uint8> encoded = zydis_encode(mnemonic, operands);
```

## Unicorn API — x86-64 Emulation

```cpp
int64 uc = uc_create();
uc_mem_map(uc, addr, size, perms);
uc_mem_write(uc, addr, bytes);
uc_reg_write(uc, reg_id, value);
uc_emu_start(uc, begin, until, timeout, count);
uint64 val = uc_reg_read(uc, reg_id);
array<uint8> data = uc_mem_read(uc, addr, size);
uc_destroy(uc);
```

## Net API

```cpp
string body = http_get(url, headers_map);
string body = http_post(url, post_body, headers_map);
int64 ws = ws_connect(url); ws_send(ws, msg); string r = ws_recv(ws);
int64 sock = udp_create(); udp_send(sock, host, port, data); udp_recv(sock, buf, timeout);
```

## Win API

```cpp
array<window_t> wins = enum_windows();
// window_t: .hwnd(), .title(), .class_name(), .pid(), .rect()
send_key(int32 vk, bool down);
send_mouse(int32 button, bool down, int32 x, int32 y);
string clip = get_clipboard(); set_clipboard(text);
```

## Filesystem API

```cpp
string content = read_file(path);
bool ok = write_file(path, content);
bool exists = file_exists(path);
array<string> entries = list_dir(path);
bool ok = create_dir(path);
bool ok = delete_file(path);
```

## Sound API

```cpp
int64 snd = load_sound(path);   // .wav or .ogg
play_sound(snd);
```

## Lifecycle

```cpp
int64 main() {
    // return > 0 to stay loaded, <= 0 to unload
    register_routine(cast<int64>(my_fn), user_data);
    return 1;
}
void my_fn(int64 data) { /* called every frame */ }
unregister_routine(handle);
```

---

# New API Additions (Feb–June 2026 Changelogs)

## Custom Draw API — Direct GPU Access (D3D11)

Full custom shader pipeline on the Universal API. Write HLSL, create vertex
buffers, textures, render targets, depth buffers, and draw any primitive
topology directly from AngelScript/Enma. Custom draw commands respect draw
order with every existing render function. All resources are tracked
per-script and auto-cleaned on unload.

### Resource Creation (all return `uint64` handle, `0` on failure)
```cpp
uint64 create_shader(string vs_source, string ps_source, string layout);
uint64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
uint64 create_index_buffer(uint32 max_indices, bool is_32bit, bool dynamic);
uint64 create_constant_buffer(uint32 size);
uint64 create_blend_state(src, dst, op, src_alpha, dst_alpha, op_alpha);
uint64 create_sampler(filter, address_u, address_v);
uint64 create_texture(uint32 width, uint32 height, array<uint8> rgba_data);
uint64 create_render_target(uint32 width, uint32 height);
uint64 create_depth_buffer(uint32 width, uint32 height);
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func);
uint64 create_rasterizer_state(int fill_mode, int cull_mode);
```

### Drawing
```cpp
custom_draw(shader, vb, data, vertex_count, topology,
            blend, sampler, texture, rt, cb, cb_data, cb_slot);
custom_draw_indexed(shader, vb, vert_data, vert_stride,
                    ib, index_data, index_count, topology,
                    blend, sampler, texture, rt, cb, cb_data, cb_slot);
```

### Render Target Operations
```cpp
custom_set_render_target(rt);
custom_set_render_target_ext(rt, depth_buffer);
custom_clear_render_target(rt, r, g, b, a);
custom_clear_depth_buffer(db);
custom_resolve_render_target(rt);     // copy RT -> backbuffer
```

### State Management
```cpp
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs);
custom_set_viewport(x, y, w, h);                          // split-screen / PiP
custom_bind_textures(shader, slot0_tex, slot1_tex, ...);  // multi-texture
custom_bind_constant_buffers(shader, slot, cb, cb_data, cb_size);
```

### Mesh & Texture Loading
```cpp
load_obj_mesh(path);                  // returns vb + ib handles
create_texture_from_file(path);
create_dynamic_texture(width, height);
update_dynamic_texture(tex, rgba_data);
```

### Compute Shaders
```cpp
uint64 cs  = create_compute_shader(cs_source);
uint64 buf = create_structured_buffer(element_size, element_count, data);
dispatch_compute(cs, groups_x, groups_y, groups_z);
read_structured_buffer(buf);
```

### Backbuffer Capture
```cpp
uint64 tex = capture_backbuffer();    // texture handle of current frame
```

### Constants
```cpp
// Topology
TOPO_POINT_LIST, TOPO_LINE_LIST, TOPO_LINE_STRIP,
TOPO_TRIANGLE_LIST, TOPO_TRIANGLE_STRIP

// Compare funcs (depth stencil)
CMP_NEVER, CMP_LESS, CMP_EQUAL, CMP_LESS_EQUAL,
CMP_GREATER, CMP_NOT_EQUAL, CMP_GREATER_EQUAL, CMP_ALWAYS

// Fill modes
FILL_WIREFRAME, FILL_SOLID

// Cull modes
CULL_NONE, CULL_FRONT, CULL_BACK
```

### Layout String Format
Comma-separated `SEMANTIC:slot:TYPE` entries, e.g.
`"POSITION:0:FLOAT2, COLOR:0:FLOAT4"`.

### Key Features
- Indexed rendering with 16-bit and 32-bit index formats
- True 3D depth testing with configurable depth-stencil state
- Rasterizer state control (culling, wireframe)
- Custom viewports for split-screen / picture-in-picture
- Multi-texture and multi-constant-buffer binding
- Compute shaders with structured buffers
- OBJ mesh loading + dynamic texture updates
- Depth-enabled render targets, backbuffer capture for post-processing

### Example: Basic Colored Triangle
```angelscript
string vs = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj);
    o.col = i.col;
    return o;
}
""";

string ps = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

uint64 shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
uint64 vb = create_vertex_buffer(24, 3, true);
uint64 blend = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

### Example: Depth-Tested 3D Scene
```angelscript
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);

custom_set_render_target_ext(rt, db);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
```

## World-to-Screen (updated Feb 2026)

```cpp
bool world_to_screen_rowmajor(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
bool world_to_screen_transposed(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
```
- Use `world_to_screen_rowmajor` for row-major view matrices.
- Use `world_to_screen_transposed` for transposed (column-major) matrices.
- ⚠️ **DEPRECATED:** `source2_world_to_screen` — replace with the variants above.

## Matrix4x4 Double Precision (Feb 2026)

```cpp
mat4 m.readas_float(uint64 addr);      // float-precision read
mat4 m.readas_double(uint64 addr);     // double-precision read
bool m.writeas_float(uint64 addr, mat4 v);
bool m.writeas_double(uint64 addr, mat4 v);
```
- ⚠️ **DEPRECATED:** default `matrix4x4` read/write — use a precision-specific variant.

## Thread Priority Helpers (Feb 2026)

```cpp
set_thread_to_highest_priority();
set_thread_to_lowest_priority();
set_thread_to_normal_priority();
```

## Atomics (Feb 2026)

```cpp
atomic_int32 a;    // lock-free thread-safe 32-bit integer
atomic_int64 b;    // lock-free thread-safe 64-bit integer
```

## GUI Additions (Feb–Mar 2026)

```cpp
get_gui_position(float &out x, float &out y);   // GUI window position
get_gui_size(float &out w, float &out h);       // GUI window size

// List widget ops
list:get(...);              list:remove(...);
list:highlight(...);        list:remove_highlight(...);
list:hide(...);             list:show(...);
```

## Callbacks (Mar 2026)

```cpp
register_callback(string name, func, bool render_on_top = false);
// render_on_top=true renders on top of everything else
```

## Window Additions (Feb 2026)

```cpp
array<uint64> hwnds = get_all_hwnds();   // all window handles
```

## Fonts (Feb 2026)

```cpp
int64 create_font(string name, float64 size, array glyph_ranges);       // glyph_ranges optional
int64 create_font_mem(array<uint8> data, float64 size, array glyph_ranges); // glyph_ranges optional
```

## Input Additions (Feb 2026)

- Controller keybinds via **XINPUT** now supported.
- `get_mouse_delta()` now returns proper movement delta (fixed).

## Unicorn Emulator Updates (Mar 2026)

```cpp
// New hook types
UC_HOOK_INSN_INVALID    // invalid instructions
UC_HOOK_INTR            // software interrupts (INT3, syscalls)

uint64 status = uc_get_last_exception(uc);     // NTSTATUS, e.g. 0xC0000005
uint64 rip    = uc_get_exception_address(uc);  // RIP where exception occurred
```
- Null pointer access is now caught gracefully instead of crashing.

## Sound API — Full Audio Engine (Mar 2026)

44100Hz stereo, up to 64 simultaneous instances. WAV (PCM 8/16-bit) parsed
directly; MP3/AAC/WMA/FLAC decoded via Media Foundation. Auto-cleanup on
script unload.

```cpp
int64 snd = load_sound(path);
free_sound(snd);
play_sound(snd, bool loop);
stop_sound(snd);
stop_all_sounds();
set_sound_volume(snd, float vol);   // 0.0 – 1.0
set_sound_pan(snd, float pan);      // -1.0 (L) – +1.0 (R)
```

## Scan API Updates (Mar 2026)

Scan functions now return `array<uint64>@` directly (no `&out` params).
The `get_vad_snapshot` regression is fixed and returns proper values.

```cpp
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
```
- ⚠️ **REMOVED (never existed):** `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64`.

## Deprecated Functions Summary

| Deprecated | Replacement |
|---|---|
| `source2_world_to_screen` | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| default `matrix4x4` read/write | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` |
| `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64` | removed — use `scan_float` / `scan_double` / `scan_string` / `scan_wstring` / `scan_pointer` |

---

## Source: `knowledge/pcx-cross-language-bridge.md`

# PCX Cross-Language Bridge — Enma vs AngelScript vs Lua

Perception.cx supports three scripting languages: Enma (the native one), AngelScript, and Lua. Each has a different API surface, different performance characteristics, and different ergonomic strengths. The AI keeps defaulting to whichever language the user opened the editor in — missing the cases where another language is materially better for the feature. This file is the comparison and decision guide, plus the patterns for cross-language coordination when one project genuinely needs multiple.

> **Read this before** starting a new feature, picking a language for a new project, or wondering whether a slow / awkward feature would be better in a different language.

---

## At-a-Glance Comparison

| Property | Enma | AngelScript | Lua |
|---|---|---|---|
| **Language family** | C++-like with extensions (FFI, coroutines, annotations) | C++-like, AngelScript registration model | Dynamic, table-centric |
| **Typing** | Static, optionally inferred | Static | Dynamic, with optional type hints in 5.4 |
| **Memory model** | Manual + RAII (deterministic destructors, no GC) | Refcounted handles for objects; value types for math primitives | Garbage-collected |
| **Performance tier** | Fastest (JIT / bytecode, no GC) | Fast (interpreted with type-erased dispatch) | Slower (interpreted, GC pauses possible) |
| **Startup cost** | Low (precompiled `.emb` deserializes fast) | Medium (compile from source on load) | Low (LuaJIT-class speed if exposed; otherwise interpreted) |
| **Hot-reload semantics** | Yes (script code replaced; globals + types persist host-side) | Yes (callbacks released on unload; `proc_t` must `deref()`) | Yes (globals reset; package cache may persist) |
| **Concurrency / threading** | First-class via `addon-thread` (mutex, condvar) and atomics | Mutex / Atomic types per registered addon | Coroutines (idiomatic Lua); no native threads |
| **FFI / native function registration** | Direct via SDK; many built-ins | Via the AngelScript registration model (host-side `RegisterObjectMethod`, etc.) | Via Lua C API (host-side `lua_register`) |
| **Error handling** | Exceptions (`try`/`catch`); rich error types | Exceptions; AS-specific exception types | `pcall` / `xpcall` returning ok-flag + value |
| **Compile-time checking** | Strong (type-checks on compile) | Strong (type-checks on compile) | Weak (most errors are runtime) |
| **Has `vec2`/`vec3`/`vec4`/`quat`/`mat4`** | Yes (math addon) | Yes (vector / matrix types per the engine-specific-api docs) | Yes via the extended-math API (`vector3`, `quaternion`, `matrix4x4`, `mat4` namespace) |
| **Has SIMD intrinsics** | Yes (`addon-simd`: `f32x4`, `i32x4`) | Not as a first-class addon at last check | Not as a first-class addon at last check |
| **Has atomic types** | Yes (`addon-atomic`: `aint32`, `aint64`) | Yes (per AS docs) | No |
| **JSON support** | Yes (`addon-json`) | Yes (per AS docs) | Yes (via `package` addon) |
| **Regex support** | Yes (`addon-regex`) | Available per AS surface | Standard Lua `string.match` patterns |
| **Coroutines** | Yes (per `lang-advanced.md`) | Variable per build — check `docs/perception/angelscript/overview.md` | Native and idiomatic |
| **AS Intrinsics namespace** | n/a | Yes — PCX-specific AS extension (per the README's AngelScript section) | n/a |
| **Debugger tooling at dev time** | Strong (LSP via `lsp/enma-lsp`, full SDK debug hooks) | Strong (LSP via `lsp/angel-lsp-pcx`) | Variable per host integration |

The single most important row is **performance tier**. For hot-path code (render routines at 144 Hz, entity loops over 256 entities, per-frame math), Enma is materially faster than AngelScript, which is materially faster than Lua. The differences below render-rate are usually negligible; at render-rate, they're felt.

Verify each row against the per-language docs for your PCX version — `docs/enma/`, `docs/perception/angelscript/`, `docs/perception/lua/`. The table is a guide; the docs are authoritative.

---

## Per-Use-Case Routing

The decision-tree, ordered by frequency:

### High-frequency render-path code → **Enma**

Render routines running at 144-240 Hz are budget-tight (see `skill://pcx-perf-budget`). Static typing avoids per-call dispatch overhead; no GC eliminates pause variance; the precompiled `.emb` format means no compile cost at script load. For ESP, radar, HUD, anything called from `on_render`: Enma is the default.

### Complex stateful UI logic with rich object lifecycle → **AngelScript**

Features with many in-flight objects with non-trivial lifetimes (target tracker that maintains per-entity state across frames, queue-of-attempts state machine, menu system with nested panels) lean on AngelScript's refcounted handles. The `Type@` syntax + automatic `deref()` (when scoped correctly) handles ownership without manual bookkeeping. See `skill://pcx-angelscript-discipline` rules 2-3 for the discipline.

### Quick prototyping / config DSL / one-off scripts → **Lua**

Dynamic typing is the fastest iteration loop. A table-based config file ("here are my hotkey assignments, my color preferences, my distance thresholds") in Lua is one screen; in Enma it's three. For exploratory work where the shape of the data isn't known yet, Lua's tables-as-everything pattern wins.

### CPU-bound math (matrix transforms, pathfinding, simulation) → **Enma**

The `addon-math3d` (`quat`, `mat4`) and `addon-simd` (`f32x4`, `i32x4`) addons give Enma the native math primitives modern game-math work needs. AngelScript has matrix types but no SIMD addon. Lua's math library is general-purpose, not game-shaped. For pathfinding / physics-y simulation / matrix-heavy work: Enma.

### Network protocol handling / file I/O → **any (use the project's primary language)**

`addon-net` (Enma) and equivalents in AS / Lua all cover sockets, HTTP, websockets. File I/O similarly (`addon-file`, `fs_*` in Lua, AS file APIs). Pick based on what the rest of the script uses; the per-call cost of network I/O dwarfs the per-call cost of the language dispatch overhead.

### Cross-binary compatibility shims → **Enma**

The `.emb` precompiled format (per `docs/enma/sdk-serialization-and-linking.md`) is portable across compatible runtime versions and ships without the script source. AngelScript scripts ship as source by default; Lua scripts ship as source or LuaJIT bytecode. For a library you'll distribute to other users running varying PCX versions, Enma's `.emb` is the most portable artifact.

### Coroutine-heavy state machines → **Enma or Lua**

Enma's coroutines are first-class (per `docs/enma/lang-advanced.md`); Lua's are idiomatic and well-documented. AngelScript's support varies per build. For a stateful "send command → await response → handle result → loop" pattern: pick by what your rest-of-the-project uses.

---

## Cross-Language Coordination

When one feature genuinely spans languages (a render-rate ESP in Enma that consumes data from a config file maintained in Lua, or an AngelScript menu wrapping an Enma compute kernel), three patterns:

### 1. Shared state via files

```
language A writes  ───>  config.json on disk  ───>  language B reads
```

- Cheap; asynchronous; no language-level coupling
- Latency = filesystem-write + filesystem-read; fine for config, slow for per-frame data
- Robust against crashes (file persists)
- Use for: config, persisted state, occasional cross-script communication

### 2. Shared state via the host process

If PCX exposes a host-side state bridge (check `docs/perception/` for cross-language data sharing — the surface is host-specific), one script can write a global the host exposes; another reads it.

- Latency low (in-process)
- Coupling: high (both scripts must agree on the global's shape)
- Use only when the latency of pattern #1 is genuinely too high (per-frame coordination)

### 3. Don't

In most cases, picking one language per feature is cheaper than coordinating across two. If you find yourself reaching for cross-language plumbing, ask: would rewriting the smaller side in the larger side's language eliminate the bridge? Usually yes. Usually it's cheaper.

The rule of thumb: cross-language coordination is for cases where the languages have genuinely different strengths the feature needs. Lua for a config DSL + Enma for the render-rate consumer is a fair split. Two features in two languages "because we have a multi-language codebase" usually means you've imported maintenance overhead for no gain.

---

## Performance Notes

Measured-style guidance (the actual numbers vary per binary, build, and platform — verify on your target):

### Equivalent across languages

These dominate the cost of any non-trivial script regardless of language choice:

- Cross-process memory reads (`ru64`, `read_memory`, etc.) — kernel transition cost dominates, language overhead invisible
- Render API calls (`draw_*`) — GPU command submission dominates
- File I/O — disk latency dominates
- Network calls — network latency dominates

If your script is dominated by these, the language choice barely matters.

### Materially different across languages

These are where the choice shows up:

- **Per-script-call native function overhead** — Enma's dispatch is the tightest; AS adds a type-check pass; Lua's varies by integration. In a tight loop of 1000 native calls per frame, the difference can be 100s of µs.
- **Garbage collection pauses** — Lua has GC; pauses are usually sub-ms but can spike. Enma has none. AS uses refcounting (deterministic, no pauses, but cycles need manual handling).
- **Hot-path arithmetic** — Enma + the SIMD addon outperforms AS + scalar math, which outperforms Lua's general-purpose number type.
- **Allocation overhead** — Lua's table allocations on the hot path show up; Enma's stack-allocated value types don't allocate; AS's refcounted handles allocate but predictably.

The implication: a render-rate routine in Lua + a render-rate routine in Enma differ by 10-50% in CPU time *not* counting the cross-process reads. With cross-process reads dominating, the user-visible difference is smaller, but on a tight script the choice matters.

---

## Migration Notes

When you start a feature in one language and realize another would be better:

### Enma ↔ AngelScript

- Type names mostly align (`uint64`, `float`, `string`, etc.).
- The proc API surface is parallel but the spellings differ — see `skill://pcx-angelscript-discipline` rule 1 for the mapping table (e.g. Enma's `register_routine(cast<int64>(on_render), 0)` becomes AS's `register_callback(on_tick, 16, 0)` with a different callback signature).
- Handle vs value: AS uses `Type@` for refs; Enma uses references / pointers. Conversion is mechanical but per-variable.
- Render APIs differ in shape: Enma takes `color` / `vec2` structs; AS takes raw RGBA ints and separate x/y floats. See `skill://pcx-angelscript-discipline` rule 8.

### Enma ↔ Lua

- Bigger jump. Lua's dynamic typing means every Enma type annotation gets discarded; in return, every Enma type-check happens at runtime.
- Numbers are subtle: Lua 5.4 has a 64-bit integer subtype, so addresses survive; pre-5.4 Lua loses precision past 2^53. See `skill://pcx-lua-discipline` rule 1.
- Lifecycle: Enma's `on_update` / `on_render` map to Lua's `register_routine` (or equivalent — check `docs/perception/lua/life-cycle.md`).
- Tables replace structs; field access syntax is `.` either way; iteration syntax differs.

### AngelScript ↔ Lua

- Largest jump. AS is C++-with-handles; Lua is dynamic + tables. Plan to rewrite, not translate.
- Reuse the architecture (what feature does what, how data flows), not the code.

For all three: the underlying *engine* knowledge (sigs, offsets, struct layouts) is language-agnostic. Port the language-specific parts; keep the offset table.

---

## Recommended Default by Project Size

| Project size | Recommendation |
|---|---|
| 1-3 file script | Pick whichever you know best; the differences don't matter at this scale. |
| 5-15 file project | **Enma is the default** unless a specific feature wants AS or Lua per the routing above. |
| 20+ file production project | **Enma** with selective AS / Lua per feature; **consistency** in the bulk of the codebase matters more than the marginal per-language wins. |
| Library you'll distribute | **Enma** — `.emb` is the most portable artifact. |
| Quick personal experiment | **Lua** — fastest iteration. |
| Performance-critical feature pulled out of a larger project | **Enma** — even if the project is in another language. |

The recommendation against mixing languages in mid-size projects isn't arbitrary: every cross-language boundary is a coupling point, a maintenance overhead, and a context switch for the next maintainer. Use the boundary when the benefit is concrete; default to one language when it's not.

---

## Cross-References

- `docs/enma/` — Enma language + SDK (50 files; start at `enma/readme.md`)
- `docs/perception/angelscript/` — AngelScript APIs (23 files; start at `overview.md`)
- `docs/perception/lua/` — Lua APIs (17 files; start at `overview.md`)
- `skill://pcx-angelscript-discipline` — 10 AS-specific rules (handles, `&out`, `array<T>`, `register_callback` shape)
- `skill://pcx-lua-discipline` — 10 Lua-specific rules (int subtype for addresses, `pcall`, hot-reload boundaries)
- `skill://pcx-perf-budget` — the perf budgets the language choice affects
- `skill://script-bundler` — `.emb` packaging that makes Enma especially portable
- `knowledge/script-organization-patterns.md` — multi-file organization patterns (largely language-agnostic, with notes per language)
- `knowledge/pcx-api-cheatsheet.md` — cross-API surface at a glance
