# `std/result`

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
| `unwrap<T, E>(r)` | `T` | panics on `Err` |
| `unwrap_or<T, E>(r, fallback: T)` | `T` | |
| `unwrap_err<T, E>(r)` | `E` | panics on `Ok` |
| `expect<T, E>(r, message: &str)` | `T` | panics with the message on `Err` |
| `expect_err<T, E>(r, message: &str)` | `E` | panics with the message on `Ok` |
| `map<T, U, E>(r, f: closure(&T).R: U)` | `Result<U, E>` | |
| `map_err<T, E, F>(r, f: closure(&E).R: F)` | `Result<T, F>` | |
| `and_then<T, U, E>(r, f: closure(&T).R: Result<U, E>)` | `Result<U, E>` | |
| `or_else<T, E, F>(r, f: closure(&E).R: Result<T, F>)` | `Result<T, F>` | |
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

- `unwrap` needs no `Copy` bound in the *signature* list above because the
  stdlib's generic handling differs from `Option`'s in places; the practical rule
  is the same: an owned payload that cannot be moved out is not `unwrap`-able —
  use `if let`/`when`, which borrow the payload.
- `?` propagates only between *identical* failure payload types. v1 has no error
  conversion, so `Result<i64, String>` cannot be propagated out of a function
  returning `Result<i64, IoErr>`; `map_err` is the bridge.
- A function returning `Unit` — including `main` — has nowhere to propagate to.

## See also

- [`std/option`](option.md)
- [Errors and panics](../language/errors.md)
