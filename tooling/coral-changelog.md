---
title: "Coral changelog"
description: "Every tagged release of Coral, newest first, with a link to the Gitea release. Short entries: what a release added to the manifest, the commands, or the toolchain store."
isPublished: true
tags: "tooling, cli"
---
Every release of [Coral](/tooling/coral), newest first. The version is
`Cargo.toml`'s `version`, the tag is in the
[coral repository](https://homelabone.xenoo.dev/gittea/Juniper/coral), and the
release asset is `coral-<version>-linux-x86_64`.

Release notes live on the Gitea releases page, and each entry below links to
its own tag. Not every tag has a release: `v0.1.0`, `v0.2.0`, `v0.2.1`,
`v0.5.1` and `v0.5.2` are tags only. The authority for what Coral does today is
[its README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md),
which the [Coral page](/tooling/coral) follows.

| Version | Date | Headline |
| --- | --- | --- |
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

## v0.5.4 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/coral/releases/tag/v0.5.4)

- A dependency can name one **folder** inside a repo:
  `sillyname = "Juniper/fpl/sillyname"`. It is fetched with
  `--filter=blob:none --sparse` and copied flat into `src/deps/<name>/`, so
  `impl "deps/sillyname/lib"` works and a sibling library in that repo is never
  downloaded.

## v0.5.3 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/coral/releases/tag/v0.5.3)
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

[Release](https://homelabone.xenoo.dev/gittea/Juniper/coral/releases/tag/v0.5.0)

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

[Release](https://homelabone.xenoo.dev/gittea/Juniper/coral/releases/tag/v0.4.0)

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

[Release](https://homelabone.xenoo.dev/gittea/Juniper/coral/releases/tag/v0.3.0)

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
- [Lighthouse changelog](/tooling/lighthouse-changelog): the editor tooling
