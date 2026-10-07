---
title: "Tutorial 15: Testing and tooling"
description: "Chapter 15 of the Kelp tutorial: checking a program with assert and exit codes, kelpc check with JSON, fmt, lint, doc, a sanitizer build that catches an unsafe out-of-bounds write, and incremental builds with the unit cache."
isPublished: true
tags: "tutorial, tooling, testing"
---
`kelpc` is more than `build` and `run`. This chapter is the daily toolbox: a way to test,
and the commands that keep a codebase tidy. The reference pages are
[the kelpc CLI](/tooling/kelpc-cli), [`kelpc doc`](/tooling/kelpc-doc),
[Sanitizers](/tooling/sanitizers) and [Testing what you write](/getting-started/testing).

## Testing

Kelp has no `kelpc test` and no test discovery. Two things are available: the
builtin `assert(cond)`, and a program that prints and sets an **exit code**.
`getting-started/testing` builds the full harness from the `testkit` library and a
Coral task; Coral was not installed where this book was checked, so I did not run
that. What follows uses only the language.

```kelp
impl "std/process"

fun double(n: i64).return: i64 = n * 2

fun is_even(n: i64).return: bool = n % 2 == 0

fun check_eq(got: i64, want: i64, name: &str, failures: mut i32) {
    if got == want {
        print("ok   ${name}")
    } else {
        print("FAIL ${name}: got ${got}, want ${want}")
        *failures += 1
    }
}

fun main() {
    var failures: i32 = 0
    check_eq(double(21), 42, "double(21)", failures)
    check_eq(double(0), 0, "double(0)", failures)
    check_eq(double(4), 9, "double(4) is deliberately wrong", failures)
    assert(is_even(4))
    print("${failures} failure(s)")
    if failures > 0 {
        process.exit(1)
    }
}
```

```text
$ ./c15a; echo "exit $?"
ok   double(21)
ok   double(0)
FAIL double(4) is deliberately wrong: got 8, want 9
1 failure(s)
exit 1
```

Both backends printed this. A failing check prints `FAIL`, counts, and the program exits 1
through `process.exit(1)`. `check_eq` takes the counter as `mut i32`, so inside it the
counter is written `*failures`, the dereference the compiler asks for. A bare `assert`
is the other tool, and it panics:

```kelp
fun main() {
    print("checking")
    assert(1 + 1 == 3)
    print("unreachable")
}
```

```text
$ ./c15assert; echo "exit $?"
panic: assertion failed
checking
exit 1
```

(`panic:` is first because stderr is not buffered and stdout was a file, as in
chapter 7.)

## `check`: does it compile?

`kelpc check` runs everything a build runs except code generation, so it is the fast
edit loop, and it takes a project directory too. `--json` prints the findings as one
JSON object, with a 1-based line and column range, for an editor or a script. For
chapter 1's `c1bad.kp`:

```text
$ kelpc check c1bad.kp --json
{"schema":1,"ok":false,"diagnostics":[{"severity":"error","message":"cannot assign value of type 'str' to 'x' declared as 'i32'","module":"c1bad","file":"c1bad.kp","line":2,"column":5,"end_line":2,"end_column":24,"notes":[]}]}
exit 1
```

Only an error gives a nonzero status; a warning on its own exits 0.

## `fmt` and `lint`

`kelpc fmt` prints the formatted source, `-w` rewrites in place and `--check` exits 1
without writing when a file is not formatted. It changes whitespace and indentation only,
never a token. Here is a deliberately messy file:

```kelp
fun   area(w:i32,h:i32).return:i32 {
  return w*h
}
fun main(){
    val n = 5
  if n > 3 {
        print("big")
    } else if n > 1 {
    print("medium")
    }
}
```

```text
$ kelpc fmt --check messy.kp
error: 'messy.kp' is not formatted
exit 1
$ kelpc fmt messy.kp
fun area(w: i32, h: i32).return: i32 {
    return w * h
}
fun main() {
    val n = 5
    if n > 3 {
        print("big")
    } else if n > 1 {
        print("medium")
    }
}
```

After `kelpc fmt -w`, `--check` passes:

```text
$ kelpc fmt -w messy.kp && kelpc fmt --check messy.kp
exit 0
```

`fmt` does not rewrite `else if` to `elif`, because that is a different spelling and
not whitespace. `lint` is the tool for that:

```text
$ kelpc lint messy.kp
warning: 'else if' compiles, but 'elif' is the preferred spelling
  --> messy.kp:8:7
exit 0
```

A warning is not a failure: `lint` exits 0 and writes nothing. After changing the line to
`} elif n > 1 {`, `kelpc lint` prints nothing, `kelpc fmt --check` says nothing and both
exit 0:

```text
exit 0
exit 0
```

The corrected program (built and run on both backends) prints `big`.

## `doc`

`///` above a `fun`, `datac`, `enum`, `trait`, `const`, field or variant documents it,
and `//!` at the top of a file documents the module. Only `pub` items are listed.

```kelp
//! Small geometry helpers used by the tutorial.

/// A rectangle with a width and a height.
pub datac Rect(val w: i32, val h: i32)

/// The area of `r`, in square units.
pub fun area(r: &Rect).return: i32 = r.w * r.h

pub fun perimeter(r: &Rect).return: i32 = 2 * (r.w + r.h)

fun main() {
    val r = Rect(w = 3, h = 4)
    print(area(&r))
    print(perimeter(&r))
}
```

`kelpc doc documented.kp -o doc15` writes `index.md` and one page per module (add
`--format html` for a single self-contained page). The output has no timestamps, so it
can be checked in and diffed:

```text
$ cat doc15/index.md
# Modules

- [`documented`](documented.md) — Small geometry helpers used by the tutorial.
$ cat doc15/documented.md
# Module `documented`

Small geometry helpers used by the tutorial.

## Types

### `Rect`

```kelp
pub datac Rect(val w: i32, val h: i32)
```

A rectangle with a width and a height.

**Fields**

- `val w: i32` — A rectangle with a width and a height.
- `val h: i32` — A rectangle with a width and a height.

## Functions

### `area`

```kelp
pub fun area(r: &Rect).return: i32
```

The area of `r`, in square units.

### `perimeter`

```kelp
pub fun perimeter(r: &Rect).return: i32
```
```

A field with no doc comment of its own is listed without a description. A
record's comment belongs to the record only; it is never inherited by its
fields.
`--check` writes nothing and fails when a listed item has no doc comment:

```text
$ kelpc doc documented.kp -o doc15b --check
documented.kp:9: public fun `perimeter` has no doc comment
exit 1
```

## Sanitizers

Safe Kelp cannot write out of bounds, but `unsafe`, `Ptr<T>`, `extern` and `asm` can.
A project that uses `unsafe` must list the module in `coral.toml` under `[unsafe]`
(see [Unsafe code](/language/unsafe)). This one writes three cells past a three-element
array:

```toml
name = "sanproj"
version = "0.1.0"
entry = "src/main.kp"

[unsafe]
modules = ["main"]
```

```kelp
fun main() {
    var cells: [i32; 3] = [10, 20, 30]
    val base: Ptr<[i32; 3]> = Ptr.from_ref(&cells)
    val p: Ptr<i32> = base.cast<i32>()
    unsafe {
        p.offset(1).write(21)
        print(p.offset(1).read())
        p.offset(5).write(99)
        print("past the end")
    }
}
```

Built normally, it is undefined behaviour and happens to run. On both backends:

```text
$ kelpc build sanproj -o sanproj_bin && ./sanproj_bin
21
past the end
```

The sanitizers are in the **C backend only**. The default backend refuses them and names
the way out; the next block is the real output of building with `KELPC_ORACLE=c
kelpc build --sanitize=address` and running the result (run without `ulimit -v`, since the
shadow memory needs a huge address range; bounded by `ulimit -t 10` and `timeout 10`
instead). The first line is the LLVM refusal; the addresses and the glibc paths differ per
run, and the shadow-byte dump is trimmed where marked:

```text
$ kelpc build --sanitize=address sanproj -o t
error: sanitizer 'address' is not available on the LLVM backend, which links no sanitizer passes; build with the C backend instead, which supports address, undefined and thread: KELPC_ORACLE=c kelpc build --sanitize=address sanproj
$ KELPC_ORACLE=c kelpc build --sanitize=address sanproj -o t && ./t
=================================================================
==1493138==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x72b94a100034 at pc 0x6009c5a05266 bp 0x7ffdd8b4bb40 sp 0x7ffdd8b4bb38
WRITE of size 4 at 0x72b94a100034 thread T0
    #0 0x6009c5a05265 in main sanproj/src/main.kp:8
    #1 0x76b94c62b284 in __libc_start_call_main (/nix/store/znb3q6g1ik34454j3vcjx824h1871asg-glibc-2.42-84/lib/libc.so.6+0x2b284) (BuildId: c160d00afab67b9f67df4297ae033ed1d3713b87)
    #2 0x76b94c62b337 in __libc_start_main@GLIBC_2.2.5 (/nix/store/znb3q6g1ik34454j3vcjx824h1871asg-glibc-2.42-84/lib/libc.so.6+0x2b337) (BuildId: c160d00afab67b9f67df4297ae033ed1d3713b87)
    #3 0x6009c5a05304 in _start (out/san-asan+0x1304)

Address 0x72b94a100034 is located in stack of thread T0 at offset 52 in frame
    #0 0x6009c5a050ff in main out/san-asan.c:1624

  This frame has 1 object(s):
    [32, 44) 'kelp_cells' <== Memory access at offset 52 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow sanproj/src/main.kp:8 in main
[shadow-byte dump trimmed]
==1493138==ABORTING
asan-exit=1
```

The report names the `.kp` line (`main.kp:8`, the `write(99)`), the kind (`WRITE of size 4`)
and the object overrun: the 12-byte `cells` at frame offsets 32 to 44, written at 52.
`undefined` and `thread` work the same way; `thread` finds races between spawned threads.
[Sanitizers](/tooling/sanitizers) has the rest.

## `--incremental`

`--incremental` splits the output into one compilation unit per source module and
caches each unit's object by the hash of its IR. The result is the same program. A
second build with nothing changed reuses every unit. `--timings` prints per-phase
times and one line per unit with `hit` or `miss`; `KELPC_CACHE_STATS=1` prints the totals.
This is the project from chapter 11, built twice into a fresh directory (timings are from
one run and will vary):

```text
$ kelpc build shapes_app --incremental --timings -o app    (first build)
kelpc cache: 0 hits, 4 misses, 4 stored
kelpc timings:
  parse: 0.6 ms
  resolve: 0.1 ms
  infer: 0.6 ms
  borrowck: 0.1 ms
  codegen: 3.3 ms
  unit compile: 16.2 ms
  link: 103.3 ms
  unit deps/mathx/lib: 5.6 ms miss
  unit main: 6.0 ms miss
  unit shapes/circle: 3.8 ms miss
  unit _support: 4.0 ms miss

$ same command again    (second build)
kelpc cache: 4 hits, 0 misses, 0 stored
kelpc timings:
  parse: 0.6 ms
  resolve: 0.1 ms
  infer: 0.6 ms
  borrowck: 0.1 ms
  codegen: 3.4 ms
  unit compile: 0.0 ms
  link: 113.7 ms
  unit deps/mathx/lib: 0.9 ms hit
  unit main: 1.0 ms hit
  unit shapes/circle: 0.8 ms hit
  unit _support: 0.6 ms hit

$ ./app
area 12.566360
unit 3.141590

$ kelpc cache stats --dir .kelpc-cache
kelpc cache: 4 entries, 9016 bytes in .kelpc-cache
```

The cache lives in `<out dir>/.kelpc-cache`, which is why `cache stats` was given
`--dir`; `KELPC_CACHE=off` skips it for one build. The C backend ignores `--incremental`.

## Exercises

1. Make `documented.kp` pass `kelpc doc --check`.
2. Which tool tells you to write `elif`, and which one would not notice `else if`?

<details>
<summary>Solutions</summary>

1. Add a doc comment above `perimeter`:

```kelp
//! Small geometry helpers used by the tutorial.

/// A rectangle with a width and a height.
pub datac Rect(val w: i32, val h: i32)

/// The area of `r`, in square units.
pub fun area(r: &Rect).return: i32 = r.w * r.h

/// The perimeter of `r`, in units.
pub fun perimeter(r: &Rect).return: i32 = 2 * (r.w + r.h)

fun main() {
    val r = Rect(w = 3, h = 4)
    print(area(&r))
    print(perimeter(&r))
}
```

```text
$ kelpc doc documented_full.kp -o doc15c --check
exit 0
```

2. `kelpc lint` warns about `else if` (`'else if' compiles, but 'elif' is the preferred
   spelling`). `kelpc fmt` does not, since it only changes whitespace, as the run above
   showed.

</details>

Next: [Freestanding: a tiny kernel](/tutorial/16-freestanding).
