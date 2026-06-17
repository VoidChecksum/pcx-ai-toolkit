> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/simd.md).

# SIMD

Registered with `register_addon_simd(engine)`. Uses SSE2 intrinsics; ops fall back to scalar for the trailing element when array length is odd.

Argument convention: `(a, b, dst)` — inputs first, output last. Output arrays must be pre-sized; the natives don't grow them.

## Elementwise float64

```c
simd_add_f64(a, b, dst)         // dst[i] = a[i] + b[i]
simd_sub_f64(a, b, dst)
simd_mul_f64(a, b, dst)
simd_div_f64(a, b, dst)
simd_min_f64(a, b, dst)
simd_max_f64(a, b, dst)
simd_abs_f64(src, dst)          // dst[i] = |src[i]|
simd_sqrt_f64(src, dst)
simd_fma_f64(a, b, c, dst)      // dst[i] = a[i] * b[i] + c[i]
simd_scale_f64(src, k, dst)     // dst[i] = src[i] * k
```

## Reductions

```c
float64 d = simd_dot_f64(a, b)         // a · b
float64 s = simd_sum_f64(a)
float64 m = simd_min_reduce_f64(a)
float64 m = simd_max_reduce_f64(a)
```

## Compare (1.0 / 0.0 per lane)

```c
simd_cmp_eq_f64(a, b, dst)
simd_cmp_lt_f64(a, b, dst)
```

## Elementwise int64

```c
simd_add_i64(a, b, dst)
simd_sub_i64(a, b, dst)
simd_mul_i64(a, b, dst)          // scalar fallback (no SSE2 packed 64-bit mul)
int64 s = simd_sum_i64(a)
```

## Memory

```c
simd_memset(arr, val)            // fill entire array with int64 val
simd_memcpy(src, dst)
```

## Packed SIMD on stride-1/2/4 arrays

`uint8[]`/`int8[]`/`int16[]`/`int32[]`/`float32[]` are packed buffers (1/2/4 bytes per element), so dedicated packed ops operate 16/8/4 lanes at a time. Each op validates the operand's `|stride|` and raises `runtime_error` on mismatch — passing an `int64[]` to `simd_add_i8` fails fast.

### int8 / uint8 (16 lanes)

```c
simd_add_i8(a, b, dst)           // wrap
simd_sub_i8(a, b, dst)
simd_cmp_eq_i8(a, b, dst)        // dst[i] = 0xFF if eq else 0x00
int64 mask = simd_movemask_i8(a) // bit i = sign bit of a[i], up to 64 bytes
simd_shuffle_i8(src, mask, dst)  // pshufb semantics per 16-byte block
```

### int16 / uint16 (8 lanes)

```c
simd_add_i16(a, b, dst)
simd_sub_i16(a, b, dst)
simd_mul_i16(a, b, dst)
```

### int32 / uint32 (4 lanes)

```c
simd_add_i32(a, b, dst)
simd_sub_i32(a, b, dst)
simd_mul_i32(a, b, dst)
```

### float32 (4 lanes; sse\_\*\_ps parity)

```c
simd_add_f32(a, b, dst)
simd_sub_f32(a, b, dst)
simd_mul_f32(a, b, dst)
simd_div_f32(a, b, dst)
simd_sqrt_f32(src, dst)
simd_min_f32(a, b, dst)
simd_max_f32(a, b, dst)
simd_abs_f32(src, dst)

float64 d = simd_dot_f32(a, b)   // returns float64 for precision
float64 s = simd_sum_f32(a)
```

### Bitwise on any stride-1 array

```c
simd_and(a, b, dst)
simd_or(a, b, dst)
simd_xor(a, b, dst)
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/simd.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
