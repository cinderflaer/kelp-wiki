---
title: "`std/option`"
description: "Option<T> and its combinators. Ungated."
isPublished: true
tags: "stdlib, errors"
---
`Option<T>` and its combinators. Ungated.

Needs no `impl` line: the module is in scope by its own name.

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
| `is_some<T>(o)` / `is_none<T>(o)` | `bool` | the same as `o.is_some()` and `o.is_none()` |
| `unwrap<T>(o: move Option<T>)` | `T` | the option is consumed; panics on `None` |
| `unwrap_or<T>(o: move Option<T>, fallback: move T)` | `T` | the option and the fallback are consumed; for an owned payload. A `Copy` payload also has the method form `o.unwrap_or(fallback)` |
| `expect<T>(o: move Option<T>, message: &str)` | `T` | the option is consumed; panics with the message |

The borrowing helpers are **methods**. Each one is written once, as a method on
the option, and takes the option as its receiver:

| Method | Returns | Notes |
| --- | --- | --- |
| `o.is_some()` / `o.is_none()` | `bool` | |
| `o.map<U>(f: closure fun(&T) => U)` | `Option<U>` | |
| `o.and_then<U>(f: closure fun(&T) => Option<U>)` | `Option<U>` | |
| `o.or_else(f: closure fun() => Option<T>)` | `Option<T>` | **`T` must be `Copy`**: the receiver is a borrow |
| `o.each(f: closure fun(&T))` | `Unit` | |
| `o.unwrap_or(fallback: T)` | `T` | **`T` must be `Copy`**: the receiver is a borrow. An owned payload uses the free `option.unwrap_or(o = ..., fallback = ...)` |

`map`, `and_then`, `or_else` and `each` have no free function of the same name.
`is_some` and `is_none` keep their free spelling, `option.is_none(o = x)`, which
is what the rest of the library uses. A method always borrows its receiver, so
`unwrap` and `expect` stay free functions, and the owned form of `unwrap_or` does
too. `unwrap_or` has a method form for a `Copy` payload: `o.unwrap_or(0)`.

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
fun main() {
    val some: option.Option<i64> = option.Option.Some(value = 7)
    val none: option.Option<i64> = option.Option.None

    print(option.is_some(o = some))          // true
    print(option.is_none(o = none))          // true

    val doubled = some.map(fun(x: &i64) => i64 = x * 2)
    print(option.unwrap(o = doubled))        // 14

    if let Some(v) = some {
        print(v + 1)                         // 8
    }

    some.each(fun(x: &i64) = print(x))
    print(some.unwrap_or(0))                 // 7, the method form: `some` is borrowed

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
