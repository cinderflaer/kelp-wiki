---
title: "`std/result`"
description: "Result<T, E> and its combinators. Ungated."
isPublished: true
tags: "stdlib, errors"
---
`Result<T, E>` and its combinators. Ungated.

```kelp
impl "std/result"
```

```kelp
enum Result<T, E> {
    Ok(val value: T)
    Err(val error: E)
}
```

`Ok`/`Err` is the other shape the `?` operator understands, so a function that
can fail returns `Result<T, E>` and its caller writes `val v = f(...)?`.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `is_ok<T, E>(r)` / `is_err<T, E>(r)` | `bool` | |
| `unwrap<T, E>(r)` | `T` | **`T` must be `Copy`**; panics on `Err` |
| `unwrap_or<T, E>(r, fallback: T)` | `T` | **`T` must be `Copy`** |
| `unwrap_err<T, E>(r)` | `E` | **`E` must be `Copy`**; panics on `Ok` |
| `expect<T, E>(r, message: &str)` | `T` | **`T` must be `Copy`**; panics with the message on `Err` |
| `expect_err<T, E>(r, message: &str)` | `E` | **`E` must be `Copy`**; panics with the message on `Ok` |
| `map<T, U, E>(r: move Result<T, E>, f: closure(&T).R: U)` | `Result<U, E>` | the result is consumed; the rebuilt side may be owned |
| `map_err<T, E, F>(r: move Result<T, E>, f: closure(&E).R: F)` | `Result<T, F>` | the result is consumed; the rebuilt side may be owned |
| `and_then<T, U, E>(r, f: closure(&T).R: Result<U, E>)` | `Result<U, E>` | **`E` must be `Copy`**: the receiver is a borrow |
| `or_else<T, E, F>(r, f: closure(&E).R: Result<T, F>)` | `Result<T, F>` | **`T` must be `Copy`**: the receiver is a borrow |
| `each<T, E>(r, f: closure(&T))` | `Unit` | |

As with `Option`, these are free functions: an `enum` carries no methods in v1.

## Example

```kelp
impl "std/result"
impl "std/str"

fun main() {
    val ok = str.parse_i64("41")
    val bad = str.parse_i64("nope")

    print(result.is_ok(r = ok))              // true
    print(result.is_err(r = bad))            // true

    if let Ok(v) = ok {
        print(v + 1)                         // 42
    }

    print(result.unwrap_or(r = bad, fallback = 0))   // 0

    val doubled = result.map(r = ok, f = fun(v: &i64).R: i64 = v * 2)
    if let Ok(v) = doubled {
        print(v)                             // 82
    }

    val described = result.map_err(r = bad, f = fun(e: &str.ParseErr).R: String = describe(e))
    if let Err(msg) = described {
        print(msg)
    }
}

fun describe(e: &str.ParseErr).R: String = when e {
    Empty -> "the text had no digits"
    Invalid -> "the text had digits then junk"
}
```

## Notes

- The helpers split by what their receiver is. `map` and `map_err` take the
  result with `move`, because each hands the side it did not transform back
  inside a fresh result: `map` over a `Result<T, Bad>` moves the `Bad` on, and
  `map_err` over a `Result<String, E>` moves the `String` on, so an owned
  success or error type works. The rest read through a borrow: `unwrap`,
  `unwrap_or`, `unwrap_err`, `expect`, `expect_err`, `and_then` and `or_else`
  hand a payload out by value or rebuild the side they did not transform, so the
  payload they touch must be `Copy`. An owned payload read out of an owned
  result comes out with `if let`/`when`, which binds it by value.
- `?` propagates only between *identical* failure payload types. v1 has no error
  conversion, so `Result<i64, String>` cannot be propagated out of a function
  returning `Result<i64, IoErr>`; `map_err` is the bridge.
- A function returning `Unit` (including `main`) has nowhere to propagate to.

## See also

- [`std/option`](/stdlib/option)
- [Errors and panics](/language/errors)
