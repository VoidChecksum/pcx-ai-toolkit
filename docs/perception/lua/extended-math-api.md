> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/extended-math-api.md).

# Extended Math API

This API provides vectors, quaternions, matrices, math constants, and helper functions found in modern game engines.

***

## 📘 Contents

* Math Constants
* Global Math Helpers
* vector2
* vector3
* quaternion
* matrix4x4
* mat4 Namespace

***

## 🔢 **Math Constants**

These are available globally:

| Name              | Value                  |
| ----------------- | ---------------------- |
| `M_PI`            | 3.141592653589793      |
| `M_TAU`           | 6.283185307179586 (2π) |
| `M_PI_2`          | π/2                    |
| `M_PI_4`          | π/4                    |
| `DEG2RAD`         | π/180                  |
| `RAD2DEG`         | 180/π                  |
| `PI_OVER_180`     | π/180                  |
| `INV_PI_OVER_180` | 180/π                  |
| `M_ZERO`          | 0                      |
| `M_ONE`           | 1                      |
| `M_EPSILON`       | 0.000001               |

Usage:

```lua
local angle = 45 * DEG2RAD
local circumference = 2 * M_PI * radius
```

***

## 🛠 **Global Math Helpers**

#### ✔ clamp(x, min, max)

Clamps a value between two bounds.

```lua
local v = clamp(5, 0, 1)  -- 1
```

#### ✔ saturate(x)

Clamps value to `[0,1]`.

```lua
local t = saturate(1.5) -- 1
```

#### ✔ sign(x)

Returns `-1`, `0`, or `1`.

#### ✔ round(x), round\_up(x), round\_down(x)

Standard rounding helpers.

#### ✔ fract(x)

Fractional part (always 0–1, even for negatives).

#### ✔ wrap(x, min, max)

Wraps a number into a cyclic range.

```lua
wrap(5, 0, 4) --> 1
```

#### ✔ lerp(a, b, t)

Linear interpolation.

#### ✔ inverse\_lerp(a, b, v)

Inverse of `lerp`.

#### ✔ remap(a1, b1, a2, b2, v)

Maps a value from one range to another.

#### ✔ smoothstep(edge0, edge1, x)

Smooth Hermite interpolation.

#### ✔ step(edge, x)

Returns 0 if x < edge, else 1.

#### ✔ is\_nan(x), is\_inf(x)

Checks numeric state.

***

## 🟦 **vector2**

A 2D double-precision vector.

#### ✔ Create

```lua
local v = vector2(x, y)
local v = vector2() -- 0,0
```

#### ✔ Fields

* `v.x`
* `v.y`

#### ✔ Operators

| Operation         | Example    |
| ----------------- | ---------- |
| add               | `v1 + v2`  |
| subtract          | `v1 - v2`  |
| multiply (scalar) | `v * 2`    |
| divide (scalar)   | `v / 2`    |
| unary minus       | `-v`       |
| equality          | `v1 == v2` |

#### ✔ Methods

```lua
v:length()
v:distance(other)
v:distance_to(other)
v:lerp(other, t)
v:min(other)
v:max(other)
```

#### ✔ Memory I/O

```lua
v:readas_float(proc, addr)
v:readas_double(proc, addr)
v:writeas_float(proc, addr)
v:writeas_double(proc, addr)
```

***

## 🟩 **vector3**

A 3D double-precision vector.

#### ✔ Create

```lua
local v = vector3(x, y, z)
local v = vector3()
```

#### ✔ Fields

`v.x`, `v.y`, `v.z`

#### ✔ Operators

Same as vector2, plus:

* `v:dot(other)`
* `v:cross_product(other)`

#### ✔ Methods

```lua
v:length()
v:length2d()
v:distance(other)
v:distance2d(other)
v:distance_to(other)
v:distance2d_to(other)
v:lerp(other, t)
v:min(other)
v:max(other)
v:dot_product(other)
v:cross_product(other)
```

#### ✔ Memory I/O

Same pattern as vector2.

***

## 🟪 **quaternion**

A 4D double-precision quaternion (x, y, z, w).

#### ✔ Create

```lua
local q = quaternion(x, y, z, w)
local q = quaternion()     -- 0,0,0,1
local q = quat_from_euler(pitch, yaw, roll)
```

#### ✔ Fields

`q.x`, `q.y`, `q.z`, `q.w`

#### ✔ Operators

| Operation           | Example    |
| ------------------- | ---------- |
| multiply quaternion | `q1 * q2`  |
| multiply scalar     | `q * 2`    |
| divide scalar       | `q / 2`    |
| add                 | `q1 + q2`  |
| subtract            | `q1 - q2`  |
| negate              | `-q`       |
| equality            | `q1 == q2` |

#### ✔ Methods

```lua
q:length()
q:normalized()
q:dot(other)
q:conjugate()
q:inverse()
q:to_euler()          -- returns pitch,yaw,roll
q:rotate(vec3)        -- rotates a vector
```

#### ✔ Memory I/O

```lua
q:readas_double(proc, addr)
q:writeas_double(proc, addr)
q:readas_float(proc, addr)
q:writeas_float(proc, addr)
```

***

## 🟥 **matrix4x4**

A 4×4 float matrix (row-major), used for transforms and 3D math.

#### ✔ Create

```lua
local m = matrix4x4()   -- zero matrix
```

#### ✔ Indexing

```lua
m[1] .. m[16]
```

#### ✔ Operators

```lua
local M = A * B
```

#### ✔ Methods (instance)

```lua
m:transform(vec3)
m:readas_float(proc, addr)
m:writeas_float(proc, addr)
m:readas_double(proc, addr)
m:writeas_double(proc, addr)
```

#### ✔ tostring()

Pretty-prints matrix for debugging.

***

## 🟧 **mat4 Namespace**

Convenient static constructors:

```lua
local I = mat4.identity()
local Z = mat4.zero()

local T = mat4.translate(tx, ty, tz)
local S = mat4.scale(sx, sy, sz)
local R = mat4.rotate_euler(pitch, yaw, roll)

local Mq = mat4.from_quaternion(q)
```

***

## 📘 **Examples**

#### TRS (Translate → Rotate → Scale)

```lua
local T = mat4.translate(10, 5, 0)
local R = mat4.rotate_euler(0, 90, 0)
local S = mat4.scale(2, 2, 2)

local M = T * R * S
local out = M:transform(vector3(1,0,0))
log(out)
```

#### Quaternion Rotation

```lua
local q = quat_from_euler(0, 0, 90)
local v = vector3(1,0,0)
local r = q:rotate(v)     -- (0,1,0)
```

#### Remapping Values

```lua
local t = inverse_lerp(0, 100, 25)   -- 0.25
local v = remap(0, 1, -1, 1, t)      -- -0.5
```

## Full API Test

```lua
log("=========== MATH HELPERS TESTS START ===========")

local function approx(a,b,eps)
    eps = eps or 0.000001
    return math.abs(a-b) <= eps
end

local function assert_eq(a,b,msg)
    if a ~= b then
        log("[ASSERT FAIL] "..msg.." | expected="..tostring(b).." got="..tostring(a))
    else
        log("[PASS] "..msg)
    end
end

local function assert_approx(a,b,msg)
    if approx(a,b) then
        log("[PASS] "..msg)
    else
        log("[ASSERT FAIL] "..msg.." | expected="..tostring(b).." got="..tostring(a))
    end
end

----------------------------------------------------------------
-- clamp(x, min, max)
----------------------------------------------------------------
assert_approx(clamp(-1, 0, 1), 0,   "clamp below")
assert_approx(clamp(0.5, 0, 1), 0.5,"clamp inside")
assert_approx(clamp(2, 0, 1), 1,    "clamp above")
-- swapped min/max should still work
assert_approx(clamp(5, 10, 0), 5,   "clamp swapped bounds")

----------------------------------------------------------------
-- saturate(x) -> [0,1]
----------------------------------------------------------------
assert_approx(saturate(-1), 0,      "saturate below")
assert_approx(saturate(0.3), 0.3,   "saturate inside")
assert_approx(saturate(5), 1,       "saturate above")

----------------------------------------------------------------
-- sign(x)
----------------------------------------------------------------
assert_eq(sign( 5),  1,  "sign positive")
assert_eq(sign(-2), -1,  "sign negative")
assert_eq(sign( 0),  0,  "sign zero")

----------------------------------------------------------------
-- round, round_up, round_down
----------------------------------------------------------------
assert_approx(round(2.3),  2,   "round 2.3")
assert_approx(round(2.5),  3,   "round 2.5")
assert_approx(round(-2.3), -2,  "round -2.3")
assert_approx(round(-2.5), -3,  "round -2.5")

assert_approx(round_up(2.1),   3, "round_up 2.1")
assert_approx(round_up(-2.1), -2, "round_up -2.1")

assert_approx(round_down(2.9),   2, "round_down 2.9")
assert_approx(round_down(-2.1), -3, "round_down -2.1")

----------------------------------------------------------------
-- fract(x)
----------------------------------------------------------------
assert_approx(fract(1.25), 0.25, "fract 1.25")
-- our implementation keeps negative fractional part in [0,1)
assert_approx(fract(-1.25), 0.75, "fract -1.25")

----------------------------------------------------------------
-- wrap(x, min, max)
----------------------------------------------------------------
assert_approx(wrap(5, 0, 4), 1,   "wrap 5 in [0,4]")
assert_approx(wrap(-1, 0, 4), 3,  "wrap -1 in [0,4]")
assert_approx(wrap(9, 2, 6), 5, "wrap 9 in [2,6]")
assert_approx(wrap(2, 2, 6), 2,   "wrap 2 (edge)")

----------------------------------------------------------------
-- lerp / inverse_lerp
----------------------------------------------------------------
assert_approx(lerp(0, 10, 0.0), 0,   "lerp t=0")
assert_approx(lerp(0, 10, 1.0), 10,  "lerp t=1")
assert_approx(lerp(0, 10, 0.25), 2.5,"lerp t=0.25")

assert_approx(inverse_lerp(0, 10, 2.5), 0.25, "inverse_lerp 2.5 in [0,10]")
assert_approx(inverse_lerp(0, 10, 0),    0.0, "inverse_lerp 0")
assert_approx(inverse_lerp(0, 10, 10),   1.0, "inverse_lerp 10")

----------------------------------------------------------------
-- remap(a1,b1,a2,b2,v)
----------------------------------------------------------------
assert_approx(remap(0, 10, 0, 100, 2.5), 25,  "remap 2.5 [0,10]->[0,100]")
assert_approx(remap(0, 1, -1, 1, 0.5),   0,   "remap 0.5 [0,1]->[-1,1]")
assert_approx(remap(-1, 1, 0, 1, 0),     0.5, "remap 0 [-1,1]->[0,1]")

----------------------------------------------------------------
-- smoothstep(edge0,edge1,x)
----------------------------------------------------------------
assert_approx(smoothstep(0,1, -0.5), 0.0,  "smoothstep below")
assert_approx(smoothstep(0,1,  0.0), 0.0,  "smoothstep 0")
assert_approx(smoothstep(0,1,  1.0), 1.0,  "smoothstep 1")
-- at x=0.5 we expect 0.5 for 3t^2-2t^3
local s05 = smoothstep(0,1,0.5)
assert_approx(s05, 0.5, "smoothstep 0.5")

----------------------------------------------------------------
-- step(edge, x)
----------------------------------------------------------------
assert_approx(step(0.5, 0.3), 0.0, "step below")
assert_approx(step(0.5, 0.5), 1.0, "step equal")
assert_approx(step(0.5, 0.9), 1.0, "step above")

----------------------------------------------------------------
-- is_nan / is_inf
----------------------------------------------------------------
local nan = 0/0
local pinf = 1/0
local ninf = -1/0

assert_eq(is_nan(nan), true,  "is_nan on NaN")
assert_eq(is_nan(0),   false, "is_nan on 0")

assert_eq(is_inf(pinf), true,  "is_inf +inf")
assert_eq(is_inf(ninf), true,  "is_inf -inf")
assert_eq(is_inf(123),  false, "is_inf 123")

log("=========== MATH HELPERS TESTS END ===========")

function main()
    return 1;
end

```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/extended-math-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
