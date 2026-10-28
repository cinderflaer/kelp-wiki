---
title: "Errors and panics"
description: "Kelp has no exceptions. A failure is a value, Option or Result, and ? passes it up. A failure with no way to recover is a panic, which ends the process."
isPublished: true
tags: "language, errors"
---
Kelp has **no exceptions and no `try`**. A failure is a value. Use `Option<T>` when
the failure carries nothing, and `Result<T, E>` when it carries a reason. A
condition that cannot be handled becomes a `panic`, which ends the process.

Source: [`syntax.md` §18](/design/syntax).

## `Option` and `Result`

Both are ordinary enums from the standard library. Neither needs an `impl` line:
write `Option<T>` and `Result<T, E>`, or the prefixed `option.Option<T>` and
`result.Result<T, E>` when the module name should show. A file that declares its
own `Option` or `Result` keeps its own type.

| Type | Import | Variants |
| --- | --- | --- |
| `Option<T>` or `option.Option<T>` | none (`impl "std/option"` still works) | `Some(value)`, `None` |
| `Result<T, E>` or `result.Result<T, E>` | none (`impl "std/result"` still works) | `Ok(value)`, `Err(error)` |

Each module provides free functions such as `option.isNone(o = maybe)`, and most
of them also exist as methods, such as `maybe.isNone()`. See
[`std/option`](/stdlib/option) and [`std/result`](/stdlib/result).

```kelp
fun main() {
    val parsed = str.parseI64(s = "41")
    if let Ok(n) = parsed {
        print(n + 1)
    }

    val maybe: Option<i32> = Option.None
    if option.isNone(o = maybe) {
        print("nothing")
    }

    print(result.unwrapOr(r = parsed, fallback = 0))
}
```

## `?`: propagation

`expr?` evaluates `expr`. If it carries a failure, the failure is returned from the
enclosing function. Otherwise the expression's value is the success payload.

```kelp
fun half(n: i64) => result.Result<i64, str.ParseErr> {
    return result.Result.Ok(value = n / 2)
}

fun quarter(n: i64) => result.Result<i64, str.ParseErr> {
    val h = half(n = n)?
    return half(n = h)
}
```

- The enclosing function must return the same kind of enum. When the failure types
  match, the failure passes through unchanged. When they differ, `?` converts it
  through `From`. Given `impl convert.From<str.ParseErr> for AppErr`, a
  `Result<_, str.ParseErr>` can be propagated out of a function that returns
  `Result<_, AppErr>`, and the operator calls `AppErr.from(e)`. Without that impl,
  the error names both types and the impl to write. `Option` has no failure
  payload, so it never converts. See
  [Generic traits, `From` and `?` conversion](/language/generic-traits).
  For a one-off conversion, `result.mapErr` also works.
- A function that returns `unit` has nowhere to propagate to. `main` may return
  `result.Result<unit, E>` instead, and then `?` works at the top level. See
  [Returning Result from `main`](#returning-result-from-main).
- The result composes inside an expression: `1 + half(n = n)?`.
- A failure returns at once, and the frame's locals are dropped as they are for a
  `return`.
- `?` moves the payload out of its operand, so **a borrow cannot be the operand**.
- `?` applies to the expression it is written on. When the success payload is a
  tuple, `?` works on the `Result` and hands the tuple back. With
  `fun mk(n: i32) => result.Result<(i32, i32), String>`, the line
  `val (a, b) = mk(n)?` binds the tuple and takes it apart. Writing `?` on the tuple
  itself is an error, because a tuple is not an `enum` ([Types](/language/types)).

## Returning `Result` from `main`

`main` may return `result.Result<unit, E>` in place of `unit`. Then `?` works at the
top level, and a failure ends the program with a message:

```kelp
fun parse_step(n: i32) => result.Result<i32, String> {
    if n > 2 {
        return result.Result.Err(error = "step ${n} is too large")
    }
    return result.Result.Ok(value = n)
}

fun main() => result.Result<unit, String> {
    val a = parse_step(1)?
    print("a = ${a}")
    val b = parse_step(5)?
    print("b = ${b}")
    return result.Result.Ok(value = ())
}
```

The rules:

- On `Ok`, the program ends with status 0.
- On `Err(e)`, the text of `e` is written to stderr with a newline, and the program
  ends with status 1. The text is what `"${e}"` gives: a `String`, an integer, or any
  type with a `Display` form such as one from `derive(text)` ([`design/traits`](/design/traits)).
  Anything `main` printed before the failure is still on stdout.
- The success type must be `unit`. `main` returning `Result<i32, E>` is refused.
- The name `kelp_main_result` is reserved while `main` returns a `Result`. The
  compiler gives that name to the body, so a function of that name is refused.
- A script (a file of top-level statements) still returns unit, so `?` is refused in
  it.

## `panic` and `assert`

`panic(message)` ends the program with a non-zero status. In a worker thread it ends
that thread instead, and its joiner sees the panic as an `Err` ([`std/thread`](/stdlib/thread#the-panic-policy)).
`assert(cond)` is the checked form, and it panics with `assertion failed`. The message is a `str` or an
owned `String`, so a message built in the failing branch needs no binding and no
`.as_str()`:

```kelp
fun main() {
    val n: i64 = 3
    panic(n.toText())          // toText returns a String, which goes straight in
}
```

Typical messages:

```
panic: assertion failed
panic: i32.to_u64: value out of range
panic: Bytes.get: index out of bounds
panic: String.from_bytes: input is not valid utf-8
```

Most failures that have no value to return are panics. Examples are an index out of
range, popping an empty list, `unwrap` on `None`, a failing system call, and a
division by zero in [`complex.div`](/libraries/complex). A scale mismatch in
[`decimal`](/libraries/decimal) is another.

On bare metal there is no stderr and no process to end. A freestanding project
names its own handler with `[target] panic`, and the handler receives the message.
The handler is either `fun(msg: str)` or `fun(msg: str, file: str, line: u32)`. A
panic inside the handler goes to a double-panic path instead of recursing. See
[Freestanding mode](/language/freestanding#panic-semantics) for both shapes, the
double-panic rule and the table of checks.

One conversion fails in both ways. A narrowing number conversion such as `n.to_byte()`
panics when the value does not fit. `n.try_to_byte()` returns an
[`Option`](/stdlib/option) instead, so the caller decides what to do.

**The divergence rule.** A block whose last statement is `panic(...)` never
returns. So it satisfies any declared return type, including a borrowed one. This
is how a "this cannot happen" accessor is written:

```kelp
fun unwrap<T>(o: &option.Option<T>) => T {
    if let Some(v) = o {
        return v
    }
    panic("Option.unwrap: value is None")
}
```

The rule covers a function body's last statement only. A `panic` cannot be the arm
of an `if` or `when` that produces a value.

## Which to use

| Situation | Tool |
| --- | --- |
| The value may be absent | `Option<T>` |
| The failure has a reason the caller can act on | `Result<T, E>` |
| The failure cannot be handled by the caller | `panic` |
| An invariant that must always hold | `assert` |
| A library accessor for a conversion that is known to be valid | `panic` at the end, under the divergence rule |

## See also

- [`std/option`](/stdlib/option), [`std/result`](/stdlib/result)
- [Return types and `return`](/language/returns)
- [Control flow](/language/control-flow) for `if let` and `when`
- [Generic traits, `From` and `?` conversion](/language/generic-traits)
- [Pitfalls](/language/pitfalls)
