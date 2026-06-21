<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_namespace.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Namespaces

Namespaces can be used to organize large projects in logical units that may be easier to remember. When using namespaces it is also not necessary to worry about using names for entities that may exist in a different part of the project under a different namespace.

```angelscript
namespace A
{
  // Entities in a namespace see each other normally.
  void function() { variable++; }
  int variable;
}

namespace B
{
  // Entities in different namespaces don't immediately see each other and
  // can reuse the same name without causing name conflicts. By using the
  // scoping operator the entity from the desired namespace can be explicitly
  // informed.
  void function() { A::function(); }
}
```

Observe that in order to refer to an entity from a different namespace the scoping operator must be used, unless it is a parent namespace in which case it is only necessary if the child namespace declare the same entity.

```angelscript
int var;
namespace Parent
{
  int var;
  namespace Child
  {
    int var;
    void func()
    {
      // Accessing variable in parent namespace requires
      // specifying the scope if an entity in a child namespace
      // uses the same name
      var = Parent::var;

      // To access variables in global scope the scoping
      // operator without any name should be used
      Parent::var = ::var;
    }
  }
}

void func()
{
  // Access variable in a nested namespace requires
  // fully qualified scope specifier
  int var = Parent::Child::var;
}
```

## Using namespace

In order to avoid having to always prefix symbols with their namespace it is also possible to use 'using namespace' to tell the compiler to also search for symbols in a specific namespace.

```angelscript
namespace test
{
  void func() {}
}
using namespace test;
void main()
{
  func(); // The function will be found within the test namespace
}
```

If 'using namespace' is used globally or within a namespace, the symbols from the given namespace will be visible throughout the entire enclosing namespace.

See also: [Statement 'using namespace'](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_statements.html#using_ns)