---
title: "Lighthouse changelog"
description: "Every released version of Lighthouse: the IntelliJ plugin, the VS Code extension and the language server they both talk to, with a link to the Gitea release."
isPublished: true
tags: "tooling"
---
Every released version of [Lighthouse](/tooling/lighthouse), newest first. Three
pieces move at their own speed, so each entry says which one it is.

| Piece | Where it is | Version today | How it is published |
| --- | --- | --- | --- |
| IntelliJ plugin | `intellij/` | 26.09.2 | Gitea releases, tag `intellij-v<version>`, plus a self-hosted update site |
| Language server | `server/` | 26.9.3 (`26.09.3` in `serverInfo`) | `cargo build --release -p lighthouse`; no release assets |

The VS Code extension was dropped on 2026-09-24: IntelliJ is the only client
today, and `vscode/` is gone from the repository. Its entries below stay, since
they are history, but the table above no longer lists it.

Only the IntelliJ plugin has releases and tags. The language server carries its
version in `Cargo.toml`, and an entry here records the version it was at when a
release was cut.

**Numbering.** Both pieces are numbered `YY.MM.N`, and the first under the
scheme is `26.09.0`. Gradle takes the padded name as written, so the plugin's
version, the tag (`intellij-v26.09.0`) and the asset
(`lighthouse-intellij-26.09.0.zip`) are the same text. Cargo refuses a leading
zero in a version component, so the server's `Cargo.toml` carries the
semver-legal spelling while its `serverInfo` reports the padded name, so the
string an editor shows matches the release.

| Release | Date | Headline |
| --- | --- | --- |
| [Language server 26.09.3](#language-server-26093-no-release) | 2026-09-25 | the debounced re-check reads the open buffer with `kelpc check --text` |
| [IntelliJ 26.09.2](#intellij-plugin-26092-2026-09-24) | 2026-09-24 | LSP4IJ, so Community works; the tooling knows the language; VS Code dropped |
| [Language server 26.09.2](#language-server-26092-no-release) | 2026-09-24 | the vendored stdlib resync and the index; carried by the plugin release |
| [Language server 26.09.1](#language-server-26091-no-release) | 2026-09-21 | the vendored stdlib resync, and `std/encoding`; no plugin release |
| [IntelliJ 26.09.0](#intellij-plugin-26090-2026-09-20) | 2026-09-20 | the `YY.MM.N` scheme, for all three pieces |
| [IntelliJ 0.2.1](#intellij-plugin-021-2026-09-19) | 2026-09-19 | the whole IDE arrives over LSP; `closure` and `'x'` in the highlighter |
| [IntelliJ 0.2.0](#intellij-plugin-020-2026-09-19) | 2026-09-19 | the project's kelp version, from the project |
| [IntelliJ 0.1.1](#intellij-plugin-011-2026-09-19) | 2026-09-19 | the auto-update feed, and the New Project entry |
| [Lighthouse v1 (0.1.0)](#lighthouse-v1-no-release) | 2026-09-19 | first version: LSP diagnostics, VS Code extension, IntelliJ plugin |

## Language server 26.09.3 (no release)

No tag and no release: only the IntelliJ plugin has those, and nothing about
the plugin changed here. This entry records the server version move, the way
the rule at the top of this page says.

- **The debounced re-check after a `didChange` reads the open buffer with
  `kelpc check --text`** instead of the file on disk (`MISSING-b6Ytr`), so an
  unsaved edit gets a real diagnostic instead of the last save's. It is rooted
  at the edited file itself rather than the project's entry, since it answers
  "is what I am looking at right now clean" rather than "is the whole
  project"; `didOpen` and `didSave` still run the wider, disk-based check,
  since at those two moments the buffer and disk already agree. A `kelpc` too
  old to know `--text` falls back to the disk-based check it always ran.

The server reports `26.09.3` in `serverInfo`.

## IntelliJ plugin 26.09.2 (2026-09-24)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/releases/tag/intellij-v26.09.2)

- The asset is `lighthouse-intellij-26.09.2.zip`, and `updatePlugins.xml` points
  at it, so the self-hosted update feed offers it.
- **The plugin reaches the free editions.** It talks to `lighthouse` through
  LSP4IJ, Red Hat's free LSP client, instead of JetBrains' own LSP API, which is
  an extension of the commercial IDEs only. LSP4IJ is an optional dependency:
  with it installed the server's features (completion, hover, navigation,
  diagnostics, inlay hints, quick fixes, folding, signature help, structure view)
  work in Community and Android Studio as well as the commercial flavours;
  without it the plugin still loads and keeps its lexer, highlighter, brace
  matcher, Coral run configurations, New Project wizard and settings page. The
  build targets Community again rather than Ultimate.
- **The tooling knows the language**: `pub` on a top-level item, tuple
  destructuring, `std/atomic`, `std/thread` and `std/ws` vendored and indexed,
  the compiler's own `fence`/`spawn`/`join`, `encoding.sha1`, `View`, `Atomic`
  and `Thread`, both capability clause forms, block comments masked, and checks
  on a debounced change as well as on open and save, with the caveat that `kelpc`
  reads the file on disk, so a check after a change reports the last saved text.
- **The VS Code extension is dropped**, and IntelliJ is the only client. The
  language server stays a plain LSP server that any client can drive.

## Language server 26.09.2 (no release)

No tag and no release: only the IntelliJ plugin has those, and the plugin's
release above carries this server. This entry records the server version move,
the way the rule at the top of this page says.

- The vendored standard library snapshot is resynced, and `std/atomic`,
  `std/thread` and `std/ws` are vendored now. It is kept in step with the
  compiler by `server/tools/sync-stdlib.sh`, with drift tests, so it cannot
  silently fall behind again.
- The index reads `pub`, binds the tuple destructuring form, masks block
  comments (a documented `fun` line in a module's header was being indexed as a
  declaration that shadowed the real one), and offers the new keywords and type
  spellings.
- Diagnostics still come from `kelpc check --json`, now also a debounced moment
  after a document changes.

The server reports `26.09.2` in `serverInfo`.

## Language server 26.09.1 (no release)

No tag and no release: only the IntelliJ plugin has those, and nothing about the
plugin changed. The VS Code extension is unchanged too, at `26.9.0`, and the
plugin stays at `26.09.0` with its `intellij-v26.09.0` tag. This entry records
the server version move, the way the rule at the top of this page says.

- **The vendored stdlib snapshot is refreshed against the shipped sources.** All
  16 modules were behind, so a jump into the standard library could open an
  older copy than the compiler builds with.
- **`std/encoding` is vendored**, and added to the two lists that name the
  modules, so the newest standard library module is no longer invisible to
  completion, hover and auto-import.
- **The index's import test spells the grant the way the compiler keeps it**,
  `impl "std/fs" caps(...)` rather than the removed `with caps(...)`. The index
  already skips the whole clause, so this tracks the surviving grammar with no
  behavior change.

The server reports `26.09.1` in `serverInfo`.

## IntelliJ plugin 26.09.0 (2026-09-20)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/releases/tag/intellij-v26.09.0)
· the language server is unchanged since 0.2.0 apart from its version fields, so
nothing here needs a newer `lighthouse` than that: `PATH` or `~/.local/bin`.

**The first release under `YY.MM.N`**, for all three pieces at once. The plugin
takes the padded name as written, so `26.09.0` is its version, its tag is
`intellij-v26.09.0` and its asset is `lighthouse-intellij-26.09.0.zip`; the
server and the extension carry `26.9.0`, because Cargo and npm both refuse a
leading zero, and the server reports the padded `26.09.0` in `serverInfo` so the
string an editor shows matches the tag.

The self-hosted update feed (`intellij/updatePlugins.xml`) points at this
release's zip, so an installed plugin updates itself from Settings > Plugins >
Updates, with no restart and no file picker. The VS Code extension is still
built locally and is not on the Marketplace, so the version move is all this
release says about it.

**Fixed.** The README no longer claims that no formatter exists. `kelpc fmt`
(with `--check` and `-w`) shipped in the previous compiler release; what is
missing is the document-formatting provider in each extension, which is what the
README now says.

## IntelliJ plugin 0.2.1 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/releases/tag/intellij-v0.2.1)
· requires `lighthouse` 0.2.0 or newer, on `PATH` or at
`~/.local/bin/lighthouse`.

**The whole IDE, over LSP.** Completion with automatic imports (`str.con`
completes to `concat`, and accepting it writes `impl "std/str"` at the top of
the file), hover, go-to-definition into project files and into the standard
library, signature help, document outline and workspace symbols, find usages,
rename, folding, inlay hints, Organize Imports, quick fixes, and diagnostics
from `kelpc` itself.

All of that comes from the language server, so it is the same experience as the
VS Code extension, and **no plugin update was needed for the features to
arrive**. This release is the highlighting polish next to them: `closure` joins
the keyword set, and a character literal is one token rather than three
punctuation characters in a row. The VS Code grammar and the extension (0.2.0)
got the same two.

The server side of it landed in the same window: the text-level index the
features are answered from, the vendored standard library under
`server/stdlib/` (`server/tools/sync-stdlib.sh` regenerates it, `$KELP_SRC`
reads a live checkout instead), and the server's own warning for an `impl`
whose namespace is never used, suppressed in any file that uses `%*alias*%`
substitution.

## IntelliJ plugin 0.2.0 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/releases/tag/intellij-v0.2.0)
· requires a `coral` that knows `toolchain kelp pin` and `installed`, which is
coral v0.3.0.

**The project's compiler version, from the project.**
`[toolchain] kelp = "v0.1.1"` in `coral.toml` now names the `kelpc` a project
builds with, and this release surfaces it. Settings > Languages & Frameworks >
Kelp lists the kelp repository's tags and the installed versions, Install
fetches one in the background, and Apply writes the pin through
`coral toolchain kelp pin <ver>`. The Coral run configuration gained a Kelp
version field (a per-run `KELPC` override; blank follows the pin), and New
Project > Kelp passes `coral init --kelp <ver>`.

Nothing is stored in the IDE's settings: the pin lives in `coral.toml`, so
committing it is what makes every machine build with the same compiler.

## IntelliJ plugin 0.1.1 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/releases/tag/intellij-v0.1.1)

The release notes are one line, "Auto-update feed release", and that is the
headline: the plugin moved to a **self-hosted update site**, so an update
arrives in the plugin manager instead of "Install Plugin from Disk" every time.
The feed is `intellij/updatePlugins.xml`, added to IntelliJ once as a custom
plugin repository.

Between v1 and this release the plugin also gained:

- **diagnostics from `lighthouse`**, wired up through the LSP client API, which
  is why the plugin is IntelliJ **Ultimate** only: the API is not in Community.
- **quick fixes with whole-word ranges**, and a run-file action in the editor
  title bar everywhere, not only where a run configuration already existed.
- **auto-close and skip-over** for `(`, `{`, `[` and `"`.
- **New Project > Kelp**, which runs `coral init`, with a real icon.
- Fixes: the JVM target and an API name that had moved, the New Project Wizard
  API, a `coral` lookup that missed `~/.coral/bin`, a removed `untilBuild` cap,
  and two documentation notes about a New Project entry that did nothing
  because `coral` was not installed.

The update feed itself needed two follow-up fixes, both in the window before
0.2.0: one that made it parseable XML, and one that stopped the declaration's
own `version="1.0"` being rewritten along with the plugin version.

## Lighthouse v1 (no release)

The first version, and it was deliberately one real feature rather than a
promise of more. No tag, no release.

- **`server/`**: a dependency-free Rust LSP server, with hand-rolled JSON-RPC
  framing and JSON, matching `kelpc`'s and Coral's no-external-crates style. It
  builds the project's entry point with `kelpc` on `didOpen` and `didSave` and
  turns the compiler's prose diagnostics into `publishDiagnostics`.
- **`vscode/`**: syntax highlighting, the `lighthouse` language client, and
  `coral build`/`run`/`check`/`clean` as VS Code tasks with a `$kelpc` problem
  matcher. `coral build` is the default build task, so it shows up as
  **Coral: Build** in Run Build Task.
- **`intellij/`**: a `.kp` file type with syntax highlighting from a
  hand-written lexer (no PSI grammar yet), and a Coral run configuration type
  that shells out to `coral <command>`.

What was not there: real diagnostics with spans and categories, blocked on
`kelpc` growing a machine-readable diagnostics interface; completion, hover and
go-to-definition, blocked on `kelpc` exposing any resolve state outside the
compiler process; and publishing to either marketplace. The first two are what
the 0.2.1 release above changed, from the index rather than from the compiler.

## Maintaining this page

This page carries **released versions only**. Nothing goes here until a release
is cut.

Changes in the meantime accumulate in `lighthouse/CHANGELOG.pending.md`, which is
gitignored and never committed: a line per user-visible change, saying which
piece it belongs to (`server`, `vscode` or `intellij`).

When a release is cut, write its entry here from that file plus the tag's commits
and the Gitea release body, then wipe the pending file back to its header. When
the features themselves come from the server, say so and say which server version
they need; a plugin release that only changes highlighting is worth one line, not
a feature list.

Write the page without em dashes. Use a colon or a comma for an aside, a
semicolon or a full stop between clauses, and a plain hyphen in a range.

## See also

- [Lighthouse](/tooling/lighthouse): the two sources of truth, the feature
  table, and the deliberate gaps
- [Editor setup](/getting-started/editor): installing both integrations
- [Changelog](/changelog) and [Coral changelog](/tooling/coral-changelog): the
  other two repositories
