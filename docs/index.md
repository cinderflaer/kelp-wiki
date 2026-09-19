# Kelp

Kelp is a statically typed, compiled systems language whose headline feature is
**capability-based security**. A module declares what it may touch, and that
authority is part of the source and checked at every call site that uses it.

```kelp
impl "std/http" with caps(net = ["127.0.0.1:*"])
impl "std/fs"

fun main() {
    print("a program that may talk to 127.0.0.1 and touch the filesystem")
}
```

Those two `impl` lines are the program's entire network and filesystem
authority. There is no other place authority can be acquired — a program cannot
read a file, open a socket, spawn a process or read the clock unless the module
making the call was granted that resource. "What can this code do?" is answered
by the first few lines of a file instead of by auditing it.

## Where to start

<div class="grid cards" markdown>

-   **New to Kelp**

    ---

    Read [Getting started](getting-started/index.md) — the language in one page,
    then a program you can build and run.

-   **The language**

    ---

    The [Language chapter](language/index.md) is the reference for the surface
    syntax: types, control flow, functions, ownership, capabilities.

-   **The standard library**

    ---

    [Standard library](stdlib/index.md) documents every `std/*` module and the
    compiler builtins (`String`, `Bytes`, `List`, `Map`, `Box`).

-   **Working on the compiler**

    ---

    [Compiler](compiler/index.md) covers the pipeline, the two backends, the
    runtime and the test gates. [Contributing](meta/contributing.md) has the
    workflow.

-   **Libraries**

    ---

    [Libraries (fpl)](libraries/index.md) is the first-party library catalogue:
    JSON, CSV, TOML, base64, dates, sets, bit packing, big integers, decimals,
    HTTP helpers and more.

-   **Known issues**

    ---

    [Known issues](meta/known-issues.md) lists the defects that affect valid
    programs today, with repros.

</div>

## What the language has

| | |
| --- | --- |
| Types | `i32` `i64` `u8` `u16` `u32` `u64` `usize` `isize` `f32` `f64` `bool` `char`, plus borrowed text as `str` and `View` |
| Data | `datac` records with `val`/`var` fields, `enum` tagged unions, exhaustive `when`, `if let`, type parameters, `const`, `pd` passdowns |
| Ownership | owned builtins `String`, `Bytes`, `List<T>`, `Map<K, V>`, `Box<T>`; moves, shared and `mut` borrows, drops at end of scope, no garbage collector |
| Errors | `Option`, `Result`, the `?` operator, `panic`/`assert` |
| Functions | `fun`, named arguments, function values and closures, receiver methods, stdlib-only argument-type overloading |
| Modules | `impl "std/fs"`, local-file imports, aliases, `pd` passdowns |
| Capabilities | `fs`, `net`, `process`, `env`, `time`, `rand` |
| Stdlib | `mem` `str` `path` `math` `fmt` `io` `fs` `process` `net` `http` `time` `rand` `env` `list` `option` `result` |
| Toolchain | `kelpc` (compiler), [Coral](tooling/index.md) (build tool and package manager), [Lighthouse](tooling/index.md) (editor support) |

There is deliberately **no** `unsafe`, no exceptions, no undefined-behaviour
escape hatch, no garbage collector, and no macros.

## A program

```kelp
datac Point(var x: i32, var y: i32)

enum Shape {
    Circle(val r: f64)
    Rect(val w: f64, val h: f64)
    Empty
}

fun area(s: &Shape).R: f64 = when s {
    Circle(r) -> 3.14159 * r * r
    Rect(w, h) -> w * h
    Empty -> 0.0
}

fun main() {
    var p = Point(x = 3, y = 4)
    p.x = 10
    print("point ${p.x},${p.y}")

    print("area ${area(Shape.Circle(r = 2.0))}")
    print("area ${area(Shape.Rect(w = 3.0, h = 4.0))}")

    var xs: List<i32> = List.empty()
    xs.push(7)
    xs.push(35)
    print("sum ${xs.get(i = 0) + xs.get(i = 1)}")
}
```

```
point 10,4
area 12.566360
area 12.000000
sum 42
```

## How this documentation relates to the repository

The authoritative in-repo documents are the `plan/*.md` files in the
[Kelp repository](https://homelabone.xenoo.dev/gittea/Juniper/kelp): `syntax.md`
is the syntax and style authority, `architecture.md` is the design,
`roadmap.md` is the plan, `done.md` is the milestone record. This wiki is a
web-friendly view of them, with the standard library and the library catalogue
added; where they disagree, the plan document wins and the page has a bug.

See [Source documents](meta/source-documents.md) for the map.
