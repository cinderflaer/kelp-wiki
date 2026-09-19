---
title: "Getting started"
description: "Eight pages, in order - build the compiler, set up an editor, write a program, turn it into a tool, test it, make it a project, and find a small thing to build next."
isPublished: true
tags: "getting-started"
---
Kelp is small enough to learn by writing it, so this chapter is a path rather
than a reference: eight pages, each one a step you can run.

1. **[Install and build](/getting-started/install)**: build `kelpc`, run a file, pick a
   backend, and what the toolchain needs from the machine.
2. **[Set up your editor](/getting-started/editor)**: Lighthouse as a language server,
   `kelpc fmt`, the VS Code and IntelliJ setups, and what to do with no editor at all.
3. **[Your first program](/getting-started/first-program)**: a guided tour of Kelp's shape in
   one file, with output, and the Coral commands that build and run it.
4. **[A first real tool](/getting-started/first-tool)**: a `head` you can use, written line
   by line: `argv`, a capability, an error path, and an exit code.
5. **[Testing what you write](/getting-started/testing)**: `testkit` and a Coral task,
   which together are the whole test harness Kelp has.
6. **[Projects and coral.toml](/getting-started/projects)**: what a project is, what a
   `coral.toml` contains, and how dependencies land in `src/deps/`.
7. **[When it does not work](/getting-started/troubleshooting)**: which program spoke, the
   failures a first week produces, and where to report a real bug.
8. **[Small projects to build](/getting-started/project-ideas)**: a ladder of ideas, from
   one-file programs that need nothing to a project with tests.

## The one-paragraph version

Kelp is a compiled, statically typed language with capability-based security.
Values are owned (`String`, `Bytes`, `List`, `Map`, `Box`, `datac`, `enum`) or
borrowed (`str`, `View`, `&T`); there is no garbage collector and no `unsafe`.
Functions are declared with `fun`, return types with `.R: T`, errors are
`Option`/`Result` values, and pattern matching is `when`. A module states what it
may touch on its `impl` lines, and that is the only thing that grants authority.

## The two tools

The build side has two tools and the split matters: `kelpc` is the compiler, and
[Coral](/tooling/coral) is the build tool and package manager around it. A single
`.kp` file needs only `kelpc`. Anything that becomes a project wants Coral, and it
is easier to start with it than to adopt it once there are dependencies.

## Where to go next

| If you want to… | Read |
| --- | --- |
| know the language's shape in one page | [Language overview](/language) |
| look up a specific construct | [Language](/language) chapter pages |
| see eighteen programs that were built and run | [Examples](/examples) |
| find something small to build | [Small projects to build](/getting-started/project-ideas) |
| call something in the standard library | [Standard library](/stdlib) |
| grant (or restrict) authority | [Capabilities](/language/capabilities) |
| use a ready-made library | [Libraries (fpl)](/libraries) |
| understand a compiler error | [When it does not work](/getting-started/troubleshooting), [Errors and panics](/language/errors), [Pitfalls](/language/pitfalls) |
| hack on `kelpc` itself | [Compiler](/compiler) |
