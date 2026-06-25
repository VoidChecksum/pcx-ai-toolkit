# Upstream Suggestions for the Enma Language & SDK

> Moved here from the repo root (`SuggestionsEnma.txt`). These are wishlist items for
> the **Enma language team** (upstream, https://enma-1.gitbook.io/enma), not toolkit
> content. They are kept here as reference for toolkit contributors who hit the same
> gaps while writing PCX scripts. If you have access to the upstream, file these as
> GitBook discussions or issues against Enma itself.

The following recommendations are compiled based on the development of the
Perception.cx (PCX) AI scripting toolkit, focusing on reverse engineering
ergonomics, template parity, and tooling enhancement.

## 1. Nesting & Nested Template Fields (Unordered Maps/Sets)

* Issue: Enma currently lacks std::unordered_map and std::unordered_set because
  composing one template's instance as a field within another template is
  not yet supported.
* PCX Impact: Scripts must frequently track entities, cache bones, and map
  game states. The lack of scalar-keyed hash maps restricts developers to
  string-keyed maps or int-keyed imaps (e.g., map<int64, V> is a compile error).
* Recommendation: Resolve the nesting limitation for template fields to enable
  native std::unordered_map<K, V> and std::unordered_set<T> supporting
  arbitrary scalar and struct keys.

Documentation gap: the Maps and Templates docs should state this limit explicitly, including supported key types, unsupported nested-template field patterns, examples such as `map<int64, V>` that fail, and PCX-safe cache patterns using currently supported maps.

## 2. Byte-Wise Pointer Arithmetic (byte* / void*)

* Issue: Pointer arithmetic in Enma is strictly typed (p + n scales by the
  sizeof(T)). Assigning raw integers to pointers is rejected at compile time
  to enforce safety, requiring verbose reinterpret_cast chains to traverse
  game structures.
* PCX Impact: When walking structures (like pBase + offset), reverse engineers
  operate directly in raw byte offsets. Scaling by type size is counter-intuitive
  when dealing with dynamic struct padding or arbitrary memory regions.
* Recommendation: Introduce a native byte* (or void* with byte-wise arithmetic) type
  that permits direct offset additions without scaling, or expose a compiler
  intrinsic for direct offset dereferencing (e.g., read_mem<T>(base, offset)).

Documentation gap: the Pointers docs should include a reverse-engineering section that explains typed scaling, shows safe byte-offset traversal through host memory APIs or casts, and calls out integer-to-pointer assignments that will not compile.

## 3. Overloaded Function Templates

* Issue: Overloaded function templates (selected by call arity) are not supported.
  This prevents compiling recursive variadic templates with a 1-argument
  template base.
* PCX Impact: Developers writing generic serialization routines, net packet
  decoders, or multi-level pointer resolvers must duplicate code rather than
  relying on recursive templates.
* Recommendation: Implement template argument matching for overloaded function
  templates to bring closer parity with C++ template metaprogramming.

Documentation gap: the Templates docs should include a "Known unsupported template patterns" section covering arity-selected overloads, recursive variadic-template base cases, examples that fail, and the simplest replacement patterns.

## 4. Character Packing & std::string Support

* Issue: The implementation of std::string in the standard library is currently
  blocked waiting for Phase 6 character sub-8-byte packing.
* PCX Impact: Game hooks and memory reads frequently read or write narrow
  character arrays (char[N]). The absence of a packed std::string makes
  mapping native C++ struct definitions into Enma scripts error-prone.
* Recommendation: Finalize char-packing to support std::string and allow
  script-level structs to mirror native C++ character arrays layout-wise.

Documentation gap: the String, Types, or struct-layout docs should state the current string and `char` representation, whether script structs can layout-match native `char[N]`, and the safe way to read or write narrow C strings from process memory.

## 5. LSP Type Inference for Template Instantiation

* Issue: Type diagnostics are resolved during the compiler's monomorphization
  phase, which means template errors are only reported at compilation time.
* PCX Impact: Developers using enma-lsp do not receive real-time feedback on
  missing methods on generic types, constraint violations, or syntax errors
  within template definitions.
* Recommendation: Enhance enma-lsp to parse template instantiations on-the-fly
  and provide inline diagnostics/autocomplete within specialized template scopes.

Documentation gap: the LSP and IDE docs should distinguish live editor diagnostics from compile-time-only monomorphization diagnostics, and explain how to force template instantiation checks before relying on generic helper code.