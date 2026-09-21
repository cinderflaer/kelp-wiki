---
title: "Contributing"
description: "Four repositories, one language. Nothing here is a monorepo, and each project's README.md is the authority for itself."
isPublished: true
tags: "meta"
---
Four repositories, one language. Nothing here is a monorepo, and each project's
`README.md` is the authority for itself.

## Layout

| Repository | What is in it |
| --- | --- |
| [`kelp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp) | `kelpc/src` (the compiler), `kelpc/std` (the standard library, in Kelp), `kelpc/runtime` (the reviewed C), `kelpc/tests` (fixtures and gates), `examples/`, `bench/speed/`, `plan/` (the design) |
| [`coral`](https://homelabone.xenoo.dev/gittea/Juniper/coral) | the build tool and package manager |
| [`lighthouse`](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse) | `server/` (the LSP server), `vscode/`, `intellij/` |
| [`fpl`](https://homelabone.xenoo.dev/gittea/Juniper/fpl) | one folder per first-party library |
| [`kelp-wiki`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki) | this documentation site |

The local checkout of all of them is `KelpLANG/`, one folder each, so a search
across the language, the stdlib and the libraries is one `rg`.

## Building and testing

```sh
cargo build --release -p kelpc
cargo test                                   # unit tests + the fixture suite
./kelpc/tests/run-all-backends.sh            # the suite once per implemented backend
```

The fixture suite compiles a fixture, runs the result and compares stdout, so it
is backend-agnostic by construction. Two heavier checks are `#[ignore]`d so the
default run stays fast:

```sh
cargo test --test memory_gate      -- --ignored               # valgrind over the binaries
cargo test --test cap_matcher      -- --ignored               # the matcher vs its C reference
```

`bench/speed/run.sh` times four workloads written in four languages and checks
their checksums.

## What a change should carry

- **A fixture** for a language change: a `.kp` program under `kelpc/tests/fixtures`
  whose stdout is the expected output. Every implemented backend runs it, so a
  construct a backend cannot lower yet fails loudly with its name rather than
  silently. The hand-written `asm` backend was removed on 2026-09-21, so a new
  fixture is written for the C backend; the `llvm` backend runs it too when the
  fixture stays inside the scalar subset, the S2A `datac` slice, the S2B heap
  slice, the S2C tagged-union slice or the S2D container slice, and refuses it by
  name otherwise.
- **A test in the corpus** for a capability-matcher or path-normalizer change:
  those two are implemented twice (Kelp and C) and compared.
- **A citation** for a documentation change: every page in this wiki names the
  section it came from, and a claim without a source is a claim to remove.
- **A line in the pending changelog** for a user-visible change, in the
  repository it landed in: `CHANGELOG.pending.md`, which is gitignored and never
  committed. A wiki changelog page is written only when a version is released:
  [Changelog](/changelog), [Coral](/tooling/coral-changelog) and
  [Lighthouse](/tooling/lighthouse-changelog) carry releases only, and the
  release writes its entry from the pending file, then wipes it.
- **A commit message that says why**, not which lines moved. The plan documents
  use the same voice.

## Version numbers

Releases are numbered `YY.MM.N`: the two-digit year, the two-digit month, and
the release number *within that month*, starting at `0`. The first release under
the scheme is `26.09.0` in each repository, and it applies to all of them
(`kelp`, `coral`, `lighthouse`).

- The **release name is the padded one**: the tag is `v26.09.0`, an asset is
  `kelpc-26.09.0-linux-x86_64`, and `kelpc version` prints `kelpc 26.09.0`. Those
  strings are compared as text (Coral refuses a release asset whose name spells a
  different version), so the padding has to be the same everywhere.
- **Cargo and npm refuse a leading zero** in a version component, so a
  `Cargo.toml` and the VS Code `package.json` carry `26.9.0` while everything a
  person reads is padded back to `26.09.0`. Gradle takes the padded name as
  written.
- **Nothing released before the scheme is renumbered.** A tag, its asset and its
  changelog entry keep the number they were cut with.
- The release that first carries the scheme says so in one line of its changelog
  entry; the pending file carries that line from the moment the scheme is
  decided.

## Style

The formatter owns whitespace: `kelpc fmt -w <path>` and `kelpc fmt --check` are
the two commands. `fmt` is idempotent, token-faithful and comment-preserving:
it never rewrites a token, so a formatted file is the same program. See
[Style](/language/style) for the rules it cannot enforce (the 100-column
limit and declaration order inside a group) and for `kelpc lint`, which reports
the case rule and the two style findings a formatter cannot make.

## Retiring a spelling

When a spelling is replaced or deleted it goes through the register rather than
straight out (`syntax.md` 23, `kelpc/src/deprecated.rs`):

1. Migrate the compiler's own sources first. A deprecation in the shipped stdlib
   would warn every program that imports that module about a file its reader
   cannot edit, and the unit test in `deprecated.rs` fails if one is left behind.
2. Add the entry: an id, what is outdated, and what to write instead. The
   deadline is that file's shared sentence, and it is the next development cycle
   for every entry.
3. Raise the finding where the construct is read (an `impl` clause is read by
   `resolve.rs`) and pin it with a test: `kelpc/tests/outdated.rs` covers the
   build contract, and the entry's own wording is a unit test.
4. **Leave the fixtures that exercise the old spelling on it.** They are the
   coverage for the deprecation path itself, and they are what the removal has to
   migrate.
5. Remove it in the next cycle: the parser, the register entry, and every source
   that still writes it.

## Reporting a defect

A useful defect report has:

1. the smallest program that shows it: three lines beats a paragraph;
2. the exact command and the exact error, including the failing generated-C line
   if the failure came from `cc`;
3. what you expected instead, in one sentence;
4. whether it is `c`-only or backend-independent (`KELPC_BACKEND` is the test).

## Working on this site

This wiki is [Wiki.js](https://kelp.xenoo.dev/) with its pages stored in this
repository. There is no build step and no site generator: Wiki.js reads the
repository every five minutes in both directions, and the file path *is* the page
path. A commit here becomes a page, and a page saved in the browser becomes a
commit, so there is nothing to run.

Pages are markdown files at the repository root. The path of a file is the path
of the page: `language/types.md` is `/language/types`, `language.md` is its
parent, and `home.md` is the home page. Adding a file adds a page. Front matter
carries the four keys the git storage module reads (`title`, `description`,
`isPublished`, `tags`), and `tags` must be a comma-space separated string, not a
YAML list. [Source documents](/meta/source-documents) has the front matter and the
navigation rules in full.

New prose written here avoids em dashes and en dashes. Use a colon or a comma
for an aside, a semicolon or a full stop between clauses, and a plain hyphen in
a range. Older pages here did not follow that rule; do not sweep them, only
write the new text that way.

The MkDocs layout this repository used before 2026-09-19 — `docs/`,
`mkdocs.yml`, `hooks/kelp_lexer.py` and the generator scripts under `tools/` — is
kept at branch `mkdocs-archive` and tag `mkdocs-final`, not in the current tree.
The `hooks/`, `site/` and `node_modules/` directories here are untracked
leftovers from it.

**Unreleased work goes on the `unreleased` branch, not on `main`.** `main` is
what Wiki.js reads, so it has to describe released versions: a new construct, a
new rule, a changed diagnostic, and any page text that depends on one, is
committed on `unreleased` and pushed there. At a release the changelog entry is
committed on that same branch first, and then the branch is merged into `main`:
that one merge is what puts the pages and the entry in front of a reader. Never
rewrite `main` and never force push it, because the sync job pulls it.

**Keep the pages current as you go, in the same turn as the code.** A change
lands with the page edit that describes it, on `unreleased`, and that includes the
pages a change makes stale, not only the page about the feature. A page that lags
the compiler is a defect the next reader pays for.

**A release pulls its dependents with it, on a branch.** `fpl`, `coral` and
`lighthouse` each carry an `unreleased` branch of their own. When a language
version is being worked on, a dependent the change touches is updated for it at
once, on that branch and in the same session as the language change. The reason
is mechanical: `coral sync` takes a remote's tip and `coral.toml` cannot name a
branch, so a `main` that needs an unreleased compiler breaks every consumer. At
the release, each `unreleased` branch merges into `main` and both are pushed. A
change that needs **no** unreleased compiler is not release-coupled, and lands on
`main` directly. [Writing a library](/libraries/writing-a-library) has the rule
for `fpl` in full.

Two pages are **generated**, not written by hand, and re-derived when their
source moves. The generators are part of that archived layout, so re-deriving one
needs a checkout of it:

| Page | Generated from | Generator (archived) |
| --- | --- | --- |
| [Roadmap](/meta/roadmap) (and the block on the [home page](/home)) | `kelp/plan/roadmap.md` (the authority), via a `../kelp` checkout | `tools/roadmap.py` at `mkdocs-final` |
| [Standard library index](/reference/stdlib-index) | `kelpc/std/*.kp`, via a `../kelp` checkout | `tools/stdlib-index.py` at `mkdocs-final` |

Mermaid diagrams are not checked by any build: Wiki.js copies a diagram's text
without judging it, so an invalid one shows up in the browser as an error box.

## See also

- [Source documents](/meta/source-documents), which file is the authority
- [Compiler](/compiler): the pipeline a change has to fit into
- [Tooling](/tooling): `kelpc`, Coral, Lighthouse
