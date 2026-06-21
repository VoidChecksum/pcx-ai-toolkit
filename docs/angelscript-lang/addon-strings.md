<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# string object

**Path:** /sdk/add_on/scriptstdstring/

This add-on registers the `std::string` type as-is with AngelScript. This gives perfect compatibility with C++ functions that use `std::string` in parameters or as return type.

A potential drawback is that the `std::string` type is a value type, thus may increase the number of copies taken when string values are being passed around in the script code. However, this is most likely only a problem for scripts that perform a lot of string operations.

Register the type with `RegisterStdString(asIScriptEngine*)`. Register the optional split method and global join function with `RegisterStdStringUtils(asIScriptEngine*)`. The optional functions require that the [array template object](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_array.html) has been registered first.

Compile the add-on with the pre-processor define `AS_USE_STLNAMES=1` to register the methods with the same names as used by C++ STL where the methods have the same significance. Not all methods from STL is implemented in the add-on, but many of the most frequent ones are so a port from script to C++ and vice versa might be easier if STL names are used.

Compile the add-on with the pre-processor define `AS_USE_ACCESSORS=1` to register `length` as a virtual property instead of the method `length()`.

## Public C++ interface

Refer to the `std::string` implementation for your compiler.

## Public script interface

See also: [Strings in the script language](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_stdlib_string.html)