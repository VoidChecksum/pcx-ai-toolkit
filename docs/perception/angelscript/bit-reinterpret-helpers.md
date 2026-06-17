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
