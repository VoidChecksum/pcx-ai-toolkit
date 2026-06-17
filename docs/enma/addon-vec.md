> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/vec.md).

# Vectors

`vec2`, `vec3`, and `vec4` are value-type structs (16 / 24 / 32 bytes, 2 / 3 / 4 `float64` components). They are part of the `math` addon — register with `register_addon_math(engine)` on the host side and (if your host hasn't already registered it for you) `import "math";` on the script side.

```enma
import "math";

int64 main() {
    vec3 a = vec3(1.0, 2.0, 3.0);
    vec3 b = vec3(4.0, 5.0, 6.0);
    vec3 c = a + b;
    return cast<int64>(c.x);
}
```

Stored inline as fields (no heap indirection). `vec3[]` lays out N × 24-byte vec3s back-to-back; `xs.push(vec3(...))` memcpys the value.

## Construction

```cpp
vec2 p = vec2(1.0, 2.0);
vec3 v = vec3(1.0, 2.0, 3.0);
vec4 q = vec4(1.0, 2.0, 3.0, 4.0);

// Default constructor zeros all components.
vec3 zero;
```

## Component access

Components are plain struct fields — there is no `.x()` / `.y()` parenthesised getter form.

```cpp
// Read
float64 x = v.x;
float64 y = v.y;
float64 z = v.z;
float64 w = q.w;       // vec4 only

// Write
v.x = 5.0;
v.z = 3.0;
q.w = 1.0;
```

Field access compiles to a direct memory read/write — no native call, no allocation.

## Operators

```cpp
vec3 s = a + b;            // vec2 / vec3 / vec4
vec3 d = a - b;
vec3 k = v * 2.5;          // scalar multiply (float64 RHS)
vec3 n = -a;               // unary negate
bool eq = (a == b);        // component-wise equality
bool truthy = !!a;         // false if all components are 0

a += b;
a -= b;
```

## Methods

Common to **vec2 / vec3 / vec4**:

```cpp
vec3 r = a.add(b);            // same as a + b
vec3 r = a.sub(b);
vec3 r = a.scale(2.0);
vec3 r = a.neg();             // alias: a.negate()
float64 d = a.dot(b);
float64 L = v.length();
float64 Lsq = v.length_sq();   // squared (no sqrt)
float64 d = a.distance(b);
vec3 n = v.normalize();        // unit vector; zero-length stays zero
vec3 l = a.lerp(b, t);         // component-wise
```

**vec2** also has:

```cpp
vec2 r = v.rotate(rad);        // rotate CCW by `rad` radians
```

**vec3** also has:

```cpp
vec3 c = a.cross(b);
vec3 r = v.reflect(n);                 // reflect across normal `n`
vec3 p = v.project(onto);              // projection of v onto `onto`
float64 a = u.angle(v);                // angle between u and v (radians)
vec3 r = v.rotate_around(axis, rad);   // Rodrigues; axis is normalized internally
```

## Scalar helpers

Free functions in the same addon:

```cpp
float64 r = deg_to_rad(180.0);           // ~π
float64 d = rad_to_deg(3.14159);         // ~180

float64 a = lerp_angle(a0, a1, t);       // shortest-path angular lerp (radians)
float64 p = move_toward(cur, tgt, step); // step without overshooting target

float64 e1 = ease_in(t);                 // t² (t in [0,1])
float64 e2 = ease_out(t);                // 1-(1-t)²
float64 e3 = ease_in_out(t);             // quadratic in-out

bool ok = approx_eq(a, b, eps);          // |a-b| <= eps
```

For quaternions and 4×4 matrices see [3D Math](addon-math3d.md). For scalar math (`sin`, `cos`, `sqrt`, `pow`, ...) see [Math](addon-math.md).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/vec.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
