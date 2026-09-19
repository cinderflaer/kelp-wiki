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
| IntelliJ plugin | `intellij/` | 0.2.1 | Gitea releases, tag `intellij-v<version>`, plus a self-hosted update site |
| VS Code extension | `vscode/` | 0.2.0 | a `.vsix` built locally with `@vscode/vsce`; not on the Marketplace |
| Language server | `server/` | 0.2.0 | `cargo build --release -p lighthouse`; no release assets |

Only the IntelliJ plugin has releases and tags. The other two carry their
version in `package.json` and `Cargo.toml`, and an entry here records the
version they were at when a release was cut.

| Release | Date | Headline |
| --- | --- | --- |
| [IntelliJ 0.2.1](#intellij-plugin-021-2026-09-19) | 2026-09-19 | the whole IDE arrives over LSP; `closure` and `'x'` in the highlighter |
| [IntelliJ 0.2.0](#intellij-plugin-020-2026-09-19) | 2026-09-19 | the project's kelp version, from the project |
| [IntelliJ 0.1.1](#intellij-plugin-011-2026-09-19) | 2026-09-19 | the auto-update feed, and the New Project entry |
| [Lighthouse v1 (0.1.0)](#lighthouse-v1-no-release) | 2026-09-19 | first version: LSP diagnostics, VS Code extension, IntelliJ plugin |

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

Add an entry when a release is cut, and say which piece it is: an IntelliJ
plugin release, or a version move in the extension or the server. When the
features themselves come from the server, say so and say which server version
they need; a plugin release that only changes highlighting is worth one line,
not a feature list.

Write the page without em dashes. Use a colon or a comma for an aside, a
semicolon or a full stop between clauses, and a plain hyphen in a range.

## See also

- [Lighthouse](/tooling/lighthouse): the two sources of truth, the feature
  table, and the deliberate gaps
- [Editor setup](/getting-started/editor): installing both integrations
- [Changelog](/changelog) and [Coral changelog](/tooling/coral-changelog): the
  other two repositories
