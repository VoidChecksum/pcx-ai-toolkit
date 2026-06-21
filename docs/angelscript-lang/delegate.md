<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_funcptr.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Function handles and delegates

A function handle is a data type that can be dynamically set to point to a global function that has a matching function signature as that defined by the variable declaration. Function handles are commonly used for callbacks, i.e. where a piece of code must be able to call back to some code based on some conditions, but the code that needs to be called is not known at compile time.

To use function handles it is first necessary to [define the function signature](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_funcdef.html) that will be used at the global scope or as a member of a class. Once that is done the variables can be declared using that definition.

Here's an example that shows the syntax for using function handles

```angelscript
// Define a function signature for the function handle
funcdef bool CALLBACK(int, int);

// An example function that shows how to use this
void main()
{
  // Declare a function handle, and set it
  // to point to the myCompare function.
  CALLBACK @func = @myCompare;

  // The function handle can be compared with the 'is' operator
  if( func is null )
  {
    print("The function handle is null\n");
    return;
  }

  // Call the function through the handle, just as if it was a normal function
  if( func(1, 2) )
  {
    print("The function returned true\n");
  }
  else
  {
    print("The function returned false\n");
  }
}

// This function matches the CALLBACK definition, since it has
// the same return type and parameter types.
bool myCompare(int a, int b)
{
  return a > b;
}
```

## Delegates

It is also possible to take function handles to class methods, but in this case the class method must be bound to the object instance that will be used for the call. To do this binding is called creating a delegate, and is done by performing a construct call for the declared function definition passing the class method as the argument.

```angelscript
class A
{
  bool Cmp(int a, int b)
  {
     count++;
     return a > b;
  }
  int count = 0;
}

void main()
{
  A a;

  // Create the delegate for the A::Cmp class method
  CALLBACK @func = CALLBACK(a.Cmp);

  // Call the delegate normally as if it was a global function
  if( func(1,2) )
  {
    print("The function returned true\n");
  }
  else
  {
    print("The function returned false\n");
  }

  printf("The number of comparisons performed is "+a.count+"\n");
}
```