<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_enums.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Enums

Enums are a convenient way of registering a family of integer constants that may be used throughout the script as named literals instead of numeric constants. Using enums often help improve the readability of the code, as the named literal normally explains what the intention is without the reader having to look up what a numeric value means in the manual.

Even though enums list the valid values, you cannot rely on a variable of the enum type to only contain values from the declared list. Always have a default action in case the variable holds an unexpected value.

The enum values are declared by listing them in an enum statement. Unless a specific value is given for an enum constant it will take the value of the previous constant + 1. The first constant will receive the value 0, unless otherwise specified.

```angelscript
enum MyEnum
{
  eValue0,
  eValue2 = 2,
  eValue3,
  eValue200 = eValue2 * 100
}
```