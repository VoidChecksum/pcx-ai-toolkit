<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_handle.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Object handles

An object handle is a type that can hold a reference to an object. With object handles it is possible to declare more than one variables that refer to the same physical object.

Not all types allow object handles to be used. None of the primitive data types, bool, int, float, etc, can have object handles. Object types registered by the application may or may not allow object handles, depending on how they have been registered.

See also: [Object handles to the application](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_obj_handle.html)

## General usage

An object handle is declared by appending the @ symbol to the data type.

```angelscript
object@ obj_h;
```

This code declares the object handle obj and initializes it to null, i.e. it doesn't hold a reference to any object.

In expressions variables declared as object handles are used the exact same way as normal objects. But you should be aware that object handles are not guaranteed to actually reference an object, and if you try to access the contents of an object in a handle that is null an exception will be raised.

```angelscript
object obj;
object@ obj_h;
obj.Method();
obj_h.Method();
```

Operators like = or any other operator registered for the object type work on the actual object that the handle references. These will also throw an exception if the handle is empty.

```angelscript
object obj;
object@ obj_h;
obj_h = obj;
```

When you need to make an operation on the actual handle, you should prepend the expression with the @ symbol. Setting the object handle to point to an object is for example done like this:

```angelscript
object obj;
object@ obj_h;
@obj_h = @obj;
```

Note that the compiler can often implicitly determine that it is the handle of the object that is needed rather than the actual object itself. In these cases it is not necessary to explicitly prepend the expression with @.

An object handle can be compared against another object handle (of the same type) to verify if they are pointing to the same object or not. It can also be compared against null, which is a special keyword that represents an empty handle. This is done using the identity operator, is.

```angelscript
object@ obj_a, obj_b;
if( obj_a is obj_b ) {}
if( obj_a !is null ) {}
```

Observe, the == and != operators will do a value comparison on the objects referred to by the handles using the [opEquals](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_ops.html#doc_script_class_cmp_ops) or [opCmp](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_ops.html#doc_script_class_cmp_ops) operator overloads. Though, if the expressions are prepended with @ the operators will have the same function as is and !is.

## Object life times

An object's life time is normally for the duration of the scope the variable was declared in. But if a handle outside the scope is set to reference the object, the object will live on until all object handles are released.

```angelscript
object@ obj_h;
{
  object obj;
  @obj_h = @obj;

  // The object would normally die when the block ends,
  // but the handle is still holding a reference to it
}

// The object still lives on in obj_h ...
obj_h.Method();

// ... until the reference is explicitly released
// or the object handle goes out of scope
@obj_h = null;
```

## Object relations and polymorphing

Object handles can be used to write common code for related types, by means of inheritance or interfaces. This allows a handle to an interface to store references to all object types that implement that interface, similarly a handle to a base class can store references to all object types that derive from that class.

```angelscript
interface I {}
class A : I {}
class B : I {}

// Store reference in handle to interface
I @i1 = A();
I @i2 = B();

void function(I @i)
{
  // Functions implemented by the interface can be
  // called directly on the interface handle. But if
  // special treatment is need for a specific type, a
  // cast can be used to get a handle to the true type.
  A @a = cast<A>(i);
  if( a !is null )
  {
    // Access A's members directly
    ...
  }
  else
  {
    // The object referenced by i is not of type A
    ...
  }
}
```

## Const handles

Sometimes it is necessary to hold handles to objects that shouldn't be allowed to be modified. This is done by prefixing the type with 'const', e.g.

```angelscript
obj @a;                      // handle to modifiable object
const obj @b;                // handle to non-modifiable object
```

A handle to a non-modifiable object can refer to both modifiable objects and non-modifiable objects, but the script will not allow the object to be modified through that handle, nor allow the handle to be passed to another handle that would allow modifications.

This syntax is not to be confused with handles that are themselves read-only, i.e. the handle cannot be re-assigned to refer to a different object. Read-only handles like this are declared by adding the 'const' keyword as a suffix after the '@' symbol.

```angelscript
obj @ const c = obj();       // read-only handle to a modifiable object
const obj @ const d = obj(); // read-only handle to a non-modifiable object
```

A read-only handle can only be initialized when declared.