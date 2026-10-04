---
title: "Tutorial 18: Where to go next"
description: "Chapter 18 of the Kelp tutorial: a small capstone, where the reference, library, tooling and plan pages are, and the fixes made after checking this tutorial against the compiler."
isPublished: true
tags: "tutorial, getting-started"
---
You have now seen the language end to end: values and functions, control flow and iterators,
text, records and enums, ownership, errors, collections, traits and generics, closures,
projects, capabilities, threads, HTTP and TLS, the tooling, a bare-metal kernel and a UI
library. This last chapter has a capstone exercise, a map of the reference, and an honest list
of what did not behave as the docs or my expectations said while I was writing this book.

## A capstone

Count the words in a text, then print them from the most to the least frequent. It uses a
`Map` (chapter 8), `split` (chapter 4), a `datac` whose **field order decides the sort**
(chapter 8: fields compare in declaration order, so `count` goes first), and `for` over the
list (chapter 3):

```kelp
impl "std/str"

// fields compare in declaration order, so `count` first sorts by count
datac Entry(val count: i64, val word: String)

fun main() {
    val text = "the cat and the dog and the bird"
    val words = str.split(text, " ")
    var counts: Map<String, i64> = Map.new()
    for w in words {
        counts.insert(key = w.as_str(), v = counts.get_or(key = w.as_str(), fallback = 0) + 1)
    }

    var entries: List<Entry> = List.empty()
    val keys = counts.keys()
    for k in keys {
        entries.push(Entry(count = counts.get(key = k.as_str()), word = k.clone()))
    }
    entries.sort()
    entries.reverse()
    for e in entries {
        print("${e.count} ${e.word}")
    }
}
```

```text
3 the
2 and
1 dog
1 cat
1 bird
```

Both backends printed this. Ties come out in reverse of their sort order (`dog`, `cat`,
`bird`), because the list is sorted ascending by `(count, word)` and then reversed.

## The reference

| For | Read |
| --- | --- |
| The surface syntax, one topic per page | [The language](/language), starting from [Lexical structure](/language/lexical) |
| Every `std/*` module | [Standard library](/stdlib) and the [index](/reference/stdlib-index) |
| First-party libraries: JSON, CSV, TOML, dates, big integers, HTTP helpers, a Discord client, and more | [Libraries (fpl)](/libraries) and the [catalogue](/libraries/catalogue) |
| Writing a library of your own | [Writing a library](/libraries/writing-a-library) |
| What a grant can and cannot stop | [Capability patterns](/reference/capability-patterns) and the [threat model](/reference/capability-threat-model) |
| The whole toolbox | [`kelpc` CLI](/tooling/kelpc-cli), [Coral](/tooling/coral), [`kelpc doc`](/tooling/kelpc-doc), [Sanitizers](/tooling/sanitizers), [Release tooling](/tooling/release-tooling), [Lighthouse](/tooling/lighthouse) for editor support |
| Working programs, with their sources | [Examples](/examples) |
| Project ideas | [Project ideas](/getting-started/project-ideas) |
| Software built on Kelp | [The Kelp family](/family), including [WebKelp](/family/webkelp) |
| Where the project is going | the [roadmap](/meta/roadmap), the [changelog](/changelog), and the plan documents in the [repository](https://homelabone.xenoo.dev/gittea/Juniper/kelp) (`plan/syntax.md` is the authority for the language; `plan/roadmap.md` for the schedule) |
| Hacking on the compiler | [Compiler](/compiler) and [Contributing](/meta/contributing) |

Pages that go deeper on the tutorial's chapters: [Ownership](/language/ownership) and
[Pitfalls](/language/pitfalls) for chapter 6, [Generic traits](/language/generic-traits)
for `From` and `?`, [Concurrency in v1](/language/concurrency) for chapter 13,
[`std/tls`](/stdlib/tls) for mutual TLS and ALPN, [Freestanding mode](/language/freestanding)
and [Polyp on bare metal](/libraries/polyp-freestanding) for chapters 16 and 17.

## Fixes made while checking the book

The tutorial initially found three compiler bugs. They are fixed for this
release, and their fixtures run on both backends:

- Expressions evaluate strictly left to right, including template pieces, call
  arguments, operators and aggregate fields. A template may therefore contain
  two side-effecting calls without the C backend reordering them.
- Several lock-typed `pd val` globals now initialise on LLVM just as they do on
  the C backend. A `Mutex`, `RwLock`, `Condvar` and lock-protected collection
  can appear together and be used from worker threads.
- `kelpc doc` keeps a record comment on its record. A same-line field without
  its own comment is listed without a description.

The sanitizer constraint remains: an AddressSanitizer binary cannot run under
`ulimit -v`, so the bound in chapter 15 is `ulimit -t` and `timeout`.

## What was not run

For honesty, the pieces of this book I did not execute: building the compiler from source and
the installer (chapter 1), Coral itself, `coral sync` and the `testkit` task (chapters 11 and
15), the GTK backend and its smoke tests (chapter 17), the bare-metal Polyp framebuffer kernels
(chapter 17) and any x86-64 or aarch64 kernel boot (chapter 16 booted riscv64 only).
Everything else printed in this tutorial is the output of a real run.

## Exercises

1. Extend the capstone to print only words that occur more than once.
2. Pick a project from [Project ideas](/getting-started/project-ideas), start it with the
   layout from chapter 11, and decide before writing a line which `impl` lines it needs and
   which grants you would give each module.

<details>
<summary>Solutions</summary>

1. Add `if e.count > 1 { ... }` around the `print` in the final loop. Verified:

```kelp
impl "std/str"

// fields compare in declaration order, so `count` first sorts by count
datac Entry(val count: i64, val word: String)

fun main() {
    val text = "the cat and the dog and the bird"
    val words = str.split(text, " ")
    var counts: Map<String, i64> = Map.new()
    for w in words {
        counts.insert(key = w.as_str(), v = counts.get_or(key = w.as_str(), fallback = 0) + 1)
    }

    var entries: List<Entry> = List.empty()
    val keys = counts.keys()
    for k in keys {
        entries.push(Entry(count = counts.get(key = k.as_str()), word = k.clone()))
    }
    entries.sort()
    entries.reverse()
    for e in entries {
        if e.count > 1 {
            print("${e.count} ${e.word}")
        }
    }
}
```

```text
3 the
2 and
```

2. There is no single answer. The check to apply is the one from chapter 12: the first lines
   of each file should say everything that file can touch.

</details>
