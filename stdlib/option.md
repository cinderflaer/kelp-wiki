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
| `unwrap<T>(o: move Option<T>)` | `T` | the option is consumed; panics on `None` |
| `unwrap_or<T>(o: move Option<T>, fallback: move T)` | `T` | the option and the fallback are consumed |
| `expect<T>(o: move Option<T>, message: &str)` | `T` | the option is consumed; panics with the message |
| `map<T, U>(o, f: closure(&T).R: U)` | `Option<U>` | |
| `and_then<T, U>(o, f: closure(&T).R: Option<U>)` | `Option<U>` | |
| `or_else<T>(o, f: fun().R: Option<T>)` | `Option<T>` | **`T` must be `Copy`**: the receiver is a borrow |
| `each<T>(o, f: closure(&T))` | `Unit` | |

There are no methods on `Option`: it is a generic `enum`, whose template declares
none, so every combinator is a free function and takes the option as its first
argument.

## Where the payload goes

`unwrap`, `unwrap_or` and `expect` hand the payload **out** by value, so they take
the option with `move`. Inside the callee the option is an owned local, so the read
that binds the payload is a partial move: it takes the value out, and the option's
own drop frees the payloads the move left behind. That is what makes
`Option<String>.unwrap()` work. The option is consumed either way, so a caller that
wants to keep it passes a fresh expression (`option.unwrap(o = find(...))`) or
matches it for a tag test (`when o { Some(_) -> .. }`). A pattern that binds an
owned payload takes it out just as `unwrap` does; a `Copy` payload is copied, so
the option stays usable.

`or_else` cannot do that: its receiver is a borrow and its `Some` arm rebuilds the
option out of the payload it borrowed, which is a copy, so it stays `Copy`-only.
The owned form of the same call is `unwrap_or`. `map`, `and_then` and `each` read
the payload through a borrow and work at every instantiation, whether the payload
is owned or `Copy`.

## Example

```kelp
impl "std/option"

fun main() {
    val some: option.Option<i64> = option.Option.Some(value = 7)
    val none: option.Option<i64> = option.Option.None

    print(option.is_some(o = some))          // true
    print(option.is_none(o = none))          // true

    val doubled = option.map(o = some, f = fun(x: &i64).R: i64 = x * 2)
    print(option.unwrap(o = doubled))        // 14

    if let Some(v) = some {
        print(v + 1)                         // 8
    }

    option.each(o = some, f = fun(x: &i64) = print(x))

    // `unwrap` and `unwrap_or` take the option with `move`, so each of them
    // consumes the option it is given: `some` is used last.
    print(option.unwrap(o = some))           // 7
    print(option.unwrap_or(o = none, fallback = 0))   // 0

    // An owned payload comes out of an owned option: `unwrap` takes the option
    // with `move`, so `text` is consumed by the call.
    val text: option.Option<String> = option.Option.Some(value = String.from_str(s = "owned"))
    print(option.unwrap(o = text))           // owned
}
```

## Notes

- The payload of a pattern binds as a **copy** for `Copy` types, **by value**
  when it is owned and the scrutinee is an owned place (a `val`/`var` binding or
  a `move T` parameter), and as a **shared borrow** otherwise. So `if let
  Some(v) = maybe` where `maybe: Option<Civil>` gives you a `Civil` and takes it
  out of `maybe`, while matching a borrow (`maybe: &Option<Civil>`) gives you a
  `&Civil`: pass `v`, not `&v`.
- `unwrap`'s panic message is `Option.unwrap: value is None`; `expect` prints the
  message you give it.
- `Option` is owned and not `Copy`, so passing one to a parameter borrows it and
  you can keep using it, unless the parameter is `move`.

## See also

- [`std/result`](/stdlib/result)
- [Errors and panics](/language/errors)
- [Control flow](/language/control-flow) for `if let` and `when`
