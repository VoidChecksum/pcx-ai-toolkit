<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Expressions

- [Assignments](#assignments)
- [Function call](#function-call)
- [Math operators](#math-operators)
- [Bitwise operators](#bitwise-operators)
- [Compound assignments](#compound-assignments)
- [Logic operators](#logic-operators)
- [Equality comparison operators](#equality-comparison-operators)
- [Relational comparison operators](#relational-comparison-operators)
- [Identity comparison operators](#identity-comparison-operators)
- [Increment operators](#increment-operators)
- [Indexing operator](#indexing-operator)
- [Conditional expression](#conditional-expression)
- [Member access](#member-access)
- [Handle-of](#handle-of)
- [Parenthesis](#parenthesis)
- [Scope resolution](#scope-resolution)
- [Type conversions](#type-conversions)
- [Anonymous objects](#anonymous-objects)

## Assignments

```angelscript
lvalue = rvalue;
```

`lvalue` must be an expression that evaluates to a memory location where the expression value can be stored, e.g. a variable. An assignment evaluates to the same value and type of the data stored. The right hand expression is always computed before the left.

## Function call

```angelscript
func();
func(arg);
func(arg1, arg2);
lvalue = func();
```

Functions are called to perform an action, and possibly return a value that can be used in further operations. If a function takes more than one argument, the argument expressions are evaluated in the reverse order, i.e. the last argument is evaluated first.

Some functions are declared with output reference parameters to return multiple values. When calling such functions the output parameter must be given as an expression that can be assigned with the returned value. If the additional output value won't be used use the special argument 'void' to tell the compiler that.

```angelscript
// This function returns a value in the output parameter
void func(int &out outputValue)
{
  outputValue = 42;
}

// Call the function with a valid lvalue expression to receive the output value
int value;
func(value);

// Call the function with 'void' argument to ignore the output value
func(void);
```

Arguments can also be named and passed to a specific argument independent of the order the parameters were declared in. No positional arguments may follow any named arguments.

```angelscript
void func(int flagA = false, int flagB = false, int flagC = false) {}

// Call the function, setting only a subset of its parameters
func(flagC: true);
func(flagB: true, flagA: true);
```

For function templates it is necessary to explicitly inform the subtypes so the compiler can evaluate the correct function template instance to call.

```angelscript
templ<int,float>(arg1, arg2);
```

## Math operators

```angelscript
c = -(a + b);
```

| **operator** | **description** | **left hand** | **right hand** | **result** |
| --- | --- | --- | --- | --- |
| `+` | unary positive |  | *NUM* | *NUM* |
| `-` | unary negative |  | *NUM* | *NUM* |
| `+` | addition | *NUM* | *NUM* | *NUM* |
| `-` | subtraction | *NUM* | *NUM* | *NUM* |
| `*` | multiplication | *NUM* | *NUM* | *NUM* |
| `/` | division | *NUM* | *NUM* | *NUM* |
| `%` | modulos | *NUM* | *NUM* | *NUM* |
| `**` | exponent | *NUM* | *NUM* | *NUM* |

Plus and minus can be used as unary operators as well. NUM can be exchanged for any numeric type, e.g. `int` or `float`. Both terms of the dual operations will be implicitly converted to have the same type. The result is always the same type as the original terms. One exception is unary negative which is not available for `uint`.

## Bitwise operators

```angelscript
c = ~(a | b);
```

| **operator** | **description** | **left hand** | **right hand** | **result** |
| --- | --- | --- | --- | --- |
| `~` | bitwise complement |  | *NUM* | *NUM* |
| `&` | bitwise and | *NUM* | *NUM* | *NUM* |
| `|` | bitwise or | *NUM* | *NUM* | *NUM* |
| `^` | bitwise xor | *NUM* | *NUM* | *NUM* |
| `<<` | left shift | *NUM* | *NUM* | *NUM* |
| `>>` | right shift | *NUM* | *NUM* | *NUM* |
| `>>>` | arithmetic right shift | *NUM* | *NUM* | *NUM* |

All except `~` are dual operators.

Both operands will be converted to integers while keeping the sign of the original type before the operation. The resulting type will be the same as the left hand operand.

## Compound assignments

```angelscript
lvalue += rvalue;
lvalue = lvalue + rvalue;
```

A compound assignment is a combination of an operator followed by the assignment. The two expressions above means practically the same thing. Except that first one is more efficient in that the lvalue is only evaluated once, which can make a difference if the lvalue is complex expression in itself.

Available operators: `+= -= *= /= %= **= &= |= ^= <<= >>= >>>=`

## Logic operators

```angelscript
if( a and b or not c )
{
  // ... do something
}
```

| **operator** | **description** | **left hand** | **right hand** | **result** |
| --- | --- | --- | --- | --- |
| `not` | logical not |  | `bool` | `bool` |
| `and` | logical and | `bool` | `bool` | `bool` |
| `or` | logical or | `bool` | `bool` | `bool` |
| `xor` | logical exclusive or | `bool` | `bool` | `bool` |

Boolean operators only evaluate necessary terms. For example in expression `a and b`, `b` is only evaluated if `a` is `true`.

Each of the logic operators can be written as symbols as well, i.e. `||` for `or`, `&&` for `and`, `^^` for `xor`, and `!` for `not`.

## Equality comparison operators

```angelscript
if( a == b )
{
  // ... do something
}
```

The operators `==` and `!=` are used to compare two values to determine if they are equal or not equal, respectively. The result of this operation is always a boolean value.

## Relational comparison operators

```angelscript
if( a > b )
{
  // ... do something
}
```

The operators `<`, `>`, `<=`, and `>=` are used to compare two values to determine their relationship. The result is always a boolean value.

## Identity comparison operators

```angelscript
if( a is null )
{
  // ... do something
}
else if( a is b )
{
  // ... do something
}
```

The operators `is` and `!is` are used to compare the identity of two objects, i.e. to determine if the two are the same object or not. These operators are only valid for reference types as they compare the address of two objects. The result is always a boolean value.

## Increment operators

```angelscript
// The following means a = i; i = i + 1;
a = i++;

// The following means i = i - 1; b = i;
b = --i;
```

These operators can be placed either before or after an lvalue to increment/decrement its value either before or after the value is used in the expression. The value is always incremented or decremented with 1.

## Indexing operator

```angelscript
arr[i] = 1;
```

This operator is used to access an element contained within the object. Depending on the object type, the expression between the `[]` needs to be of different types.

## Conditional expression

```angelscript
choose ? a : b;
```

If the value of `choose` is `true` then the expression returns `a` otherwise it will return `b`.

Both `a` and `b` must be of the same type. If they are not, the compiler will attempt an implicit conversion by following the principle of least cost, i.e. the expression that will be converted is the one that cost less to convert. This cost is determined the same way as is done for [matching arguments in function calls](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_overload.html).

If the conversion doesn't work, or the conversion of either expression cost the same, then the compiler will give an error.

The conditional expression can be used as an lvalue, i.e. on the left value of an assignment expression, if both `a` and `b` are lvalues of the same type.

```angelscript
int a, b;
(expr ? a : b) = 42;
```

## Member access

```angelscript
object.property = 1;
object.method();
```

`object` must be an expression resulting in a data type that have members. `property` is the name of a member variable that can be read/set directly. `method` is the name of a member method that can be called on the object.

## Handle-of

```angelscript
// Make handle reference the object instance
@handle = @object;

// Clear the handle and release the object it references
@handle = null;
```

Object handles are references to an object. More than one handle can reference the same object, and only when no more handles reference an object is the object destroyed.

The members of the object that the handle references are accessed the same way through the handle as if accessed directly through the object variable, i.e. with `.` operator.

See also: [Object handles](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_handle.html)

## Parenthesis

```angelscript
a = c * (a + b);
if( (a or b) and c )
{
  // ... do something
}
```

Parenthesis are used to group expressions when the [operator precedence](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_operator_precedence.html) does not give the desired order of evaluation.

## Scope resolution

```angelscript
int value;
void function()
{
  int value;       // local variable overloads the global variable
  ::value = value; // use scope resolution operator to refer to the global variable
}
```

The scope resolution operator `::` can be used to access variables or functions from another scope when the name is overloaded by a local variable or function. Write the scope name on the left (or blank for the global scope) and the name of the variable/function on the right.

See also: [Namespaces](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_namespace.html)

## Type conversions

```angelscript
// implicitly convert the clss handle to a intf handle
intf @a = @clss();

// explicitly convert the intf handle to a clss handle
clss @b = cast<clss>(a);
```

Object handles can be converted to other object handles with the cast operator. If the cast is valid, i.e. the true object implements the class or interface being requested, the operator returns a valid handle. If the cast is not valid, the cast returns a null handle.

The above is called a reference cast, and only works for types that support object handles. In this case the handle still refers to the same object, it is just exposed through a different interface.

Types that do not support object handles can be converted with a value cast instead. In this case a new value is constructed, or in case of objects a new instance of the object is created.

```angelscript
// implicit value cast
int a = 1.0f;

// explicit value cast
float b = float(a)/2;
```

In most cases an explicit cast is not necessary for primitive types, however, as the compiler is usually able to do an implicit cast to the correct type.

## Anonymous objects

Anonymous objects, i.e. objects that are created without being declared as variables, can be instantiated in expressions by calling invoking the object's constructor as if it was a function. Both reference types and value types can be created like this.

```angelscript
// Call the function with a new object of the type MyClass
func(MyClass(1,2,3));
```

For types that support it, the anonymous objects can also be initialized with initialization lists.

```angelscript
// Call the function with a dictionary, explicitly informing the type of the initialization list
func(dictionary = {{'banana',1}, {'apple',2}, {'orange',3}});

// When there is only one possible type that support initialization lists it is possible
// to omit the type and let the compiler implicitly determine it based on the use
funcExpectsAnArrayOfInts({1,2,3,4});
```

If the desired type for the anonymous object is a template, it may be necessary to explicitly inform the template type;

```angelscript
funcExpectsAnArray(array<int> = {1,2,3,4});
```