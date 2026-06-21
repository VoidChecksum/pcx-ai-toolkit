<!-- Source: https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_class_inheritance.html
     Fetched: 2026-06-20
     License: AngelScript is licensed under the zlib/libpng license (see license.md).
     Reproduced under that license with attribution to Andreas Jönsson / AngelCode.
     This is the core AngelScript language reference, scraped from the official manual.
     Do not edit manually — regenerate via tools/scrape-angelscript-manual.py (TODO) or re-fetch. -->

# Inheritance and polymorphism

AngelScript supports single inheritance, where a derived class inherits the properties and methods of its base class. Multiple inheritance is not supported, but polymorphism is supported by implementing [interfaces](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_global_interface.html), and code reuse is provided by including [mixin classes](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_script_mixin.html).

All the class methods are virtual, so it is not necessary to specify this manually. When a derived class overrides an implementation, it can extend the original implementation by specifically calling the base class' method using the scope resolution operator. When implementing the constructor for a derived class the constructor for the base class is called using the `super` keyword. If none of the base class' constructors is manually called, the compiler will automatically insert a call to the default constructor in the beginning. The base class' destructor will always be called after the derived class' destructor, so there is no need to manually do this.

```angelscript
// A derived class
class MyDerived : MyBase
{
  // The default constructor
  MyDerived()
  {
    // Calling the non-default constructor of the base class
    super(10);

    b = 0;
  }

  // Overloading a virtual method
  void DoSomething()
  {
    // Call the base class' implementation
    MyBase::DoSomething();

    // Do something more
    b = a;
  }

  int b;
}
```

A class that is derived from another can be implicitly cast to the base class. The same works for interfaces that are implemented by a class. The other direction requires an [explicit cast](https://www.angelcode.com/angelscript/sdk/docs/manual/doc_expressions.html#conversion), as it is not known at compile time if the cast is valid.

```angelscript
class A {}
class B : A {}
void Foo()
{
  A @handle_to_A;
  B @handle_to_B;

  @handle_to_A = A(); // OK
  @handle_to_A = B(); // OK. The reference will be implicitly cast to A@

  @handle_to_B = A(); // Not OK. This will give a compilation error
  @handle_to_B = B(); // OK

  @handle_to_A = handle_to_B; // OK. The reference will be implicitly cast to A@
  @handle_to_B = handle_to_A; // Not OK. This will give a compilation error

  @handle_to_B = cast<B>(handle_to_A); // OK. Though, the explicit cast will return null
                                       // if the object in handle_to_a is not really an
                                       // instance of B
}
```

## Extra control with final, abstract, and override

A class can be marked as 'final' to prevent the inheritance of it. This is an optional feature and mostly used in larger projects where there are many classes and it may be difficult to manually control the correct use of all classes. It is also possible to mark individual class methods of a class as 'final', in which case it is still possible to inherit from the class, but the finalled method cannot be overridden.

Another keyword that can be used to mark a class is 'abstract'. Abstract classes cannot be instantiated, but they can be derived from. Abstract classes are most frequently used when you want to create a family of classes by deriving from a common base class, but do not want the base class to be instantiated by itself. It is currently not possible to mark methods as abstract so all methods must have an implementation even for abstract classes.

```angelscript
// A final class that cannot be inherited from
final class MyFinal
{
  MyFinal() {}
  void Method() {}
}

// A class with individual methods finalled
class MyPartiallyFinal
{
  // A final method that cannot be overridden
  void Method1() final {}

  // Normal method that can still be overridden by derived class
  void Method2() {}
}

// An abstract class
abstract class MyAbstractBase {}
```

When deriving a class it is possible to tell the compiler that a method is meant to override a method in the inherited base class. When this is done and there is no matching method in the base class the compiler will emit an error, as it knows that something wasn't implemented quite the way it was meant. This is especially useful to catch errors in large projects where a base class might be modified, but the derived classes was forgotten.

```angelscript
class MyBase
{
  void Method() {}
  void Method(int) {}
}

class MyDerived : MyBase
{
  void Method() override {}      // OK. The method is overriding a method in the base class
  void Method(float) override {} // Not OK. The method isn't overriding a method in base class
}
```