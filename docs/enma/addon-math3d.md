> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/math3d.md).

# 3D Math (quat + mat4)

`quat` and `mat4` are value-type structs in the `math` addon (same registration as [Vectors](addon-vec.md) and [Math](addon-math.md)). Register with `register_addon_math(engine)` on the host side and `import "math";` in your script if needed.

* `quat` — unit quaternion, 32 bytes, four `float64` fields (`x`, `y`, `z`, `w`). `w` is the scalar.
* `mat4` — 4×4 row-major matrix, 128 bytes, 16 `float64` fields named `m00` … `m33`.

Both default-construct to all zeros. Use `quat_identity()` / `mat4_identity()` for the canonical "do nothing" values.

## Quaternion (`quat`)

### Construction

```cpp
quat q;                                    // typed default: (0, 0, 0, 0)
quat q4 = quat(1.0, 0.0, 0.0, 0.0);        // explicit components

quat id = quat_identity();                  // (0, 0, 0, 1) — no rotation
quat e  = quat_from_euler(yaw, pitch, roll); // Tait-Bryan ZYX, radians
quat a  = quat_from_axis_angle(vec3(0.0, 0.0, 1.0), deg_to_rad(90.0));
```

### Accessors

`x` / `y` / `z` / `w` are plain struct fields — read and write directly, no parenthesised getter form.

```cpp
// Read
float64 x = q.x;
float64 w = q.w;

// Write
q.x = 0.0;
q.w = 1.0;
```

Direct component writes do **not** re-normalize. Call `q.normalize()` afterwards if you need a unit quaternion.

### Operations

```cpp
quat n = q.normalize();
quat c = q.conjugate();         // xyz negated, w preserved
quat i = q.inverse();           // == conjugate when q is unit-length

quat r = a.mul(b);              // Hamilton product; same as a * b
quat s = a.add(b);              // component-wise; same as a + b
quat g = q.negate();            // alias: q.neg(); same as -q

float64 d   = a.dot(b);         // 4-component dot product
float64 L   = q.length();
float64 Lsq = q.length_sq();

vec3 rotated = q.rotate(vec3(0.0, 0.0, 1.0));  // assumes unit quat
vec3 euler   = q.to_euler();                    // (yaw, pitch, roll) in vec3 x/y/z

quat midway  = a.slerp(b, t);                   // shorter great-circle arc
```

### Operators

```cpp
quat r = a * b;            // Hamilton product (non-commutative)
quat s = a + b;            // component-wise add
quat n = -q;               // unary negate
bool eq = (a == b);        // exact-component equality
a += b;
a -= b;
```

## 4×4 Matrix (`mat4`)

Row-major. Default constructor produces a zero matrix — use `mat4_identity()` for the identity.

### Construction

```cpp
mat4 zero;                                  // typed default: all 0
mat4 i = mat4_identity();
mat4 t = mat4_translation(vec3(x, y, z));
mat4 s = mat4_scale(vec3(sx, sy, sz));
mat4 rx = mat4_rotation_x(rad);
mat4 ry = mat4_rotation_y(rad);
mat4 rz = mat4_rotation_z(rad);
mat4 ra = mat4_rotation_axis(vec3 axis, rad);  // Rodrigues; axis normalized internally
mat4 fq = mat4_from_quat(q);
mat4 p  = mat4_perspective(fov_rad, aspect, near_z, far_z);     // RH, GL-style depth
mat4 o  = mat4_orthographic(left, right, bottom, top, near_z, far_z);
mat4 v  = mat4_look_at(vec3 eye, vec3 target, vec3 up);          // RH view matrix
```

### Element access

You can read/write individual cells through the named fields (`m00`, `m01`, ..., `m33`) or use the `get`/`set` methods which take row/col.

```cpp
m.m00 = 1.0;
float64 c = m.m12;

float64 v = m.get(row, col);            // row, col in 0..3
m.set(row, col, value);
```

`mat4_get(m, row, col)` and `mat4_set(m, row, col, v)` are free-function aliases for the methods.

### Operations

```cpp
mat4 t = m.transpose();
mat4 i = m.inverse();              // returns identity if singular
float64 d = m.determinant();
mat4 c = a.mul(b);                  // row-major a*b; same as a * b
mat4 g = m.scale(2.0);              // scalar multiply
mat4 n = m.neg();                   // unary negate

vec3 p = m.transform_point(v);      // applies translation; perspective-divides if w != 1
vec3 d = m.transform_vec3(v);       // ignores translation (use for directions)
vec4 q = m.transform_vec4(v);       // full 4-component transform
```

### Operators

```cpp
mat4 c = a * b;
mat4 s = a + b;
mat4 d = a - b;
mat4 n = -m;
bool eq = (a == b);
a += b;
a -= b;
a *= b;
```

## Common patterns

```cpp
// Build a TRS world matrix.
mat4 world = mat4_translation(pos) * mat4_from_quat(rot) * mat4_scale(scl);
vec3 world_pos = world.transform_point(local_pos);

// Compose a view-projection matrix.
mat4 view = mat4_look_at(camera_pos, target, vec3(0.0, 1.0, 0.0));
mat4 proj = mat4_perspective(deg_to_rad(60.0), 16.0/9.0, 0.1, 1000.0);
mat4 vp = proj * view;
vec3 ndc = vp.transform_point(world_pos);    // perspective-divides via w

// Slerp between two orientations.
quat a = quat_identity();
quat b = quat_from_axis_angle(vec3(0.0, 1.0, 0.0), deg_to_rad(90.0));
quat current = a.slerp(b, t);    // t in [0, 1]
vec3 facing = current.rotate(vec3(0.0, 0.0, 1.0));
```

## Notes

* All angles are radians. Use `deg_to_rad` / `rad_to_deg` from [Vectors](addon-vec.md#scalar-helpers) to convert.
* `mat4_perspective` uses right-handed coordinates and OpenGL-style depth (`z` clipped to `[-1, 1]` after perspective divide). Direct3D conventions need the depth row tweaked.
* `mat4.inverse()` returns the identity when the matrix is singular (zero determinant). Check `m.determinant() != 0.0` if your code can produce non-invertible matrices.
* Quaternion multiplication is non-commutative: `a * b != b * a` in general. `a * b` means "rotate by `b` first, then by `a`".
* `quat_from_euler` and `q.to_euler()` both use Tait-Bryan ZYX (yaw, pitch, roll). Round-tripping isn't exact at gimbal-lock orientations (`pitch = ±π/2`).


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/math3d.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
