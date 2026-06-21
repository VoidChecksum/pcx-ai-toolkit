<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_strings.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Custom string type

Almost all applications have some need to manipulate text strings in one way or another. However most applications have very different needs, and also different ways of representing their string types. For that reason, AngelScript doesn't come with its own built-in string type that the application would be forced to adapt to, instead AngelScript allows the application to [register its own string type](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_api.html).

This article presents the options for customizing the script language to the application's needs with regards to strings. If you do not want, or do not need to have AngelScript use your own string type, then I suggest you use the standard add-on for [std::string registration](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html).

## Registering the custom string type

To make the script language support strings, the string type must first be [registered as type](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_type.html) with the engine. The application is free to use any valid type name, not necessarily 'string', though it is probably the most commonly used name. The custom string type can also be either value type or a reference type at the preference of the application developer.

Once the string type is registered, the application must also provide a string factory to allow the scripts to use literal string constants. The string factory must implement the `asIStringFactory` interface, and be registered with the `asIScriptEngine::RegisterStringFactory` method.

The string factory must implement all 3 methods of the `asIStringFactory` interface. The `GetStringConstant` method receives the raw string data by the compiler and should return a pointer to the custom string object that represents that string. The `ReleaseStringConstant` is called when the engine no longer needs the string constant, e.g. when discarding a module. The `GetRawStringData` is called by the engine when the raw string data is needed, e.g. when saving bytecode or when requesting a copy of a string constant.

Although not necessary, the application should preferably implement caching of the string constants, so that if two calls to GetStringConstant with the same raw string data is received the string factory returns the address of the same string instance in both calls. This will reduce the amount of memory needed to store the string constants, especially when scripts use the same string constants in many places. Remember, when using caching, the ReleaseStringConstant must only free the string object when the last call for that same object is done.

See also: [The standard string add-on](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html)

## Unicode vs ASCII

Is your application using Unicode or plain ASCII for the text? If you use Unicode, then you'll want to encode the scripts in UTF-8, which the AngelScript compiler supports natively. By default AngelScript expects the scripts to have been encoded in UTF-8, but should you prefer ASCII you can turn this off by setting the engine property `asEP_SCRIPT_SCANNER` to 0 right after creating the engine.

```cpp
// Set engine to use ASCII scanner for script code
engine->SetEngineProperty(asEP_SCRIPT_SCANNER, 0);
```

> `asEP_SCRIPT_SCANNER` — Select scanning method: 0 - ASCII, 1 - UTF8. Default: 1 (UTF8).

If you do use Unicode, then you'll also want to choose the desired encoding for the string literals, either UTF-8 or UTF-16. By default the string literals in AngelScript are encoded with UTF-8, but if your application is better prepared for UTF-16 then you'll want to change this by setting the engine property `asEP_STRING_ENCODING` to 1 before compiling your scripts.

```cpp
// Set engine to use UTF-16 encoding for string literals
engine->SetEngineProperty(asEP_STRING_ENCODING, 1);
```

> `asEP_STRING_ENCODING` — Select string encoding for literals: 0 - UTF8/ASCII, 1 - UTF16. Default: 0 (UTF8)

Observe that the string factory called by the engine to create new strings gives the size of the string data in bytes even for UTF-16 encoded strings, so you'll need to divide the size by two to get the number of characters in the string.

## Multiline string literals

There is also a couple of options that affect the script language itself a bit. If you like the convenience of allowing string literals to span multiple lines of code, then you can turn this on by setting the engine property `asEP_ALLOW_MULTILINE_STRINGS` to true. Without this the compiler will give an error if it encounters a line break before the end of the string.

```cpp
// Set engine to allow string literals with line breaks
engine->SetEngineProperty(asEP_ALLOW_MULTILINE_STRINGS, true);
```

> `asEP_ALLOW_MULTILINE_STRINGS` — Allow linebreaks in string constants. Default: false.

Observe that the line ending encoding of the source file will not be modified by the script compiler, so depending on how the file has been saved, you may get strings using different line endings.

The [heredoc strings](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_strings.html) are not affected by this setting, as they are designed to support multiline text sections.

## Character literals

By default AngelScript doesn't have character literals as C and C++ does. A string literal can be written with double quotes or single quotes and still have the same meaning. This makes it convenient to embed scripts in XML files or C/C++ source files where double quotes would otherwise end the script code.

If you want to have single quoted literals mean a single character literal instead of a string, then you can do so by setting the engine property `asEP_USE_CHARACTER_LITERALS` to true. The compiler will then convert single quoted literals to an integer number representing the first character.

```cpp
// Set engine to use character literals
engine->SetEngineProperty(asEP_USE_CHARACTER_LITERALS, true);
```

> `asEP_USE_CHARACTER_LITERALS` — Interpret single quoted strings as character literals. Default: false.

Observe that the `asEP_SCRIPT_SCANNER` property has great importance in this case, as an ASCII character can only represent values between 0 and 255, whereas a Unicode character can represent values between 0 and 1,114,111.