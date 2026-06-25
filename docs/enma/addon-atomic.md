> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/atomic.md).

# Atomic

Script-exposed atomic integers and memory barriers backed by `std::atomic<>`. Use these when multiple threads touch the same value. Plain `aint32` / `aint64` keywords exist as Enma types but the codegen doesn't currently emit LOCK-prefixed ops for assignments on them, so reach for the atomic types instead.

> **Do not use `aint32` / `aint64` for synchronization.** They are language-level integer types, but assignment is not currently emitted as a hardware atomic operation. For cross-thread synchronization, use `atomic_int32` / `atomic_int64` and their methods.

## Types

* `atomic_int32(init) -> atomic_int32`
* `atomic_int64(init) -> atomic_int64`

Both heap-allocated, scope-dropped. Factory takes the initial value.

## Methods (identical on both widths)

```cpp
int64 load();
void  store(int64 v);
int64 exchange(int64 v);              // returns old value
bool  compare_exchange(int64 exp, int64 des);  // swaps if current == exp; returns true on success

int64 add(int64 v);                    // returns old
int64 sub(int64 v);
int64 bit_and(int64 v);
int64 bit_or(int64 v);
int64 bit_xor(int64 v);

int64 inc();                           // returns NEW value
int64 dec();                           // returns NEW value
```

All ops use `std::memory_order_seq_cst`. Relaxed / acquire / release variants aren't exposed yet.

## Barriers (free functions)

```cpp
memory_barrier();   // seq_cst
read_barrier();     // acquire
write_barrier();    // release
```

Equivalent to `std::atomic_thread_fence` at the matching order.

## Example: counter

```cpp
atomic_int64 counter = atomic_int64(0);

void worker() {
    int32 i = 0;
    while (i < 100000) {
        counter.add(1);
        i = i + 1;
    }
}

// Spawn N threads, each calling worker()...
int64 final = counter.load();
```

## Example: CAS loop

```cpp
atomic_int64 x = atomic_int64(0);

int32 try_double() {
    int32 retries = 0;
    while (true) {
        int64 cur = x.load();
        if (x.compare_exchange(cur, cur * 2)) return retries;
        retries = retries + 1;
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
GET https://enma-1.gitbook.io/enma/addons/atomic.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
