> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/maps.md).

# Maps (string + imap int-keyed)

Registered with `register_addon_map(engine)`.

## Creation

```c
map<string, int64> m;                     // typed declaration; default-constructs
map<string, int64> typed;                 // K/V tracked for native sig checks
```

## Methods

```c
m.get("key")                    // read value
m.get_or_default("key", 0)      // read value or fallback
m.set("key", 42)                // write value
m.contains("key")               // true if key exists
m.has_value(42)                 // true if any entry's value == 42
m.size()                        // number of entries
m.remove("key")                 // delete entry
m.clear()                       // remove all entries
m.free()                        // release memory
m.keys()                        // → string[]
m.values()                      // → element[]
m.merge(other)                  // copy all entries from other into m
```

Subscript access:

```c
m["key"] = 42
int64 v = m["key"]
```

Iteration:

```c
for (string k, int64 v : m) { ... }
```

## imap — int64-keyed hash map

Companion to `map<K, V>` for int64 keys. Same hash-based O(1) ops, but the key is an int64 directly. Headline use case: pair with constexpr FNV-1a to avoid string compares in hot loops.

```c
imap<int64> tbl;                         // typed declaration; default-constructs
```

Methods mirror `map`:

```c
tbl.set(42, 100)
tbl.get(42)
tbl.get_or_default(42, 0)
tbl.has(42)        // alias of contains
tbl.contains(42)
tbl.remove(42)
tbl.length()       // alias of size
tbl.size()
tbl.clear()
tbl.keys()         // → int64[]
tbl.values()       // → element[]
```

Subscript + iteration also supported:

```c
tbl[42] = 100
int64 v = tbl[42]
for (int64 k, int64 v : tbl) { ... }
```

Compile-time hashed lookup:

```c
constexpr int64 fnv1a(string s) {
    int64 h = -3750763034362895579;
    int32 i = 0;
    while (i < cast<int32>(s.length())) {
        h = h ^ s.char_at(i);
        h = h * 1099511628211;
        i = i + 1;
    }
    return h;
}
constexpr int64 H_PLAYER = fnv1a("player");
constexpr int64 H_ENEMY  = fnv1a("enemy");

imap<int64> handlers
handlers.set(H_PLAYER, 100)
handlers.set(H_ENEMY,  50)

// Hot loop — no string allocation, no strcmp; H_PLAYER is folded to an
// int64 immediate at compile time.
for (int64 k : keys) {
    if (handlers.has(k)) total = total + handlers.get(k)
}
```

`imap` fields auto-initialize in classes with a user ctor — same as a no-ctor class.

```c
class W {
    imap<int64> m;       // auto-init runs before W()'s body
    W() {}
}
```

Same for `map<K,V>`, `sorted_map<K,V>`, and other addon-registered container types: typed declarations on classes with or without user ctors default-construct.

## Class / struct as V

`map<K, T>` and `imap<T>` accept user-defined class or struct types as V. Class instances are heap-allocated reference handles — mutating an instance fetched via `get` flows back into the map (alias semantics, like C++ references). To clone, use `*pt` (deref).

```c
class Player {
    int64 id; string name; int64 hp;
    Player() {}
    Player(int64 i, string n, int64 h) { id = i; name = n; hp = h; }
}

// String-keyed lookup by name
map<string, Player> by_name;
by_name.set("alice", new Player(1, "alice", 100));
by_name.set("bob",   new Player(2, "bob",    85));

// Reference semantics — mutation flows back into the map
Player p = by_name.get("alice");
p.hp = 50;
println(cast<string>(by_name.get("alice").hp));   // 50

// Int-keyed lookup by id
imap<Player> by_id;
by_id.set(1, new Player(1, "alice", 100));
by_id.set(2, new Player(2, "bob",    85));

// Iterate
for (string k, Player v : by_name) {
    println(k + " -> " + cast<string>(v.hp));
}
```

`map<K, T*>` / `imap<T*>` supports pointer-typed V — `get` / subscript return a typed `T*`. The container does NOT auto-free pointer elements at scope-drop; you own the `delete` calls for each entry.

## Pattern: ECS-style entity registry

Several maps over the same heap instances — common in entity / scripting contexts. Each `Player*` is shared between `active`, `by_id`, and `by_name`.

```c
class Player {
    int64 id; string name; int64 hp;
    Player(int64 i, string n, int64 h) { id = i; name = n; hp = h; }
}

list<Player>             active;
imap<Player>             by_id;
map<string, Player>      by_name;

void spawn(int64 id, string name, int64 hp) {
    Player* p = new Player(id, name, hp);
    active.push_back(p);
    by_id.set(id, p);
    by_name.set(name, p);
}
```

When `active` (or any container holding the Player) drops, the heap class instances inside are automatically freed. Aliased entries in the other containers don't double-free — the runtime guards against it via `heap_is_tracked`.

## Heap cleanup on container drop

When a `map<string, V>` / `imap<V>` / `list<V>` etc. with class or string V goes out of scope, the IR-level scope-drop walks the elements and frees each one. This applies to:

* Local containers at function scope-end
* Container fields when the owning class is `delete`'d
* Containers held in `try` blocks unwound by `throw`

Global containers don't free at `main` return (so routines / callbacks that fire after `main` keep working). The engine's heap teardown reclaims any leftover memory when the engine is destroyed.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/maps.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
