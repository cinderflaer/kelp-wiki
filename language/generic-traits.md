---
title: "Generic traits, `From` and `?` conversion"
description: "A trait may take type parameters, `std/convert` declares From and Into, a trait method with no receiver is called on the type, and `?` converts a failure through an `impl From<E1> for E2`. No blanket impls, and no dyn of a generic trait."
isPublished: true
tags: "language, errors"
---
Source section:
[`plan/traits.md` §11](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/traits.md).

A trait can take **type parameters of its own**, so it can say "I convert a `T`"
rather than only "I have these methods". On top of that, `?` converts a failure
through a `From` impl, which is what closed the error-conversion gap
[Errors and panics](/language/errors) used to list. Dispatch stays static, so
neither backend learned a new lowering.

## A trait with parameters

```kelp
trait Scale<T> {
    fun Self.scaled(by: T).R: Self
}
```

The parameter list is the one a `datac`, an `enum` and a `fun` take, written
after the trait's name and before any `:` supertrait list. A parameter is in
scope in every method signature of the trait alongside `Self`. The trait name
**plus its arguments** is one *trait instance*: `Make<i64>` and `Make<bool>` are
different traits to implement and to bound, sharing one declaration. The
arguments an `impl` or a bound writes are a named type (a `datac` or `enum`) or a
builtin type; a container, tuple, array, borrow, function type or handle is
refused where it is written.

## Static methods

A trait method written with **no receiver** is static. It is called on the type,
or through a bounded type parameter, and `Self` as its return type is the
implementing type:

```kelp
trait Scale<T> {
    fun Self.scaled(by: T).R: Self
}

datac Meters(val v: i64)

impl Scale<i64> for Meters {
    fun Self.scaled(by: i64).R: Meters = Meters(v = self.v * by)
}

trait Make<T> {
    fun make(seed: T).R: Self
}

impl Make<i64> for Meters {
    fun make(seed: i64).R: Meters = Meters(v = seed)
}

impl Make<bool> for Meters {
    fun make(seed: bool).R: Meters {
        if seed {
            return Meters(v = 1)
        }
        return Meters(v = 0)
    }
}

fun build<X: Make<i64>>(n: i64).R: X {
    return X.make(seed = n)
}

fun grow<S: Scale<i64>>(s: S).R: S {
    return s.scaled(by = 3)
}

fun main() {
    val five: i64 = 5
    val m = Meters.make(seed = five)
    val t = Meters.make(seed = true)
    print(m.scaled(by = 4).v)
    print(t.v)
    print(grow(m).v)
    val b = build<Meters>(n = 9)
    print(b.v)
    val eleven: i64 = 11
    val c: Meters = Make.make(seed = eleven)
    print(c.v)
}
```

It prints, on both backends:

```
20
1
15
9
11
```

- `Meters.make(seed = five)` is resolved against every impl of every trait that
  declares a static `make`. A type that implements two instances of one trait
  (`Make<i64>` and `Make<bool>`) is dispatched by the **argument type**.
- A bare integer literal is an `i32`, so `Meters.make(seed = 5)` finds no
  `Make<i32>` and is refused (`no static method 'Meters.make' matches the
  argument type(s) 'i32'`). Bind the value to a typed `val` first, as the
  example does. In a bounded function such as `build<X: Make<i64>>(n: i64)` the
  parameter's own type does the job.
- `X.make(seed = n)` inside `build<X: Make<i64>>` is the same call through a
  bound.
- A call written with the trait's name, `Make.make(seed = eleven)`, is accepted
  only where the expected type fixes the implementing type (`val c: Meters =
  Make.make(...)`); otherwise the message points at the `Type.make(...)`
  spelling.
- **A receiver method named the same in two instances is a collision.** Two
  impls of `Scale<i64>` and `Scale<bool>` for one type both declare
  `Meters.scaled`, and a type cannot answer one method name through two traits:

  ```
  error: traits 'Scale' and 'Scale' both declare 'Meters.scaled': one type cannot answer a call of that name through two traits, so rename the method in one of them
  ```

  Only static methods are distinguished by their arguments.

An impl writes the trait's arguments after its name:
`impl Make<i64> for Meters`. There is one impl per (trait instance, type) pair;
a second identical one is a coherence error that names both:

```
error: trait 'std.convert.From' already has an impl for 'T' (written in module 'from_duplicate_impl'): a trait is implemented for a type at most once
```

Writing the wrong number of arguments is refused too (`trait 'std.convert.From'
takes 1 type argument(s), and 'impl std.convert.From for E' writes 0`).

## `std/convert`: `From` and `Into`

[`std/convert`](/stdlib/convert) declares the two conversion traits and nothing
else:

```kelp
pub trait From<T> {
    fun from(value: T).R: Self
}

pub trait Into<T> {
    fun Self.into().R: T
}
```

There are **no blanket impls**: a type that wants `into` writes its own
`impl Into<U> for X`, and `?` uses `From` only.

## `?` converts through `From`

`expr?` is unchanged when the operand's failure type is the enclosing function's
failure type. When the two differ, and an `impl From<E1> for E2` exists where
`E1` is the operand's failure and `E2` the function's, `?` calls `E2.from(e1)`
and returns that:

```kelp
impl "std/convert"
impl "std/result"
impl "std/str"

enum AppErr {
    Parse(val text: String)
    Range(val value: i64)
}

impl convert.From<str.ParseErr> for AppErr {
    fun from(value: str.ParseErr).R: AppErr {
        return AppErr.Parse(text = "not a number")
    }
}

impl convert.From<i64> for AppErr {
    fun from(value: i64).R: AppErr = AppErr.Range(value = value)
}

fun parse(s: &str).R: result.Result<i64, str.ParseErr> {
    return str.parse_i64(s = s)
}

fun small(s: &str).R: result.Result<i64, AppErr> {
    val n = parse(s = s)?
    if n > 100 {
        return result.Result.Err(error = AppErr.from(value = n))
    }
    return result.Result.Ok(value = n)
}

fun show(r: result.Result<i64, AppErr>) {
    when r {
        Ok(v) -> print(v)
        Err(e) -> when e {
            Parse(t) -> print(t)
            Range(v) -> print("too big: ${v}")
        }
    }
}

fun main() {
    show(small(s = "42"))
    show(small(s = "x"))
    show(small(s = "500"))
}
```

```
42
not a number
too big: 500
```

`parse` fails with a `str.ParseErr` and `small` returns an `AppErr`, so the `?`
on `parse(s = s)` goes through the first impl. The value-too-big case builds an
`AppErr` explicitly with `AppErr.from(value = n)`, which picks the second impl
by the argument's type.

- With no matching impl the message names both failure types and the impl to
  write:

  ```
  error: '?' cannot convert a failure: 'std.result.Result<i32, IoErr>' carries 'IoErr' and the enclosing function returns 'std.result.Result<i32, AppErr>', whose failure carries 'AppErr' — write 'impl From<IoErr> for AppErr { fun from(value: IoErr).R: AppErr { ... } }' so the operator has a conversion to call
  ```

- The two enums may be different declarations; only the failure payload may now
  differ, and only through `From`.
- `Some`/`None` has no payload to convert, so `Option` into `Option` is
  unchanged.
- `?` never uses `Into`, so an `Into` impl with no `From` does not convert.
- `result.map_err` still works wherever a one-off conversion is wanted.

## Limits

Each of these is refused where it is written:

- **No blanket impls** (`impl<T> Into<U> for T`), for any trait.
- **`dyn` of a generic trait** (`&dyn`, `Box<dyn>`): the vtable has no slot for a
  parameter.

  ```
  error: '&dyn convert.From' is not allowed: the trait takes type parameters ('T'), and a trait object has no vtable slot for one; use a bounded type parameter ('<T: std.convert.From<...>>') instead
  ```

- **An associated type in a generic trait**
  ([Associated types](/language/associated-types)).
- **A supertrait that itself has arguments** (`trait Sorted<T>: Compare<T>`). A
  supertrait without arguments works.
- **Generic methods** (`fun Self.map<U>(...)`) and generic static methods.
- **An equality constraint or a `where` clause** on a parameter.

The compiler trusts a `From` body like any other method body: nothing requires
the returned value to be built from `value`.

## See also

- [Errors and panics](/language/errors)
- [Traits and static dispatch](/language/traits)
- [`std/convert`](/stdlib/convert)
- [Associated types](/language/associated-types)
