---
title: "Tools and tests"
description: "Testing with assert and exit status, checking a file, formatting and linting it, and checking documentation with kelpc, with the real output of each command."
isPublished: true
tags: "tutorial, tooling, testing"
---
**You will learn:** how to test a Kelp file with `assert`, and how to use
`kelpc` to check, format, lint and document a file.

## Tests with assert

A test in Kelp is a program that `assert`s what should be true. When an
assertion is false, the program stops with a panic and a non-zero exit status.
When every assertion holds, the program finishes normally.

Here is a module to test, `lib.kp`. The `///` line above a function is its
documentation, which the `doc` command reads later:

```kelp
/// Doubles a number.
pub fun double(n: i64) => i64 = n * 2

pub fun is_even(n: i64) => bool = n % 2 == 0
```

And a test file, `tests.kp`, that imports it:

```kelp project
impl "lib"

fun main() {
    assert(lib.double(21) == 42)
    assert(lib.is_even(4))
    assert(!lib.is_even(5))
    print("all checks passed")
}
```

```text
$ kelpc run tests.kp
all checks passed
```

Now make one check fail, by asserting that 5 is even:

```kelp project
impl "lib"

fun main() {
    assert(lib.is_even(5))
    print("never printed")
}
```

```text
$ kelpc run failing.kp
panic: assertion failed
```

The exit status is 1. A script or a continuous-integration job can rely on it.
The program stops at the first failed `assert`, so a suite of many checks is
easier to read with a test library. The [testing page](/getting-started/testing)
describes one.

## Checking a file

`kelpc check` answers whether a file compiles, without writing an executable.
It is the command to run first, and the one an editor can run on every save.

With `--json` it prints the result as one JSON object, which a tool can read:

```text
$ kelpc check --json tests.kp
{"schema":1,"ok":true,"diagnostics":[]}
```

## Formatting

`kelpc fmt` prints a file in the standard layout. It changes indentation and
spacing and never changes what the program means. With `-w` it rewrites the file
in place, and with `--check` it only reports whether the file is already formatted.

Here is a file with unusual spacing:

```kelp
fun double(n: i64) => i64 {
return n*2
}

fun main(){
assert(double(21)==42)
print("ok")
}
```

```text
$ kelpc fmt messy.kp
fun double(n: i64) => i64 {
    return n * 2
}

fun main() {
    assert(double(21) == 42)
    print("ok")
}
```

## Linting

`kelpc lint` prints warnings. A warning does not stop a build, and the exit status
stays zero. It checks four things: a run of `//` lines that could be one block
comment, a name that does not follow the project's naming case, a redundant `&` on a
`List` or `str` parameter, and a comparison a plain condition says better. This file
compares a `bool` with `true`, which compiles and means the same as the condition alone:

```kelp
fun main() {
    val ready = true
    if ready == true {
        print("go")
    }
}
```

```text
$ kelpc lint lint.kp
warning: '== true' is redundant: write the condition alone
  --> lint.kp:3:14
```

## Documentation

`kelpc doc` writes a page per module from the `pub` items and their `///`
comments. With `--check` it writes nothing and fails when a public item has no
comment, which is useful in a project that wants every public name documented:

```text
$ kelpc doc --check lib.kp
lib.kp:4: public fun `is_even` has no doc comment
```

The command exits non-zero, so the check can stop a build. Adding a `///` line
above `is_even` makes it pass.

## Try it

1. Add `assert(lib.double(0) == 1)` to `tests.kp` and run it. What is the panic
   message?
2. Run `kelpc fmt --check messy.kp`. Does it exit zero or non-zero?

Next: [Build something](/tutorial/18-build-something).
