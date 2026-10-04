---
title: "Tutorial"
description: "A hands-on tutorial book for Kelp, for readers who know some Python, Rust or C: every program was built and run on both backends, and every output and compiler error is quoted from a real run."
isPublished: true
tags: "tutorial, getting-started"
---
This tutorial teaches Kelp by writing programs. It is for a reader who already
programs (Python, Rust or C level) and has not seen Kelp. Each chapter is one
page of a few hundred words and some code, and ends with exercises whose solutions
are folded under a `Solutions` heading.

How it was checked: every program in the tutorial was built with a prebuilt
`kelpc 26.09.5` and run on **both** the default LLVM backend and the C oracle
(`KELPC_ORACLE=c`), with identical output; the page quotes the source and the
output. Every compiler refusal shown is the real text of `kelpc check`. Where a
feature surprised the author, the page says what it actually does.

The reference pages are linked from each chapter instead of repeated: start from
the [Language chapter](/language), the [Standard library](/stdlib) and the
[tooling pages](/tooling).

## Chapters

1. [Install and hello world](/tutorial/01-hello)
2. [Values, types and functions](/tutorial/02-values)
3. [Control flow and iterators](/tutorial/03-control-flow)
4. [Text](/tutorial/04-text)
5. [Records, enums and methods](/tutorial/05-data)
6. [Ownership, borrowing and moves](/tutorial/06-ownership)
7. [Errors: Option, Result and panic](/tutorial/07-errors)
8. [Collections](/tutorial/08-collections)
9. [Traits and generics](/tutorial/09-traits)
10. [Closures and scoped blocks](/tutorial/10-closures)
11. [Projects and modules](/tutorial/11-projects)
12. [Capabilities](/tutorial/12-capabilities)
13. [Concurrency](/tutorial/13-concurrency)
14. [Networking, HTTP and TLS](/tutorial/14-networking)
15. [Testing and tooling](/tutorial/15-tooling)
16. [Freestanding, a tiny kernel](/tutorial/16-freestanding)
17. [Polyp UI](/tutorial/17-polyp)
