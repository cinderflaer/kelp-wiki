---
title: "`decimal`: fixed-point decimals over `i64`"
description: "A Decimal is an i64 value scaled by 10^-scale - scale = 2 means value is in hundredths, so 1234 at scale 2 is 12.34. Exact for money-shaped arithmetic in a way f64 is not, at the cost of a bounded..."
isPublished: true
tags: "library, data-formats"
---
A `Decimal` is an `i64` `value` scaled by `10^-scale`: `scale = 2` means `value`
is in hundredths, so `1234` at scale 2 is `12.34`. Exact for money-shaped
arithmetic in a way `f64` is not, at the cost of a bounded range (`i64`) and a
fixed number of fractional digits per value.

No capability.

```toml
[dependencies]
decimal = "Lilly/fpl/decimal"
```

```kelp
impl "deps/decimal/lib"
```

## Types

```kelp
datac Decimal(val value: i64, val scale: u32)

enum ParseErr {
    Empty    // the input text was empty
    Invalid  // bad character, bad position, or more fractional digits than `scale`
}
```

## Construction

| Function | Returns |
| --- | --- |
| `from_i64(n: i64, scale: u32)` | `Decimal`: `n * 10^scale` |
| `from_str(s: &str, scale: u32)` | `result.Result<Decimal, ParseErr>` |
| `pow10_i64(n: u32)` | `i64`: `10^n` |

`from_str` accepts `"12.34"`, `"-0.5"`, `"7"` (which at scale 2 is `700`, i.e.
`7.00`). Rules:

- An optional leading `-`, then digits, then an optional `.` and digits.
- At least one digit is required; a trailing `.` with no digits is `Invalid`;
  trailing junk is `Invalid`.
- **More fractional digits than `scale` is `Invalid`, not silent truncation.**
  Round the input yourself first if that is what you want.

## Arithmetic

| Function | Returns | Notes |
| --- | --- | --- |
| `to_string(d: &Decimal)` | `String` | decimal point reinserted, left-zero-padded (`5` at scale 2 is `"0.05"`) |
| `add(a: &Decimal, b: &Decimal)` | `Decimal` | **panics** `decimal.add: scales differ, rescale first` |
| `sub(a: &Decimal, b: &Decimal)` | `Decimal` | same panic |
| `mul(a: &Decimal, b: &Decimal)` | `Decimal` | exact: the raw values multiply and the **scales add**, so the result is at a wider scale than either input. No rounding |
| `rescale(d: &Decimal, new_scale: u32)` | `Decimal` | widening is exact; narrowing rounds **half away from zero** |

`add`/`sub` have no implicit rescale on the way in: a caller mixing scales says
which one wins by calling `rescale` first. After `mul`, `rescale` the result down
when a narrower scale is wanted.

## Example

```kelp project
impl "deps/decimal/lib"

fun main() {
    val a = decimal.from_str("12.34", 2)
    if let Ok(x) = a {
        print(decimal.to_string(x))
        print(x.value)
        print(x.scale)
        val y = decimal.from_i64(3, 2)
        val s = decimal.add(x, &y)
        print(decimal.to_string(&s))
        val m = decimal.mul(x, &y)
        print(decimal.to_string(&m))
        val r = decimal.rescale(&m, 2)
        print(decimal.to_string(&r))
        val w = decimal.rescale(&m, 4)
        print(decimal.to_string(&w))
    }
    val neg = decimal.from_str("-0.05", 2)
    if let Ok(x) = neg {
        print(decimal.to_string(x))
    }
    val bad = decimal.from_str("1.234", 2)
    print(result.is_err(bad))
    val empty = decimal.from_str("", 2)
    print(result.is_err(empty))
}
```

Output:

```
12.34
1234
2
15.34
37.0200
37.02
37.0200
-0.05
true
true
```

## Notes

- Range: `value` is an `i64`, so the maximum scaled value is about 9.22×10¹⁸;
  `from_i64` and `mul` can overflow silently: integer `+`/`-`/`*` overflow is
  unchecked ([syntax.md](/design/syntax) §5).
  Keep `scale` small if `value` is large.
- `rescale` narrowing uses the "round half away from zero" rule, with the
  half-way test done exactly on the integer remainder.
- There is no division, no comparison, no floor/ceil, no negative `scale`.
- `to_string` always writes exactly `scale` fractional digits.
