# Coral

Coral is the build tool and package manager for Kelp. The division is the point:
`kelpc` stays the compiler; Coral owns the project — manifest, tasks, build
cache, dependencies, toolchains — and calls `kelpc` as a subprocess, never the
reverse.

It is a plain Rust CLI with no external crates, kept simple enough to port to Kelp
part by part once the language covers what it needs (self-hosting is a project
goal, `kelp/plan/roadmap.md`'s MK8). This page follows
[Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md),
which is the authority.

## Commands

| Command | What it does |
| --- | --- |
| `coral init [name]` | scaffold a new project (`--kelp <ver>` writes a toolchain pin too) |
| `coral sync [--dry-run] [--offline]` | install the pinned toolchain and fetch dependencies, **without building** |
| `coral build [--release] [--offline]` | compile the project's entry point with `kelpc` |
| `coral run [--release] [--offline] [-- args...]` | build, then run, forwarding argv and the exit code |
| `coral check [--offline]` | build without keeping the artifact |
| `coral clean` | remove `build/` |
| `coral task <name> [-- args...]` | run a `[tasks]` entry |
| `coral task` | list the tasks declared in `coral.toml` |
| `coral toolchain kelp list` | git tags on the kelp repo |
| `coral toolchain kelp installed` | the versions on disk |
| `coral toolchain kelp install <ver>` | install a version |
| `coral toolchain kelp use <ver>` | point the whole machine at a version |
| `coral toolchain kelp pin <ver>` / `pin` / `pin --clear` | pin *this project*, print the pin, or drop it |
| `coral toolchain coral ...` | the same list for Coral itself |

There is **no `coral add` and no `coral update`**. A dependency is a line in
`coral.toml`, and `coral sync` is what fetches it.

Coral finds `kelpc` in this order: `$KELPC`, then the project's `[toolchain]`
pin, then `~/.coral/bin/kelpc`, then `PATH`.

## The manifest

`coral.toml` is the same flat `name`/`version`/`entry` manifest `kelpc` reads —
`kelpc` stops parsing at the first `[section]`, so it never sees what follows.
Coral's own sections come after:

```toml
name = "myproject"
version = "0.1.0"
entry = "src/main.kp"

[tasks]
report = "src/tasks/report.kp"

[dependencies]
util      = "Juniper/kelp-util"      # the whole repo
sillyname = "Juniper/fpl/sillyname"  # one folder inside a repo

[toolchain]
kelp = "v0.1.1"
```

## Project layout

```
coral.toml
src/main.kp
src/tasks/*.kp     # kelpc requires every compiled file under src/
src/deps/<name>/   # coral sync / coral build, gitignored
tests/
build/             # coral build / run / check, gitignored
```

## Dependencies

A dependency is a line you write. It names a repo, or one folder inside a repo:

```toml
[dependencies]
util      = "Juniper/kelp-util"          # the whole repo
sillyname = "Juniper/fpl/sillyname"      # one folder inside a repo
local     = "file:///srv/git/fpl#other"  # a full URL, folder after '#'
```

- `owner/repo` resolves against your Gitea, reached over SSH through the
  `thinkbox` host alias (`CORAL_REGISTRY` overrides the default for local
  testing). The first two segments are the repo; everything after them is a folder
  inside it.
- Anything containing `://` or an `@` is taken as a full URL and used as written —
  a local path, another host, a test repo — and names a folder with a `#`
  fragment, because a URL's path means whatever its host says it means.

**A folder dependency lands flat.** `Juniper/fpl/sillyname` puts the *contents* of
`sillyname/` at `src/deps/sillyname/`, so the import is
`impl "deps/sillyname/lib"` no matter which repo or folder it came from, and a
sibling library in the same repo is neither fetched nor importable. The clone
behind it uses `--filter=blob:none --sparse`, so only the folder you named comes
down. Naming a folder that is not there lists the ones that are.

**A folder has to stand alone.** Only the folder you named is downloaded, so a
library in `fpl` cannot import a sibling in `fpl` — the sibling was never fetched,
and there is no `deps/fpl/...` in your tree to name. Two libraries that genuinely
share code become one folder, or the *consumer* declares both and wires them
together.

**A library has no version, on purpose.** There is no version constraint, no
registry index and no lockfile: a dependency is a git remote, and what makes a
build reproducible is that `src/deps/<name>/` **is** the tree it built with and
stays that way until something refreshes it. `coral build` therefore never touches
a dependency that is already present — a warm tree builds offline and identically.
`coral sync` is the command that moves a dependency forward, by taking its
remote's tip.

`index.toml` and README tables in a library repo are catalogue metadata for
humans; Coral does not read them. Dependencies land under `src/` because `kelpc`
resolves every `impl` path against the project's `src/` and refuses one that steps
outside it (no `.`/`..`, no absolute paths).

A vendored `src/deps/<name>/` that Coral did not write is a dependency like any
other, and a build uses it as it is. Only `coral sync` needs to fetch, and for a
whole-repo dependency it needs a checkout to pull; a folder dependency is replaced,
because what Coral left there is a plain tree, not a repo.

## `coral sync`

A build needs its inputs, so `coral build` installs a missing pinned compiler and
fetches missing dependencies — that is what makes a fresh clone build with one
command. `coral sync` is the same work **without the build**, and it exists because
materializing declared inputs is a different step from compiling. Every toolchain
splits them for the same reasons (`cargo fetch`, `npm ci`, `go mod download`):

- **Run it once and cache it.** CI warms a cache with `coral sync`, then builds.
- **Audit it.** A sync prints exactly what it installed and fetched, before any of
  it is used to produce an artifact.
- **It makes `--offline` mean something.** After a sync, `coral build --offline`
  asserts that the build did no I/O.
- **It is what moves a dependency forward**, since a build never refreshes one
  that is already there.

```
coral sync                 # the pinned toolchain, then every [dependencies] entry
coral sync --dry-run       # print the plan, change nothing
coral sync --offline       # refuse if anything is missing; never touch the network
coral build --offline      # build with no I/O at all
```

A sync does two things, precisely:

- **The toolchain.** Every `[toolchain]` pin is installed if it is not in
  `~/.coral/toolchains/` already; installing drops the other versions, because the
  store holds one at a time. A project with *no* pin gets a **report** rather than
  an install — which compiler a pin-less project builds with is `~/.coral/bin/kelpc`'s
  business, and changing that is `coral toolchain kelp use`, a machine-wide change
  a per-project command should not make behind your back.
- **The dependencies.** Every `[dependencies]` entry is fetched to its remote's
  tip — a whole repo, or one folder inside one.

`--offline` refuses instead of fetching or installing, and names what is missing. A
dependency that is already there is left at the commit it is at rather than being
refused, so `coral build --offline` runs the same checks and cannot slip past what
a sync would have refused. A sync is also the current answer to "what compiler is
this about to use?", which a build only tells you when it installs one:

```
$ coral sync
coral: no [toolchain] pin — builds use kelpc v0.1.0 (from ~/.coral/bin)
coral: refreshing 'util' from ssh://gitea@thinkbox:2222/Juniper/kelp-util.git
coral: 'util' is at 4f2a9c1e...
coral: 'myproject' synced (installed 0, fetched 1)
```

## Pinning the compiler

`[toolchain] kelp` names the `kelpc` a project builds with, so the project builds
with the compiler it was written against instead of whatever `coral toolchain kelp
use` last set for the machine:

```
coral toolchain kelp pin v0.1.1   # write it into coral.toml
coral toolchain kelp pin          # print it
coral toolchain kelp pin --clear  # remove it
coral build                       # uses v0.1.1, installing it if needed
```

The pin is a **line edit**, not a manifest rewrite — comments and section order
survive. A pinned version that is not installed is installed on the spot. The
compiler binary's bytes are part of the build fingerprint, so changing the pin
rebuilds rather than replaying a cached artifact. Since the store holds one
version at a time, a pin that is not the stored version displaces whatever is there
when the project next builds — two projects pinned to different versions cost one
reinstall per switch.

## Toolchains

A version means a git tag on the kelp (or coral) repo. `install` prefers the
tag's own Gitea release: when the release carries an asset named for this platform
(`kelpc-0.1.1-linux-x86_64`), that binary is downloaded, marked executable, and
placed at `~/.coral/toolchains/kelp/<ver>/kelpc` — no cargo involved. A tag with
no release attached (or no asset for this platform, or nothing but a `.zip`) falls
back to `git clone --branch <ver> --depth 1` plus `cargo build --release`, and the
fallback is announced with its reason.

The release list lives behind the Gitea HTTPS API. A **private instance answers an
unauthenticated request with a sign-in page at HTTP 200**, which is neither a
missing release nor a network error, so the two are told apart: a 404 means "no
release for this tag" and builds from source, while a sign-in page says so and
suggests a token. A sign-in page that arrives where the binary should be is
detected and refused rather than installed.

**One version at a time.** The store holds a single version of each component, so
`install` replaces rather than adds: the new binary lands first, and only then is
every other version — and every half-finished one — deleted. A failed install
therefore leaves the working version alone. If the version just dropped was the one
`~/.coral/bin/kelpc` named, the link is repointed at the stored version. There is no
lock on the store, so two `coral` processes installing different versions at once
would fight over it.

`~/.coral/bin` is not put on `PATH` automatically — `use` prints a one-time
reminder if it is not there yet, the same as rustup's `~/.cargo/bin`.

## Environment variables

| Variable | Effect |
| --- | --- |
| `KELPC` | the compiler to use, ahead of the pin, `~/.coral/bin` and `PATH` |
| `CORAL_HOME` | overrides `~/.coral` (used by Coral's own tests) |
| `CORAL_REGISTRY` | overrides the default Gitea registry that `owner/repo` resolves against |
| `CORAL_TOKEN` / `GITEA_TOKEN` | a Gitea token, sent as `Authorization: token …` for the release list and asset download |

## What is not here yet

Workspaces, `coral fmt`/`lint`/`bench`, and publishing. `coral sync` covers the
toolchain and the dependencies; a folder dependency has no manifest at all, and a
whole-repo one that carries its own `[dependencies]` is not followed, so nothing
fetches a dependency of a dependency. A per-target cache to warm is still a sketch.

There was a `coral.lock`; it is gone. With no versions to resolve there is nothing
for a lockfile to pin that the checkout itself does not already record.

## See also

- [Projects and coral.toml](../getting-started/projects.md)
- [Libraries (fpl)](../libraries/index.md) and
  [Writing a library](../libraries/writing-a-library.md)
- [`kelpc` CLI](kelpc-cli.md)
