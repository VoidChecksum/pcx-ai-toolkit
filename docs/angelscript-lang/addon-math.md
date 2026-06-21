<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_math.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# math functions

**Path:** /sdk/add_on/scriptmath/

This add-on registers the math functions from the standard C runtime library with the script engine. Use `RegisterScriptMath(asIScriptEngine*)` to perform the registration.

By defining the preprocessor word `AS_USE_FLOAT=0`, the functions will be registered to take and return doubles instead of floats.

The function `RegisterScriptMathComplex(asIScriptEngine*)` registers a type that represents a complex number, i.e. a number with real and imaginary parts.

## Public script interface

```angelscript
// Trigonometric functions
float cos(float rad);
float sin(float rad);
float tan(float rad);

// Inverse trigonometric functions
float acos(float val);
float asin(float val);
float atan(float val);
float atan2(float y, float x);

// Hyperbolic functions
float cosh(float rad);
float sinh(float rad);
float tanh(float rad);

// Logarithmic functions
float log(float val);
float log10(float val);

// Power to
float pow(float val, float exp);

// Square root
float sqrt(float val);

// Absolute value
float abs(float val);

// Ceil and floor functions
float ceil(float val);
float floor(float val);

// Returns the fraction
float fraction(float val);

// Approximate float comparison, to deal with numeric imprecision
bool closeTo(float a, float b, float epsilon = 0.00001f);
bool closeTo(double a, double b, double epsilon = 0.0000000001);

// Conversion between floating point and IEEE 754 representations
float  fpFromIEEE(uint raw);
double fpFromIEEE(uint64 raw);
uint   fpToIEEE(float fp);
uint64 fpToIEEE(double fp);
```

### Functions

**cos, sin, tan**
Calculates the trigonometric functions cosine, sine, and tangent. The input angle should be given in radian.

**acos, asin, atan**
Calculates the inverse of the trigonometric functions cosine, sine, and tangent. The returned angle is given in radian.

**atan2**
Calculates the inverse of the trigonometric function tangent. The input is the y and x proportions. The returned angle is given in radian.

**cosh, sinh, tanh**
Calculates the hyperbolic of the cosine, sine, and tangent. The input angle should be given in radian.

**log, log10**
Calculates the logarithm of the input value. log is the natural logarithm and log10 is the base-10 logarithm.

**pow**
Calculates the based raised to the power of exponent.

**sqrt**
Calculates the square root of the value.

**abs**
Returns the absolute value.

**ceil, floor**
ceil returns the closest integer number that is higher or equal to the input. Floor returns the closest integer number that is lower or equal to the input.

**fraction**
Returns the fraction of the number, i.e. what remains after taking away the integral number.

**closeTo**
Due to numerical errors with the binary representation of real numbers it is often difficult to do direct comparisons of two float values. The closeTo function will return true of the two values are almost equal, allowing for a small difference up to the size of the epsilon value.

**fpFromIEEE, fpToIEEE**
Translates the float to and from IEEE 754 representation. This can be used if one wishes to directly inspect or manipulate the floating point value in the binary representation.

### The complex type

```angelscript
// This type represents a complex number with real and imaginary parts
class complex
{
  // Constructors
  complex();
  complex(const complex &in);
  complex(float r);
  complex(float r, float i);

  // Equality operator
  bool opEquals(const complex &in) const;

  // Compound assignment operators
  complex &opAddAssign(const complex &in);
  complex &opSubAssign(const complex &in);
  complex &opMulAssign(const complex &in);
  complex &opDivAssign(const complex &in);

  // Math operators
  complex opAdd(const complex &in) const;
  complex opSub(const complex &in) const;
  complex opMul(const complex &in) const;
  complex opDiv(const complex &in) const;

  // Returns the absolute value (magnitude)
  float abs() const;

  // Swizzle operators
  complex get_ri() const;
  void set_ri(const complex &in);
  complex get_ir() const;
  void set_ir(const complex &in);

  // The real and imaginary parts
  float r;
  float i;
}
```

**complex**
The constructors allow for implicit construction, making a copy, implicit conversion from float, and explicit initialization from two float values.

**=, !=**
Compares two complex values.

**=, +=, -=, \*=, /=**
Assign and compound assignment of complex values.

**+, -, \*, /**
Math operators on complex values.

**abs**
Returns the absolute (magnitude) of the complex value.

**r, i**
Retrieves the real and imaginary part of the complex value.

**ri, ir**
Swizzle operators return a complex value with the ordering of the real and imaginary parts as indicated by the name.