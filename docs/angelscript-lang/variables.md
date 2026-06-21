<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_variable.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Variables

Global variables may be declared in the scripts, which will then be shared between all contexts accessing the script module.

Variables declared globally like this are accessible from all functions. The value of the variables are initialized at compile time and any changes are maintained between calls. If a global variable holds a memory resource, e.g. a string, its memory is released when the module is discarded or the script engine is reset.

```angelscript
int MyValue = 0;
const uint Flag1 = 0x01;
```

Variables of primitive types are initialized before variables of non-primitive types. This allows class constructors to access other global variables already with their correct initial value. The exception is if the other global variable also is of a non-primitive type, in which case there is no guarantee which variable is initialized first, which may lead to null-pointer exceptions being thrown during initialization.

Be careful with calling functions that may access global variables from within the initialization expression of global variables. While the compiler tries to initialize the global variables in the order they are needed, there is no guarantee that it will always succeed. Should a function access a global variable that has not yet been initialized you will get unpredictable behaviour or a null-pointer exception.