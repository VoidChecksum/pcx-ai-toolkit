> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/regex.md).

# Regex

Registered with `register_addon_regex(engine)`.

ECMAScript regex syntax. The compiled `regex` type is an addon type with a destructor that runs at scope exit.

## Construction

```cpp
regex re("[0-9]+");                       // ctor-form var-decl
regex re2 = regex("\\w+");                // assignment form
regex empty("[");                          // bad pattern → null handle
```

If the pattern fails to compile, the returned handle is 0 (null). Methods on a null handle are safe — they return false / empty.

## Methods

```cpp
bool   f = re.matches("12345")             // entire string matches pattern
bool   h = re.has_match("abc 123")         // any substring matches
string m = re.first("abc 123 def")         // first match text, or ""
array  all = re.find_all("a12 b345 c6")    // array<string> of all matches
string r = re.replace("a12b34", "#")       // "a#b#" (all matches replaced)
array  parts = re.split("a,b,c,d")         // split on matches
array  g = re.groups("name=42")            // [full, group1, group2, ...]
```

**Note:** `match` is a reserved keyword in Enma (used for pattern-matching expressions), so the single-match accessor is named `first`.

## Capture groups

`groups` returns an array where `[0]` is the full match and `[1..n]` are the capture groups in order:

```cpp
regex re = regex("([a-z]+)=([0-9]+)");
array g = re.groups("age=30");
// g[0] == "age=30", g[1] == "age", g[2] == "30"
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/regex.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
