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
