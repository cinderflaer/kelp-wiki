# `complex` — complex numbers over `f64`

The four arithmetic operations, conjugate, magnitude, angle, polar construction
and text formatting.

No capability.

```toml
[dependencies]
complex = "Juniper/fpl/complex"
```

```kelp
impl "deps/complex/lib" as complex
```

## Type

```kelp
datac Complex(val re: f64, val im: f64)
```

Both fields are public and immutable; every operation returns a new `Complex`.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `add(a: &Complex, b: &Complex)` | `Complex` | |
| `sub(a: &Complex, b: &Complex)` | `Complex` | |
| `mul(a: &Complex, b: &Complex)` | `Complex` | `(a.re·b.re − a.im·b.im) + (a.re·b.im + a.im·b.re)i` |
| `div(a: &Complex, b: &Complex)` | `Complex` | **panics** `complex.div: division by zero` when `b.re² + b.im² == 0` |
| `conj(a: &Complex)` | `Complex` | `re − im·i` |
| `abs(a: &Complex)` | `f64` | `\|a\|` = `sqrt(re² + im²)` |
| `arg(a: &Complex)` | `f64` | the angle in radians, `atan2(im, re)`, in `(−π, π]` |
| `from_polar(r: f64, theta: f64)` | `Complex` | `r·cos θ + i·r·sin θ` |
| `to_string(a: &Complex)` | `String` | `re+imi` or `re-imi`, six decimals per part, like `print`'s own float format |

## Example

```kelp
impl "deps/complex/lib" as complex

fun main() {
    val a = complex.Complex(re = 1.0, im = 2.0)
    val b = complex.Complex(re = 3.0, im = -4.0)
    print(complex.to_string(&a))
    print(complex.to_string(complex.add(&a, &b)))
    print(complex.to_string(complex.sub(&a, &b)))
    print(complex.to_string(complex.mul(&a, &b)))
    print(complex.to_string(complex.div(&a, &b)))
    print(complex.to_string(complex.conj(&a)))
    print(complex.abs(&a))
    print(complex.arg(&a))
    val p = complex.from_polar(2.0, 0.0)
    print(complex.to_string(&p))
}
```

Output:

```
1.000000+2.000000i
4.000000-2.000000i
-2.000000+6.000000i
11.000000+2.000000i
-0.200000+0.400000i
1.000000-2.000000i
2.236068
1.107149
2.000000+0.000000i
```

## Notes

- `div` is the naive formula, not the scaled/finite variant that avoids
  overflow when `b.re` or `b.im` is near the float limit. Fine for ordinary
  magnitudes.
- `abs` is `sqrt(re² + im²)`, so a component large enough to overflow its square
  loses precision; `mathx.hypot` would be the safer form if you need it.
- No `pow`, `sqrt`, `exp`, `log`, `sin`/`cos` of a complex argument — only the
  operations listed above.
- `to_string` always prints exactly six decimals per part and drops the sign of a
  negative zero (`-0.0` prints as `+0.000000`).
