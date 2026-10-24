---
title: "Errors"
description: "Kelp has no exceptions. A missing value is an Option, a failure with a reason is a Result, ? passes a failure up, and panic ends the program. Each rule with its real output."
isPublished: true
tags: "tutorial, language, errors"
---
**You will learn:** how Kelp reports failure as a value, how `?` passes it up, and
when a failure should end the program instead.

Kelp has no exceptions and no `try` block. A function that can fail says so in its
return type, so the caller always sees the failure.

## The program

```kelp
impl "std/option"
impl "std/result"
impl "std/str"

fun find(xs: &List<i32>, want: i32) => option.Option<int> {
    var i: int = 0
    while i < xs.len() {
        if xs.get(i) == want {
            return option.Option.Some(value = i)
        }
        i += 1
    }
    return option.Option.None
}

fun half(n: i64) => result.Result<i64, String> {
    if n % 2 == 1 {
        return result.Result.Err(error = String.from_str(s = "odd number"))
    }
    return result.Result.Ok(value = n / 2)
}

fun quarter(n: i64) => result.Result<i64, String> {
    val h = half(n = n)?
    return half(n = h)
}

fun parse_half(text: &str) => result.Result<i64, String> {
    val n = str.parse_i64(s = text)
    if let Ok(v) = n {
        return half(n = v)
    }
    return result.Result.Err(error = String.from_str(s = "not a number"))
}

fun show(text: &str) {
    when parse_half(text) {
        Ok(v) -> print("half of ${text} is ${v}")
        Err(e) -> print("${text}: ${e}")
    }
}

fun main() {
    var xs: List<i32> = List.empty()
    xs.push(4)
    xs.push(6)

    if let Some(i) = find(xs, 6) {
        print("found at ${i}")
    }
    print(option.is_none(o = find(xs, 9)))

    show("10")
    show("7")
    show("ten")

    when quarter(12) {
        Ok(v) -> print("quarter of 12 is ${v}")
        Err(e) -> print("error: ${e}")
    }
    when quarter(6) {
        Ok(v) -> print("quarter of 6 is ${v}")
        Err(e) -> print("error: ${e}")
    }
}
```

```text
found at 1
true
half of 10 is 5
7: odd number
ten: not a number
quarter of 12 is 3
error: odd number
```

## Option: a value that may be missing

`option.Option<T>` is either `Some(value)` or `None`. `find` returns `None` when
the number is not in the list. The caller has to look at the result before it can
use the value, and `if let Some(i) = find(xs, 6)` does that: the block runs only
for `Some`, and `i` is the number inside it.

`option.is_none(o = ...)` is the same test as a function call. A few helpers in
the `option` module are written this way.

The `impl "std/option"` line at the top is what makes the type name available.
Each standard module is imported this way.

## Result: a value or a reason

`result.Result<T, E>` is either `Ok(value)` or `Err(error)`. Use `Result` when the
caller needs to know why something failed. `half` returns an error for an odd
number, and `parse_half` turns a text that is not a number into an error too.

`when` takes both cases apart. Every variant must have an arm, or there must be
an `else ->` arm, so you cannot forget the failure case.

## `?`: pass the failure up

`half(n = n)?` means: if `half` returned `Err`, return that error from
`quarter` right now. If it returned `Ok`, the expression is the number inside.
Without `?`, `quarter` would need a `when` or `if let` for each call. With it, the
happy path reads straight through. The function that uses `?` must return a
`Result` with a compatible error type.

## panic: when there is nothing to do

A panic ends the program with a message and exit status 1. Use it when the
program has reached a state that should never happen, or when a failure has no
sensible recovery. `assert(cond)` is a check that panics with
`assertion failed` when `cond` is false.

```kelp
fun main() {
    val n: i64 = 3
    assert(n == 3)
    panic("n was not 3")
}
```

```text
panic: n was not 3
```

Some operations panic on their own. Reading past the end of a list is one:

```kelp
fun main() {
    var xs: List<i32> = List.empty()
    xs.push(1)
    print(xs.get(7))
}
```

```text
panic: List.get: index out of bounds
```

When the caller can recover, return a value instead. The conversion functions show
the pattern: `n.to_u8()` panics when `n` does not fit, and `n.try_to_u8()` returns
an `Option` for the caller to test.

## Which to use

| Situation | Use |
| --- | --- |
| The value may be absent | `Option<T>` |
| The failure has a reason the caller can act on | `Result<T, E>` |
| The program cannot continue | `panic` or `assert` |

The [errors reference](/language/errors) has the full rules, including how `?`
converts between error types.

## Try it

1. Change `quarter` so that its second `half` call is replaced by `result.Result.Ok(value = h)`.
   Which output line changes?
2. Write `fun first_even(xs: &List<i32>) => option.Option<i32>` that returns
   the first even element, or `None`.

Next: [Collections](/tutorial/08-collections).
