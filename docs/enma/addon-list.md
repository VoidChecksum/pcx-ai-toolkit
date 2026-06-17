> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/list.md).

# List

Registered with `register_addon_list(engine)`.

`list<T>` is a generic double-ended container. **O(1) push/pop\_back, O(1) random access, O(n) push\_front/pop\_front.** Use it for queues / deques / entity lists; for a strict LIFO stack or growable buffer, `array<T>` is cheaper (single contiguous block).

```cpp
list<Entity> ents;
ents.push_back(new Entity(1));
ents.push_back(new Entity(2));
ents.push_front(new Entity(0));
println(cast<string>(ents.size()));   // 3
```

## Construction

```cpp
list<int64> a;             // empty list
list<Point> ents;          // class T — class storage works (reference-aliased)
```

`list<T*>` is supported — V is a user-managed pointer, `get` / subscript return a typed `T*`. The list does not auto-free pointer elements; you `delete` them.

## Add / remove

```cpp
lst.push_back(x)         // append (alias: push)
lst.push_front(x)        // prepend
lst.pop_back()           // remove + return last (alias: pop)
lst.pop_front()          // remove + return first
lst.insert(idx, x)       // insert at idx (clamps oob → end)
lst.remove(idx)          // remove + return element at idx (returns 0 if oob)
```

`pop_*` on an empty list returns `0` (not a crash). `remove(idx)` does the same for out-of-bounds.

## Access

```cpp
lst.get(idx)             // bounds-checked; returns 0 if oob (alias: at)
lst.set(idx, x)          // bounds-checked; no-op if oob
lst[idx]                 // subscript (read + write)
lst.first()              // front element (0 if empty)
lst.last()               // back element (0 if empty)
```

## Search

```cpp
lst.contains(x)          // true if any element equals x (alias: has)
lst.index_of(x)          // index of first match, or -1
```

## Size

```cpp
lst.size()               // alias: length
lst.empty()              // == size() == 0
```

## Modify

```cpp
lst.clear()              // empty the list
lst.reverse()            // in-place reverse
```

## Conversion / combine / copy

```cpp
array<T> arr = lst.to_array();    // snapshot to array<T>, preserves order
list<T>  cp  = lst.copy();        // independent shallow copy
src.extend(other);                // append every element of `other` to `src`
```

`copy()` and `extend()` copy *handles* — for class T, both lists end up holding handles to the same heap instances. To deep-copy a class T element, use `*pt` deref or define a `clone()` method on your class.

## Iteration

`list<T>` supports the kv-iterable foreach form. Index is the "key", element is the value:

```cpp
list<int64> nums;
nums.push_back(10); nums.push_back(20); nums.push_back(30);

// Index + value
for (int64 i, int64 v : nums) {
    println(cast<string>(i) + " -> " + cast<string>(v));
}

// Value only — discard the index
for (int64 i, int64 v : nums) {
    println(cast<string>(v));
}
```

## Class storage

`list<T>` for class T stores reference handles. Insert via `new T(...)` inline; the list takes ownership (heap-tracked). Retrieved values are *aliased* — mutations flow back into the list:

```cpp
class Entity { int64 id; int64 hp; Entity(int64 i, int64 h) { id = i; hp = h; } }

list<Entity> ents;
ents.push_back(new Entity(1, 100));

Entity e = ents.first();    // alias — same heap object
e.hp = 50;                   // mutates the stored Entity

Entity e2 = ents.first();
println(cast<string>(e2.hp)); // 50
```

For an independent copy, use `*p` (deref) on a `T*` pointer if you have one — or define a `clone()` method on the class.

## Class field with list — auto-cleanup

A class with a `list<T>` field cleans up automatically on `delete`. The runtime walks the list field, frees each heap-tracked element, then runs the list's own dtor. Works one level deep — for nested class containers the inner level may need explicit cleanup (see Known limitations).

```cpp
class Squad {
    list<Entity> members;
    string name;
    Squad(string n) { name = n; }
}

Squad* sq = new Squad("alpha");
sq->members.push_back(new Entity(1, 100));
sq->members.push_back(new Entity(2, 100));
delete sq;   // members + each Entity inside freed
```

## Class storage in maps + cross-container sharing

The same heap class instance can live in multiple containers — `list`, `imap`, `map<string, T>` — and mutation in any one is visible in all. When the containers drop, `heap_is_tracked` guards prevent double-free.

```cpp
class Player { int64 id; int64 hp; Player(int64 i, int64 h) { id = i; hp = h; } }

list<Player>             active;
imap<Player>             by_id;
map<string, Player>      by_name;

Player* p = new Player(1, 100);
active.push_back(p);
by_id.set(1, p);
by_name.set("alpha", p);

// Mutate via one — visible everywhere
Player a = by_id.get(1);
a.hp = 50;
println(cast<string>(by_name.get("alpha").hp));   // 50
println(cast<string>(active.first().hp));         // 50
```

## list vs array vs map — which to pick

| Need                            | Use                                                              |
| ------------------------------- | ---------------------------------------------------------------- |
| LIFO stack, growable buffer     | `array<T>` (cheaper — single contiguous block, no front-end ops) |
| FIFO queue, deque, both ends    | `list<T>`                                                        |
| String → V lookup               | `map<string, V>`                                                 |
| int → V lookup                  | `imap<V>`                                                        |
| Ordered key map (range queries) | `sorted_map<K, V>`                                               |
| Unique-element set              | `hash_set<T>`                                                    |

## Notes

* `pop_*()` on empty returns 0; if you store 0 as a real value, use `empty()` to disambiguate.
* `push_front` / `pop_front` are O(n) on the current storage — fine for occasional use, avoid in tight hot loops.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/list.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
