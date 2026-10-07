---
title: "Tutorial 2: Values, types and functions"
description: "Chapter 2 of the Kelp tutorial: integer and float types, val and var, explicit conversions, functions with .return return types, named arguments, function values and tuples, with the real compiler errors."
isPublished: true
tags: "tutorial, language"
---
[Chapter 1](/tutorial/01-hello) got you a running program. This chapter is the
small stuff every later chapter leans on: types, bindings and functions.

## One program, the whole chapter

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

fun apply(f: fun(i32).return: i32, x: i32).return: i32 = f(x)
fun double(x: i32).return: i32 = x * 2

fun main() {
    val n = 7
    var total: i64 = 0
    total += n.to_i64()
    total *= 3
    print("total = ${total}")
    val ratio: f64 = n.to_f64() / 2.0
    print("ratio = ${ratio}")
    val big: u8 = 200
    print("idx = ${big.to_usize()}")
    val wide: i32 = 300
    if let Some(v) = wide.try_to_u8() {
        print("fits ${v}")
    } else {
        print("300 does not fit in a u8")
    }
    print("limit ${LIMIT} add ${add(a = 2, b = 3)} diff ${abs_diff(3, 10)}")
    print("apply ${apply(double, 21)}")
    val (lo, hi) = (1, 9)
    print("pair ${lo} ${hi}")
    val c = 'k'
    print("flag ${n > 3} char ${c}")
}
```

```text
total = 21
ratio = 3.500000
idx = 200
300 does not fit in a u8
limit 10 add 5 diff 7
apply 42
pair 1 9
flag true char k
```

Run on the default LLVM backend and with `KELPC_ORACLE=c`, it prints exactly that on both.

## Types

The scalar types are `i32 i64 u8 u16 u32 u64 usize isize f32 f64 bool char`. The
[Types](/language/types) page has the full table, including which types are `Copy`
and which are owned or borrowed. Two points matter right away.

**There is no implicit numeric conversion.** `n * 1.0` is not a conversion, it is
an error:

```kelp
fun main() {
    val n = 5
    val x: f64 = n * 1.0
    print(x)
}
```

```text
$ kelpc check c2bad2.kp
error: operator requires matching numeric operands, found 'i32' and 'f64'
  --> c2bad2.kp:3:18
```

Convert explicitly: `n.to_f64()`. `to_<T>()` exists on every integer type for
every integer type, widening is exact and **narrowing panics** when the value does
not fit. Where a conversion can lose a value there is a fallible twin,
`try_to_<T>()`, returning an `Option`. The program above uses it: 300 does not fit
in a `u8`, so the `else` branch ran. (`Option` and `if let` are chapters 5 and 7;
the `impl "std/option"` line at the top of the file is what makes the type
available.) A float has no `to_<int>` at all, because it would silently drop the
fraction.

A `char` is a Unicode scalar value, **not** an integer. `if` and `while` take a
`bool` and nothing else converts to one.

## `val`, `var` and `const`

`val` binds once. `var` can be reassigned. Both need an initializer, and the type
is either inferred from it or written after a colon. An integer literal is `i32`
when nothing says otherwise, which is why the program wrote `var total: i64 = 0`.

```kelp
fun main() {
    val n = 5
    n = 6
    val x: i64 = n * 1.0
    print(n)
}
```

```text
$ kelpc check c2bad.kp
error: cannot assign to 'n': not declared 'var'
  --> c2bad.kp:3:5
```

`total += 7` and the other compound forms (`-=`, `*=`, `/=`, `%=`) exist for
arithmetic. Top-level names are not `val`/`var`: they are `const` (a compile-time
constant, like `LIMIT` above) or `pd` passdowns, covered on
[Constants and passdowns](/language/passdowns). See
[Bindings and assignment](/language/bindings) for destructuring and the mutable
path rule.

## Functions

```kelp
fun add(a: i32, b: i32).return: i32 = a + b
```

The return type is written `.return: T` **after** the parameter list. There is no
`->`. An expression body (`= expr`) needs `.return`; a block body ends with
`return expr`; no `.return` means the function returns `Unit`, which holds nothing.
`abs_diff` in the program is the block form.

By default a parameter is a **shared borrow** of the argument; `mut T` means an
exclusive borrow and `move T` takes ownership. You will use all three from chapter 6.

Calls may use **named arguments** with `name = value`, in any order, wherever the
function has more than one parameter: `add(a = 2, b = 3)`. Positional calls are
fine too, and the program mixed them. A user program cannot overload a name.

A bare function name is a **value** whose type is `fun(i32).return: i32`, so
`apply(double, 21)` passes a function as an argument. Closures that capture
variables are chapter 10.

## Tuples

`val (lo, hi) = (1, 9)` takes a tuple apart, and `pair.0` reads one position.
They are covered in [Types](/language/types).

## Exercises

1. Write `fahrenheit(c: f64).return: f64` and print it for 0 and 100 degrees, once
   with a positional argument and once with a named one.
2. The following line fails to compile: `val half: f64 = 7 / 2`. Why, and what is
   the smallest change?

<details>
<summary>Solutions</summary>

1.

```kelp
fun fahrenheit(c: f64).return: f64 = c * 9.0 / 5.0 + 32.0

fun main() {
    print("0 C = ${fahrenheit(0.0)} F")
    print("100 C = ${fahrenheit(c = 100.0)} F")
}
```

```text
0 C = 32.000000 F
100 C = 212.000000 F
```

2. The compiler says:

```text
$ kelpc check c2x2bad.kp
error: cannot assign value of type 'i32' to 'half' declared as 'f64'
  --> c2x2bad.kp:2:5
```

   The right side is two `i32` literals, so it is an `i32` (an integer division);
   the left side is declared `f64`, and nothing converts. Make the literals
   floats, or convert one operand with `.to_f64()`:

```kelp
fun main() {
    val a: f64 = 7.0 / 2.0
    val n: i32 = 7
    val b: f64 = n.to_f64() / 2.0
    print("${a} ${b}")
}
```

```text
3.500000 3.500000
```

</details>

Next: [Control flow and iterators](/tutorial/03-control-flow).
