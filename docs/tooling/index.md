# Tooling

Three programs sit around the language, and the split between them is deliberate:
the compiler never learns about projects, and the project tool never compiles
anything itself.

| Piece | What it owns | Repository |
| --- | --- | --- |
| `kelpc` | lexing, preprocessing, parsing, type inference, move and borrow checking, code generation | [Juniper/kelp](https://homelabone.xenoo.dev/gittea/Juniper/kelp) |
| Coral | the project: manifest, tasks, build cache, dependencies, toolchains | [Juniper/coral](https://homelabone.xenoo.dev/gittea/Juniper/coral) |
| Lighthouse | editor support: a language server plus a VS Code extension and an IntelliJ plugin | [Juniper/lighthouse](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse) |

The versions these pages were written against, as observed on the machine that
built them, are `kelpc 0.2.2` and Coral `v0.5.4`. They are not part of the
language's contract; a checkout builds its own.

## How they divide the work

**`kelpc` is standalone.** Hand it a `.kp` file and it compiles it, with no
manifest and no project. Hand it a directory with a `coral.toml` in it and it
compiles that project instead, using exactly three fields from the manifest
(`name`, `version`, `entry`); it stops parsing at the first `[section]`, which is
how Coral keeps its own keys out of the compiler's way. A loose file is its own
module root; inside a project, `impl` paths resolve against `src/`. See
[`kelpc` CLI](kelpc-cli.md#projects).

**Coral owns the project, and calls `kelpc` as a subprocess, never the reverse**
([Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md)).
It reads the manifest, materialises declared inputs (a pinned compiler, fetched
dependencies), decides whether a build is up to date, and then runs `kelpc` on the
entry point. That is why "how do I build?" and "how do I name a dependency?" are
two different pages: one is a command, the other is a manifest line.

**Lighthouse never builds your artifacts.** It runs `kelpc` on open and on save to
learn what does not compile, and answers editor questions (completion, hover,
go-to-definition, rename) from a text-level index it builds itself. It is the only
one of the three that runs while you type.

## When `kelpc` alone is enough

| Situation | Tool |
| --- | --- |
| a single file, or a handful of files with no dependencies | `kelpc` |
| a program that imports a library from a git remote | Coral, because fetching a dependency is Coral's job |
| a project that must build with one specific compiler version | Coral, with a `[toolchain]` pin |
| CI that must assert "this build did no I/O" | Coral, with `sync` then `build --offline` |
| formatting one file, or checking formatting in CI | `kelpc fmt` |
| a task list (`report`, `bench`, `release`) that the project owns | Coral, with `[tasks]` |

## What you need for what

| To do this | You need | Page |
| --- | --- | --- |
| compile or run a file, choose a backend, format sources | `kelpc` | [`kelpc` CLI](kelpc-cli.md) |
| have a project with dependencies, tasks, a pinned compiler | Coral (and `kelpc` for the actual compile) | [Coral](coral.md) |
| completion, hover, diagnostics, rename in an editor | Lighthouse, plus `kelpc` for diagnostics | [Lighthouse](lighthouse.md) |
| understand what a dependency is, and why a folder must stand alone | the library model | [Libraries (fpl)](../libraries/index.md) |
| write one | the library rules | [Writing a library](../libraries/writing-a-library.md) |

## Pages

- [`kelpc` CLI](kelpc-cli.md): every subcommand and flag, where artifacts land, the
  two backends, `fmt`'s rules and its refusals, environment variables, and what a
  project changes about module resolution.
- [Coral](coral.md): the manifest key by key, the command surface, the dependency
  model, what a sync installs and fetches, the toolchain store, environment
  variables, and a transcript of a real session.
- [Lighthouse](lighthouse.md): the two sources of truth, the feature table, editor
  setup for both integrations, the standard-library snapshot, the tests, and the
  deliberate gaps.

## See also

- [Install and build](../getting-started/install.md)
- [Projects and coral.toml](../getting-started/projects.md)
- [Compiler](../compiler/index.md)
