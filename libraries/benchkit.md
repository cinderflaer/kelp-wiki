---
title: "`benchkit`: warmup and repeat timing"
description: "Timing over a closure on the monotonic clock, with median/percentile over the runs."
isPublished: true
tags: "library, testing"
---
Timing over a closure on the monotonic clock, with median/percentile over the
runs.

**Gated on `time`** (it calls `time.now_mono_ns()`):

```toml
[dependencies]
benchkit = "Juniper/fpl/benchkit"
```

```kelp
impl "deps/benchkit/lib" caps(time = [])
```

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `time_once(f: closure())` | `i64` | nanoseconds for one call, monotonic clock |
| `time_many(f: closure(), warmup: usize, runs: usize)` | `List<i64>` | `warmup` untimed runs, then `runs` timed ones, one entry each |
| `median_ns(xs: &List<i64>)` | `i64` | the middle value; **the lower of the two middles** on an even count (cheap: no averaging, no float rounding). **Panics** on an empty list |
| `percentile_ns(xs: &List<i64>, p: f64)` | `i64` | nearest-rank: the smallest sample such that at least `p` percent of the batch is no larger. **Panics** on empty, or `p` outside `[0, 100]` |
| `sorted_copy(xs: &List<i64>)` | `List<i64>` | a sorted copy (the builtin `List<i64>.sort()` is usable, which is why `median_ns`/`percentile_ns` need no sort of their own) |
| `report_line(label: &str, xs: &List<i64>)` | `String` | one line: `<label>: median=<..>ns p90=<..>ns p99=<..>ns (n=<..>)` |

`trunc_to_usize(x: f64, n: usize)` is the smallest `usize` rank not above `x`,
clamped to `n - 1`: the float-to-rank helper `percentile_ns` uses, since `f64`
has no integer conversion.

`f` is a plain `Unit`-returning closure: its result, if it has one, is not the
point; the elapsed time is. So the workload under test is whatever computation
or side effect `f`'s body does.
`report_line` only builds the text; the caller owns printing it, so a report can
collect several lines before printing any.

## Example

```kelp project
impl "deps/benchkit/lib" caps(time = [])
impl "std/time"

fun main() {
    val one = benchkit.time_once(fun() = time.sleep_ms(1))
    print(one >= 0)
    val xs = benchkit.time_many(fun() = time.sleep_ms(1), 2, 5)
    print(xs.len())
    print(benchkit.median_ns(xs) >= 0)
    print(benchkit.percentile_ns(xs, 100.0) >= benchkit.percentile_ns(xs, 0.0))
    print(benchkit.report_line("sleep1ms", xs))
    val sorted = benchkit.sorted_copy(xs)
    print(sorted.len())
}
```

Output (timings vary):

```
true
5
true
true
sleep1ms: median=1054061ns p90=1064981ns p99=1064981ns (n=5)
5
```

## Notes

- One run is one call: no batching of iterations inside `time_once`, so a very
  fast workload measures the clock's own overhead. Wrap a loop in `f` if the
  workload is smaller than a few hundred nanoseconds.
- `time_many`'s warmup runs are untimed to let a cache, branch predictor or
  allocator settle.
- Percentiles use nearest-rank, so `percentile_ns(xs, 100.0)` is the maximum and
  `percentile_ns(xs, 0.0)` is the minimum. The index is computed by walking whole
  units off the float (`f64` has no integer conversion), which is O(n) worst case,
  fine for benchmark sample sizes.
- A closure that captures an owned value moves it; pass what the workload needs
  as a parameter if the closure must stay callable elsewhere.
