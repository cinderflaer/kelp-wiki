---
title: "`std/ops`"
description: "The operator traits Add, Sub, Mul, Div, Rem, Neg and Ord. Implementing one for a datac or enum gives it the operator; both operands are borrowed. Declarations only, no blanket impls. Ungated and freestanding."
isPublished: true
tags: "stdlib"
---
The operator traits. Ungated, pure language, and admitted to the freestanding set.

```kelp
impl "std/ops"
```

```kelp
pub trait Add { fun Self.add(rhs: &Self).return: Self }
pub trait Sub { fun Self.sub(rhs: &Self).return: Self }
pub trait Mul { fun Self.mul(rhs: &Self).return: Self }
pub trait Div { fun Self.div(rhs: &Self).return: Self }
pub trait Rem { fun Self.rem(rhs: &Self).return: Self }
pub trait Neg { fun Self.neg().return: Self }
pub trait Ord { fun Self.cmp(other: &Self).return: i32 }
```

With `impl ops.Add for T`, `a + b` means `a.add(&b)` and `a += b` means
`a = a.add(&b)`; `Sub`, `Mul`, `Div` and `Rem` follow their operators, `Neg`
gives `-a`, and `Ord` gives `<`, `<=`, `>` and `>=` through the sign of `cmp`
(negative, zero, positive, as `memcmp`). `Ord` does not supply `==`, which still
comes from a declared `eq`.

The traits can be written as `ops.Add` after `impl "std/ops"`. A trait for a
builtin type has to be implemented in the trait's own module, so a user
`impl ops.Add for i32` is refused. There are no blanket impls and nothing is
derived.

The whole rule set, with a worked example that runs on both backends, is
[Operator traits and `Display`](/language/operator-traits).

## See also

- [Operator traits and `Display`](/language/operator-traits)
- [Operators and expressions](/language/expressions)
- [`std/fmt`](/stdlib/fmt) for `Display`
