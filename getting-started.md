---
title: "Getting started"
description: "Three pages, in order -"
isPublished: true
tags: "getting-started"
---
Three pages, in order:

1. **[Install and build](/getting-started/install)**: build `kelpc`, run a file, pick a
   backend, and what the toolchain needs from the machine.
2. **[Your first program](/getting-started/first-program)**: a guided tour of Kelp's shape in
   one file, with output, and the Coral commands that build and run it.
3. **[Projects and coral.toml](/getting-started/projects)**: what a project is, what a
   `coral.toml` contains, and how dependencies land in `src/deps/`.

## The one-paragraph version

Kelp is a compiled, statically typed language with capability-based security.
Values are owned (`String`, `Bytes`, `List`, `Map`, `Box`, `datac`, `enum`) or
borrowed (`str`, `View`, `&T`); there is no garbage collector and no `unsafe`.
Functions are declared with `fun`, return types with `.R: T`, errors are
`Option`/`Result` values, and pattern matching is `when`. A module states what it
may touch on its `impl` lines, and that is the only thing that grants authority.

The build side has two tools and the split matters: `kelpc` is the compiler, and
[Coral](/tooling/coral) is the build tool and package manager around it. A single
`.kp` file needs only `kelpc`. Anything that becomes a project wants Coral, and it
is easier to start with it than to adopt it once there are dependencies.

## Where to go next

| If you want to… | Read |
| --- | --- |
| know the language's shape in one page | [Language overview](/language) |
| look up a specific construct | [Language](/language) chapter pages |
| call something in the standard library | [Standard library](/stdlib) |
| grant (or restrict) authority | [Capabilities](/language/capabilities) |
| use a ready-made library | [Libraries (fpl)](/libraries) |
| understand a compiler error | [Errors and panics](/language/errors), [Pitfalls](/language/pitfalls) |
| hack on `kelpc` itself | [Compiler](/compiler) |
