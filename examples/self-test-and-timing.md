---
title: "Self-test and timing"
description: "A self-test report and a timing line in one program: the shape a small project uses to check and measure itself without a test framework."
isPublished: true
tags: "example, testing"
---

The `self-test-and-timing` program prints a self-test report and a timing line.
Both come from one program, which is the shape a small project uses to check and measure itself.

| | |
| --- | --- |
| Source | [`src/self-test-and-timing.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/self-test-and-timing.kp) |
| Needs | `testkit = "Lilly/fpl/testkit"`, `benchkit = "Lilly/fpl/benchkit"` |
| Shows | typed check helpers, a pass/fail report, warmup plus repeats, percentiles |

## The dependencies, and one grant

```toml
[dependencies]
testkit  = "Lilly/fpl/testkit"
benchkit = "Lilly/fpl/benchkit"
```

```kelp
impl "deps/testkit/lib"
impl "deps/benchkit/lib" caps(time = [])
```

`benchkit` reads the monotonic clock, so the consumer delegates `time` to it.
`testkit` needs nothing: it counts and prints.

## The program

```kelp project
impl "deps/testkit/lib"
impl "deps/benchkit/lib" caps(time = [])
impl "std/str"

fun sum_to(n: i64).return: i64 {
    var acc: i64 = 0
    var i: i64 = 1
    while i <= n {
        acc += i
        i += 1
    }
    return acc
}

fun work() {
    val ignored = sum_to(1000)
    if ignored < 0 {
        print("unreachable")
    }
}

fun main() {
    var report = testkit.new_report()
    testkit.check_eq_i64(report, sum_to(10), 55, "sum_to(10)")
    testkit.check_eq_i64(report, sum_to(0), 0, "sum_to(0)")
    testkit.check_eq_str(report, "kelp", "kelp", "two literals compare equal")
    testkit.check_eq_bool(report, sum_to(3) == 6, true, "sum_to(3)")
    testkit.check(report, sum_to(100) > 0, "a large sum is positive")
    print(testkit.summary(&report))

    if !testkit.all_passed(&report) {
        print(testkit.failure_list(&report))
    }

    val samples = benchkit.time_many(fun() = work(), 2, 5)
    print(benchkit.report_line("sum_to(1000)", samples))
}
```

## Run it

```sh
kelpc run self-test-and-timing.kp
```

## Output

```
ok   sum_to(10)
ok   sum_to(0)
ok   two literals compare equal
ok   sum_to(3)
ok   a large sum is positive
5 passed, 0 failed
sum_to(1000): median=20ns p90=70ns p99=70ns (n=5)
```

The nanoseconds differ run to run; the shape of the line does not.

## What to take from it

- **Each check prints as it runs,** so a long run leaves a log rather than only a
  final count. `summary` adds "5 passed, 0 failed" and `failure_list` reprints
  only the names that failed.
- **There is no overloaded `check_eq`.** A user module cannot overload a name, so
  the equality helpers are spelled per type: `check_eq_i64`, `check_eq_str`,
  `check_eq_bool`, `check_eq_u64`, `check_eq_usize`, `check_eq_f64`.
- **`check_eq_f64` compares with `==`,** so it is exact. A computed float needs a
  tolerance comparison, which is `check(report, diff < 0.0001, "name")`.
- **The report is passed as a `mut` parameter,** not held in a module-level
  variable: a passdown is module-scoped, so a library could not keep the
  caller's tally in one.
- **`time_many` runs warmup iterations first,** untimed, and then one timed
  iteration per sample. Two warmup runs and five samples is a reasonable default
  for a fast function; a slower one wants fewer samples.
- **The closure is `closure()`,** a value that returns nothing. `work()` exists
  because a closure that must return a value does not match that type. The
  nanoseconds are per call, so a workload smaller than the clock's own overhead
  should loop inside the closure instead.

## See also

- [`testkit`](/libraries/testkit) and [`benchkit`](/libraries/benchkit)
- [`std/time`](/stdlib/time) for the clock `benchkit` reads
- [Modules and imports](/language/modules) for the `pd` borrow rule the tally
  pattern follows
