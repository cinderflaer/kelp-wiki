---
title: "`testkit`: a tiny self-test harness"
description: "A running tally plus typed check_eq_ helpers, printing ok <name> / FAIL <name> as each check runs and summarising at the end."
isPublished: true
tags: "library, testing"
---
A running tally plus typed `check_eq_*` helpers, printing `ok   <name>` /
`FAIL <name>` as each check runs and summarising at the end.

No capability.

```toml
[dependencies]
testkit = "Juniper/fpl/testkit"
```

```kelp
impl "deps/testkit/lib"
```

## Type

```kelp
datac Report(var passed: usize, var failed: usize, var failures: List<String>)
```

The tally is an explicit `mut Report` parameter rather than a module-scope
counter: a passdown belongs to the module that declares it, so a library cannot
keep the caller's state in one — a `mut` parameter is what crosses the module
boundary.

## Functions

| Function | Returns | Prints |
| --- | --- | --- |
| `new_report()` | `Report` | — |
| `check(r: mut Report, cond: bool, name: &str)` | `Unit` | `ok   <name>` or `FAIL <name>` |
| `check_eq_i64(r, actual, expected, name)` | `Unit` | as `check` |
| `check_eq_u64`, `check_eq_usize`, `check_eq_f64`, `check_eq_bool` | `Unit` | as `check` |
| `check_eq_str(r, actual: &str, expected: &str, name)` | `Unit` | compares with `str.eq` |
| `failure_list(r: &Report)` | `String` | the failure names, one per line |
| `all_passed(r: &Report)` | `bool` | true when `failed == 0` |
| `summary(r: &Report)` | `String` | `"<n> passed, <m> failed"` |

Every `check*` prints immediately, so a run's output is a log as it happens, not
just a final count. Output goes to stdout via the builtin `print`/`print!`.

## Why the type is in the name

A user module cannot overload a function name (`syntax.md` §7.2 is stdlib-only),
so there is no single `check_eq`: the equality checks are spelled per type
(`check_eq_i64`, `check_eq_str`, ...).

`check_eq_f64` compares with `==`, so it is exact: for a computed float, compare
a difference against a tolerance with `check`.

## Example

```kelp
impl "deps/testkit/lib"

fun main() {
    var r = testkit.new_report()
    testkit.check(r, true, "always true")
    testkit.check_eq_i64(r, 4, 4, "add")
    testkit.check_eq_str(r, "ab", "ab", "concat")
    testkit.check_eq_usize(r, 2, 3, "wrong length")
    testkit.check_eq_bool(r, false, false, "false is false")
    print(testkit.summary(&r))
    print(testkit.all_passed(&r))
    print(testkit.failure_list(&r))
}
```

Output:

```
ok   always true
ok   add
ok   concat
FAIL wrong length
ok   false is false
4 passed, 1 failed
false
wrong length
```

## Notes

- No exit code: a failing run still exits 0. Call `process.exit(1)` yourself when
  you want CI to see a failure.
- No test discovery, no filtering, no timing, no parallel runs. It is a counter
  and a printer.
- `check` takes `mut Report`, so the report must live in a `var`.
- `failure_list` is for re-printing just the failures after a long run scrolled
  them out of view.
