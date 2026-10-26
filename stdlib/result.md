---
title: "`std/result`"
description: "Result<T, E> and its combinators. Ungated."
isPublished: true
tags: "stdlib, errors"
---
`Result<T, E>` and its combinators. Ungated.

Needs no `impl` line: the module is in scope by its own name.

```kelp
enum Result<T, E> {
    Ok(val value: T)
    Err(val error: E)
}
```

`Ok`/`Err` is the other shape the `?` operator understands, so a function that
can fail returns `Result<T, E>` and its caller writes `val v = f(...)?`.

## `Result<unit, E>`

A function that only succeeds or fails has `Result<unit, E>`, which can also be
written `Result<(), E>`: `()` is the type of the absent value, the same type as
`unit`. Since 26.10.4 its success value is written `()`, so `Ok(value = ())`
constructs and matches like any other `Ok`:

```kelp
fun check_positive(x: i32) => result.Result<unit, String> {
    if x > 0 {
        return result.Result.Ok(value = ())
    }
    return result.Result.Err(error = "not positive")
}
```

The `Ok` arm of a `unit` payload occupies no storage. `unit` still cannot be a
tuple element, a `datac` field or a container element ([Types](/language/types)).

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `is_ok<T, E>(r)` / `is_err<T, E>(r)` | `bool` | |
| `unwrap<T, E>(r)` | `T` | **`T` must be `Copy`**; panics on `Err` |
| `unwrap_or<T, E>(r, fallback: T)` | `T` | **`T` must be `Copy`**; the same as `r.unwrap_or(fallback)` |
| `unwrap_err<T, E>(r)` | `E` | **`E` must be `Copy`**; panics on `Ok` |
| `expect<T, E>(r, message: &str)` | `T` | **`T` must be `Copy`**; panics with the message on `Err` |
| `expect_err<T, E>(r, message: &str)` | `E` | **`E` must be `Copy`**; panics with the message on `Ok` |
| `map<T, U, E>(r: move Result<T, E>, f: closure fun(&T) => U)` | `Result<U, E>` | the result is consumed; the rebuilt side may be owned |
| `map_err<T, E, F>(r: move Result<T, E>, f: closure fun(&E) => F)` | `Result<T, F>` | the result is consumed; the rebuilt side may be owned |

The borrowing helpers `and_then`, `or_else` and `each` are **methods** only. They
are written once, on the result as its receiver, and have no free function of the
same name:

| Method | Returns | Notes |
| --- | --- | --- |
| `r.and_then<U>(f: closure fun(&T) => Result<U, E>)` | `Result<U, E>` | **`E` must be `Copy`**: the receiver is a borrow |
| `r.or_else<F>(f: closure fun(&E) => Result<T, F>)` | `Result<T, F>` | **`T` must be `Copy`**: the receiver is a borrow |
| `r.each(f: closure fun(&T))` | `Unit` | |
| `r.unwrap_or(fallback: T)` | `T` | **`T` must be `Copy`**: the receiver is a borrow. The `Err` payload is dropped, not read; see the rule below |
| `r.orExit(message: &str)` | `T` | **`T` must be `Copy`**: the receiver is a borrow. On `Err` the message goes to standard error as one line and the program exits with status 2 (issue #263); see the note below |

`is_ok` and `is_err` keep their free spelling, `result.is_ok(r)`, and each one is
the same as the method `r.is_ok()` or `r.is_err()`. `map` and `map_err` take the
result with `move`, so they stay free functions.

## Example

```kelp
fun main() {
    val ok = str.parse_i64("41")
    val bad = str.parse_i64("nope")

    print(result.is_ok(r = ok))              // true
    print(result.is_err(r = bad))            // true

    if let Ok(v) = ok {
        print(v + 1)                         // 42
    }

    print(result.unwrap_or(r = bad, fallback = 0))   // 0
    print(bad.unwrap_or(-1))                 // -1, the method form

    val doubled = result.map(r = ok, f = fun(v: &i64) => i64 = v * 2)
    if let Ok(v) = doubled {
        print(v)                             // 82
    }

    val described = result.map_err(r = bad, f = fun(e: &str.ParseErr) => String = describe(e))
    if let Err(msg) = described {
        print(msg)
    }
}

fun describe(e: &str.ParseErr) => String = when e {
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
  payload they touch must be `Copy`.
- **Errors that a default hides.** `r.unwrap_or(d)` returns `d` on `Err` and drops
  the error without reading, logging or passing it on, so its error type needs no
  `Copy`. Use it only where the error carries nothing the caller needs: an
  optional setting, or a parse with a plain default. Where the error matters, use
  `when`, `?` or `map_err`, so the caller can see why the step failed. An owned payload read out of an owned
  result comes out with `if let`/`when`, which binds it by value.
- **`orExit` ends the program.** `r.orExit(message)` gives the `Ok` value. On `Err` it writes `message` and a newline to standard error and exits with status 2, with no unwinding and no destructors, the way `process.exit` does. It is for a usage error, such as an argument that does not parse, where the person at the terminal is the one who must act. For a failure the program can handle, use `when`, `?` or `map_err`. The `Err` payload is not read, so its type needs no `Copy`.

  ```kelp
  impl "std/str"
  impl "std/result"

  fun main() {
      val port = str.parse_u64("8080").orExit("bad port")   // 8080
      print(port.toText())
      val bad = str.parse_u64("80x80").orExit("bad port")   // stderr: bad port, exit 2
      print(bad.toText())
  }
  ```
- `?` propagates only between *identical* failure payload types. v1 has no error
  conversion, so `Result<i64, String>` cannot be propagated out of a function
  returning `Result<i64, IoErr>`; `map_err` is the bridge.
- A function returning `Unit` (including `main`) has nowhere to propagate to.

## See also

- [`std/option`](/stdlib/option)
- [Errors and panics](/language/errors)
