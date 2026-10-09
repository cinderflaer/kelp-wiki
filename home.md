---
title: "Kelp"
description: "Kelp is a statically typed, compiled systems language with capability-based security: a module declares what it may touch, and every call site that uses that authority is checked."
isPublished: true
tags: "overview"
---

Kelp is a statically typed, compiled systems language whose headline feature is
**capability-based security**. A module declares what it may touch, and that
authority is part of the source and checked at every call site that uses it. A
program cannot read a file, open a socket, spawn a process or read the clock unless
the module making the call was granted that resource, so "what can this code do?"
is answered by the first few lines of a file. The language itself is small: records
and tagged unions, ownership without a garbage collector, `Option` and `Result` with
`?`, and modules.

## Current release

**26.10.5** (2026-10-09). The release notes and the binary are on the
[v26.10.5 release page](https://homelabone.xenoo.dev/gittea/Lilly/kelp/releases/tag/v26.10.5).
Every release is listed in the [changelog](/changelog).

## Start here

- [Tutorial](/tutorial): a hands-on book for readers who already program.
- [Getting started](/getting-started): install `kelpc`, then write a program, a tool and its tests.
- [Language](/language): the surface syntax, one page per topic.
- [Standard library](/stdlib): every `std/*` module and the compiler builtins.

## Sections

| Section | What is in it |
| --- | --- |
| [Tutorial](/tutorial) | A hands-on book, in chapters, for readers who know another language. |
| [Getting started](/getting-started) | Eight steps: install, editor, first program, first tool, testing, projects, troubleshooting, project ideas. |
| [Language](/language) | The surface syntax, one page per topic, with a grammar summary. |
| [Standard library](/stdlib) | Every `std/*` module, the capability it needs, and the compiler builtins. |
| [Libraries](/libraries) | The 28 first-party libraries in the fpl repository, each one a dependency you fetch. |
| [Tooling](/tooling) | `kelpc` (the compiler), Coral (the build tool) and Lighthouse (editor support). |
| [Compiler](/compiler) | How `kelpc` turns sources into a program: the pipeline, the backend and the tests. |
| [Family](/family) | Software built on Kelp, starting with WebKelp. |
| [Reference](/reference) | Lookup pages: the standard library index and the capability model. |
| [Meta](/meta) | How this documentation relates to the code, the roadmap, and the audit. |

Where the authority lives is explained in [Source documents](/meta/source-documents).
