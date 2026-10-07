---
title: "Testing what you write"
description: "Kelp has no `kelpc test` and no test discovery. What it has is testkit, a library that counts and prints, and Coral tasks, which compile and run an entry file - together that is the whole harness, and this page builds one."
isPublished: true
tags: "getting-started, testing"
---
Kelp has no `kelpc test` and no test discovery. What it has is two pieces you
assemble yourself:

- **`testkit`**, a library that keeps a running tally and prints `ok` or `FAIL`
  for each check;
- **a Coral task**, which compiles and runs one entry file, forwards `argv` and the
  exit code, and caches the result.

That is the whole harness. It is enough for a library of a few hundred lines, and
it is honest about what it does not do: no filtering, no parallel runs, no timing.

## Where the test file goes

Under `src/`. This is the one rule that is easy to get wrong, because `coral init`
creates a top-level `tests/` directory that **cannot hold a task entry**: `kelpc`
requires every entry file to live inside the project's `src/`. Declaring
`[tasks] test = "tests/main.kp"` fails with

```text
error: entry file '/tmp/calc/tests/main.kp' is not inside '/tmp/calc/src'
```

so the task goes in `src/tasks/`, which is the other directory `coral init`
writes. A task entry may import the project's own modules and its dependencies,
because `impl` paths resolve against `src/` like anywhere else. Building the task
compiles everything it imports, so a test task is a compile check of those modules
even when every check passes. Both functions are `pub` because the task file is
another module: it reaches `calc`'s items only where `calc` exports them (A-13).

## A project with a test task

Three files. First, the code under test, in `src/shapes/calc.kp`:

```kelp
pub fun double(n: i64).return: i64 = n * 2

pub fun is_even(n: i64).return: bool = n % 2 == 0
```

Then `src/tasks/test.kp`:

```kelp
// src/tasks/test.kp -- `coral task test`

impl "shapes/calc"
impl "deps/testkit/lib"
impl "std/process"

fun main() {
    var report = testkit.new_report()

    testkit.check_eq_i64(report, calc.double(21), 42, "double(21)")
    testkit.check(report, calc.is_even(4), "4 is even")
    testkit.check(report, !calc.is_even(5), "5 is odd")

    print(testkit.summary(&report))

    // testkit prints, and never fails a run by itself: the exit code is ours.
    if !testkit.all_passed(&report) {
        print(testkit.failure_list(&report))
        process.exit(1)
    }
}
```

And the manifest, after `coral init calc`:

```toml
name = "calc"
version = "0.1.0"
entry = "src/main.kp"

[dependencies]
testkit = "Juniper/fpl/testkit"

[tasks]
test = "src/tasks/test.kp"
```

```sh
coral sync          # fetch testkit into src/deps/testkit/
coral task          # list the tasks declared in coral.toml
coral task test     # build and run it
```

```text
test	src/tasks/test.kp
coral: building 'task-test' (tasks)
ok   double(21)
ok   4 is even
ok   5 is odd
3 passed, 0 failed
```

A failing check prints its name and nothing else about it, and the run ends
non-zero because the program asked for that:

```text
coral: building 'task-test' (tasks)
ok   double(21)
FAIL 5 is even
ok   5 is odd
2 passed, 1 failed
5 is even
```

## The `testkit` surface

| Function | Notes |
| --- | --- |
| `testkit.new_report()` | a `Report` to pass around; keep it in a `var` |
| `testkit.check(r, cond, name)` | one boolean assertion |
| `testkit.check_eq_i64` / `_u64` / `_usize` / `_f64` / `_bool` / `_str` | a typed equality check |
| `testkit.summary(&r)` | `"3 passed, 1 failed"` |
| `testkit.all_passed(&r)` | `bool`, for your own exit code |
| `testkit.failure_list(&r)` | the failure names, one per line |

Three details that follow from the language rather than from the library:

- **The checks are spelled per type.** A user module cannot overload a function
  name, so there is no single `check_eq`, only `check_eq_i64`, `check_eq_str` and
  the rest.
- **`check` takes `mut Report`**, so the report is a `var`, and every call passes
  it first.
- **`check_eq_f64` compares with `==`**, which is exact. For a computed float,
  compare a difference against a tolerance with `check`.

## The zero-dependency option

Before reaching for `testkit`, `assert` is built in and checked on every build:

```kelp
fun double(n: i64).return: i64 = n * 2

fun main() {
    assert(double(21) == 42)
    print("the assertion held")
}
```

A failure ends the run at that line with `panic: assertion failed` and exit 1. What
it does not give you is a name, a tally, or a way to keep going after a failure, so
it is best for one or two invariants and worst for a suite.

## What a test task can check

A task is an ordinary program, so it can do anything a program can: read a file
with an `fs` grant, call a library, print a report. The two shapes worth reaching
for first:

| Shape | What it looks like |
| --- | --- |
| Unit checks | the task above: import the module, assert on the pure functions |
| A golden output | compare what a function builds against a literal `str` you wrote in the test |

Keep the first one small. When a check needs real data, a literal in the test file
is usually easier than a fixture on disk, because a path passed to `fs` has to be
absolute.

Ideas at this size: keep `count_from` from [A first real tool](/getting-started/first-tool)
where it is and import that file as a module from the test (`impl "head"`,
because a module's own `main` is just a function when it is not the entry point),
then check `"7"`, `"0"`, `"-1"` and `"seven"`; test a cipher's round trip; test
that a sorted list is in order by walking it and comparing neighbours.

## See also

- [`testkit`](/libraries/testkit): the full API, and the output format
- [`benchkit`](/libraries/benchkit): timing, when "is it correct" becomes "is it fast"
- [Coral](/tooling/coral): tasks, caching, and where a task's artifact lands
- [tests_and_bench](/examples/tests_and_bench): a report and a timing line in one program
- [Projects and coral.toml](/getting-started/projects)
