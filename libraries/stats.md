---
title: "`stats`: descriptive statistics and linear regression"
description: "mean, median, variance, standard deviation, percentile, histogram and ordinary least squares over List<f64>."
isPublished: true
tags: "library, math"
---
mean, median, variance, standard deviation, percentile, histogram and ordinary
least squares over `List<f64>`.

No capability.

```toml
[dependencies]
stats = "Lilly/fpl/stats"
```

```kelp
impl "deps/stats/lib"
```

## Type

```kelp
datac Fit(val slope: f64, val intercept: f64, val r_squared: f64)
```

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `mean(xs: &List<f64>)` | `f64` | **panics** on an empty list |
| `median(xs: &List<f64>)` | `f64` | middle element, or the average of the two middles. **panics** on empty |
| `variance(xs: &List<f64>)` | `f64` | **population** variance (divide by `n`) |
| `stddev(xs: &List<f64>)` | `f64` | `sqrt(variance(xs))`, population form |
| `percentile(xs: &List<f64>, p: f64)` | `f64` | `p` in `[0, 100]`, linear interpolation between ranks. **panics** on empty |
| `histogram(xs: &List<f64>, buckets: usize)` | `List<i64>` | equal-width buckets between min and max |
| `linear_regression(xs: &List<f64>, ys: &List<f64>)` | `Fit` | OLS plus `r²`; **panics** if the lists differ in length, either is empty, or every `x` is identical |
| `sorted_copy(xs: &List<f64>)` | `List<f64>` | insertion sort, and a copy: `List.sort` sorts in place |
| `floor_to_usize(x: f64)` | `usize` | count whole units below `x`; `f64` has no `to_<int>` |

## Population vs sample

`variance`/`stddev` are the **population** forms (divide by `n`, not `n − 1`).
A user module cannot overload a function name ([syntax.md](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md) §7.2), so there is no
second spelling: take the sample form yourself by multiplying by `n / (n − 1)`.

## Histogram semantics

- Width is `(max − min) / buckets`; the maximum value is counted in the last
  bucket rather than falling one past the end.
- `buckets == 0` returns an empty `List<i64>`; an empty `xs` returns a list of
  `buckets` zeros.
- When every value is identical (`span == 0`) all values land in bucket 0.

## Percentile semantics

`percentile(xs, p)` sorts, computes `rank = p/100 · (n − 1)`, and linearly
interpolates between the neighbouring ranks. It agrees with `median` on an
odd-length list; on an even one both interpolate the two middle ranks.

## Example

```kelp project
impl "deps/stats/lib"

fun main() {
    var xs: List<f64> = List.empty()
    xs.push(2.0)
    xs.push(4.0)
    xs.push(4.0)
    xs.push(4.0)
    xs.push(5.0)
    xs.push(5.0)
    xs.push(7.0)
    xs.push(9.0)
    print(stats.mean(xs))
    print(stats.median(xs))
    print(stats.variance(xs))
    print(stats.stddev(xs))
    print(stats.percentile(xs, 50.0))
    val hist = stats.histogram(xs, 4)
    print(hist.len())
    print(hist.get(0))

    var ys: List<f64> = List.empty()
    var i: usize = 0
    while i < 8 {
        ys.push(i.to_f64())
        i += 1
    }
    val fit = stats.linear_regression(ys, ys)
    print(fit.slope)
    print(fit.intercept)
    print(fit.r_squared)
}
```

Output:

```
5.000000
4.500000
4.000000
2.000000
4.500000
4
1
1.000000
0.000000
1.000000
```

## Notes

- `sqrt` comes from `std/math`; `f64` has no integer conversion, so bucket
  indices are counted off by repeated subtraction (fine for the ranks and
  buckets this library computes).
- The mean is computed by naive summation, so a list with huge and tiny values
  loses precision; there is no compensated/Kahan form.
- `r_squared` is `1.0` when `ss_tot == 0` (all `y` equal), which is the
  convention this library picked rather than a refused fit.
