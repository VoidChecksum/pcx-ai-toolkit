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
