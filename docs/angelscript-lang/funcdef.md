<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_funcdef.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Funcdefs

Funcdefs are used to define a function signature that will be used to store pointers to functions with matching signatures. With this a function pointer can be created, which is able to store dynamic pointers that can be invoked at a later time as a normal function call.

```angelscript
// Define a function signature for the function pointer
funcdef bool CALLBACK(int, int);
```

See also: [Function handles](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_funcptr.html) for more information on how to use this.