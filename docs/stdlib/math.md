# `std/math`

Floating-point math, plus `abs`/`min`/`max`/`clamp`: the only overloaded names
in the language. Ungated.

```kelp
impl "std/math"
```

## Constants

| Constant | Value |
| --- | --- |
| `math.PI` | `3.141592653589793` |
| `math.E` | `2.718281828459045` |
| `math.TAU` | `6.283185307179586` |

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `sqrt(x)` | `f64` | |
| `pow(base, exp)` | `f64` | |
| `floor(x)` / `ceil(x)` / `round(x)` / `trunc(x)` | `f64` | `f64` in, `f64` out: there is no float→int conversion |
| `exp(x)` / `ln(x)` / `log2(x)` / `log10(x)` | `f64` | |
| `sin(x)` / `cos(x)` / `tan(x)` | `f64` | radians |
| `atan2(y, x)` | `f64` | the quadrant-aware arctangent |
| `is_nan(x)` / `is_finite(x)` | `bool` | |
| `sign(x)` | `f64` | `-1.0`, `0.0` or `1.0` |
| `abs(x)` | `i32` / `i64` / `f64` | overloaded |
| `min(a, b)` / `max(a, b)` | same as arguments | overloaded over `i32`, `i64`, `f64` |
| `clamp(x, lo, hi)` | same as arguments | overloaded over `i32`, `i64`, `f64` |

`abs`, `min`, `max` and `clamp` are the **only** functions in the language that
may be overloaded, and that overloading exists only inside the shipped standard
library (syntax.md §7.2). A user module cannot repeat the trick; that is why
[`listx`](../libraries/listx.md) has `sum_i32`/`sum_i64`/`sum_f64` and
[`mathx`](../libraries/mathx.md) spells checked arithmetic per width.

```kelp
impl "std/math"

fun main() {
    print(math.sqrt(2.0))
    print(math.pow(2.0, 10.0))
    print(math.floor(1.9))
    print(math.abs(-3))
    print(math.min(3, 9))
    print(math.clamp(11, 0, 10))
    print(math.PI)
}
```

```
1.414214
1024.000000
1.000000
3
3
10
3.141593
```

## Notes

- Everything returns `f64` and takes `f64`; there is no `f32` variant.
- `round` rounds half away from zero, as C's `round` does; `floor`/`ceil`/`trunc`
  are the directed ones.
- `sign` on `-0.0` and on NaN returns `0.0` (the `else` branch), which is worth
  knowing before using it as a multiplier.
- The missing pieces: `gcd`, `lcm`, `is_prime`, `factorial`, `hypot`,
  `log_base`, degree/radian conversion, checked and saturating `i64` arithmetic,
  are in [`mathx`](../libraries/mathx.md).
- Integer `+`/`-`/`*` overflow is unchecked, so `abs(i64::MIN)` wraps; `mathx`'s
  saturating forms are the fix.

## See also

- [`mathx`](../libraries/mathx.md)
- [`stats`](../libraries/stats.md): `mean`, `median`, `variance`, regression
- [`complex`](../libraries/complex.md)
