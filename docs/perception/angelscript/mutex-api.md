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
