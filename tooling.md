---
title: "Tooling"
description: "Three programs sit around the language: kelpc compiles, Coral owns the project, and Lighthouse serves editors. The split is deliberate, and this page shows which one you need."
isPublished: true
tags: "tooling"
---
Three programs sit around the language. `kelpc` compiles, Coral owns the
project, and Lighthouse serves your editor. Each one does one job, and none of
them does another's. This page explains the split and points you to the page for
each tool.

| Piece | What it owns | Repository |
| --- | --- | --- |
| `kelpc` | lexing, preprocessing, parsing, type inference, move and borrow checking, code generation, formatting, linting, docs | [Lilly/kelp](https://homelabone.xenoo.dev/gittea/Lilly/kelp) |
| Coral | the project: manifest, tasks, build cache, dependencies, toolchains | [Lilly/coral](https://homelabone.xenoo.dev/gittea/Lilly/coral) |
| Lighthouse | editor support: a language server and an IntelliJ plugin | [Lilly/lighthouse](https://homelabone.xenoo.dev/gittea/Lilly/lighthouse) |

## Versions

Versions move on their own schedule, so check the release pages rather than
trusting a number written here. As of this page:

| Piece | Newest tagged release | Notes |
| --- | --- | --- |
| `kelpc` | `v26.10.4` (`kelpc 26.10.4`) | the `main` branch's `Cargo.toml` carries the same version |
| Coral | no tag for the Kelp port yet | `main` is Coral written in Kelp; the newest tag, `v26.09.4`, is the older Rust build |
| Lighthouse | IntelliJ plugin `26.09.2` | the language server is `26.9.5` in `server/Cargo.toml` and has no tag |

Coral's Rust implementation survives only on the `rust-legacy` branch, kept for
reference. Do not use it in production.

## How they divide the work

**`kelpc` is standalone.** Hand it a `.kp` file and it compiles it, with no
manifest and no project. Hand it a directory with a `coral.toml` in it and it
compiles that project instead. It reads the flat keys it needs (`name`,
`version`, `entry`, plus `http_pool` and `naming_case`) and the sections that
change what it compiles (`[build]`, `[target]`, `[caps]`, `[unsafe]` and
`[extern]`). It skips the sections that belong to Coral. See
[`kelpc` CLI](/tooling/kelpc-cli#projects).

**Coral owns the project, and calls `kelpc` as a subprocess.** It reads the
manifest, installs a pinned compiler, fetches dependencies, decides whether a
build is up to date, and then runs `kelpc` on the entry point. That is why "how
do I build?" and "how do I name a dependency?" are two different pages: one is a
command, the other is a manifest line. The Coral README is the authority for its
design: [Coral's README](https://homelabone.xenoo.dev/gittea/Lilly/coral/src/branch/main/README.md).

**Lighthouse never builds your artifacts.** It runs `kelpc check --json` on open,
on save and shortly after you stop typing, and `kelpc lint` on open and on save,
so that you see what does not compile. It answers editor questions (completion, hover,
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
| the style rules a formatter cannot enforce, reported as warnings | `kelpc lint` |
| a task list (`report`, `bench`, `release`) that the project owns | Coral, with `[tasks]` |

## What you need for what

| To do this | You need | Page |
| --- | --- | --- |
| compile or run a file, format sources | `kelpc` | [`kelpc` CLI](/tooling/kelpc-cli) |
| generate documentation from `///` comments | `kelpc doc` | [`kelpc doc`](/tooling/kelpc-doc) |
| have a project with dependencies, tasks, a pinned compiler | Coral (and `kelpc` for the actual compile) | [Coral](/tooling/coral) |
| completion, hover, diagnostics, rename in an editor | Lighthouse, plus `kelpc` for diagnostics | [Lighthouse](/tooling/lighthouse) |
| understand what a dependency is, and why a folder must stand alone | the library model | [Libraries (fpl)](/libraries) |
| write one | the library rules | [Writing a library](/libraries/writing-a-library) |

## Pages

- [`kelpc` CLI](/tooling/kelpc-cli): every subcommand and flag, where artifacts
  land, the one backend and its oracle, `fmt`'s rules and its refusals,
  environment variables, and what a project changes about module resolution.
- [`kelpc doc`](/tooling/kelpc-doc): the documentation generator: `///` and `//!`
  comments, its options and `--check`, what a page shows, and its limits.
- [Sanitizer builds](/tooling/sanitizers): `--sanitize=address|undefined|thread`
  and `[build] sanitize`, the C-backend-only rule, and what each sanitizer catches.
- [Front-end fuzzing and parser limits](/tooling/fuzzing): the fuzzer, and the
  200-level nesting and 800-link chain limits with their exact errors.
- [Benchmarks](/tooling/benchmarks): the thirteen-program suite, its rules, and
  the current results against C and Rust.
- [Release tooling](/tooling/release-tooling): `build/release.sh`, the
  reproducibility check, the verifying installer, and `kelpc version --verbose`.
- [Coral](/tooling/coral): the manifest key by key, the command surface, the
  dependency model, the toolchain store, and environment variables.
- [Lighthouse](/tooling/lighthouse): the two sources of truth, the feature table,
  editor setup for the IntelliJ plugin, and the deliberate gaps.
- [Coral changelog](/tooling/coral-changelog) and
  [Lighthouse changelog](/tooling/lighthouse-changelog): every release of each
  repository, and what it changed.

## See also

- [Install and build](/getting-started/install)
- [Projects and coral.toml](/getting-started/projects)
- [Compiler](/compiler)
