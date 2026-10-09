---
title: "Tutorial 7: Errors: Option, Result and panic"
description: "Chapter 7 of the Kelp tutorial: failures are values. Option for absence, Result for a reason, the ? operator and its From conversion, and panic for what cannot be handled, with real refusals and a real panic."
isPublished: true
tags: "tutorial, language, errors"
---
Kelp has **no exceptions**. A failure is an ordinary value: `Option<T>` when there is
nothing to say beyond "absent", `Result<T, E>` when there is a reason, and `panic`
when the program cannot go on. The reference is [Errors and panics](/language/errors);
the library halves are [`std/option`](/stdlib/option) and [`std/result`](/stdlib/result).

## The program

```kelp
impl "std/convert"
impl "std/option"
impl "std/result"
impl "std/str"

datac User(val id: i32, val name: String)

enum AppErr {
    BadNumber
    OutOfRange(val value: i64)
}

impl convert.From<str.ParseErr> for AppErr {
    fun from(value: str.ParseErr).return: AppErr = AppErr.BadNumber
}

fun find_user(users: &List<User>, id: i32).return: option.Option<String> {
    for u in users {
        if u.id == id {
            return option.Option.Some(value = u.name.clone())
        }
    }
    return option.Option.None
}

fun parse_age(text: &str).return: result.Result<i64, AppErr> {
    val n = str.parse_i64(text)?
    if n < 0 || n > 150 {
        return result.Result.Err(error = AppErr.OutOfRange(value = n))
    }
    return result.Result.Ok(value = n)
}

fun report(text: &str) {
    when parse_age(text) {
        Ok(n) -> print("age ${n}")
        Err(e) -> when e {
            BadNumber -> print("'${text}' is not a number")
            OutOfRange(v) -> print("${v} is out of range")
        }
    }
}

fun main() {
    var users: List<User> = List.empty()
    users.push(User(id = 1, name = "ada"))
    users.push(User(id = 2, name = "grace"))

    if let Some(name) = find_user(&users, 2) {
        print("found ${name}")
    }
    val missing = find_user(&users, 9)
    print("missing is none: ${option.is_none(missing)}")

    report("42")
    report("x1")
    report("200")
    report("-5")

    val n = result.unwrap_or(str.parse_i64("oops"), 0)
    print("fallback ${n}")
}
```

```text
found grace
missing is none: true
age 42
'x1' is not a number
200 is out of range
-5 is out of range
fallback 0
```

Both backends agreed.

## `Option` and `Result`

They are plain enums (`Some`/`None` and `Ok`/`Err`), so everything from chapter 5
applies: construct them by variant (`option.Option.Some(value = ...)`), take them
apart with `when` or `if let`. Their combinators are free
functions in `std/option` and `std/result` (`option.unwrap_or(missing, 0)`), and
the ones that only borrow are also methods: `missing.is_none()`, `found.map(f)`.
Import the module with `impl "std/option"`.

Two details the program shows. `find_user` returns `option.Option<String>`: the name
is cloned out, because the `Option` must own its payload and `users` is only
borrowed. And `result.unwrap_or(r, 0)` supplies a fallback instead of panicking.

## `?` propagates

`expr?` evaluates `expr`; on a failure it returns that failure from the enclosing
function, and otherwise the expression's value is the success payload. `parse_age`
used it on `str.parse_i64(text)?`. The failure is dropped through the usual
cleanup, exactly like a `return`. The operand cannot be a borrow, and the enclosing
function must itself return an `Option`-shaped or `Result`-shaped enum:

```kelp
impl "std/str"

fun main() {
    val n = str.parse_i64("5")?
    print(n)
}
```

```text
$ kelpc check c7bad2.kp
error: '?' propagates a failure out of the enclosing function, so that function has to return an enum shaped 'Ok'/'Err' or 'Some'/'None' — it returns 'unit'
  --> c7bad2.kp:4:13
```

## `?` converts through `From`

`str.parse_i64` fails with a `str.ParseErr`, but `parse_age` returns an
`AppErr`. When the two failure types differ, `?` calls `AppErr.from(e)`, which
exists because the program wrote

```kelp
impl convert.From<str.ParseErr> for AppErr {
    fun from(value: str.ParseErr).return: AppErr = AppErr.BadNumber
}
```

The trait is `convert.From<T>` from [`std/convert`](/stdlib/convert); the
[generic traits page](/language/generic-traits) covers it, and chapter 9 comes back
to traits. Leave the impl out and the compiler tells you exactly what to write:

```kelp
impl "std/result"
impl "std/str"

enum AppErr {
    BadNumber
}

fun parse(text: &str).return: result.Result<i64, AppErr> {
    val n = str.parse_i64(text)?
    return result.Result.Ok(value = n)
}

fun main() {
    print("unused")
}
```

```text
$ kelpc check c7bad1.kp
error: '?' cannot convert a failure: 'std.result.Result<i64, std.str.ParseErr>' carries 'std.str.ParseErr' and the enclosing function returns 'std.result.Result<i64, AppErr>', whose failure carries 'AppErr' — write 'impl From<std.str.ParseErr> for AppErr { fun from(value: std.str.ParseErr).return: AppErr { ... } }' so the operator has a conversion to call
  --> c7bad1.kp:9:13
```

`std/convert` has no blanket `Into`, and `?` never uses `Into`, only `From`.

## `panic`

`panic(message)` ends the process with a non-zero status, and the language panics for
you on out-of-range indexing, popping an empty list, a bad narrowing conversion and
`unwrap` on `None`. Run this:

```kelp
fun main() {
    var xs: List<i32> = List.empty()
    xs.push(1)
    print("before")
    print(xs.get(5))
    print("after")
}
```

```text
$ ./c7panic; echo "exit $?"      (both streams captured into one file)
panic: List.get: index out of bounds
before
exit 1
```

Notice the order: `panic:` comes before `before`. The panic message goes to stderr
at once, while stdout was a file here and so was buffered until exit; on a terminal
you would see them in order. The exit status is 1 on both backends.

| Situation | Tool |
| --- | --- |
| absent value | `Option<T>` |
| failure with a reason | `Result<T, E>` |
| failure the caller cannot act on | `panic` |
| invariant that must hold | `assert` |

## Exercises

1. Write `half(n: i64).return: Option<i64>` returning `None` for an odd number, and
   `quarter` that uses `?` on `half` and then calls it again.
2. In the first program, what does `report("-5")` print, and which variant of
   `AppErr` is involved? (Decide from the code, then compare with the output.)

<details>
<summary>Solutions</summary>

1.

```kelp
impl "std/option"

fun half(n: i64).return: option.Option<i64> {
    if n % 2 != 0 {
        return option.Option.None
    }
    return option.Option.Some(value = n / 2)
}

fun quarter(n: i64).return: option.Option<i64> {
    val h = half(n)?
    return half(h)
}

fun main() {
    val inputs: [i64; 3] = [8, 6, 7]
    for n in inputs {
        if let Some(q) = quarter(n) {
            print("quarter of ${n} is ${q}")
        } else {
            print("${n} has no whole quarter")
        }
    }
}
```

```text
quarter of 8 is 2
6 has no whole quarter
7 has no whole quarter
```

(`inputs` is annotated `[i64; 3]` because an integer array literal defaults to
`i32`, and `quarter` wants an `i64`.)

2. `-5` parses fine, so the `?` does not fire; the range check `n < 0` does, and
   the result is `Err(AppErr.OutOfRange(value = -5))`. The program prints
   `-5 is out of range`: it is the line after `200 is out of range` in the output above, because the program already runs `report("-5")`.

</details>

Next: [Collections](/tutorial/08-collections).
