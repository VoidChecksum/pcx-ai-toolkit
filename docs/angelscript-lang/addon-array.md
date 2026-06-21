<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_array.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# array template object

**Path:** /sdk/add_on/scriptarray/

The `array` type is a [template object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_template.html) that allow the scripts to declare arrays of any type. Since it is a generic class it is not the most performatic due to the need to determine characteristics at runtime. For that reason it is recommended that the application registers a [template specialization](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_template.html#doc_adv_template_2) for the array types that are most commonly used.

The type is registered with `RegisterScriptArray(asIScriptEngine *engine, bool defaultArrayType)`. The second parameter should be set to true if you wish to allow the syntax form `type[]` to declare arrays.

Compile the add-on with the pre-processor define `AS_USE_STLNAMES=1` to register the methods with the same names as used by C++ STL where the methods have the same significance. Not all methods from STL is implemented in the add-on, but many of the most frequent once are so a port from script to C++ and vice versa might be easier if STL names are used.

Compile the add-on with the pre-processor define `AS_USE_ACCESSORS=1` to register `length` as a virtual property instead of the method `length()`.

Compile the add-on with the pre-processor define `AS_NO_IMPL_OPS_WITH_STRING_AND_PRIMITIVE=1` to disable the implicit operations with primitives that automatically formats the primitive values to strings.

## Public C++ interface

```cpp
class CScriptArray
{
public:
  // Set the memory functions that should be used by all CScriptArrays
  static void SetMemoryFunctions(asALLOCFUNC_t allocFunc, asFREEFUNC_t freeFunc);

  // Factory functions
  static CScriptArray *Create(asITypeInfo *arrayType);
  static CScriptArray *Create(asITypeInfo *arrayType, asUINT length);
  static CScriptArray *Create(asITypeInfo *arrayType, asUINT length, void *defaultValue);
  static CScriptArray *Create(asITypeInfo *arrayType, void *listBuffer);

  // Memory management
  void AddRef() const;
  void Release() const;

  // Type information
  asITypeInfo *GetArrayObjectType() const;
  int GetArrayTypeId() const;
  int GetElementTypeId() const;

  // Get the current size
  asUINT GetSize() const;

  // Returns true if the array is empty
  bool IsEmpty() const;

  // Pre-allocates memory for elements
  void Reserve(asUINT numElements);

  // Resize the array
  void Resize(asUINT numElements);

  // Get a pointer to an element. Returns 0 if out of bounds
  void *At(asUINT index);
  const void *At(asUINT index) const;

  // Set value of an element.
  // The value arg should be a pointer to the value that will be copied to the element.
  // Remember, if the array holds handles the value parameter should be the
  // address of the handle. The refCount of the object will also be incremented
  void SetValue(asUINT index, void *value);

  // Copy the contents of one array to another (only if the types are the same)
  CScriptArray &operator=(const CScriptArray&);

  // Compare two arrays
  bool operator==(const CScriptArray &) const;

  // Array manipulation
  void InsertAt(asUINT index, void *value);
  void RemoveAt(asUINT index);
  void InsertLast(void *value);
  void RemoveLast();

  void SortAsc();
  void SortAsc(asUINT startAt, asUINT count);
  void SortDesc();
  void SortDesc(asUINT startAt, asUINT count);
  void Sort(asUINT startAt, asUINT count, bool asc);
  void Sort(asIScriptFunction *less, asUINT startAt, asUINT count);
  void Reverse();

  int Find(void *value) const;
  int Find(asUINT startAt, void *value) const;
  int FindByRef(void *ref) const;
  int FindByRef(asUINT startAt, void *ref) const;

  // Returns the address of the inner buffer for direct manipulation
  void *GetBuffer();
};
```

## Public script interface

See also: [Arrays in the script language](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_arrays.html)

## C++ example

This function shows how a script array can be instantiated from the application and then passed to the script.

```cpp
// Registered with AngelScript as 'array<string> @CreateArrayOfString()'
CScriptArray *CreateArrayOfStrings()
{
  // If called from the script, there will always be an active
  // context, which can be used to obtain a pointer to the engine.
  asIScriptContext *ctx = asGetActiveContext();
  if( ctx )
  {
    asIScriptEngine* engine = ctx->GetEngine();

    // The script array needs to know its type to properly handle the elements.
    // Note that the object type should be cached to avoid performance issues
    // if the function is called frequently.
    asITypeInfo* t = engine->GetTypeInfoByDecl("array<string>");

    // Create an array with the initial size of 3 elements
    CScriptArray* arr = CScriptArray::Create(t, 3);

    for( asUINT i = 0; i < arr->GetSize(); i++ )
    {
      // Set the value of each element
      string val("test");
      arr->SetValue(i, &val);
    }

    // The ref count for the returned handle was already set in the array's constructor
    return arr;
  }
  return 0;
}
```