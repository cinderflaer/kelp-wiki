---
title: "`std/option`"
description: "Option<T> and its combinators. Ungated."
isPublished: true
tags: "stdlib, errors"
---
`Option<T>` and its combinators. Ungated.

```kelp
impl "std/option"
```

```kelp
enum Option<T> {
    Some(val value: T)
    None
}
```

The enum is the point: `Some`/`None` is one of the two shapes `?` and `if let`
understand, so a function that can fail one way returns `Option<T>` and its caller
writes `val x = f(...)?`. Nothing in the compiler knows this module exists: the
*shape* is the contract, so a program's own `Option` works identically.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `is_some<T>(o)` / `is_none<T>(o)` | `bool` | |
| `unwrap<T>(o)` | `T` | **`T` must be `Copy`**; panics on `None` |
| `unwrap_or<T>(o, fallback: T)` | `T` | **`T` must be `Copy`** |
| `expect<T>(o, message: &str)` | `T` | **`T` must be `Copy`**; panics with the message |
| `map<T, U>(o, f: closure(&T).R: U)` | `Option<U>` | |
| `and_then<T, U>(o, f: closure(&T).R: Option<U>)` | `Option<U>` | |
| `or_else<T>(o, f: fun().R: Option<T>)` | `Option<T>` | **`T` must be `Copy`** |
| `each<T>(o, f: closure(&T))` | `Unit` | |

There are no methods on `Option`: an `enum` carries no methods in v1, so every
combinator is a free function and takes the option as its first argument.

## Why some of them need `Copy`

An owned payload cannot be read out of an `enum`: a payload binds as a borrow,
and a partial move only takes a field of an owned `datac` local. So
`option.unwrap` on an `Option<String>` is a compile error: the way out is
`if let`/`when`, which borrows the payload, or a `Box` you can `take()` from.

## Example

```kelp
impl "std/option"

fun main() {
    val some = option.Option.Some(value = 7)
    val none: option.Option<i64> = option.Option.None

    print(option.is_some(o = some))          // true
    print(option.is_none(o = none))          // true
    print(option.unwrap(o = some))           // 7
    print(option.unwrap_or(o = none, fallback = 0))   // 0

    val doubled = option.map(o = some, f = fun(x: &i64).R: i64 = x * 2)
    print(option.unwrap(o = doubled))        // 14

    if let Some(v) = some {
        print(v + 1)                         // 8
    }

    option.each(o = some, f = fun(x: &i64) = print(x))
}
```

## Notes

- The payload of a pattern binds as a **copy** for `Copy` types and as a shared
  borrow otherwise, so `if let Some(v) = maybe` where `maybe: Option<Civil>` gives
  you a `&Civil`: pass `v`, not `&v`.
- `unwrap`'s panic message is `Option.unwrap: value is None`; `expect` prints the
  message you give it.
- `Option` is owned and not `Copy`, so passing one to a parameter borrows it and
  you can keep using it, unless the parameter is `move`.

## See also

- [`std/result`](/stdlib/result)
- [Errors and panics](/language/errors)
- [Control flow](/language/control-flow) for `if let` and `when`
