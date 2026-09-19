# Getting started

Three pages, in order:

1. **[Install and build](install.md)** — build `kelpc`, run a file, pick a
   backend, and what the toolchain needs from the machine.
2. **[Your first program](first-program.md)** — a guided tour of Kelp's shape in
   one file, with output.
3. **[Projects and coral.toml](projects.md)** — what a project is, what a
   `coral.toml` contains, and how dependencies land in `src/deps/`.

## The one-paragraph version

Kelp is a compiled, statically typed language with capability-based security.
Values are owned (`String`, `Bytes`, `List`, `Map`, `Box`, `datac`, `enum`) or
borrowed (`str`, `View`, `&T`); there is no garbage collector and no `unsafe`.
Functions are declared with `fun`, return types with `.R: T`, errors are
`Option`/`Result` values, and pattern matching is `when`. A module states what it
may touch on its `impl` lines, and that is the only thing that grants authority.

## Where to go next

| If you want to… | Read |
| --- | --- |
| know the language's shape in one page | [Language overview](../language/index.md) |
| look up a specific construct | [Language](../language/index.md) chapter pages |
| call something in the standard library | [Standard library](../stdlib/index.md) |
| grant (or restrict) authority | [Capabilities](../language/capabilities.md) |
| use a ready-made library | [Libraries (fpl)](../libraries/index.md) |
| understand a compiler error | [Errors and panics](../language/errors.md), [Pitfalls](../language/pitfalls.md) |
| hack on `kelpc` itself | [Compiler](../compiler/index.md) |
