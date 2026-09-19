# Tooling

Three programs sit around the language, and the split between them is
deliberate: the compiler never learns about projects, and the project tool never
compiles anything itself.

| Piece | What it is | Repository |
| --- | --- | --- |
| `kelpc` | the compiler: lexing, preprocessing, parsing, type inference, move/borrow checking, code generation | [Juniper/kelp](https://homelabone.xenoo.dev/gittea/Juniper/kelp) |
| Coral | the build tool and package manager: manifest, tasks, build cache, dependencies, toolchains | [Juniper/coral](https://homelabone.xenoo.dev/gittea/Juniper/coral) |
| Lighthouse | editor support: a language server plus VS Code and IntelliJ integrations | [Juniper/lighthouse](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse) |

## How they divide the work

**`kelpc` is the compiler, and it is standalone.** It takes `.kp` sources and
produces a binary, through either backend. A loose file compiles on its own, with
no manifest and no project; `kelpc` also reads a `coral.toml` when it is handed a
project, and then it uses exactly three fields from it (`name`, `version`,
`entry`).

**Coral owns the project, not the compiler.** `kelpc` stays the compiler; Coral
owns the project — the `coral.toml` manifest, tasks, build cache and dependencies
— and calls `kelpc` as a subprocess, never the reverse (roadmap open item 72,
[Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md)).
That is why "how do I build?" and "how do I name a dependency?" are two different
chapters: one is a command, the other is a manifest line.

**Lighthouse is editor-side only.** It never builds your program's artifacts: it
runs `kelpc` to find out what does not compile, indexes your sources and the
standard library to answer the questions an editor asks (completion, hover,
go-to-definition, rename), and talks LSP to the editor.

## What you need for what

| To… | You need |
| --- | --- |
| build or run a single `.kp` file | `kelpc` |
| format a file, or check it in CI | `kelpc fmt` |
| have a project with dependencies, tasks and a pinned compiler | Coral |
| completion, hover, diagnostics in the editor | Lighthouse (+ `kelpc` for diagnostics) |

## Pages

- [`kelpc` CLI](kelpc-cli.md) — subcommands, backends, artifacts, `fmt`
- [Coral](coral.md) — manifest, commands, dependencies, toolchains
- [Lighthouse](lighthouse.md) — the language server and the editor integrations

## See also

- [Install and build](../getting-started/install.md)
- [Libraries (fpl)](../libraries/index.md) — what a dependency looks like from the
  consumer's side
