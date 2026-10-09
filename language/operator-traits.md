---
title: "Operator traits and `Display`"
description: "std/ops declares Add, Sub, Mul, Div, Rem, Neg and Ord and std/fmt declares Display. Implementing one for a datac or enum gives it the operator, `<` and friends, or `${x}` and print. Both operands are only borrowed. No derive, bitwise or && overloads."
isPublished: true
tags: "language"
---
Source: [`plan/traits.md` §13](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/traits.md).

A `datac` or `enum` can have the arithmetic operators, the order operators and
string interpolation by implementing a trait. `std/ops` declares
one trait per operator and [`std/fmt`](/stdlib/fmt) gains `Display`. Each
operator is a **desugar in the front end** into an ordinary method call, so the
borrow checker and both backends see a plain call and a freestanding image may
use one. This replaces the old rule that there is "no operator overloading": a
user type is overloaded by implementing the trait, and the builtin types are
unchanged.

## The traits

| Trait | Method | Gives |
| --- | --- | --- |
| `ops.Add` | `fun Self.add(rhs: &Self).return: Self` | `a + b` is `a.add(&b)` |
| `ops.Sub` | `fun Self.sub(rhs: &Self).return: Self` | `a - b` |
| `ops.Mul` | `fun Self.mul(rhs: &Self).return: Self` | `a * b` |
| `ops.Div` | `fun Self.div(rhs: &Self).return: Self` | `a / b` |
| `ops.Rem` | `fun Self.rem(rhs: &Self).return: Self` | `a % b` |
| `ops.Neg` | `fun Self.neg().return: Self` | `-a` is `a.neg()` |
| `ops.Ord` | `fun Self.cmp(other: &Self).return: i32` | `<`, `<=`, `>`, `>=` through the sign of `cmp` |
| `fmt.Display` | `fun Self.to_text().return: String` | `"${x}"` and `print(x)` |

`cmp` returns negative for less, zero for equal and positive for greater, like
`memcmp`. Each operator trait takes no type parameters and declares exactly the
one method, so a type either has the operator or does not.

## The module

```kelp
impl "std/ops"
```

`std/ops` is ungated and admitted to the freestanding set. Its whole content is
the seven declarations in [The traits](#the-traits), with no blanket impls and
nothing derived. The traits can be written as `ops.Add` after `impl "std/ops"`.
`std/fmt` supplies `Display`; see [`std/fmt`](/stdlib/fmt).

## An example

```kelp
impl "std/ops"
impl "std/fmt"

datac Vec2(val x: i64, val y: i64)

impl ops.Add for Vec2 {
    fun Self.add(rhs: &Vec2).return: Vec2 = Vec2(x = self.x + rhs.x, y = self.y + rhs.y)
}

impl ops.Sub for Vec2 {
    fun Self.sub(rhs: &Vec2).return: Vec2 = Vec2(x = self.x - rhs.x, y = self.y - rhs.y)
}

impl ops.Neg for Vec2 {
    fun Self.neg().return: Vec2 = Vec2(x = 0 - self.x, y = 0 - self.y)
}

impl fmt.Display for Vec2 {
    fun Self.to_text().return: String {
        var out = String.empty()
        val xs = fmt.int(self.x)
        val ys = fmt.int(self.y)
        out.push_str("(")
        out.push_str(xs.as_str())
        out.push_str(", ")
        out.push_str(ys.as_str())
        out.push_str(")")
        return out
    }
}

datac Version(val major: i32, val minor: i32)

impl ops.Ord for Version {
    fun Self.cmp(other: &Version).return: i32 {
        if self.major != other.major {
            return self.major - other.major
        }
        return self.minor - other.minor
    }
}

fun sum_all<T: ops.Add>(a: T, b: T, c: T).return: T = a + b + c

fun main() {
    val a = Vec2(x = 1, y = 2)
    val b = Vec2(x = 10, y = 20)
    val c = a + b - Vec2(x = 1, y = 1)
    print(c)
    print("negated: ${-c}")
    var acc = Vec2(x = 1, y = 2)
    acc += b
    print(acc.to_text())
    print(sum_all(a, b, c))
    val v1 = Version(major = 1, minor = 9)
    val v2 = Version(major = 2, minor = 0)
    print(v1 < v2)
    print(v1 >= v2)
}
```

It prints, identically on both backends:

```
(10, 21)
negated: (-10, -21)
(11, 22)
(21, 43)
true
false
```

- `a + b - Vec2(...)` chains: each `+` or `-` calls the method and the result is
  a fresh `Vec2`.
- `print(c)` and `"negated: ${-c}"` go through `to_text`.
- `acc += b` keeps the long-standing desugar `acc = acc + b`, so it becomes
  `acc = acc.add(&b)`. `-=`, `*=`, `/=` and `%=` follow their operators.
- `sum_all<T: ops.Add>` uses `+` on a type parameter. A generic body is checked
  once per concrete type, so `T` is a `Vec2` by the time the operator is lowered.
- `v1 < v2` and `v1 >= v2` come from `Ord`.

## The rules

- **Operands are borrowed, not moved.** `a + b` leaves `a` and `b` owned and
  valid, which is why `add` takes `&Self`. Both operands are evaluated once, left
  to right.
- **Both operands must be the same type**, a borrow of it counting. Two different
  user types, or a user type and a number, are refused:

  ```
  error: cannot use '+' on 'A' and 'B': the operands must have the same type
  ```

- **A type without the trait is refused, and the message names it:**

  ```
  error: cannot use '+' on 'P': it does not implement 'Add' from 'std/ops' (write 'impl Add for P { fun Self.add(rhs: &Self).return: P }', importing 'std/ops')
  ```

- **`Ord` is not equality.** `==` and `!=` still come from a declared `eq`
  ([Operators and expressions](/language/expressions)); a type with `Ord` and no
  `eq` has no `==`:

  ```
  error: cannot compare 'P' values with '==': '==' and '!=' come from a declared 'eq' method, and 'Ord' does not supply one; write 'fun P.eq(other: &P).return: bool'
  ```

  A type with only `eq` still has no `<`.
- **`Display` in a template.** A `datac` or `enum` without it is refused, and the
  message shows the impl to write:

  ```
  error: cannot interpolate a value of type 'P' into a string template: it does not implement 'Display' (write 'impl fmt.Display for P { fun Self.to_text().return: String }', importing 'std/fmt')
  ```

  The receiver is a borrow, so printing leaves the value owned. `x.to_text()`
  may be called directly wherever the method is declared.
- **A template is not a value.** `to_text` has to build its `String` with
  `String.empty()` and `push_str`, `fmt.*` or `str.concat`; writing
  `"(${self.x}, ${self.y})"` as a return value is refused.
- **Builtins are untouched.** `i32 + i32`, `f64` arithmetic and the formatting of
  numbers, `bool`, `char`, `str`, `String`, `Bytes` and `View` are as before, and
  a user `impl Add for i32` is refused by the orphan rule:

  ```
  error: 'impl std.ops.Add for i32' is written in module 'ops_orphan_builtin', but 'i32' is a builtin type, which has no module: implement a trait for a builtin in the trait's own module ('std/ops')
  ```

## What is not overloadable

- Bitwise operators, shifts, `&&`, `||`, `!`, `~` and `?` (`?` converts through
  [`From`](/language/generic-traits) instead).
- Any operator through a trait of your own: the front end names the `std/ops`
  traits by their canonical names, not "any trait with a method called `add`".
- `derive`: the compiler generates no impl. A type has no `<` or `Display` unless
  it writes one.

The compiler trusts each method's shape as declared. It does not check that `add`
really adds, or that `cmp` agrees with `eq` on the same type.

## See also

- [`std/fmt`](/stdlib/fmt)
- [Operators and expressions](/language/expressions)
- [Traits and static dispatch](/language/traits)
