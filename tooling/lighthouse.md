---
title: "Lighthouse"
description: "Lighthouse is the editor support for Kelp - a language server, plus the IntelliJ plugin that talks to it. This page follows Lighthouse's README, which is the authority, and it..."
isPublished: true
tags: "tooling"
---
Lighthouse is the editor support for Kelp: a language server, plus the IntelliJ
plugin that talks to it. This page follows
[Lighthouse's README](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/src/branch/main/README.md),
which is the authority, and it says where a claim comes from a run instead.

| Piece | What it is |
| --- | --- |
| `server/` | the `lighthouse` language server: a Rust binary with no external crates, the same constraint `kelpc` and Coral hold themselves to |
| `intellij/` | an IntelliJ plugin: `.kp` file type, everything the server offers, a Kelp project entry, a Coral run configuration, a gutter run icon on `fun main()`, and the project's compiler version in Settings |

The server has no command-line flags: it reads no arguments in `server/src/main.rs`
and speaks LSP over stdio, which is why the editor launches it and nothing else
does. Running `lighthouse --help` prints nothing at all. It is a plain LSP
server, so any editor whose LSP client can start it can drive it; the IntelliJ
plugin is the client this repository ships, and it is the only one.

## Two sources of truth

The split explains what the server can and cannot do, and it is worth reading
before trusting a squiggle or a completion.

**`kelpc` is the authority on what compiles.** On open and on save, the server
builds the current file's project and turns whatever `kelpc` prints on stderr into
diagnostics, grouped by the file each error points at. It finds the compiler
through `$KELPC` first (`server/src/diagnostics.rs`), which is what makes a
development build of the compiler usable with a release build of the server.

**Everything else comes from an index the server builds itself.** `kelpc` has no
way to be asked about a symbol, so `server/src/index.rs`
reads the project's `.kp` files and the standard library, and answers from the text.
The index has a scanner and no type checker.

What that means per feature:

| Feature | Where the answer comes from | What a wrong answer costs |
| --- | --- | --- |
| Diagnostics | `kelpc`, run on open and on save | none: the compiler is the authority |
| Completion | the index | a missing or lower-ranked item |
| Hover, inlay hints | the index, including the little it can infer | an absent or less precise type |
| Go-to-definition, symbols | the index | a jump that is not offered |
| Signature help | the index | an argument list that is not shown |
| References, rename | the index, checked against the source text before the edit | a reference missed, never a bad edit |
| Auto-import, organize imports | the index, applied as a literal `impl` line | an import you can see in the diff and reject |

The consequence the README draws from this is the important one: **the index
guesses and the compiler decides**. A wrong guess can cost an offer, and it cannot
produce a wrong edit on its own, because every auto-import is an `impl` line the
programmer sees before accepting it and every rename re-reads the text it is about
to change.

One error shape is repaired automatically: a misspelled bare-call name
(`println` for `print`) becomes a quick fix, ranked by edit distance against the
file's own `fun` declarations plus the free-standing builtins (`print`, `print!`,
`panic`, `assert`).

## Features

| Feature | What it does |
| --- | --- |
| Completion | names in scope, this file's declarations, imported namespaces, builtins and keywords; after a `.` it offers a `datac`'s fields, an `enum`'s variants, `fun Type.method` declarations, and the compiler's own methods on `List`, `Map`, `Box`, `String` and `Bytes` |
| Auto-import | `str.con` completes to `concat`, and accepting it writes `impl "std/str"` at the top of the file; the same fix is a code action on a name that resolves nowhere (`Import "shapes/circle" and qualify as circle.Circle`), and `impl "` completes module paths |
| Hover | the declaration as written, its `///` documentation, and where it came from; a binding shows the type the index could infer |
| Go-to-definition | into a project file or into the standard library, from a vendored copy of the shipped sources |
| Signature help | parameter names and types with the active argument tracked, including named arguments |
| Symbols and folding | document outline with `datac` fields and `enum` variants as children, workspace symbol search, brace and comment folding |
| References and rename | workspace-wide and token-aware: a name inside a comment or a string is not a reference, and a rename will not touch one |
| Inlay hints | the inferred type of a `val`/`var` whose initializer is a call or a field access |
| Organize imports | sort, de-duplicate and drop unused `impl` lines (`source.organizeImports`) |
| Its own warnings | an `impl` whose namespace is never used, which `kelpc` does not report; suppressed in a file that uses `alias %*x*%` substitution, where the answer is unknowable |

## The standard library is a snapshot

`kelpc` embeds its standard library in the binary rather than shipping `.kp` files,
so the server carries its own copy: `server/stdlib/`, one `.kp` per shipped
module except `std/rt` (17 modules today), regenerated from a
kelp checkout by `server/tools/sync-stdlib.sh`. That copy is what go-to-definition
into the standard library and completion of `str.*` are answered from.

Two environment variables change that:

| Variable | Effect |
| --- | --- |
| `KELP_SRC` | a kelp checkout to read `kelpc/std` from, instead of the embedded copy (`server/src/stdlib.rs`), which is what developing the language and the server together wants |
| `KELPC` | the compiler to run for diagnostics, ahead of `PATH` |

Go-to-definition into the standard library writes the sources to
`~/.cache/lighthouse/stdlib/` on first use, because the server cannot point into a
compiler binary.

## Editor setup: IntelliJ

**The plugin requires IntelliJ IDEA Ultimate.** The LSP client API is not in
Community builds, and the README records that the classes are absent from a real
Community distribution. Everything else in the plugin is ordinary, but building
against Ultimate is what lets it use the server at all.

```sh
cd lighthouse/intellij
./gradlew buildPlugin     # the plugin zip
./gradlew runIde          # a sandboxed IDE with the plugin loaded
```

Install one of two ways:

1. **From disk**: `./gradlew buildPlugin`, then **Settings ▸ Plugins ▸ ⚙ ▸ Install
   Plugin from Disk…**.
2. **From the self-hosted update site**, added once under **Settings ▸ Plugins ▸ ⚙
   ▸ Manage Plugin Repositories**:

   ```text
   https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/raw/branch/main/intellij/updatePlugins.xml
   ```

   A published version then shows up as an ordinary update. To publish one, bump
   `version` in `build.gradle.kts`, run `./gradlew buildPlugin`, and copy the zip
   and the refreshed `updatePlugins.xml` to the update site.

What the plugin adds:

| Piece | What it does |
| --- | --- |
| `.kp` file type and highlighting | a hand-written lexer, not the server's |
| Everything in the feature table | through the LSP client |
| **File ▸ New ▸ Project ▸ Kelp** | scaffolds a project with `coral init`, with a version field and a **Kelp version** field for the `[toolchain]` pin |
| A Coral run configuration type | build and run a project from the IDE |
| A gutter run icon | on `fun main()` |
| **Settings ▸ Languages & Frameworks ▸ Kelp** | the project's compiler version, which is the `[toolchain] pin` in `coral.toml`, and which can install a version with `coral toolchain kelp install <ver>` in the background |

That last row is the one to know about: the plugin reads and writes the project's
pin, so the IDE uses the project's compiler rather than its own. See
[Coral's pinning section](/tooling/coral#the-manifest).

## Tests

```sh
cd server && cargo test
```

Unit tests cover the scanner, the index (run against the real vendored standard
library), the JSON parser and the analysis layer. `server/tests/lsp.rs` is
end-to-end: it starts a real server, speaks JSON-RPC to it over stdio, and checks
the features against a temporary project, including that auto-import arrives as one
visible edit, that a definition lands in a file, that a message the parser cannot
read is skipped rather than fatal, and that a source file full of non-ASCII does
not end the session.

## Deliberate gaps

- **Diagnostics come from `kelpc check --json`.** The server runs the compiler
  with `--json` and reads one document, so every finding carries its own 1-based
  range (turned into LSP's 0-based positions on the way out) and its severity:
  `error`, `warning` or `outdated`. A `kelpc` older than 26.09.1 still has its
  prose read by `server/src/diagnostics.rs`, which is the fallback that goes away
  once no supported compiler predates the flag.
- **No whole-program resolution.** The index reads one file at a time and has no
  type checker, so a generic receiver (`fun Pair<A, B>.first`) resolves only when
  the call site spells the argument types, and a receiver reached through a chain
  of calls usually cannot be typed at all. The compiler holds the answer and does
  not share it.
- **No semantic tokens.** Highlighting is the hand-written lexer in `intellij/`;
  `kelpc`'s own lexer is the only authoritative one, and nothing calls it.
- **The plugin is not published to the Marketplace.** It installs from the
  self-hosted update site above.

The README also lists "Formatting. No `kelpc fmt` exists to call" as missing, which
is now half stale: `kelpc fmt` shipped, with `-w` and `--check` (see
[`kelpc` CLI](/tooling/kelpc-cli#fmt)). What is still missing is the server *calling* it,
so an editor still has nothing to invoke for format-on-save.

## See also

- [`kelpc` CLI](/tooling/kelpc-cli)
- [Coral](/tooling/coral)
- [Tooling](/tooling)
- [Install and build](/getting-started/install)
- [Standard library](/stdlib)
