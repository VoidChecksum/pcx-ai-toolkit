> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/bits.md).

# Bits

Registered with `register_addon_bits(engine)`.

All operations treat the input as an unsigned bit pattern. 64-bit variants operate on the full `int64`. `_i32` variants mask to the low 32 bits first (useful when you want strict 32-bit semantics: rotates wrap at 32, clz/ctz return 32 for zero, etc.).

## Population count

```cpp
int64 n1 = popcount(0xFF)        // 8
int64 n2 = popcount(-1)          // 64 (all bits set)
int64 n3 = popcount_i32(-1)      // 32 (masked to low 32)
```

## Leading / trailing zeros

`clz` returns the number of leading (high) zero bits. `ctz` returns the number of trailing (low) zero bits. Both return the bit width of the type (64 or 32) when the input is zero (not undefined like C's intrinsics).

```cpp
int64 a = clz(1)                  // 63
int64 b = clz(0)                  // 64
int64 c = ctz(256)                // 8   (bit 8 is the first set bit)
int64 d = ctz_i32(cast<int64>(0x00001000)) // 12
```

## Rotates

Rotate by `n & (width - 1)`; wraps cleanly at the boundary.

```cpp
int64 a = rotl(0x12345678, 4)
int64 b = rotr(a, 4)              // b == 0x12345678
int64 c = rotl_i32(0x12345678, 8) // 0x34567812
```

## Byte swap

```cpp
int64 a = bswap(0x0102030405060708)  // 0x0807060504030201
int64 b = bswap_i32(0x12345678)      // 0x78563412
```

## Parity

Returns 1 if the number of set bits is odd, else 0.

```cpp
int64 p1 = parity(7)     // 1 (three ones)
int64 p2 = parity(3)     // 0 (two ones)
```

## Bit reverse

Reverses the full bit pattern. `bit_reverse(1)` puts a single bit at position 63 (MSB); the `_i32` variant reverses within the low 32 bits.

```cpp
int64 r = bit_reverse(1)            // 0x8000000000000000
int64 s = bit_reverse_i32(1)        // 0x80000000
```

## Single-bit ops

```cpp
int64 a = set_bit(0, 3)             // 8       (set bit 3)
int64 b = clear_bit(15, 1)          // 13      (clear bit 1)
int64 c = toggle_bit(5, 1)          // 7       (flip bit 1)
int64 t = test_bit(4, 2)            // 1       (bit 2 is set in 4)
```

## Bit-range extract / insert

`extract_bits(v, lo, hi)` pulls bits in **inclusive** `[lo, hi]`. `insert_bits(v, val, lo, hi)` returns `v` with the same range overwritten by `val`.

```cpp
int64 a = extract_bits(0xDEAD, 0, 7)          // 0xAD  (bits 0..7)
int64 b = extract_bits(0xDEAD, 8, 15)         // 0xDE  (bits 8..15)
int64 c = insert_bits(0xFF00, 0xAB, 0, 7)     // 0xFFAB
```

## Power-of-two helpers

```cpp
bool  p = is_pow2(16)               // true
int64 n = next_pow2(5)              // 8       (smallest pow2 >= v; 1 if v <= 1)
int64 q = prev_pow2(17)             // 16      (largest pow2 <= v; 0 if v == 0)
```

## Alignment

Round to a multiple of `n` (typically a power of two).

```cpp
int64 a = align_up(13, 8)           // 16
int64 b = align_down(13, 8)         // 8
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/bits.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
