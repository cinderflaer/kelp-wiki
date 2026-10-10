---
title: "Coral changelog"
description: "Every tagged release of Coral, newest first, with a link to the Gitea release. Short entries: what a release added to the manifest, the commands, or the toolchain store."
isPublished: true
tags: "tooling, cli"
---
Every release of [Coral](/tooling/coral), newest first. The version is
`Cargo.toml`'s `version`, the tag is in the
[coral repository](https://homelabone.xenoo.dev/gittea/Lilly/coral), and the
release asset is `coral-<version>-linux-x86_64`.

The Kelp port of Coral is the build tool on `main`, under `src/`, and the Rust build
moved to the `rust-legacy` branch. The newest tag, `v26.10.5`, is the first release of
the port. `v26.09.4` is the last tag that builds the Rust version.

Release notes live on the Gitea releases page, and each entry below links to
its own tag. Not every tag has a release: `v0.1.0`, `v0.2.0`, `v0.2.1`,
`v0.5.1` and `v0.5.2` are tags only. The authority for what Coral does today is
[its README](https://homelabone.xenoo.dev/gittea/Lilly/coral/src/branch/main/README.md),
which the [Coral page](/tooling/coral) follows.

**Numbering.** Releases are numbered `YY.MM.N`: the two-digit year, the
two-digit month, and the release number within that month starting at `0`. The
first under the scheme is [`v26.09.0`](#v26090-2026-09-20), and every release
from it on reports its own number. Cargo refuses a leading zero in a version component, so `Cargo.toml` carries
the semver-legal spelling of a release name while the tag and the asset are
written padded: the `26.09.1` release is `26.9.1` in the manifest, tagged
`v26.09.1`, with asset `coral-26.09.1-linux-x86_64`.
`toolchain install` compares an asset name against the tag as text, so the two
spellings have to be the same one.

| Version | Date | Headline |
| --- | --- | --- |
| [v26.10.5](#v26105-2026-10-09) | 2026-10-09 | the Kelp port is the build tool; the toolchain tracks the newest Kelp release only |
| [v26.09.4](#v26094-2026-09-28) | 2026-09-28 | a quoted `#folder` dependency value parses again; an official Nix flake |
| [v26.09.3](#v26093-2026-09-25) | 2026-09-25 | a second implementation, written in Kelp, ships beside the Rust one |
| [v26.09.2](#v26092-2026-09-24) | 2026-09-24 | `coral version`, `coral fmt`/`lint`, `coral test` |
| [v26.09.1](#v26091-2026-09-21) | 2026-09-21 | the `coral docs` family: `get`, `list`, `search` |
| [v26.09.0](#v26090-2026-09-20) | 2026-09-20 | the `YY.MM.N` scheme; `naming_case` and `http_pool`; an asset named for another version is refused |
| [v0.5.4](#v054-2026-09-19) | 2026-09-19 | a dependency can name one folder inside a repo |
| [v0.5.3](#v053-2026-09-19) | 2026-09-19 | a missing release is not an unreadable one; refuse a sign-in page |
| [v0.5.2](#v052-2026-09-19) | 2026-09-19 | refuse a removed command before anything needs a manifest |
| [v0.5.1](#v051-2026-09-19) | 2026-09-19 | dependencies are manifest lines; `coral add`/`update` and the lockfile go |
| [v0.5.0](#v050-2026-09-19) | 2026-09-19 | one toolchain version at a time |
| [v0.4.0](#v040-2026-09-19) | 2026-09-19 | `coral sync`; `--offline` and `--locked` |
| [v0.3.0](#v030-2026-09-19) | 2026-09-19 | pin the compiler per project; install from release assets |
| [v0.2.1](#v021-2026-09-19) | 2026-09-19 | `find_kelpc` checks `~/.coral/bin/kelpc` before `PATH` |
| [v0.2.0](#v020-2026-09-19) | 2026-09-19 | toolchain management: install and switch a kelp and a coral |
| [v0.1.0](#v010-2026-09-19) | 2026-09-19 | Coral v1: init, build, run, check, clean, tasks, cache, deps |

## v26.10.5 (2026-10-09)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v26.10.5)

The first release of the Kelp port. Coral is written in Kelp and ships as
`coral-26.10.5-linux-x86_64`. Its Rust predecessor stays on the `rust-legacy` branch.

- **The toolchain is always the newest Kelp release.** `coral toolchain` manages only
  the Kelp compiler. `latest` names the newest `vYY.MM.N` tag, and `update` installs
  and links it. There are no version pins in a manifest and no way to install an
  older release.
- **Registry and owner come from configuration.** Nothing about one Gitea instance is
  compiled in. The registry is read from `CORAL_REGISTRY`, then the config file; the
  owner from `CORAL_OWNER`, then the config file. The config file is
  `$CORAL_CONFIG`, else `$XDG_CONFIG_HOME/coral/config.toml`, else
  `~/.config/coral/config.toml`.
- **`fpl/<name>` dependencies.** A source names a first-party library as `fpl/<name>`,
  and the catalog in the port maps that name to its repository. A catalog entry is a
  whole repository; a folder inside one is written `fpl/<name>/<folder>`.
- **Quoted `#` values parse as in the Rust build.** A `#` inside quotes is part of the
  value, so a `#folder` fragment in a quoted dependency survives. A `#` outside quotes
  still starts a comment.
- **Messages carry no em or en dashes.** Toolchain and error text uses plain punctuation.
- **68 fixtures.** The Rust unit tests that matter are ported to Kelp fixtures, and
  `coral test` runs them. The suite passes on the release commit.

## v26.09.4 (2026-09-28)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v26.09.4)

- The asset is `coral-26.09.4-linux-x86_64` beside the `v26.09.4` tag.
- **A quoted dependency value keeps its `#folder` fragment** (BUG-v2Tqm). The
  `#`-starts-a-comment rule is quote-aware now, so the documented full-URL form
  `local = "file:///srv/git/fpl#other"` parses into the value instead of being
  truncated at the `#` and refused as an unterminated string. A `#` outside
  quotes still starts a comment.
- **The repository carries an official `flake.nix`.** `nix build` produces
  `result/bin/coral` from a pinned `nixos-26.05`, reads the package version from
  `Cargo.toml` so a release bump moves it, and runs the 65 unit tests as part of
  the build (`git` is a build input: the `deps` tests build a scratch
  repository). `nix develop` opens a shell with the same `cargo` and `rustc`.
  The flake carries no `kelpc` on purpose, since the compiler is installed
  through `coral toolchain kelp`. See
  [Install and build](/getting-started/install#install-coral-with-nix).

## v26.09.3 (2026-09-25)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v26.09.3)

- The asset is `coral-26.09.3-linux-x86_64` beside the `v26.09.3` tag; the Rust
  binary this release ships is unchanged from `26.09.2`.
- **A second implementation of Coral, written in Kelp, ships beside the Rust
  one** at `kelp/` in the repository (a `coral.toml` plus `src/*.kp`): the two
  coexist, and the Rust binary is still the released tool. `init`, `build`,
  `run`, `check`, `clean`, `task`, `fmt`, `lint`, `sync`, `docs get`/`list`/
  `search` and `test` all work against the ordinary path, verified end to end
  with the released `kelpc`. No language or stdlib change was needed for any
  of it. `PORT_REPORT.md` on the `kelp-rewrite` branch of the repository carries the lane board.
- Nine small gaps were found and filed while porting, none of which block
  using either implementation today: no fallible form of the `std/fs`
  mutators, no way to set a file's executable bit, no compile-time target
  OS/architecture value, a literal `$` cannot be written in a string literal,
  no way to construct `Result<unit, E>`'s success value, a child process
  cannot inherit the parent's stdio, no way to tell a signal-killed child from
  one that exited with that code, and one Rust-side bug, a dependency value
  cannot carry the documented `#folder` fragment.

## v26.09.2 (2026-09-24)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v26.09.2)

- The asset is `coral-26.09.2-linux-x86_64` beside the `v26.09.2` tag.
- **`coral version`** (and `coral --version`) prints the release the binary was
  built from, `coral 26.09.2`, padded the way the tag and the asset spell it.
  Before this, both spellings were accepted as flags and then fell through to the
  manifest lookup, so an installed binary answered `error: no coral.toml in this
  directory or any parent` instead of naming itself.
- **`coral fmt` and `coral lint`** forward to the compiler's own formatter and
  linter. With no path named, both read the project's own sources (`.kp` files
  under `src/` and `tests/`, skipping `src/deps` and `build/` so a fetched
  dependency is never rewritten). `coral fmt --check` writes nothing and exits
  nonzero on a file that is not formatted; `coral lint` exits zero on a warning,
  and sends no setting of its own because `kelpc lint` already reads
  `coral.toml`'s `naming_case`.
- **`coral test`** runs a project's `tests/` fixtures: `<name>.expected` for the
  exact stdout, an optional `<name>.exit` for the exit code, a `.refused` marker
  for a fixture that must be refused (with `<name>.error` naming the text the
  message must contain), and an optional `.flags` line. Each fixture is built and
  run in a staged project under `build/test/<name>/` whose `src/` mirrors the
  project's own, because the compiler refuses a `.kp` file under a project but
  outside `src/`, so a fixture can import the project's modules. `--json` prints
  one document instead of one line per fixture, and `--valgrind` runs each
  accepted fixture under valgrind.

## v26.09.1 (2026-09-21)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v26.09.1)

- The asset is `coral-26.09.1-linux-x86_64` beside the `v26.09.1` tag, the
  padded spelling `toolchain install` compares against the tag as text.
- **`coral docs get <file>.kp`** renders one file's documentation comments, each
  with the declaration it documents and never a body. It needs no project, no
  manifest and no `kelpc`, so one file is enough.
- **`coral docs list`** walks the project's own sources (`src/`, `tests/`,
  skipping a fetched `deps/` tree and a build directory) and prints every
  documented thing, one line each: where it is, its key, and the first line of
  its prose.
- **`coral docs search <query>`** prints the matching entries with their prose.
  Key and prose are both searched, a query written `fun:test` searches that kind
  of key only, and no match is an error, so a script can ask whether the project
  documents something.
- An entry's key comes from the declaration a block sits above (`fun:test`,
  `field:bytes`, `variant:Empty`, `module:<file stem>`) or from a one-line
  `[docs(kind: name)]` head. A head that cannot be read, or a block that
  documents no declaration, is a warning on stderr with the file and line.
- `kelpc` is not involved: a documentation comment is trivia to the compiler, so
  this is a reader over the source text with no parse and no symbol table.
- **Fixed, documentation:** the README's library-capability example drops `with`
  from `impl "std/fs" caps(...)`, the spelling the compiler keeps. A fix caused
  by the Kelp syntax removal, not a Coral behavior change.

## v26.09.0 (2026-09-20)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v26.09.0)

- The first release under `YY.MM.N`, and the first whose asset name carries it:
  `coral-26.09.0-linux-x86_64` beside the `v26.09.0` tag. `toolchain install`
  reads that name against the tag as text, so the padded month is the one
  spelling used for both.
- `naming_case` is accepted in `coral.toml`'s compiler section with `kelpc`'s
  own checks and wording: `0` is `camelCase` (the default), `1` is `snake_case`,
  anything else is refused. Coral does not read the value; it only has to accept
  what `kelpc` accepts, so a project cannot write a setting one tool ignores.
- `http_pool` is read as a bare whole number, which is how `kelpc` splices it
  into `std/http`. Coral used to demand a quoted string and then refuse the
  number, so the key could not be set at all.
- `toolchain kelp|coral install <ver>` **refuses a release asset whose name
  carries a different version**, where it used to take the first asset that
  matched the binary name and the platform. An asset attached under the wrong
  name can no longer install the wrong compiler; a name with no version at all
  is still accepted, and the tag is built from source instead.
- The README's dependency example drops the `as` clause (outdated), and the
  library flow is written end to end: what Coral needs from a library, what a
  folder has to carry, and how the manifest line and the `impl` line fit
  together.

## v0.5.4 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v0.5.4)

- A dependency can name one **folder** inside a repo:
  `sillyname = "Lilly/fpl/sillyname"`. It is fetched with
  `--filter=blob:none --sparse` and copied flat into `src/deps/<name>/`, so
  `impl "deps/sillyname/lib"` works and a sibling library in that repo is never
  downloaded.

## v0.5.3 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v0.5.3)
· tag and release notes cover the dependency flow introduced in v0.5.1.

- `coral toolchain <component> install <ver>` tells a **missing release** apart
  from an **unreadable one**, and refuses to install a sign-in page: a
  redirected HTML login response is not a binary.

## v0.5.2 (2026-09-19)

Tag only.

- `coral add` and `coral update` are refused **before** anything needs a
  manifest, so they say "removed, use `[dependencies]` and `coral sync`" in
  every directory instead of "no coral.toml in this directory or any parent".
  Only commands that still exist may complain about a missing manifest.

## v0.5.1 (2026-09-19)

Tag only; the release notes for v0.5.3 describe the same flow end to end.

- A dependency is a line written by hand in `[dependencies]`, and `coral sync`
  is what fetches it. `coral add`, `coral update`, `coral.lock`, `--locked` and
  `manifest::write` are gone: a library has no version, so there is no version
  to resolve and no commit for a lock to pin.
- `build`/`run`/`check`/`task` fetch a dependency that is **missing** and never
  touch one that is present, so a warm tree builds offline and identically.
  What makes a build reproducible is that `src/deps/<name>/` is the checkout it
  built with.
- Unknown flags are refused rather than ignored, with a message naming what
  replaced `--locked`; `--help`/`-h` prints the usage.
- Also fixed: `toolchain install` cloned before checking that the version is a
  tag, so a version that only existed in a manifest failed as a raw
  `git clone` error.

## v0.5.0 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v0.5.0)

- **One toolchain version at a time.** `install` and `use` leave the store
  under `~/.coral/toolchains/` holding the version just installed. The new
  binary lands first and only then is every other version deleted, so a failed
  install cannot take a working one with it; a half-finished install (a
  directory with no binary in it) goes with the rest. When a prune drops the
  version `~/.coral/bin/<binary>` named, the link is repointed at the stored
  version, including a link left dangling by an earlier `rm -rf`.
- A version that is not a plain tag is refused: `install ..` and `use a/b` used
  to join straight onto the store path.
- The cost, recorded in the README: two projects pinned to different versions
  trade the slot, so each build reinstalls what the other displaced.

## v0.4.0 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v0.4.0)

- **`coral sync`**: materialize declared inputs without building, so the step
  you cache, the step you can audit, and `--offline` are separate from compile.
  `--dry-run` prints the plan and changes nothing; `--locked` refuses if the
  manifest and lock disagree; `--offline` refuses if anything is missing.
- **A dependency is checked out at the locked commit**, not at the remote tip.
  Previously `build` only fetched a *missing* directory, so the revision was
  whatever `coral add` happened to clone, and a present but stale tree was used
  as-is. `coral update` is what moved it forward.
- **One rule, two callers**: `deps::ensure_dep` decides what "up to date" means,
  and both the build path and `sync` go through it, so the two cannot disagree.
- `--offline` and `--locked` are threaded through `build`, `run`, `check` and
  `task`, and each refuses at the point of the side effect rather than after it.
- Fixed while threading that: `coral task` never fetched dependencies, so a
  task that `impl`s one could not build.
- `sync` reports rather than installs when a project has no `[toolchain]` pin,
  and prints which compiler a pin-less project will build with.
- First tests in the repository: eight unit tests over the lock/manifest
  agreement rules. The rest was verified by hand against a local `file://`
  registry with no network.
- The crate's version had been stuck at `0.1.0` while the tags had reached
  v0.3.0, so releases had no version identity inside the binary.

## v0.3.0 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/coral/releases/tag/v0.3.0)

- **Per-project compiler pinning.** `[toolchain] kelp = "v0.1.1"` in
  `coral.toml` names the `kelpc` a project builds with. Resolution order is
  `$KELPC`, the project pin, `~/.coral/bin/kelpc`, `PATH`, and a pinned version
  that is not installed yet is installed on the spot.
- New commands: `coral toolchain kelp pin <ver>` and `pin --clear` (a line
  edit, so comments and section order survive it), `coral toolchain kelp
  installed`, and `coral init --kelp <ver>`.
- `coral toolchain kelp|coral install <ver>` downloads the tag's own release
  asset when the release has one for this platform, and falls back to a source
  build when it does not, which is what keeps a tag with no release installable.

## v0.2.1 (2026-09-19)

Tag only.

- `find_kelpc` checks `~/.coral/bin/kelpc` directly before `PATH`, because a
  login-shell profile can rebuild `PATH` from the system profile and discard a
  plain `export PATH=...` line, which is what made a `toolchain use` look as if
  it had not happened.

## v0.2.0 (2026-09-19)

Tag only.

- **Toolchain management**: `coral toolchain kelp|coral list|install <ver>|use
  <ver>`. `list` reads git tags over HTTPS with `git ls-remote --tags`, `install`
  clones one and builds it into `~/.coral/toolchains/<repo>/<version>/`, and
  `use` symlinks `~/.coral/bin/<kelpc|coral>` at an installed build,
  auto-installing if it is missing. Same shape as rustup's `~/.cargo/bin`.
  `CORAL_HOME` overrides `~/.coral`.
- `coral init` grew `--version <v>`, `--no-git` and `--no-sample` (an empty
  `main()` instead of the "hello, kelp!" sample), for the IntelliJ wizard's
  settings panel.

## v0.1.0 (2026-09-19)

Tag only. The first Coral, and the first two fixes on top of it.

- **Coral v1**: `coral init/build/run/check/clean`, driving `kelpc` as a
  subprocess. Profiles only choose where the artifact lands, because `kelpc`'s
  own dev/release split did not exist yet.
- `[tasks]`: a task is a `.kp` file with its own `fun main()` and its own `impl`
  lines, run through the same build and cache path as the project.
- An FNV-1a fingerprint over every file under `src/` plus the `kelpc` binary
  skips a rebuild when nothing relevant changed.
- `coral add`/`update`: dependencies came from Gitea over SSH through the
  `thinkbox` host alias, with `coral.lock` pinning the commit.
- `kelpc`'s own manifest parser was loosened in step, to stop reading
  `coral.toml` at the first `[section]` instead of rejecting it, which is what
  lets Coral's `[tasks]`/`[dependencies]` sections coexist with the flat
  `name`/`version`/`entry` keys the compiler reads.
- Fixed on top: `coral init .` scaffolds in place instead of naming the project
  `.`, and dependencies fetch into `src/deps/` rather than a top-level `deps/`.

## Maintaining this page

This page carries **released versions only**. Nothing goes here until a version
is tagged.

Changes in the meantime accumulate in `coral/CHANGELOG.pending.md`, which is
gitignored and never committed: a line when a user-visible change lands, in the
manifest, the commands or the toolchain store.

When a version drops, write its entry here from that file plus the tag's commit
and the Gitea release body, then wipe the pending file back to its header. Keep
it to the headline plus the bullets a user needs, and link the tag; let the Gitea
release carry the long version.

A tag with no release still gets an entry, marked as a tag only. That is how
`v0.1.0`, `v0.2.0`, `v0.2.1`, `v0.5.1` and `v0.5.2` are recorded above.

Write the page without em dashes. Use a colon or a comma for an aside, a
semicolon or a full stop between clauses, and a plain hyphen in a range.

## See also

- [Coral](/tooling/coral): the manifest, the commands, the dependency model
- [Projects and coral.toml](/getting-started/projects): the same thing from the
  project's side
- [Changelog](/changelog): the language and the compiler
- [Lighthouse changelog](/changelog/lighthouse): the editor tooling
