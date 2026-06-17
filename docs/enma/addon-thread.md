> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/thread.md).

# Thread

Registered with `register_addon_thread(engine)`.

Three addon types for thread synchronization: `mutex`, `lock_guard` (RAII over a mutex), and `cond_var`. `mutex` is backed by `std::shared_mutex`, so the same handle supports both exclusive (writer) and shared (reader) locks. `cond_var` is a thin wrapper around `std::condition_variable_any`.

## mutex

```cpp
mutex m;
m.lock();
// critical section (exclusive)
m.unlock();

bool got = m.try_lock();          // non-blocking exclusive
if (got) m.unlock();

// Reader-writer usage:
m.lock_shared();                  // multiple shared holders allowed
// read-only critical section
m.unlock_shared();
```

### Methods

```cpp
void m.lock()             // exclusive (writer)
void m.unlock()
bool m.try_lock()

void m.lock_shared()      // shared (reader); concurrent shared holders allowed
void m.unlock_shared()
bool m.try_lock_shared()
```

Use `lock` / `unlock` for plain mutual exclusion; the shared variants when multiple readers can safely run together but writers need to be alone (`std::shared_mutex` semantics).

## lock\_guard

RAII wrapper: constructor locks, destructor unlocks. Copies are rejected at runtime because two guards can't both own the same lock.

```cpp
mutex m;
{
    lock_guard g = lock_guard(m);
    // m is held here
}   // scope exit -> dtor -> m is released
```

Attempting to copy raises a runtime error:

```cpp
lock_guard a = lock_guard(m);
lock_guard b = a;       // runtime: "lock_guard is non-copyable"
```

## cond\_var

`cond_var` is `std::condition_variable_any`, which waits on any mutex. The mutex must already be held by the caller when `wait` is invoked; it's released during the wait and reacquired before returning.

```cpp
mutex m;
cond_var cv;

// Consumer:
m.lock();
while (!queue_has_items()) {
    cv.wait(cast<int64>(/* mutex handle */));
}
// drain queue...
m.unlock();

// Producer:
m.lock();
queue_push(x);
cv.notify_one();    // or notify_all()
m.unlock();
```

### Methods

```cpp
void cv.wait(int64 mutex_handle)
void cv.notify_one()
void cv.notify_all()
```

## Free helpers

```cpp
sleep_us(1000)              // sleep for N microseconds
yield_cpu()                 // hint scheduler to yield this quantum
int64 n = hardware_threads() // platform's reported core count
```

## Cross-thread usage

For a real multi-thread scenario, the host spawns threads from native code and shares the mutex handle across threads. Mutex/cond\_var handles can be passed across threads safely.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/thread.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
