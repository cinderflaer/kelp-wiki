---
title: "Tutorial"
description: "A tutorial for programmers who have not seen Kelp: from the first program to a small command-line tool that reads a file, counts its words and reports errors through exit codes. Every program was compiled and run with kelpc 26.10.4."
isPublished: true
tags: "tutorial, getting-started"
---
This tutorial teaches Kelp by writing programs. It is for someone who already
programs in Python, Rust, C or a similar language and has not seen Kelp before.
You do not need to know any systems programming, but the ideas about ownership
and capabilities are new, so each chapter spends a little time on them.

The tutorial is short on purpose. Each chapter teaches one idea, shows the code,
shows the output, and ends with a small "try it". The last chapter combines the
ideas into a real tool.

## What you need

- The `kelpc` compiler, version 26.10.6 or later. [Install](/getting-started/install)
  explains the routes to get it.
- A text editor. [Editor setup](/getting-started/editor) lists the options.

## How the examples were checked

Every program in this tutorial was compiled and run with the `kelpc 26.10.6`
release binary. The output under each program is the output of that run, copied
without edits. Every compiler error shown is the text `kelpc check` printed for
the file beside it. Where a file path appears in an error, it is shortened to the
file name.

If a program here does not match what you see, the tutorial is wrong or your
compiler is a different version. Check `kelpc version` first.

## Chapters

1. [Install and hello world](/tutorial/01-hello): run a program, build it, read an error.
2. [Values, types and functions](/tutorial/02-values): the scalar types, `val` and `var`, and functions.
3. [Control flow](/tutorial/03-control-flow): `if`, `while`, `for`, `when` and `return`.
4. [Text](/tutorial/04-text): `str` and `String`, templates, and parsing numbers.
5. [Records, enums and ownership](/tutorial/05-data): `datac`, `enum`, methods, and who owns a value.
6. [Errors](/tutorial/07-errors): `Option`, `Result`, `?` and `panic`.
7. [Collections](/tutorial/08-collections): `List`, `Map`, `Box` and arrays.
8. [Traits and generics](/tutorial/09-traits): shared behaviour and bounded type parameters.
9. [Closures and iterators](/tutorial/10-closures): functions that capture values, and `for` over an iterator.
10. [Modules and capabilities](/tutorial/11-projects): splitting code into files, and what a module is allowed to touch.
11. [Tools and tests](/tutorial/15-tooling): `assert`, `check`, `fmt`, `lint` and `doc`.
12. [Build something](/tutorial/18-build-something): a word counter that reads a file and reports its words.

The [language reference](/language) has every rule in full. The chapters link to
it where a topic is larger than the tutorial.
