---
title: "Values, types and functions"
description: "Integer and float types, val and var, explicit conversions, functions with a .return type, named arguments and function values, with real compiler errors."
isPublished: true
tags: "tutorial, language"
---
**You will learn:** how values get types, why Kelp never converts numbers for you,
and how to write functions.

## A first program

```kelp
impl "std/option"

const LIMIT: i32 = 10

fun add(a: i32, b: i32).return: i32 = a + b

fun abs_diff(a: i32, b: i32).return: i32 {
    if a > b {
        return a - b
    }
    return b - a
}

fun double(x: i32).return: i32 = x * 2

fun apply(f: fun(i32).return: i32, x: i32).return: i32 = f(x)

fun main() {
    val n = 7
    var total: i64 = 0
    total += n.to_i64()
    total *= 3
    print("total = ${total}")
    val ratio: f64 = n.to_f64() / 2.0
    print("ratio = ${ratio}")
    val wide: i32 = 300
    if let Some(v) = wide.try_to_u8() {
        print("fits ${v}")
    } else {
        print("300 does not fit in a u8")
    }
    print("limit ${LIMIT}, add ${add(a = 2, b = 3)}, diff ${abs_diff(3, 10)}")
    print("apply ${apply(double, 21)}")
    val (lo, hi) = (1, 9)
    print("pair ${lo} ${hi}")
    val c = 'k'
    print("big ${n > 3} char ${c}")
}
```

```text
total = 21
ratio = 3.500000
300 does not fit in a u8
limit 10, add 5, diff 7
apply 42
pair 1 9
big true char k
```

Some of this is new. `impl "std/option"` brings in the `Option` type that the
`if let` uses; [Errors](/tutorial/07-errors) explains it fully.

## Types

The scalar types are `i32`, `i64`, `u8`, `u16`, `u32`, `u64`, `usize`, `isize`,
`f32`, `f64`, `bool` and `char`. A whole-number literal is an `i32` unless the
context asks for another type. A decimal literal is an `f64`. The
[types reference](/language/types) has the full table.

**Kelp never converts numbers implicitly.** Mixing types is an error:

```kelp
fun main() {
    val n = 5
    val x: f64 = n * 1.0
    print(x)
}
```

```text
$ kelpc check bad1.kp
error: operator requires matching numeric operands, found 'i32' and 'f64'
  --> bad1.kp:3:18
```

You convert on purpose with a method. `n.to_f64()` turns an integer into a float,
and `n.to_i64()` turns it into an `i64`. A conversion that might not fit, such as
`300` into a `u8`, has a second form, `try_to_u8()`, that returns an `Option`.
This is why the program above printed the `else` branch. A conversion that does
not fit and is not written with `try_` panics, which ends the program.

A `char` is a Unicode character, not a number. It is not an integer, and a
condition must be a `bool`.

## `val`, `var` and `const`

`val` names a value that cannot change. `var` names one that can. Both need a
starting value, and the type is either inferred from it or written after a colon:

```kelp
fun main() {
    val n = 5
    n = 6
    print(n)
}
```

```text
$ kelpc check bad2.kp
error: cannot assign to 'n': not declared 'var'
  --> bad2.kp:3:5
```

Use `var` when the value changes, and `val` otherwise. `total += 7` is a shorthand
for `total = total + 7`. `const` names a value fixed at compile time, like
`LIMIT` above. Those are the only ways to name a value at the top of a file.

## Functions

```kelp
fun add(a: i32, b: i32).return: i32 = a + b
```

- The parameters are `name: type`.
- The return type comes after the parameter list, written `.return: type`. Kelp has
  no `->`.
- A function with an `=` body returns that expression. A function with a block
  body uses `return`.
- A function with no `.return` returns nothing.

A call may name its arguments: `add(a = 2, b = 3)`. Naming them is useful when
the meaning of a number is not obvious. Positional calls work too.

A function name is a value. The parameter `f` in `apply` has the type
`fun(i32).return: i32`, which means "a function that takes an `i32` and returns an
`i32`", so `apply(double, 21)` passes `double` itself. Kelp does not allow two
functions with the same name, so one name means one function.

Parameters borrow their values by default. The
[next chapters](/tutorial/05-data) explain what that means and how to take
ownership or change a value through a parameter.

## Try it

1. Write `fun fahrenheit(c: f64).return: f64 = c * 9.0 / 5.0 + 32.0`, then print
   it for `0.0` and for `100.0`, once with a positional argument and once with a
   named one.
2. The line `val half: f64 = 7 / 2` does not compile. Why? Fix it in two ways:
   with float literals, and with `.to_f64()`.

Next: [Control flow](/tutorial/03-control-flow).
