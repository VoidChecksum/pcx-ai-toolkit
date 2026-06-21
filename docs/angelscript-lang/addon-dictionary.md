<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_addon_dict.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# dictionary object

**Path:** /sdk/add_on/scriptdictionary/

The dictionary object maps string values to values or objects of other types.

Register with `RegisterScriptDictionary(asIScriptEngine*)`.

Compile the add-on with the pre-processor define `AS_USE_STLNAMES=1` to register the methods with the same names as used by C++ STL where the methods have the same significance. Not all methods from STL is implemented in the add-on, but many of the most frequent once are so a port from script to C++ and vice versa might be easier if STL names are used.

## Public C++ interface

```cpp
typedef std::string dictKey;

class CScriptDictionary
{
public:
  // Factory functions
  static CScriptDictionary *Create(asIScriptEngine *engine);

  // Reference counting
  void AddRef() const;
  void Release() const;

  // Perform a shallow copy of the other dictionary
  CScriptDictionary &operator=(const CScriptDictionary &other);

  // Sets a key/value pair
  void Set(const dictKey &key, void *value, int typeId);
  void Set(const dictKey &key, asINT64 &value);
  void Set(const dictKey &key, double &value);

  // Gets the stored value. Returns false if the value isn't compatible with informed type
  bool Get(const dictKey &key, void *value, int typeId) const;
  bool Get(const dictKey &key, asINT64 &value) const;
  bool Get(const dictKey &key, double &value) const;

  // Index accessors. If the dictionary is not const it inserts the value if it doesn't already exist.
  // If the dictionary is const then a script exception is set if it doesn't exist and a null pointer is returned
  CScriptDictValue *operator[](const dictKey &key);
  const CScriptDictValue *operator[](const dictKey &key) const;

  // Returns the type id of the stored value, or negative if it doesn't exist
  int GetTypeId(const dictKey &key) const;

  // Returns true if the key is set
  bool Exists(const dictKey &key) const;

  // Returns true if the dictionary is empty
  bool IsEmpty() const;

  // Returns the number of keys in the dictionary
  asUINT GetSize() const;

  // Deletes the key
  bool Delete(const dictKey &key);

  // Deletes all keys
  void DeleteAll();

  // Get an array of all keys
  CScriptArray *GetKeys() const;

  // STL style iterator
  class CIterator
  {
  public:
    void operator++();    // Pre-increment
    void operator++(int);  // Post-increment
    bool operator==(const CIterator &other) const;
    bool operator!=(const CIterator &other) const;

    // Accessors
    const dictKey &GetKey() const;
    int GetTypeId() const;
    bool GetValue(asINT64 &value) const;
    bool GetValue(double &value) const;
    bool GetValue(void *value, int typeId) const;
    const void * GetAddressOfValue() const;
  };

  CIterator begin() const;
  CIterator end() const;
  CIterator find(const dictKey &key) const;
};
```

## Public script interface

See also: [Dictionaries in the script language](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_datatypes_dictionary.html)

## Example usage from C++

Here's a skeleton for iterating over the entries in the dictionary. For brevity the code doesn't show how to interpret the values, for more information on that see `asETypeIdFlags` and `asIScriptEngine::GetTypeInfoById`.

```cpp
void iterateDictionary(CScriptDictionary *dict)
{
  // Iterate over each entry
  for (auto it : *dict)
  {
    // Determine the name of the key
    std::string keyName = it.GetKey();
    cout << "\"" << keyName << "\"" << " = ";

    // Get the type and address of the value
    int typeId = it.GetTypeId();
    const void *addressOfValue = it.GetAddressOfValue();

    // Cast the value to the correct C++ type according to the typeId and then print it
    ...
  }
}
```