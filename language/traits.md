---
title: "Traits and static dispatch"
description: "Source section - syntax.md \u00a79.5. A trait is a named set of method signatures, `impl Trait for Type` gives them to a datac or enum, and `fun f<T: A + B>` bounds a type parameter. Dispatch is static: no vtable, no dyn."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §9.5](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

A `trait` is a named set of method **signatures**, and `impl` makes a type
provide them. A generic function may then require that its type parameter
implements one. Dispatch is **static**: the method a `T` calls is the one the
concrete type declares, resolved once per instantiation, exactly as
[Generics and type parameters](/language/generics) resolves any type parameter.

## Declaring a trait

```kelp
trait Shape {
    fun Self.area().R: f64
    fun mut Self.scale(f: f64)
}
```

A trait is a top-level declaration. Its body is one or more signatures in the
receiver form of [Methods and receivers](/language/methods), with `Self` where
the method's type would be. A signature is
`fun [mut] Self.name([param, ...])[.R: T]` and has **no body**: no `=` and no
`{ ... }`.

- `Self` names the implementing type. It is also legal in the signature's other
  types, where it means the same thing:
  `fun Self.smaller_than(other: &Self).R: bool`.
- `mut` on the receiver is part of the signature, and the impl has to match it.
- The trait name is an ordinary top-level name. `pub trait Shape` exports it the
  way a `pub datac` is exported, and a trait declared in another module is
  reached through the alias as `shape.Shape`.
- A trait may not declare a type parameter, and neither may one of its methods,
  so `trait Name<T>` and `fun Self.m<T>()` are both refused by name. A signature
  names only `Self`, the types of the declaring module, and what that module
  exports.
- `Drop` is the one name a user cannot use. `trait Drop` is refused where it is
  written, with the destructor spelling in the message:

  ```
  error: the trait 'Drop' is built in: a type's destructor is written 'fun mut T.drop()', not through a trait
  ```

  `fun mut T.drop()` is unchanged, and so is every other compiler-known name
  pair (`hash`/`eq`).

## Implementing a trait

```kelp
datac Circle(var r: f64)

impl Shape for Circle {
    fun Self.area().R: f64 = r * r * 3.14159
    fun mut Self.scale(f: f64) { r = r * f }
}
```

The impl line is `impl Trait for Type { ... }`. The parser tells it from an
import by the token after `impl`: a **string literal** is `impl "path"` (an
import), and an **identifier** is this form. The block declares one method per
declared signature, and each one is an ordinary method, so inside it the type's
fields are read and written by their bare names. The receiver is written
`Self`, not the type's own name, so the block reads the same whether it sits in
the trait's module or the type's.

- **Coherence**: at most one impl of a trait for a type in the whole program. A
  second one is an error naming both:

  ```
  error: trait 'Shape' already has an impl for 'Circle' (written in module 'traits_duplicate_impl'): a trait is implemented for a type at most once
  ```

- **The impl lives in the trait's module or in the type's module**, and nowhere
  else. That is what keeps the type's own module able to add a behaviour, and
  the trait's module able to supply an impl for a type it did not declare,
  without a third module inventing a relation the two owners never agreed to:

  ```
  error: 'impl shape.Shape for circle.Circle' is written in module 'bad', which owns neither: an impl lives in the trait's module ('shape') or in the type's ('circle')
  ```

- **The type has to be a `datac` or an `enum`** declared in the program. A
  builtin (`i32`, `String`, `List<T>`, ...), a tuple, an array, a borrow and a
  generic *instantiation* are each refused by name:

  ```
  error: 'i32' is a builtin type ('i32'), so a trait cannot be implemented for it in this slice: a builtin's operations come from the compiler
  ```

- **Every declared signature must be implemented**, with exactly the declared
  signature: the same receiver spelling (`Self`, with or without `mut`), the
  same parameter names and types in the same order, and the same return type. A
  missing method, an extra method, a mismatched signature and a mismatched
  receiver are distinct errors, each naming the trait and the method.

  ```
  error: trait 'Shape' declares 'fun Self.name().R: str', and 'impl Shape for Circle' does not implement it: add 'fun Self.name().R: str { ... }' to the block
  error: 'shrink' is not declared by trait 'Shape': an 'impl' implements exactly the trait's methods, so remove it or add the signature to the trait
  error: method 'area' does not match trait 'Shape': the trait declares 'fun Self.area().R: f64', the impl writes 'fun Circle.area().R: i32'
  error: method 'grow' takes its receiver differently than trait 'Grow' declares it: the trait writes 'fun mut Self.grow(by: f64)', the impl writes 'fun Circle.grow(by: f64)'
  ```

- **An inherent method of the same name on the same type is refused at the
  impl**, because it would leave two answers to one call. Rename one of them:

  ```
  error: 'impl Shape for Circle' declares 'Circle.area', which 'Circle' already has as an explicit method: a trait method and an explicit method cannot share a name, so rename one of them
  ```

- An impl naming a trait that is not declared gets
  `'impl Shape for Circle' names no declared trait: declare 'trait Shape { ... }' first (or import the module that does)`.

Because a trait impl's methods *are* the type's methods, nothing else changes:
an impl method is reached through a value exactly as an inherent one is, it is
emitted by both backends through the same per-type function, and a trait method
on a type that also declares its own `drop` still drops through the same
generated `kelp_drop_<T>`.

## Bounding a type parameter

A type parameter carries bounds after a `:`, separated by `+`:

```kelp
fun area_of<T: Shape>(s: &T).R: f64 = s.area()
fun describe<T: Shape + Named>(s: &T).R: f64 = s.area() + s.name_length()
```

- **Inside the body, a method call on a `T` resolves exactly as it would on the
  concrete type**, because a generic function's body is already checked once per
  instantiation with `T` bound to the concrete type. The bound is what makes
  that resolution succeed; the emitted call is the ordinary direct call the
  type's method already had.
- **At every call, the type argument must implement every bound.** The check
  runs where the instantiation is created, so a satisfied call compiles to the
  same monomorphized function it would have without the bound, and an
  unsatisfied one is an error naming the callee, the type and the trait:

  ```
  error: the call to 'area_of' needs 'Point' to implement the trait 'Shape', and it does not: write 'impl Shape for Point { ... }' in the trait's module or in the type's
  ```

- Bounds are checked transitively, and that needs no symbolic reasoning:
  `fun f<T: A>(x: &T) { g(x) }` where `g<U: A>` is fine for every type that
  satisfies `f`'s bound, and calling `g<U: B>` from the same body is an error at
  that call as soon as `f` is instantiated with a type that does not implement
  `B`. A generic function that is never called is never checked, exactly as in
  [Generics and type parameters](/language/generics).
- As with any generic function, an explicit instantiation may be written at the
  call site: `area_of<Figure>(s = f)`.

## Static dispatch, end to end

This program compiles and runs with the output shown:

```kelp
trait Shape {
    fun Self.area().R: f64
    fun mut Self.scale(f: f64)
}

datac Circle(var r: f64)

impl Shape for Circle {
    fun Self.area().R: f64 = r * r * 3.14159
    fun mut Self.scale(f: f64) { r = r * f }
}

fun area_of<T: Shape>(s: &T).R: f64 = s.area()

fun main() {
    var c = Circle(r = 2.0)
    print(area_of(c))
    c.scale(f = 2.0)
    print(area_of(c))
}
```

```
12.566360
50.265440
```

Nothing in either backend changes for a trait. There is no vtable, no witness
argument, no new `tir` node and no new C type, so a freestanding build has
traits too.

A trait may be implemented for a `datac` and for an `enum`, and a method on a
generic type may call a bounded generic with the receiver's own parameter. The
cross-module project works both ways the module rule allows: the type's module
implements an imported trait, and the trait's module implements a type it did
not declare (`tests/projects/traits_cross`, which prints `12.000000`, `27.000000`,
`circle`, `ring`, `12.000000`).

## What is deliberately not in this slice

Each of these is refused where it is written, with the message naming the
follow-up:

- **`dyn` and trait objects.** A trait is a bound on a type parameter, not a
  type of its own, so there is no runtime tag and no dynamic dispatch.
  Substituting an `enum` is the workaround.

  ```
  error: 'dyn' trait objects are not in this slice: dispatch is static, so a trait is a bound on a type parameter ('fun f<T: Name>(x: &T)'), and a value that is one of several shapes is an 'enum'
  ```

- **Default methods.** Every method is written in the impl.

  ```
  error: a trait declares method signatures only, so a default body is not in this slice: write the body in the 'impl' block ('impl Name for Type { fun Self.m(...) { ... } })'
  ```

- **Associated types and consts, or any non-`fun` item inside a trait.**

  ```
  error: associated types and consts are not in this slice: a trait declares method signatures only
  ```

- **Trait-bounded `impl Trait` in argument position.** Name the type parameter
  and bound it instead:

  ```
  error: a trait cannot be a parameter's type in this slice: name a type parameter and bound it ('fun f<T: Name>(x: &T)'), rather than writing 'impl Name'
  ```

- **Implementing a trait for a builtin type** (`i32`, `String`, `List<T>`, ...):
  a builtin's methods come from the compiler and its representation is not a
  `datac`'s.

- **`where` clauses.** Write the bound on the parameter:

  ```
  error: a 'where' clause is not in this slice: write the bound on the type parameter itself ('fun f<T: Name>(...)'), and write several of them separated by '+' ('fun f<T: A + B>')
  ```

- **Trait inheritance** (`trait A: B`). List both bounds at the use site:

  ```
  error: a trait cannot inherit in this slice: there are no supertraits, so list every trait a function needs at the bound ('fun f<T: A + B>')
  ```

- **Operator overloading through a trait.** `==`/`!=` still come from a declared
  `eq` ([Operators and expressions](/language/expressions)), and nothing else
  looks at a trait.

Also out: a bound on a method's own type parameters (a method has none beyond its
receiver's), an impl for a generic *instantiation*
(`impl Name for Pair<i32, String>`), a trait that is generic over its types, and
a second impl of a trait for a type.

The bound is a guarantee that the trait's methods exist, not that they are the
only methods in scope: a call to an inherent method of the concrete type, or to
a method of another bound on the same parameter, compiles too.

## See also

- [Generics and type parameters](/language/generics)
- [Methods and receivers](/language/methods)
- [`datac` and `enum`](/language/data-types)
- [Operators and expressions](/language/expressions)
- [Limits in v1](/language/limits)
