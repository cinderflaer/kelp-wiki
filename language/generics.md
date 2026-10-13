---
title: "Generics and type parameters"
description: "Type parameters on datac, enum and fun, how each use site instantiates them, explicit type arguments, bounds, and generic receivers and methods."
isPublished: true
tags: "language, collections"
---
Source: [`syntax.md` §3 and §9.3](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md).

`datac`, `enum` and `fun` may take type parameters. Each use site instantiates them
into a concrete type, and two instantiations of one template are two different
types with their own generated code.

## Declaring parameters

```kelp
datac Pair<A, B>(val first: A, val second: B)

enum Maybe<T> {
    Some(val value: T)
    None
}

fun identity<T>(x: T) => T = x
```

- The parameter list sits between the name and the `(` or `{`, written as
  `<A, B>`. A function's list sits after its name.
- A parameter is in scope in every field or payload type of its declaration, and
  in a function's parameter list and return type.
- A parameter name cannot be a builtin type name. A generic type cannot share its
  name with a non-generic one.

## Writing an instantiation

The arguments are written wherever a type is written:

```kelp
val p: Pair<i32, String> = Pair(first = 1, second = String.from_str(s = "one"))
val n: Maybe<i32> = Maybe.Some(value = 7)
val xs: List<Maybe<i32>> = List.empty()
```

- The argument count is checked. Writing `Pair` with no arguments is an error that
  names the arguments it needs.
- A type argument must be a concrete type. There is no way to write a parameter at
  a use site.
- A type argument may not be `str` or a reference, because a field or payload may
  not hold a borrow in v1 ([Types](/language/types)).
- A generic type may refer to itself through a `Box` or a `List`, and that is the
  only way to write a recursive generic type.

## Inference

The expected type is consulted first, then each argument:

```kelp
val a: Maybe<i32> = Maybe.Some(value = 7)   // T from the payload
val b: Maybe<i32> = Maybe.None              // T from the expected type only
val p = Pair(first = 1, second = String.from_str(s = "one"))   // A = i32, B = String
```

- A parameter that neither the expected type nor the arguments determine is an
  error that names it, with the fix to write: `val x: Maybe<i32> = ...`.
- An integer literal takes its type from the expected type or from the other
  argument, not from the `i32` default.
- A payload-less variant cannot take an instantiation, because there is no call to
  attach it to. Write the expected type instead, as `b` above does.

## Explicit type arguments

When inference has nothing to go on, the instantiation is written at the call site
as `Name<...>(`. The `<` is written against the name and the `(` against the `>`:

```kelp
val some = Maybe.Some<i64>(value = 7)
print(identity<i32>(x = 5))
```

Write a space before `<` when you mean a comparison. `a < b > (c)` is a comparison
chain; `a<b>(c)` is read as an instantiation and then fails on `b` not being a
type. Adjacency is the one thing that separates the two spellings.

An explicit instantiation with the wrong number of arguments is an error naming the
count, and so is one written on something that is not generic: a non-generic type,
a non-generic function, or a method, whose parameters come from its receiver.

## Generic receivers

A receiver method on a generic type writes the type's own parameters, in order:

```kelp
fun Pair<A, B>.first_of() => A = first
fun mut Pair<A, B>.replace_second(v: B) { second = v }
```

- The parameters must be exactly the type's, in order. A rename is refused with the
  spelling to write.
- The type arguments are the receiver's own instantiation, so `p.first_of()` on a
  `Pair<i32, String>` is instantiated once for `A = i32, B = String`. There is no
  inference to do, and no way to call a method on the template itself.
- **A method may add type parameters of its own** (26.10.3), written after its
  name: `fun Pair<A, B>.map_first<C>(f: fun(A) => C) => Pair<C, B>`. They
  are inferred at the call from the arguments (and the expected type), may carry
  bounds (`<T: Named>`), and work on a plain type too (`fun Box2.map<U>(...)`). A
  name that repeats one of the receiver type's parameters is refused, and a
  `const` parameter of a method's own is not supported yet.
- **A method on a generic `enum` is allowed** (26.10.3): `fun Opt<T>.is_has()` and
  `fun Opt<T>.map<U>(...)` are written like a method on a generic `datac`, and a
  value of the instantiation calls them (`o.map(f)`). A method always borrows its
  receiver, so one that must take the value apart by `move` (`unwrap_or`) stays a
  free function, as in `std/option`.

## Generic functions

A `fun` may take type parameters after its name, and each call site instantiates
them:

```kelp
fun identity<T>(x: T) => T = x
fun empty_of<T>() => List<T> = List.empty()
```

- A parameter or a return type that names `T` is resolved for each instantiation.
- The arguments are inferred from the argument types, and the return type from the
  expected type. That is the only thing `empty_of()` has to go on, so a call with
  nothing to infer from is an error naming the parameter.
- The body is checked once per instantiation, because `T` is a concrete type
  inside it. A generic function that is never called is never checked.
- `main` may not take type parameters.
- A parameter of a non-`Copy` type is a shared borrow, exactly as it is in a
  non-generic function, so `fun first<T>(xs: List<T>) => T` cannot return an owned
  element: `get` borrows it, and only a `Copy` value can come back out of a borrow
  ([Ownership and borrowing](/language/ownership)).

## Bounding a type parameter

A type parameter may carry one or more **bounds** after a `:`, separated by
`+`. The bound names a `trait` ([Traits and static dispatch](/language/traits)):

```kelp
fun area_of<T: Shape>(s: &T) => f64 = s.area()
fun describe<T: Shape + Named>(s: &T) => f64 = s.area() + s.name_length()
```

- At every call, the type argument must implement every bound, and a call that
  does not is an error naming the callee, the type and the trait. The check runs
  where the instantiation is created, so a satisfied call compiles to the same
  monomorphized function it would have without the bound. A supertrait is
  satisfied transitively: a type implementing `B`, where `B: A`, satisfies a
  `T: A` bound and may call `A`'s methods through a `<T: B>`.
- Inside the body, a method call on a `T` resolves against the concrete type
  each instantiation binds, so the code the bound admits is the type's own
  direct call. Dispatch stays static: a bound never adds a vtable.
- Bounds are checked transitively. A bounded generic may call another bounded
  generic with its own parameter, and the inner call is checked when the outer
  function is instantiated.
- The bound goes on the parameter, or in a `where` clause after the signature.
  The `where` clause names a parameter from the `<...>` list:

  ```kelp
  trait Name {
      fun Self.name_len() => i32
  }

  fun show<T>(x: &T) => i32 where T: Name {
      return x.name_len()
  }
  ```
- A bound may name a trait with arguments (`<X: From<i32>>`), and a bounded
  parameter reaches a trait's associated type as `I::Item`
  ([Generic traits](/language/generic-traits),
  [Associated types](/language/associated-types)).
- A parameter may be a compile-time value, `<const N: usize>`
  ([Const generics](/language/const-generics)), and `fun f(x: impl Trait)` is
  sugar for a bounded parameter.
- A trait may also be written behind a borrow as a trait object, `&dyn Name`, or
  owned as `Box<dyn Name>`, which is dynamic dispatch through a vtable and is a
  different mechanism from a bound; see
  [Traits and static dispatch](/language/traits) and
  [Owned trait objects](/language/box-dyn).

## What is not generic

- A method's own `const` parameter is not supported yet.
- A type argument is always a concrete type. There are no higher-rank or
  higher-kinded forms.
- `main` cannot take type parameters.

## See also

- [Types](/language/types)
- [`datac` and `enum`](/language/data-types)
- [Functions](/language/functions)
- [Methods and receivers](/language/methods)
- [Traits and static dispatch](/language/traits)
- [Const generics and `impl Trait` arguments](/language/const-generics)
- [Associated types](/language/associated-types)
- [Limits in v1](/language/limits)
