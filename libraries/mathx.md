---
title: "`mathx`: the arithmetic `std/math` stops short of"
description: "gcd/lcm, primality, factorial, hypot, a chosen-base logarithm, degree/radian conversion, and checked/saturating i64 arithmetic."
isPublished: true
tags: "library, math"
---
`gcd`/`lcm`, primality, factorial, `hypot`, a chosen-base logarithm,
degree/radian conversion, and checked/saturating `i64` arithmetic.

No capability.

```toml
[dependencies]
mathx = "Lilly/fpl/mathx"
```

```kelp
impl "deps/mathx/lib"
```

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `gcd(a: i64, b: i64)` | `i64` | non-negative; `gcd(0, 0) = 0` |
| `lcm(a: i64, b: i64)` | `i64` | non-negative; `0` when either argument is 0; can overflow `i64` silently |
| `is_prime(n: i64)` | `bool` | trial division to `sqrt(n)`; `false` for anything below 2 |
| `factorial(n: i64)` | `i64` | **panics** on a negative input or on overflow past `i64::MAX` (20! already overflows) |
| `hypot(x: f64, y: f64)` | `f64` | `sqrt(x² + y²)` |
| `log_base(x: f64, base: f64)` | `f64` | `ln(x) / ln(base)` |
| `to_radians(deg: f64)` | `f64` | |
| `to_degrees(rad: f64)` | `f64` | |

Constants: `I64_MAX` (`9223372036854775807`), `I64_MIN` (`-9223372036854775808`).

## Checked and saturating `i64`

Kelp's integer `+`/`-`/`*` overflow is unchecked ([syntax.md](/design/syntax) §5): it silently
wraps. There is no
overflow flag to read, so these detect it by inspecting signs (add/sub) or by
dividing the product back out (mul).

| Function | Returns |
| --- | --- |
| `add_checked_i64(a, b)` | `option.Option<i64>`: `None` on overflow |
| `sub_checked_i64(a, b)` | `option.Option<i64>` |
| `mul_checked_i64(a, b)` | `option.Option<i64>` |
| `add_saturating_i64(a, b)` | `i64`: clamps to `I64_MAX` / `I64_MIN` |
| `sub_saturating_i64(a, b)` | `i64` |
| `mul_saturating_i64(a, b)` | `i64`: clamps toward the sign of the true product |

## Example

```kelp project
impl "deps/mathx/lib"
impl "std/option"

fun main() {
    print(mathx.gcd(12, 18))
    print(mathx.lcm(4, 6))
    print(mathx.is_prime(97))
    print(mathx.is_prime(1))
    print(mathx.factorial(10))
    print(mathx.hypot(3.0, 4.0))
    print(mathx.log_base(8.0, 2.0))
    print(mathx.to_radians(180.0))
    val ok = mathx.add_checked_i64(1, 2)
    print(option.unwrap(o = ok))
    val over = mathx.add_checked_i64(9223372036854775807, 1)
    print(option.is_none(o = over))
    print(mathx.add_saturating_i64(9223372036854775807, 1))
    print(mathx.sub_saturating_i64(-9223372036854775807 - 1, 1))
    val big = mathx.mul_checked_i64(1000000000000, 1000000000000)
    print(option.is_none(o = big))
    print(mathx.to_degrees(mathx.to_radians(90.0)))
}
```

Output:

```
6
12
true
false
3628800
5.000000
3.000000
3.141593
3
true
9223372036854775807
-9223372036854775808
true
90.000000
```

## Notes

- `lcm` can overflow: `lcm(2^62, 2)` has no `i64` answer and wraps silently.
- `is_prime` is a predicate, not a sieve; for many primes at once, sieve in the
  caller.
- Checked forms return `Option`, and `Option` has no methods: unwrap with
  `option.unwrap(o = ..)`, `option.unwrap_or(o = .., fallback = ..)`,
  `option.is_some(o = ..)`, `option.is_none(o = ..)`.
