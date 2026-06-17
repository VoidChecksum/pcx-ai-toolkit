> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/language-guide/functions.md).

# Functions

## Basic Functions

```c
int32 add(int32 a, int32 b) {
    return a + b;
}

void greet() {
    println("hello");
}
```

## Default Parameters

Defaulted params must come after all required params.

```c
int32 connect(int32 port, int32 timeout = 5000) {
    return port + timeout;
}

connect(8080);        // timeout = 5000
connect(8080, 1000);  // timeout = 1000
```

## Reference Parameters

Pass by reference with `&`. Changes to the parameter modify the caller's variable.

```c
void swap(int32& a, int32& b) {
    int32 t = a;
    a = b;
    b = t;
}

int32 x = 10;
int32 y = 20;
swap(x, y);  // x=20, y=10
```

## Out Parameters

`out` is an alternative syntax for reference parameters. Identical semantics to `&`.

```c
void compute(int32 input, out int32 result, out int32 remainder) {
    result = input / 10;
    remainder = input % 10;
}

int32 r = 0;
int32 rem = 0;
compute(42, r, rem);  // r=4, rem=2
```

## Variadic Functions

Use `...` at the end of the parameter list. Inside the body, `__va_count` is the number of variadic args and `__va_arg(i)` reads the i-th:

```c
int64 sum(...) {
    int64 s = 0;
    int64 i = 0;
    while (i < __va_count) {
        s = s + __va_arg(i);
        i = i + 1;
    }
    return s;
}

int32 main() { return cast<int32>(sum(1, 2, 3, 4, 5)); }   // 15
```

Fixed params before `...` are read normally:

```c
void log(int32 level, ...) {
    int64 i = 0;
    while (i < __va_count) {
        println(__va_arg(i));
        i = i + 1;
    }
}
log(1, 10, 20, 30);
```

Args are passed through as `int64`-sized slots; the callee is responsible for interpreting each one.

## Shadowing Native Functions

A script function with the **same signature** as a native (addon-registered) function wins at every call site. Different signatures don't shadow — the resolver picks whichever overload matches the call's argument types, so a script `wrap(string)` and a native `wrap(float, float, float)` coexist and dispatch by arity/type. To force the script version for a given site, give it a unique name.

```c
// Same signature as math addon's wrap → script version wins.
float64 wrap(float64 x, float64 lo, float64 hi) { return 999.0; }
```

## Forward Declarations

Declare a function signature before its implementation. Useful for mutual recursion.

```c
int32 is_even(int32 n);

int32 is_odd(int32 n) {
    if (n == 0) return 0;
    return is_even(n - 1);
}

int32 is_even(int32 n) {
    if (n == 0) return 1;
    return is_odd(n - 1);
}
```

## Extern Functions

Declare a function implemented in another module or native code.

```c
extern int32 lib_func(int32 x);
```

## Function References

Prefix a function name with `@` to take its address:

```c
int64 fn_ptr = @add;
```

For a typed reference, assign to a matching delegate.

## Lambdas

### Bracket Style

```c
delegate int32 Transform(int32 x);
Transform fn = [](int32 x) -> int32 { return x * 2; };
int32 r = fn(21);  // 42
```

### Arrow Lambdas

Expression body (result returned implicitly):

```c
delegate int32 Transform(int32 x);
Transform fn = (int32 x) => x * 2;
int32 r = fn(21);  // 42
```

Block body:

```c
int64 fn = (int32 a, int32 b) => {
    int32 sum = a + b;
    return sum * 2;
};
```

Zero parameters:

```c
int64 fn = () => 42;
```

### Closures

Lambdas automatically capture variables from the enclosing scope:

```c
delegate int32 Transform(int32 x);
int32 base = 100;
Transform adder = [](int32 x) -> int32 { return base + x; };
int32 r = adder(5);  // 105
```

Explicit capture lists:

```c
int32 a = 10;
int32 b = 20;
int64 fn = [a, b](int32 x) -> int32 { return a + b + x; };
```

Arrow lambdas capture implicitly as well:

```c
int32 scale = 3;
int64 fn = (int32 x) => x * scale;
```

### Capture by reference

Prefix a capture name with `&` to bind the outer slot by reference. Writes inside the lambda land in the outer scope's local; reads see live changes. Without `&` (bare `[x]`), the capture is a snapshot taken at closure-construction time and outer changes don't propagate.

```c
int64 main() {
    int64 counter = 0;
    auto inc = [&counter]() { counter = counter + 1; };
    inc(); inc(); inc();
    return counter;                   // 3
}
```

`&` works for primitives, value-structs (member writes land in the outer struct), strings, arrays, maps, and any treg-typed local. It also composes: nested lambdas can each take `[&x]` of the same outer variable and they all share one address.

```c
int64 main() {
    int64 outer = 0;
    auto bump = [&outer]() {
        auto inner = [&outer]() { outer = outer + 1; };
        inner(); inner();
    };
    bump(); bump();
    return outer;                     // 4
}
```

Bare `[x]` mixed with `[&y]` is allowed and the value/reference semantics apply independently per capture. Lifetime: the outer scope must outlive the closure — once the outer frame drops, dereferencing the captured address is undefined behaviour. Returning a closure that ref-captures a local of the returning function is the classic foot-gun.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/language-guide/functions.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
