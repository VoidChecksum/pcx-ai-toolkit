<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_dictionary.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# dictionary

> **Note**
> Dictionaries are only available in the scripts if the application [registers the support for them](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_dict.html). The syntax for using dictionaries may differ for the application you're working with so consult the application's manual for more details.

The dictionary stores key-value pairs, where the key is a string, and the value can be of any type. Key-value pairs can be added or removed dynamically, making the dictionary a good general purpose container object.

```angelscript
obj object;
obj @handle;

// Initialize with a list
dictionary dict = {{'one', 1}, {'object', object}, {'handle', @handle}};

// Examine and access the values through get or set methods ...
if( dict.exists('one') )
{
  // get returns true if the stored type is compatible with the requested type
  bool isValid = dict.get('handle', @handle);
  if( isValid )
  {
    dict.delete('object');
    dict.set('value', 1);
  }
}
```

Dictionary values can also be accessed or added by using the index operator.

```angelscript
// Read and modify an integer value
int val = int(dict['value']);
dict['value'] = val + 1;

// Read and modify a handle to an object instance
@handle = cast<obj>(dict['handle']);
if( handle is null )
  @dict['handle'] = object;
```

Dictionaries can also be created and initialized within expressions as [anonymous objects](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html#anonobj).

```angelscript
// Call a function that expects a dictionary as input and no other overloads
// In this case it is possible to inform the initialization list without explicitly giving the type
foo({{'a', 1},{'b', 2}});

// Call a function where there are multiple overloads expecting different
// In this case it is necessary to explicitly define the type of the initialization list
foo2(dictionary = {{'a', 1},{'b', 2}});
```

Dictionaries of dictionaries are created using [anonymous objects](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html#anonobj) as well.

```angelscript
dictionary d2 = {{'a', dictionary = {{'aa', 1}, {'ab', 2}}},
                 {'b', dictionary = {{'ba', 1}, {'bb', 2}}}};
```

The dictionary object supports [foreach loops](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_statements.html#while) to easily iterate over all contained elements.

```angelscript
dictionary dict = {{'a',1},{'b',2},{'c',3}};
int sum = 0;

// sum the values and clear the entries
foreach( auto value, auto key : dict ) // The key variable can be omitted if not needed
{
  sum += int(value);
  dict[key] = 0; // use the key to modify the current element in the dictionary
}
```

## Supporting dictionary object

The dictionary object is a [reference type](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_obj.html), so it's possible to use handles to the dictionary object when passing it around to avoid costly copies.

### Operators

**= assignment**
The assignment operator performs a shallow copy of the content.

**[] index operator**
The index operator takes a string for the key, and returns a reference to the [value](#supporting-dictionaryvalue-object). If the key/value pair doesn't exist it will be inserted with a null value.

### Methods

**`void set(const string &in key, ? &in value)`**
**`void set(const string &in key, int64 &in value)`**
**`void set(const string &in key, double &in value)`**
Sets a key/value pair in the dictionary. If the key already exists, the value will be changed.

**`bool get(const string &in key, ? &out value) const`**
**`bool get(const string &in key, int64 &out value) const`**
**`bool get(const string &in key, double &out value) const`**
Retrieves the value corresponding to the key. The methods return false if the key is not found, and in this case the value will maintain its default value based on the type.

**`array<string> @getKeys() const`**
This method returns an array with all of the existing keys in the dictionary. The order of the keys in the array is undefined.

**`bool exists(const string &in key) const`**
Returns true if the key exists in the dictionary.

**`bool delete(const string &in key)`**
Removes the key and the corresponding value from the dictionary. Returns false if the key wasn't found.

**`void deleteAll()`**
Removes all entries in the dictionary.

**`bool isEmpty() const`**
Returns true if the dictionary doesn't hold any entries.

**`uint getSize() const`**
Returns the number of keys in the dictionary.

## Supporting dictionaryValue object

The dictionaryValue type is how the [dictionary](#supporting-dictionary-object) object stores the values. When accessing the values through the dictionary index operator a reference to a dictionaryValue is returned.

The dictionaryValue type itself is a value type, i.e. no handles to it can be held, but it can hold handles to other objects as well as values of any type.

### Operators

**= assignment**
The value assignment operator should be used to copy a value into the dictionaryValue.

**@= handle assignment**
The handle assignment operator should be used to set the dictionaryValue to refer to an object instance.

**cast\<type\> cast operator**
The cast operator is used to dynamically cast the handle held in the dictionaryValue to the desired type. If the dictionaryValue doesn't hold a handle, or the handle is not compatible with the desired type, the cast operator will return a null handle.

**type() conversion operator**
The conversion operator is used to return a new value of the desired type. If no value conversion is found, an uninitialized value of the desired type is returned.