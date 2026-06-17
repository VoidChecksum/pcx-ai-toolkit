> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/extended-math-api.md).

# Extended Math API

The Extended Math API supplies:

* Double-precision scalar helpers
* 2D vectors (`vector2`)
* 3D vectors (`vector3`)
* Quaternions (`quaternion`)
* 4×4 matrices (`matrix4x4`)
* Read/write helpers for interacting with raw memory values

All math types support operator overloading and can be used naturally in AngelScript expressions.

***

## **2. Constants**

All constants are `const double` and available globally:

| Name        | Description               |
| ----------- | ------------------------- |
| `M_PI`      | Pi (3.14159…)             |
| `M_TAU`     | Tau (2π)                  |
| `M_PI_2`    | π/2                       |
| `M_PI_4`    | π/4                       |
| `RAD2DEG`   | Convert radians → degrees |
| `DEG2RAD`   | Convert degrees → radians |
| `M_ZERO`    | 0.0                       |
| `M_ONE`     | 1.0                       |
| `M_EPSILON` | Small epsilon (1e-6)      |

***

## **3. Scalar Math Functions**

#### **clamp(x, a, b) → double**

Clamp `x` into range `[a, b]`.

#### **saturate(x) → double**

Clamp `x` into `[0,1]`.

#### **sign(x) → int**

Returns `-1`, `0`, or `1`.

#### **round / round\_up / round\_down**

#### **fract(x)**

Positive fractional part.

#### **wrap(x, min, max)**

Wrap value into interval like modulo.

#### **lerp(a, b, t)**

Linear interpolate.

#### **inverse\_lerp(a, b, v)**

Returns `t` such that `lerp(a,b,t) = v`.

#### **remap(a1, b1, a2, b2, v)**

Map a value between ranges.

#### **smoothstep(edge0, edge1, x)**

Smoothed curve between two edges.

#### **step(edge, x)**

Binary step function.

#### **is\_nan(x)**

Check for NaN.

#### **is\_inf(x)**

Check for infinity.

***

## **4. vector2**

```cpp
struct vector2 {
    double x;
    double y;
}
```

### **Constructors**

```cpp
vector2()                    // (0,0)
vector2(double x, double y)
vector2(const vector2 &in)
```

### **Operators**

```cpp
vector2 opAdd(const vector2 &in) const
vector2 opSub(const vector2 &in) const
vector2 opNeg() const
vector2 opMul(double s) const
vector2 opDiv(double s) const
bool    opEquals(const vector2 &in) const
```

### **Methods**

```cpp
double  length() const
double  distance(const vector2 &in other) const
double  distance_to(const vector2 &in other) const
vector2 lerp(const vector2 &in other, double t) const
vector2 min(const vector2 &in other) const
vector2 max(const vector2 &in other) const
```

### **Memory Helpers**

```cpp
void readas_double(proc_t& in, uint64 addr)
void readas_float(proc_t& in, uint64 addr)
bool writeas_double(proc_t& in, uint64 addr) const
bool writeas_float(proc_t& in, uint64 addr) const
```

***

## **5. vector3**

```cpp
struct vector3 {
    double x, y, z;
}
```

### **Constructors**

```cpp
vector3()
vector3(double x, double y, double z)
vector3(const vector3 &in)
```

### **Operators**

```cpp
vector3 opAdd(const vector3 &in) const
vector3 opSub(const vector3 &in) const
vector3 opNeg() const
vector3 opMul(double s) const
vector3 opDiv(double s) const
bool    opEquals(const vector3 &in) const
```

### **Methods**

```cpp
double length() const
double length2d() const
double distance(const vector3 &in) const
double distance2d(const vector3 &in) const
double distance_to(const vector3 &in) const
double distance2d_to(const vector3 &in) const
vector3 lerp(const vector3 &in, double t) const
vector3 min(const vector3 &in) const
vector3 max(const vector3 &in) const
double  dot_product(const vector3 &in) const
vector3 cross_product(const vector3 &in) const
```

### **Memory Helpers**

```cpp
void readas_double(proc_t& in, uint64 addr)
void readas_float(proc_t& in, uint64 addr)
bool writeas_double(proc_t& in, uint64 addr) const
bool writeas_float(proc_t& in, uint64 addr) const
```

***

## **6. quaternion**

```cpp
struct quaternion {
    double x, y, z, w;
}
```

### **Constructors**

```cpp
quaternion()                              // identity
quaternion(double x, double y, double z, double w)
```

### **Static**

```cpp
quaternion quat_from_euler(double pitch, double yaw, double roll)
```

(Euler angles in degrees.)

### **Operators**

```cpp
quaternion opMul(const quaternion &in) const
quaternion opMul(double s) const
quaternion opDiv(double s) const
quaternion opAdd(const quaternion &in) const
quaternion opSub(const quaternion &in) const
quaternion opNeg() const
bool       opEquals(const quaternion &in) const
```

### **Methods**

```cpp
double     length() const
quaternion normalized() const
double     dot(const quaternion &in) const
quaternion conjugate() const
quaternion inverse() const
void       to_euler(double &out pitch, double &out yaw, double &out roll) const
vector3    rotate(const vector3 &in v) const
```

### **Memory Helpers**

```cpp
void readas_double(proc_t& in, uint64 addr)
void readas_float(proc_t& in, uint64 addr)
bool writeas_double(proc_t& in, uint64 addr) const
bool writeas_float(uproc_t& in, uint64 addr) const
```

***

## **7. matrix4x4**

```cpp
struct matrix4x4 {
    double m[16];   // Internal storage — not meant to be accessed as mat.m
};

// Instead of mat.m, you should access elements using either:
//   mat[index]          — linear index
//   mat[row][col]       — row/column indexing
```

### **Constructor**

```cpp
matrix4x4()     // zero matrix
```

### **Global Functions**

```cpp
matrix4x4 mat4_identity()
matrix4x4 mat4_zero()
matrix4x4 mat4_translate(double tx, double ty, double tz)
matrix4x4 mat4_scale(double sx, double sy, double sz)
matrix4x4 mat4_rotate_euler(double pitch, double yaw, double roll)
matrix4x4 mat4_from_quaternion(const quaternion &in q)
```

### **Operators**

```cpp
matrix4x4 opMul(const matrix4x4 &in) const
```

### **Methods**

```cpp
vector3 transform(const vector3 &in v) const
void    readas_float(proc_t& in, uint64 addr) // Reading precision is float
bool    writeas_float(proc_t& in, uint64 addr) const // Writing precision is float
void    readas_double(proc_t& in, uint64 addr) // Reading precision is double
bool    writeas_double(proc_t& in, uint64 addr) const // Writing precision is double
```

***

## **8. Memory Helpers Summary**

Every math type supports reading/writing data from a 64-bit address:

#### **Read**

* `readas_double(`proc\_t& in`, addr)` – read consecutive doubles
* `readas_float(`proc\_t& in`, addr)` – read consecutive floats

#### **Write**

* `writeas_double(`proc\_t& in`, addr)` – write consecutive doubles
* `writeas_float(`proc\_t& in`, addr)` – write consecutive floats

***

## **9. Random**

```cpp
void random_seed(uint64 seed): set RNG seed 
double random(): random value in [0.0, 1.0)
double random_range(double min, double max): random in [min, max]
int64 random_int(int64 min, int64 max): random integer in [min, max]
bool random_bool(): random true or false
double random_gaussian(double mean, double stddev): normal distribution
vector2 random_unit_vec2(): random unit direction 2D
vector3 random_unit_vec3(): random unit direction on sphere
```

***

## **10. Example Usage**

#### **Vector math**

```cpp
vector2 a(1,2);
vector2 b(4,-1);
vector2 c = a + b;
double d = a.distance(b);
```

#### **3D vector operations**

```cpp
vector3 velocity = direction.normalized() * speed;
```

#### **Quaternion rotation**

```cpp
quaternion q = quat_from_euler(0, 90, 0);
vector3 forward(1,0,0);

vector3 rotated = q.rotate(forward);
```

#### **Matrix transform**

```cpp
matrix4x4 T = mat4_translate(10, 0, 0);
vector3 pos = T.transform(vector3(1,2,3));
```

#### **Reading a position from memory**

```cpp
vector3 pos;
pos.readas_float(proc, address);
```

#### **Writing back**

```cpp
pos.x += 5;
pos.writeas_float(proc, address);
```

## Full API Test

```cpp
void print_vec2(const string &in label, const vector2 &in v)
{
    log(label + " = (" + v.x + ", " + v.y + ")");
}

void print_vec3(const string &in label, const vector3 &in v)
{
    log(label + " = (" + v.x + ", " + v.y + ", " + v.z + ")");
}

void print_quat(const string &in label, const quaternion &in q)
{
    log(label + " = (" + q.x + ", " + q.y + ", " + q.z + ", " + q.w + ")");
}

int main()
{
    log("=== AS Extended Math FULL TEST ===");
    
    // ----------------------------------------------------------------
    // Scalars & constants
    // ----------------------------------------------------------------
    log("M_PI        = " + M_PI);
    log("M_TAU       = " + M_TAU);
    log("RAD2DEG(PI) = " + (M_PI * RAD2DEG));
    log("DEG2RAD(180)= " + (180.0 * DEG2RAD));
    
    log("clamp(5,0,3)       = " + clamp(5.0, 0.0, 3.0));
    log("saturate(-0.5)     = " + saturate(-0.5));
    log("saturate(0.5)      = " + saturate(0.5));
    log("saturate(2.0)      = " + saturate(2.0));
    log("sign(-2.0)         = " + sign(-2.0));
    log("sign(0.0)          = " + sign(0.0));
    log("sign(3.0)          = " + sign(3.0));
    log("round(1.4)         = " + round(1.4));
    log("round(1.5)         = " + round(1.5));
    log("fract(-1.25)       = " + fract(-1.25));
    log("wrap(370,0,360)    = " + wrap(370.0, 0.0, 360.0));
    log("lerp(0,10,0.25)    = " + lerp(0.0, 10.0, 0.25));
    log("inverse_lerp(0,10,2.5) = " + inverse_lerp(0.0, 10.0, 2.5));
    log("remap(0..100 -> -1..1, 25) = " + remap(0.0, 100.0, -1.0, 1.0, 25.0));
    log("smoothstep(0,1,0.5)= " + smoothstep(0.0, 1.0, 0.5));
    log("step(0.5, 0.25)    = " + step(0.5, 0.25));
    log("step(0.5, 0.75)    = " + step(0.5, 0.75));
    // Basic sanity; your C++ doesn’t expose make_nan/make_inf so just use 0
    log("is_nan(0.0)        = " + (is_nan(0.0) ? "true" : "false"));
    log("is_inf(1.0)        = " + (is_inf(1.0) ? "true" : "false"));
    
    // ----------------------------------------------------------------
    // vector2
    // ----------------------------------------------------------------
    vector2 v2a;            // default (0,0)
    v2a.x = 1.0;
    v2a.y = 2.0;
    
    vector2 v2b(4.0, -1.0); // ctor
    
    print_vec2("v2a", v2a);
    print_vec2("v2b", v2b);
    
    vector2 v2_add = v2a + v2b;
    vector2 v2_sub = v2a - v2b;
    vector2 v2_neg = -v2a;
    vector2 v2_mul = v2a * 2.0;
    vector2 v2_div = v2b / 2.0;
    
    print_vec2("v2a + v2b", v2_add);
    print_vec2("v2a - v2b", v2_sub);
    print_vec2("-v2a",      v2_neg);
    print_vec2("v2a * 2",   v2_mul);
    print_vec2("v2b / 2",   v2_div);
    
    log("v2a == v2a ? " + (v2a == v2a ? "true" : "false"));
    log("v2a == v2b ? " + (v2a == v2b ? "true" : "false"));
    
    log("v2a.length()        = " + v2a.length());
    log("v2a.distance(v2b)   = " + v2a.distance(v2b));
    log("v2a.distance_to(v2b)= " + v2a.distance_to(v2b));
    
    vector2 v2_lerp = v2a.lerp(v2b, 0.5);
    print_vec2("v2a.lerp(v2b,0.5)", v2_lerp);
    
    print_vec2("v2a.min(v2b)", v2a.min(v2b));
    print_vec2("v2a.max(v2b)", v2a.max(v2b));
    
    // ----------------------------------------------------------------
    // vector3
    // ----------------------------------------------------------------
    vector3 v3a;            // default (0,0,0)
    v3a.x = 1.0; v3a.y = 2.0; v3a.z = 3.0;
    
    vector3 v3b(4.0, -1.0, 0.5);
    
    print_vec3("v3a", v3a);
    print_vec3("v3b", v3b);
    
    print_vec3("v3a + v3b", v3a + v3b);
    print_vec3("v3a - v3b", v3a - v3b);
    print_vec3("-v3a",      -v3a);
    print_vec3("v3a * 2",   v3a * 2.0);
    print_vec3("v3b / 2",   v3b / 2.0);
    
    log("v3a.length()        = " + v3a.length());
    log("v3a.length2d()      = " + v3a.length2d());
    log("v3a.distance(v3b)   = " + v3a.distance(v3b));
    log("v3a.distance2d(v3b) = " + v3a.distance2d(v3b));
    
    vector3 v3_lerp = v3a.lerp(v3b, 0.5);
    print_vec3("v3a.lerp(v3b,0.5)", v3_lerp);
    
    print_vec3("v3a.min(v3b)", v3a.min(v3b));
    print_vec3("v3a.max(v3b)", v3a.max(v3b));
    log("v3a.dot_product(v3b) = " + v3a.dot_product(v3b));
    print_vec3("v3a.cross_product(v3b)", v3a.cross_product(v3b));
    
    // ----------------------------------------------------------------
    // quaternion
    // ----------------------------------------------------------------
    quaternion q;   // default (0,0,0,1)
    print_quat("q (default)", q);
    
    quaternion qEuler = quat_from_euler(30.0, 45.0, 10.0);
    print_quat("qEuler (30,45,10)", qEuler);
    
    log("qEuler.length()     = " + qEuler.length());
    print_quat("qEuler.normalized()", qEuler.normalized());
    
    quaternion q2(0.1, 0.2, 0.3, 0.9);
    print_quat("q2", q2);
    
    log("qEuler.dot(q2)      = " + qEuler.dot(q2));
    print_quat("qEuler.conjugate()", qEuler.conjugate());
    print_quat("qEuler.inverse()",   qEuler.inverse());
    print_quat("qEuler * q2",        qEuler * q2);
    print_quat("qEuler * 0.5",       qEuler * 0.5);
    print_quat("qEuler / 2.0",       qEuler / 2.0);
    print_quat("qEuler + q2",        qEuler + q2);
    print_quat("qEuler - q2",        qEuler - q2);
    print_quat("-qEuler",            -qEuler);
    
    log("qEuler == qEuler ? " + (qEuler == qEuler ? "true" : "false"));
    log("qEuler == q2 ? "      + (qEuler == q2      ? "true" : "false"));
    
    double pitch, yaw, roll;
    qEuler.to_euler(pitch, yaw, roll);
    log("qEuler.to_euler() -> pitch=" + pitch + ", yaw=" + yaw + ", roll=" + roll);
    
    vector3 v3Test(1.0, 0.0, 0.0);
    vector3 v3Rot = qEuler.rotate(v3Test);
    print_vec3("qEuler.rotate(1,0,0)", v3Rot);
    
    // ----------------------------------------------------------------
    // matrix4x4
    // ----------------------------------------------------------------
    matrix4x4 I = mat4_identity();
    matrix4x4 T = mat4_translate(1.0, 2.0, 3.0);
    matrix4x4 S = mat4_scale(2.0, 3.0, 4.0);
    matrix4x4 R = mat4_rotate_euler(30.0, 45.0, 10.0);
    matrix4x4 Qm = mat4_from_quaternion(qEuler);
    
    vector3 v3_id = I.transform(v3a);
    vector3 v3_t  = T.transform(v3a);
    vector3 v3_s  = S.transform(v3a);
    vector3 v3_r  = R.transform(v3a);
    vector3 v3_qm = Qm.transform(v3a);
    
    print_vec3("I.transform(v3a)",  v3_id);
    print_vec3("T.transform(v3a)",  v3_t);
    print_vec3("S.transform(v3a)",  v3_s);
    print_vec3("R.transform(v3a)",  v3_r);
    print_vec3("Qm.transform(v3a)", v3_qm);
    
    matrix4x4 M = T * S * R;
    vector3 v3_m = M.transform(v3a);
    print_vec3("M.transform(v3a)", v3_m);
    
    log("=== Extended Math test DONE ===");
    return 1;
}

```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/angel-script/extended-math-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
