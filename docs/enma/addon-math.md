> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/math.md).

# Math

Registered with `register_addon_math(engine)`. This addon also defines the [vec2/vec3/vec4](addon-vec.md) and [quat / mat4](addon-math3d.md) types — all math types live under the same addon registration.

## Trigonometry

```cpp
sin(x)    cos(x)    tan(x)
asin(x)   acos(x)   atan(x)   atan2(y, x)
```

## Hyperbolic

```cpp
sinh(x)    cosh(x)    tanh(x)
asinh(x)   acosh(x)   atanh(x)
```

## Power & Logarithm

```cpp
sqrt(x)    cbrt(x)    pow(x, y)    hypot(a, b)
log(x)     log2(x)    log10(x)    log_base(x, base)    exp(x)
```

## Rounding

```cpp
floor(x)   ceil(x)    round(x)
round_up(x)            // == ceil(x)
round_down(x)          // == floor(x)
```

## Float utilities

```cpp
fabs(x)                  // absolute value
fmod(x, y)               // float modulo
fmin(a, b)               // minimum
fmax(a, b)               // maximum
fclamp(x, lo, hi)        // clamp to range
```

## Integer utilities

```cpp
iabs(x)                  // absolute value
imin(a, b)               // minimum
imax(a, b)               // maximum
iclamp(x, lo, hi)        // clamp to range
```

## Overloaded `abs` / `min` / `max` / `clamp`

These names dispatch on argument type — works for both `int64` and `float64`.

```cpp
abs(x)         min(a, b)     max(a, b)     clamp(x, lo, hi)
```

## Constants

```cpp
float64 p = pi();        // 3.14159265358979...
float64 e = euler();     // 2.71828182845904...
```

## Random

```cpp
seed(42);                       // seed the RNG
float64 f = rand();             // random float [0, 1)
int64 n = rand_int(0, 100);     // random integer in [lo, hi)
bool b = random_bool();         // 50/50 coin flip
float64 g = random_gaussian(mu, sigma);   // normal distribution
```

## Interpolation

```cpp
lerp(a, b, t);                  // a + (b-a)*t
inverse_lerp(a, b, v);          // (v-a)/(b-a); 0 if a==b
```

## Classification

```cpp
bool n = is_nan(v);
bool i = is_inf(v);
bool f = is_finite(v);
```

## Sign / fractional / wrap

```cpp
sign(v)        // -1.0 / 0.0 / +1.0
fract(v)       // v - floor(v) (positive for negatives)
wrap(v, lo, hi)// wrap v into [lo, hi)
```

## Float bit ops

```cpp
copysign(mag, sgn);             // |mag| with sign of sgn
nextafter(from, toward);         // next representable float toward `toward`
```

## Bit-cast helpers

```cpp
uint32 bits = f32_to_u32(x);     // float32 -> its IEEE-754 bits
float32 f   = u32_to_f32(bits);  // bits -> float32
uint64 b    = f64_to_u64(x);     // float64 -> bits
float64 d   = u64_to_f64(b);     // bits -> float64
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/math.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
