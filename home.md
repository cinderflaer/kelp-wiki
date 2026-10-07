---
title: "Kelp"
description: "Kelp is a statically typed, compiled systems language whose headline feature is capability-based security. A module declares what it may touch, and that authority is part of the source and checked..."
isPublished: true
tags: "overview"
---
Kelp is a statically typed, compiled systems language whose headline feature is
**capability-based security**. A module declares what it may touch, and that
authority is part of the source and checked at every call site that uses it.

```kelp
impl "std/http" caps(net = ["127.0.0.1:*"])
impl "std/fs"

fun main() {
    print("a program that may talk to 127.0.0.1 and touch the filesystem")
}
```

Those two `impl` lines are the program's entire network and filesystem
authority. There is no other place authority can be acquired: a program cannot
read a file, open a socket, spawn a process or read the clock unless the module
making the call was granted that resource. "What can this code do?" is answered
by the first few lines of a file instead of by auditing it.

## Where to start

<div class="grid cards" markdown>

-   **New to Kelp**

    ---

    Read [Getting started](/getting-started): the language in one page,
    then a program, a tool with an exit code, and tests around it.

-   **Tutorial**

    ---

    The [Tutorial](/tutorial) is a hands-on book for readers who program but
    have not seen Kelp: every program was built and run on both backends.

-   **The language**

    ---

    The [Language chapter](/language) is the reference for the surface
    syntax: types, control flow, functions, ownership, capabilities.

-   **The standard library**

    ---

    [Standard library](/stdlib) documents every `std/*` module and the
    compiler builtins (`String`, `Bytes`, `List`, `Map`, `Box`).

-   **Working on the compiler**

    ---

    [Compiler](/compiler) covers the pipeline, the backend, the runtime and the
    test gates. [Contributing](/meta/contributing) has the
    workflow.

-   **Libraries**

    ---

    [Libraries (fpl)](/libraries) is the first-party library catalogue:
    JSON, CSV, TOML, base64, dates, sets, bit packing, big integers, decimals,
    HTTP helpers, Discord bots and more.

-   **The Kelp family**

    ---

    [Kelp family](/family) is software built on Kelp: [WebKelp](/family/webkelp),
    a markdown-style language that compiles to HTML and CSS, and the
    [conventions](/family/writing-tools-in-kelp) such projects share.
    Try the [live demo](https://homelabone.xenoo.dev/webkelpdemo/) or the
    [playground](https://homelabone.xenoo.dev/webkelpplay/).

-   **Release history**

    ---

    [Changelog](/changelog) records every `kelpc` release: what the language
    and the compiler gained, version by version. [Coral](/tooling/coral-changelog)
    and [Lighthouse](/tooling/lighthouse-changelog) have their own.

</div>

<!-- roadmap:start -->
## Roadmap

Of the 11 marks, **5 are done** (MK1-MK4, and now MK6), **4 in progress** (MK5, MK7, MK8, MK9), **0 not started** and 2 proposed. **MK6 (concurrency) is done**: `thread.spawn`/`thread.join`, `thread.sleep_ms`/`thread.current_id`, the memory model published at [Concurrency in v1](/language/concurrency), and concurrent downloads with one connection pool per worker thread (`examples/download_pool.kp`). No dates: the milestones are ordered by dependency, not by calendar. A
mark moves when its prerequisites land, and `plan/roadmap.md` is the record.

```mermaid
flowchart LR
    subgraph done["Done"]
        MK1["MK1 Core language<br/>very large"]
        MK2["MK2 Modules and compile-time<br/>small"]
        MK3["MK3 Heap and containers<br/>large"]
        MK4["MK4 Capability security<br/>medium"]
    end
    subgraph active["In progress"]
        MK5["MK5 Standard library program<br/>large"]
        MK7["MK7 LLVM backend<br/>large"]
        MK8["MK8 Language ergonomics<br/>large"]
        MK9["MK9 Systems substrate<br/>very large"]
    end
    subgraph planned["Not started"]
        MK6["MK6 Concurrency<br/>very large"]
    end
    subgraph proposed["Proposed"]
        MK10["MK10 Capability model extensions<br/>large"]
        MK11["MK11 Verification and semantics<br/>very large"]
    end
    classDef statusDone fill:#2e8b57,color:#ffffff,stroke:#24633f
    classDef statusActive fill:#c47f00,color:#ffffff,stroke:#9a6400
    classDef statusPlanned fill:#5b6b7a,color:#ffffff,stroke:#455260
    classDef statusProposed fill:#7c6a94,color:#ffffff,stroke:#615275
    class MK1,MK2,MK3,MK4 statusDone
    class MK5,MK6,MK7,MK8,MK9 statusActive
    class MK10,MK11 statusProposed
```

[The roadmap page](/meta/roadmap) points at `plan/roadmap.md`, which is the
authority: it has every mark's scope and status, the five-row critical path, and
what is named but not scheduled. This block is kept by hand against it, and has
to be updated when it moves.
<!-- roadmap:end -->

## What the language has

| | |
| --- | --- |
| Types | `i32` `i64` `u8` `u16` `u32` `u64` `usize` `isize` `f32` `f64` `bool` `char`, plus borrowed text as `str` and `View` |
| Data | `datac` records with `val`/`var` fields, tuple types read by a destructuring binding or `t.0`, `enum` tagged unions, exhaustive `when`, `if let`, type parameters (including `const N: usize`), `const`, `pd` passdowns |
| Ownership | owned builtins `String`, `Bytes`, `List<T>`, `Map<K, V>`, `Box<T>` and the fixed-size array `[T; N]`; moves, shared and `mut` borrows, drops at end of scope, no garbage collector |
| Memory | `static`/`static mut`, `defer`, `Atomic<T>`, and `unsafe` with `Ptr<T>`, volatile access and `repr(...)` layout control, gated per module by `coral.toml`'s `[unsafe]` list |
| Errors | `Option`, `Result`, the `?` operator (converting a failure through `From`), `panic`/`assert` |
| Functions | `fun`, named arguments, function values and closures, receiver methods, stdlib-only argument-type overloading |
| Traits | `trait`/`impl`, default methods, supertraits, associated types, generic traits, `&dyn` and `Box<dyn>`, operator and `Display` traits, the `Iterator` trait behind `for` |
| Modules | `impl "std/fs"`, local-file imports, aliases, `pd` passdowns |
| Capabilities | `fs`, `net`, `process`, `env`, `time`, `rand` |
| Stdlib | `mem` `str` `path` `math` `fmt` `io` `fs` `process` `net` `http` `ws` `encoding` `time` `rand` `env` `list` `option` `result` `atomic` `thread` `sync` `iter` `ops` `convert` |
| Toolchain | `kelpc` (compiler), [Coral](/tooling) (build tool and package manager), [Lighthouse](/tooling) (editor support) |

There are deliberately **no** exceptions, no garbage collector, and no macros.
`unsafe` exists, but it is not ambient: a module may contain it only if
`coral.toml` lists that module under `[unsafe] modules` (see
[Unsafe code and raw pointers](/language/unsafe)).

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

See [Source documents](/meta/source-documents) for the map.

## Repositories

The project lives in Gitea, at
[`homelabone.xenoo.dev/gittea/Juniper`](https://homelabone.xenoo.dev/gittea/Juniper).

| Repository | What it holds |
| --- | --- |
| [`kelp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp) | The compiler `kelpc` in Rust, plus the `plan/*.md` documents that are the authority for the language. |
| [`fpl`](https://homelabone.xenoo.dev/gittea/Juniper/fpl) | One folder per first-party Kelp library: `argparse`, `bigint`, `csv`, `json` and the rest of the catalogue. |
| [`coral`](https://homelabone.xenoo.dev/gittea/Juniper/coral) | The build tool and package manager. |
| [`lighthouse`](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse) | Editor support: the LSP server and the IntelliJ plugin. |
| [`webkelp`](https://homelabone.xenoo.dev/gittea/Juniper/webkelp) | A markdown-style language that compiles to HTML and CSS, written in Kelp. See [Kelp family](/family). |
| [`kelp-wiki`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki) | The sources for this documentation. `main` is the MkDocs source; the `wikijs` branch is what this wiki imports. |

All repositories, including the ones unrelated to Kelp:
[homelabone.xenoo.dev/gittea/Juniper](https://homelabone.xenoo.dev/gittea/Juniper).
