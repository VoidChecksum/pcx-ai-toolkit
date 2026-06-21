<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/ (Doxygen, AngelScript 2.38.0)
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# AngelScript core language reference

This directory holds a curated scrape of the **core AngelScript language reference** from the
official manual at <https://www.angelcode.com/angelscript/sdk/docs/manual/> (Doxygen, version
2.38.0). It documents the AngelScript scripting language itself — data types, expressions,
statements, functions, classes, handles, inheritance, funcdefs/delegates, enums, namespaces,
co-routines, and the standard script add-ons (string, array, dictionary, math). It is **not**
the PCX Perception.cx AngelScript API bindings, which live separately under
`docs/perception/angelscript/`.

AngelScript is licensed under the zlib/libpng license (see `license.md`). All pages here are
reproduced under that license with attribution to Andreas Jönsson / AngelCode. Each `.md` file
carries a provenance + license header identifying its source URL and fetch date.

## Files

| File | Source page | Topic |
| --- | --- | --- |
| `overview.md` | [doc_overview.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_overview.html) | AngelScript overview (engine, modules, contexts, language, memory) |
| `license.md` | [doc_license.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_license.html) | zlib/libpng license text |
| `datatypes.md` | [doc_datatypes.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes.html) | Data types (index of primitives, objects, handles, strings, auto) |
| `strings.md` | [doc_strings.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_strings.html) | Custom string type (registration, Unicode/ASCII, multiline/char literals) |
| `arrays.md` | [doc_arrays.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_arrays.html) | Custom array type (template types, specializations) |
| `dictionary.md` | [doc_datatypes_dictionary.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_dictionary.html) | dictionary type (script-side usage, operators, methods) |
| `expressions.md` | [doc_expressions.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html) | Expressions (assignment, math, logic, comparison, casts, anonymous objects) |
| `statements.md` | [doc_script_statements.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_statements.html) | Statements (if/switch, loops, foreach, break/continue, return, try-catch) |
| `functions.md` | [doc_script_func.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func.html) | Functions (declaration, parameter/return refs, overloading, defaults, anon) |
| `variables.md` | [doc_global_variable.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_variable.html) | Global variables (init order, lifetime) |
| `script-class.md` | [doc_script_class.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class.html) | Script classes (index: constructors, methods, inheritance, ops, accessors) |
| `script-class-props.md` | [doc_script_class_prop.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_prop.html) | Property accessors (virtual + indexed) |
| `inheritance.md` | [doc_script_class_inheritance.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_inheritance.html) | Inheritance and polymorphism (super, final, abstract, override, casts) |
| `handles.md` | [doc_script_handle.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_handle.html) | Object handles (usage, lifetimes, polymorphing, const handles) |
| `generics.md` | [doc_generic.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_generic.html) | The generic calling convention (embedding; template types are the script-side "generics") |
| `funcdef.md` | [doc_global_funcdef.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_funcdef.html) | Funcdefs (function signature definitions) |
| `delegate.md` | [doc_datatypes_funcptr.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_funcptr.html) | Function handles and delegates |
| `enums.md` | [doc_global_enums.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_enums.html) | Enums (named integer constants) |
| `namespaces.md` | [doc_global_namespace.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_namespace.html) | Namespaces and `using namespace` |
| `coroutines.md` | [doc_adv_coroutine.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_adv_coroutine.html) | Co-routines (embedding-side; no standalone script coroutine page exists) |
| `addons-overview.md` | [doc_addon.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon.html) | Add-ons overview and script extensions index |
| `addon-strings.md` | [doc_addon_std_string.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_std_string.html) | std::string add-on (scriptstdstring) |
| `addon-array.md` | [doc_addon_array.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_array.html) | array template object add-on (scriptarray) |
| `addon-dictionary.md` | [doc_addon_dict.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_dict.html) | dictionary object add-on (scriptdictionary) |
| `addon-math.md` | [doc_addon_math.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_math.html) | math functions add-on (scriptmath, complex type) |

## Requested filenames that do not exist on the server

The task brief named several pages whose exact URLs return HTTP 404 on the manual server. For
each, the table above used the real manual page covering the same topic:

| Requested (404) | Real page used |
| --- | --- |
| `doc_statements.html` | `doc_script_statements.html` |
| `doc_functions.html` | `doc_script_func.html` |
| `doc_variables.html` | `doc_global_variable.html` |
| `doc_inheritance.html` | `doc_script_class_inheritance.html` |
| `doc_handle.html` | `doc_script_handle.html` |
| `doc_funcdef.html` | `doc_global_funcdef.html` |
| `doc_delegate.html` | `doc_datatypes_funcptr.html` (covers delegates) |
| `doc_enum.html` | `doc_global_enums.html` |
| `doc_namespace.html` | `doc_global_namespace.html` |
| `doc_coroutine.html` | `doc_adv_coroutine.html` (embedding-side; no script coroutine page) |
| `doc_dictionary.html` | `doc_datatypes_dictionary.html` |
| `doc_addon_1.html` | `doc_addon.html` |
| `doc_addon_strings.html` | `doc_addon_std_string.html` |

## Not included (deferred)

The following manual pages were intentionally **not** scraped. They are either C++ embedding /
engine-registration material (out of scope for a script-writer language reference) or remaining
add-on / sample / good-practice pages. A future contributor can fetch them to extend coverage.

### C++ embedding / registration (engine-side, not the script language)

- [doc_register_api.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_api.html) — registering the API
- [doc_register_func.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_func.html)
- [doc_register_prop.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_prop.html)
- [doc_register_type.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_type.html)
- [doc_register_obj.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_obj.html)
- [doc_register_global.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_register_global.html)
- [doc_callbacks.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_callbacks.html)
- [doc_exceptions.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_exceptions.html)
- [doc_adv_*](https://www.angelcode.com/angelscript/sdk/docs/manual/) — all `doc_advanced_*` / `doc_adv_*` embedding pages (templates, access masks, concurrent scripts, custom options, etc.)
- [doc_module.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_module.html)
- [doc_call_script_func.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_call_script_func.html)
- [doc_debug.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_debug.html)
- [doc_memory.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_memory.html)
- [doc_gc.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_gc.html)

### Remaining script-side / reference pages not scraped

- [doc_datatypes_primitives.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_primitives.html) — primitives
- [doc_datatypes_obj.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_obj.html) — objects and handles
- [doc_datatypes_strings.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_strings.html) — string literals / heredoc
- [doc_datatypes_arrays.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_arrays.html) — array script usage
- [doc_datatypes_auto.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_auto.html) — auto declarations
- [doc_script_class_desc.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_desc.html), [doc_script_class_construct.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_construct.html), [doc_script_class_memberinit.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_memberinit.html), [doc_script_class_destruct.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_destruct.html), [doc_script_class_methods.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_methods.html), [doc_script_class_private.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_private.html), [doc_script_class_ops.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_ops.html) — class sub-topics
- [doc_script_func_decl.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_decl.html), [doc_script_func_ref.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_ref.html), [doc_script_func_retref.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_retref.html), [doc_script_func_overload.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_overload.html), [doc_script_func_defarg.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_func_defarg.html), [doc_script_anonfunc.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_anonfunc.html) — function sub-topics
- [doc_global_func.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_func.html), [doc_global_virtprop.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_virtprop.html), [doc_global_class.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_class.html), [doc_global_interface.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_interface.html), [doc_script_mixin.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_mixin.html), [doc_global_typedef.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_typedef.html), [doc_global_import.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_import.html)
- [doc_script_shared.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_shared.html) — shared script entities
- [doc_operator_precedence.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_operator_precedence.html) — operator precedence
- [doc_reserved_keywords.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_reserved_keywords.html) — reserved keywords/tokens
- [doc_script_bnf.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_bnf.html) — script language grammar
- [doc_script_stdlib.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_stdlib.html) — standard library index
- [doc_good_practice.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_good_practice.html) — good practices
- [doc_samples.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_samples.html) and [doc_samples_corout.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_samples_corout.html) — samples

### Remaining add-on pages not scraped

- [doc_addon_application.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_application.html) — application module add-ons
- [doc_addon_any.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_any.html) — any object
- [doc_addon_handle.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_handle.html) — ref object
- [doc_addon_weakref.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_weakref.html) — weakref object
- [doc_addon_file.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_file.html) — file object
- [doc_addon_filesystem.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_filesystem.html) — filesystem object
- [doc_addon_grid.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_grid.html) — grid template object
- [doc_addon_datetime.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_datetime.html) — datetime object
- [doc_addon_socket.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_socket.html) — socket object
- [doc_addon_helpers_try.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_helpers_try.html) — exception routines
- [doc_addon_ctxmgr.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_ctxmgr.html) — context manager (default co-routine impl)
- [doc_addon_autowrap.html](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_autowrap.html) — automatic wrapper functions