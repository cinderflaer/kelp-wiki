---
title: "Operators and expressions"
description: "Source section - syntax.md \u00a75."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §5](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

## Precedence

Loosest first (§5):

| Level | Operators | Associativity |
| --- | --- | --- |
| 1 | `\|\|` | left |
| 2 | `&&` | left |
| 3 | `==` `!=` | left |
| 4 | `<` `<=` `>` `>=` | left |
| 5 | `\|` (bitwise or) | left |
| 6 | `^` (bitwise xor) | left |
| 7 | `&` (bitwise and) | left |
| 8 | `<<` `>>` | left |
| 9 | `+` `-` | left |
| 10 | `*` `/` `%` | left |
| 11 | unary `-` `!` `~` `&` `&mut` `*`, postfix `?`, call, field access | — |

> **The bitwise operators bind tighter than the comparisons**
>
> Unlike C, and deliberately:
>
> ```kelp
> if flags & MASK == 0 { }   // Kelp: (flags & MASK) == 0
>                            // C:    flags & (MASK == 0) — the classic bug
> ```
>
> `|` stays looser than `^`, which stays looser than `&`, so masking still
> reads the way C programmers expect (`a | b & c` is `a | (b & c)`); only the
> comparison boundary moved.

## Arithmetic

```kelp
val a = 7 / 2        // 3 — integer division truncates toward zero
val b = -7 % 3       // -1 — % follows the dividend's sign, as in C
val c = 7.0 / 2.0    // 3.5
```

- Integer `/` truncates toward zero and `%` follows the dividend's sign.
  **Division by zero is undefined rather than checked.**
- Integer `+`, `-` and `*` overflow is **not checked**: it wraps. If a wrap
  matters, use the checked or saturating helpers in
  [`mathx`](/libraries/mathx).
- Float arithmetic is IEEE: `nan`, `inf` and `-0.0` behave as usual, and
  `math.is_nan` / `math.is_finite` exist to test them.

## Bitwise

`& | ^ << >> ~` require two integers **of the same type** (or one, for `~`) and
produce that type. `bool` is not a bitwise domain: `a & b` on two booleans reads
as a non-short-circuiting `and`, and `&&` is right there.

A shift count is the same type as the value, and a shift by ≥ the width is
undefined, exactly as in C. `>>` on a signed type is arithmetic
(sign-propagating), and `~x` is `0 - x - 1`, so on a `u32` it flips all 32 bits.
Mask it (`~x & 255`) when you wanted a byte.

```kelp
val masked = flags & 3
val high = byte >> 4
val low = byte & 15
val flipped = ~byte
```

## Borrows and dereference

```kelp
val r = &c                 // shared borrow
var w = &mut c             // exclusive borrow
val field = (*r).count     // dereference, then field access
(*w).count = 9             // dereference, then write
```

`&x` borrows, `a & b` masks: position decides. See
[Ownership and borrowing](/language/ownership) for the rules the checker enforces.

## The `?` operator

`expr?` evaluates `expr` and, if it carries a failure, **returns that failure out
of the enclosing function**. Otherwise the expression's value is the success
payload.

```kelp
fun quarter(n: i64).R: result.Result<i64, String> {
    val h = half(n = n)?          // half returns Result<i64, String>
    return result.Result.Ok(value = h / 2)
}
```

Rules (§5.2):

- It works on `Option` **or** `Result`: the compiler knows the *shape*, not the
  module, so a program's own declaration of either works.
- The enclosing function must return an enum of the same shape, with the same
  failure payload type. v1 has no error conversion, so `Result<i64, String>`
  cannot be propagated out of a function returning `Result<i64, IoErr>`.
- A function returning `Unit` (including `main`) has nowhere to propagate to.
- The value composes: `1 + half(n = n)?`.
- A failure returns immediately, so the enclosing function's locals are dropped
  on the way out, exactly as any `return` drops them.
- `?` is postfix and binds tighter than every binary operator. Because it moves a
  payload out of the operand, **a borrow cannot be an operand**: match a
  borrowed operand with `when` or `if let` instead.
- It applies to the expression it is written on and to nothing else, so a tuple
  is never its operand. When a tuple is the *success* payload, `?` reaches the
  `Result` the element is and hands the tuple back: with
  `fun mk(n: i32).R: Result<(i32, i32), String>`, the line
  `val (a, b) = mk(n)?` binds the tuple and takes it apart. A tuple is not an
  `enum`, so `?` written on the tuple itself is the ordinary "the operand must be
  an `enum`" refusal ([Types](/language/types)).

## Tuple values

`(lo, hi)` is a tuple value, and `(i32, i32)` is its type: two or more positions,
in order ([Types](/language/types)).

```kelp
val pair = (1, 2)
val (lo, hi) = min_max(xs)      // destructuring is the only way to read one
```

- `(e)` is the parenthesized expression `e`, not a one-element tuple: `val x =
  (5)` binds an `i32`, and `()` is refused by name because the absent value is
  `unit`.
- There is **no positional access** on a value: `pair.0` is not a field access.
  Read a position with a destructuring binding
  ([Bindings and assignment](/language/bindings)), or bind the whole tuple to a
  `val` first.
- A tuple is a record, so it is not printable: `print` takes a scalar, a `str`
  or a `String`. Print each position instead.

## Compound assignment

`= += -= *= /= %=` are the assignment operators. `+=` on an owned value (for
example pushing through a `mut` receiver) works the same way a method call does.

## See also

- [Control flow](/language/control-flow)
- [Ownership and borrowing](/language/ownership)
- [Errors and panics](/language/errors)
