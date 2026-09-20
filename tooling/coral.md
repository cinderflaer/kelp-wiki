---
title: "Coral"
description: "Coral is the build tool and package manager for Kelp. The division is the point - kelpc stays the compiler, and Coral owns the project (manifest, tasks, build cache, dependencies, toolchains) and..."
isPublished: true
tags: "tooling"
---
Coral is the build tool and package manager for Kelp. The division is the point:
`kelpc` stays the compiler, and Coral owns the project (manifest, tasks, build
cache, dependencies, toolchains) and calls `kelpc` as a subprocess.

It is a plain Rust CLI with no external crates, kept simple enough to port to Kelp
part by part once the language covers what it needs; self-hosting is a project
goal (`kelp/plan/roadmap.md`, MK8). This page follows
[Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md),
which is the authority, and it marks the places where the binary on this machine
does something the README does not describe. Those are listed again in
[Where the README and the binary disagree](#where-the-readme-and-the-binary-disagree).

The build this page was written against is Coral `v0.5.4`
(`coral toolchain coral installed`).

## Install and where Coral lives

Coral manages Kelp's compiler and itself, both fetched from your Gitea. The
versions on disk live under `~/.coral/toolchains/`, and `~/.coral/bin` is what
`use` points at:

```sh
coral toolchain coral install v0.5.4
coral toolchain coral use v0.5.4        # ~/.coral/bin/coral -> that build
coral toolchain kelp install v0.1.4
coral toolchain kelp use v0.1.4         # ~/.coral/bin/kelpc -> that build
```

`~/.coral/bin` is not put on `PATH` for you. `use` prints a one-time reminder if
it is missing, the same way rustup treats `~/.cargo/bin`.

## The command surface

Run `coral` with no arguments inside a project and it prints this list. The
wording is the binary's:

```text
usage: coral <command> [args]

commands:
  init [name] [--no-git] [--no-sample] [--version <v>] [--kelp <ver>]
                            scaffold a new project (coral.toml, src/main.kp, tests/, src/tasks/)
                            --kelp writes the project's [toolchain] pin
  build [--release] [--offline] [--locked]
                            compile the project's entry point with kelpc
  run [--release] [--offline] [--locked] [-- args...]
                            build, then run the result, forwarding argv and the exit code
  check [--offline] [--locked]
                            build without keeping the artifact
  sync [--dry-run] [--offline] [--locked]
                            install the pinned toolchain and fetch dependencies, without building
                            --dry-run prints the plan and changes nothing
                            --offline refuses instead of fetching (or installing) anything
                            --locked refuses if coral.toml and coral.lock disagree
  clean                     remove build/
  task <name> [-- args...]  run a [tasks] entry
  task                      list the tasks declared in coral.toml
  add <owner/repo> [--as <name>]
                            fetch a dependency from your Gitea and record it in coral.toml
  update [name]             re-fetch one dependency, or all of them
  toolchain kelp|coral list           list versions (git tags) available on your Gitea
  toolchain kelp|coral installed      list the versions under ~/.coral/toolchains/ (at most one)
  toolchain kelp|coral install <ver>  fetch and build one (a release binary, if it has one)
                                      the store keeps one version per component: install drops the others
  toolchain kelp|coral use <ver>      point ~/.coral/bin/kelpc or /coral at that version
                                      and drop the other versions the same way
  toolchain kelp pin <ver>            pin this project to a version in coral.toml ([toolchain])
  toolchain kelp pin                  print this project's pinned version
  toolchain kelp pin --clear          remove the pin (go back to the global default)
```

| Command | What it does |
| --- | --- |
| `coral init [name]` | scaffold a project: `coral.toml`, `src/main.kp`, `src/tasks/`, `tests/`, a `.gitignore`, and a git repository unless `--no-git` |
| `coral build [--release]` | compile the entry point into `build/<mode>/` |
| `coral run [-- args...]` | build, then run, forwarding argv and the exit code |
| `coral check` | build into `build/check/` without producing something to ship |
| `coral sync` | materialise declared inputs: the pinned compiler and every dependency |
| `coral add <owner/repo> [--as <name>]` | fetch a dependency and record it in the manifest |
| `coral update [name]` | re-fetch one dependency, or all of them, to the remote tip |
| `coral task` | list the `[tasks]` entries |
| `coral task <name>` | build and run one task |
| `coral clean` | remove `build/` |
| `coral toolchain kelp|coral ...` | list, installed, install, use, pin |

There is **no `coral --version`**: it is not a command, and the binary answers
`unknown command '--version'`. Ask the toolchain subcommand instead. `coral fmt`,
`coral lint`, `coral bench` and `coral publish` are also unknown commands today,
which is the "not here yet" list further down.

## The manifest

`coral.toml` is the flat `name`/`version`/`entry` manifest `kelpc` reads, plus the
sections Coral owns. `kelpc` stops parsing at the first `[section]`, so it never
sees what follows.

```toml
name = "myproject"
version = "0.1.0"
entry = "src/main.kp"
http_pool = 4

[tasks]
report = "src/tasks/report.kp"

[dependencies]
util = "Juniper/kelp-util"           # the whole repo
json = "Juniper/fpl/json"            # one folder inside a repo
local = "file:///srv/git/fpl#other"  # a full URL, folder after '#'

[toolchain]
kelp = "v0.1.4"
```

### Flat keys

| Key | Who reads it | Notes |
| --- | --- | --- |
| `name` | `kelpc`, Coral | used in build messages and artifact names |
| `version` | `kelpc`, Coral | the project's own version |
| `entry` | `kelpc`, Coral | the file that must hold `main` |
| `http_pool` | `kelpc` (spliced into `std/http`) | a bare whole number (`http_pool = 4`), the one value in the manifest that is not a quoted string |
| `naming_case` | `kelpc` (`kelpc lint`) | a bare whole number, `0` for `camelCase` (the default) or `1` for `snake_case`: the case the lint asks your names to be written in ([Style](/language/style#the-naming-case)). Coral accepts the key with the compiler's own checks and does not read the value |

The flat key set is **closed**. An unknown one is refused by name:

```text
$ coral build
error: unknown key 'bogus' in coral.toml
```

Sections are not closed: an unrecognised section such as `[bogus]` is accepted and
ignored, which is how Coral stays compatible with a manifest carrying sections it
does not know yet.

### Sections

| Section | Shape | Notes |
| --- | --- | --- |
| `[tasks]` | `name = "path/to/file.kp"` | each task compiles as its own unit, and `src/tasks/` is where `init` puts them |
| `[dependencies]` | `name = "owner/repo[/folder]"` | see [Dependencies](#dependencies) |
| `[toolchain]` | `kelp = "v0.1.4"` | written by `coral toolchain kelp pin`, a line edit that leaves comments and section order alone |

Pinning is how a project builds with the compiler it was written against instead
of whatever `coral toolchain kelp use` last set machine-wide:

```sh
coral toolchain kelp pin v0.1.4    # write it into coral.toml
coral toolchain kelp pin           # print it
coral toolchain kelp pin --clear   # drop it, back to the global default
```

## A worked session

Everything below is copied from a run in a scratch directory, with `$KELPC`
pointing at a compiler built from source. `coral init demo` created the manifest,
a source file, the two directories a project grows into, a `.gitignore`, and a git
repository:

```text
$ coral init demo
coral: created 'demo' in 'demo'
$ find . -path ./.git -prune -o -print | sort
.
./.gitignore
./coral.toml
./src
./src/main.kp
./src/tasks
./tests

$ cat coral.toml
name = "demo"
version = "0.1.0"
entry = "src/main.kp"

$ cat .gitignore
build/
src/deps/
```

`coral init` writes the two directories a project grows into (`src/tasks/`,
`tests/`) and tells git to ignore the two Coral owns (`build/`, `src/deps/`).

Building, running, checking and releasing:

```text
$ coral task
no tasks declared in coral.toml

$ coral build
coral: building 'demo' (dev)

$ coral run
coral: 'demo' is up to date
hello, kelp!

$ coral check
coral: building 'demo' (check)
coral: 'demo' checks out

$ coral build --release
coral: building 'demo' (release)

$ coral clean
```

The second run is the interesting one: an unchanged project is not recompiled, and
what you see is the program's own output.

Where each kind of build lands, inside the project's `build/`:

| Target | Artifacts |
| --- | --- |
| dev | `build/dev/demo`, `build/dev/demo.c` |
| release | `build/release/demo`, `build/release/demo.c` |
| check | `build/check/demo`, `build/check/demo.c` (nothing is written to `dev/` or `release/`) |
| a task | `build/tasks/task-<name>`, `build/tasks/task-<name>.c` |
| build cache | `build/.coral-cache/<unit>.<mode>.fp`, the fingerprints that make `coral run` say "up to date" |

Tasks are built as their own units. Declaring one and running it:

```toml
[tasks]
hello = "src/tasks/hello.kp"
```

```text
$ coral task
hello	src/tasks/hello.kp

$ coral task hello
coral: building 'task-hello' (tasks)
task ran

$ find build/tasks -type f
build/tasks/task-hello
build/tasks/task-hello.c
```

## Dependencies

A dependency is a line you write, naming a repository or one folder inside one:

```toml
[dependencies]
util = "Juniper/kelp-util"           # the whole repo
json = "Juniper/fpl/json"            # one folder inside a repo
local = "file:///srv/git/fpl#other"  # a full URL, folder after '#'
```

- `owner/repo` resolves against your Gitea (`CORAL_REGISTRY` overrides the
  default). The first two segments are the repository; anything after them names a
  folder inside it.
- Anything containing `://` or an `@` is treated as a full URL and used as written,
  and names a folder with a `#` fragment, because a URL's path means whatever its
  host says it means.

### A whole-repo dependency

This is the form that works end to end on this build. `coral add` fetches it and
records the line:

```text
$ coral add Juniper/fpl
coral: fetching 'fpl' from ssh://gitea@thinkbox:2222/Juniper/fpl.git
coral: added 'fpl' (Juniper/fpl) at c0977b86eab836b69b28c55ac977b31f1ea67770

$ cat coral.toml
name = "adddemo"
version = "0.1.0"
entry = "src/main.kp"

[dependencies]
fpl = "Juniper/fpl"

$ find src/deps -maxdepth 1
src/deps
src/deps/fpl
```

The whole repository lands under `src/deps/fpl/`, so the import names the folder
inside it:

```kelp
impl "deps/fpl/json/lib" as json
```

`impl` paths are resolved against the project's `src/`, which is why fetched code
lands under `src/deps/` rather than a top-level `deps/`. `coral update` moves it
forward:

```text
$ coral update
coral: updating 'fpl'
coral: 'fpl' is now at c0977b86eab836b69b28c55ac977b31f1ea67770
```

### A folder dependency is broken on this build

The intended behaviour is documented in
[Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md):
a folder dependency lands **flat**, so `Juniper/fpl/json` puts the contents of
`json/` at `src/deps/json/`, and the import is `impl "deps/json/lib"` no matter
which repository it came from. The clone behind it is supposed to use
`--filter=blob:none --sparse` so only the named folder comes down.

This build appends the folder to the repository path and tries to clone that:

```text
$ coral sync
coral: no [toolchain] pin — builds use kelpc v0.1.4 (from ~/.coral/bin)
coral: fetching 'json' at the remote tip
error: cloning 'ssh://gitea@thinkbox:2222/Juniper/fpl/json.git' failed:
...
error: Invalid repo name
```

`coral add Juniper/fpl/json` fails the same way, because `add` takes an
`owner/repo` and reads `fpl/json` as a repository name. **Workaround: depend on the
whole repository and import the folder inside it**, as in the previous section.
That is a different tree on disk and a different `impl` path, so it is worth
knowing before the folder form works again.

### What the model promises, beyond those mechanics

- **A library has no version, on purpose.** There is no version constraint, no
  registry index, and no lockfile that pins a version. A dependency is a git
  remote, and what makes a build reproducible is that `src/deps/<name>/` **is** the
  tree it built with and stays that way until something refreshes it.
- **Only `sync`, `add` and `update` move a dependency forward.** `coral build`
  fetches a dependency that is missing and leaves one that is present alone, which
  is why a warm tree builds offline and identically.
- **A folder must stand alone.** Only the folder you named is downloaded, so a
  library cannot import a sibling library in the same repository: the sibling was
  never fetched and there is no path to name it by. Two libraries that share code
  become one folder, or the consumer declares both. This is the rule that shapes
  the [fpl catalogue](/libraries), where every library is a folder and
  none of them import each other.
- **A vendored `src/deps/<name>/` is a dependency like any other.** A directory
  Coral did not write is used as it is.
- **Catalogue metadata is for humans.** `index.toml` and README tables in a library
  repository are not read by Coral; the manifest's path is the name.

## Moving inputs forward, refusing to guess

`coral sync` is `build`'s front half, and it exists separately for the same reasons
`cargo fetch`, `npm ci` and `go mod download` do: it can be run once and cached, it
prints exactly what it installed and fetched before any of it produces an artifact,
and it is what makes `--offline` mean something.

```sh
coral sync                 # the pinned toolchain, then every [dependencies] entry
coral sync --dry-run       # print the plan, change nothing
coral sync --offline       # refuse if anything is missing; never touch the network
coral build --offline      # build with no I/O at all
```

A sync does two things. It installs every `[toolchain]` pin that is not already in
`~/.coral/toolchains/`, and it fetches every `[dependencies]` entry to its remote's
tip. A project with **no** pin gets a report rather than an install, because which
compiler a pin-less project uses is `~/.coral/bin/kelpc`'s business and changing
that is a machine-wide decision a per-project command should not make:

```text
$ coral sync --dry-run
coral: no [toolchain] pin — builds use kelpc v0.1.4 (from ~/.coral/bin)
coral: would fetch 'json' at the remote tip
coral: 'depdemo' would install 0 and fetch 1 (nothing changed)

$ coral sync --offline
coral: no [toolchain] pin — builds use kelpc v0.1.4 (from ~/.coral/bin)
error: dependency 'json' is not present at the remote tip, and --offline forbids fetching it — run 'coral sync' where the network is available

$ coral build
coral: fetching 'fpl' at the remote tip
coral: building 'g' (dev)
```

The offline refusal names what is missing rather than failing later. A dependency
that is already present is left at the commit it is at, so `coral build --offline`
runs the same checks and cannot slip past what a sync would have refused.

## `coral.lock` and `--locked`

A successful sync, `add` or `update` writes `coral.lock`, one line per dependency:

```text
# coral.lock — generated by `coral add`/`coral update`; do not edit by hand.
name = "fpl" source = "Juniper/fpl" commit = "c0977b86eab836b69b28c55ac977b31f1ea67770"
```

`--locked` refuses to build when the manifest and the lock disagree, and says which
entry is the problem:

```text
$ coral build --locked
error: --locked: the manifest and the lock disagree:
  - 'argparse' is in coral.toml but has no coral.lock entry — run 'coral sync' to pin it
```

That is the CI shape: `coral sync --locked` after checkout, then `coral build
--locked`, and a manifest edit that was never synced fails instead of silently
fetching something new.

## Toolchains

A version means a git tag on the kelp or coral repository. `install` prefers the
tag's own Gitea release: when the release carries an asset named for this platform
(`kelpc-0.1.4-linux-x86_64`), that binary is downloaded, marked executable and put
at `~/.coral/toolchains/kelp/<ver>/kelpc`, with no cargo involved. An asset whose
name carries a *different* version is ignored, so a mislabelled asset cannot
install the wrong compiler; a name that carries no version at all is accepted (a
generic single-binary release). A tag with no release, no usable asset for this
platform, or nothing but a `.zip` falls back to
`git clone --branch <ver> --depth 1` plus `cargo build --release`, and the fallback
is announced with its reason
([Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md)).

Two details from the README that are worth knowing before trusting a failed
install: the release list lives behind the Gitea HTTPS API, a private instance
answers an unauthenticated request with a **sign-in page at HTTP 200**, and Coral
tells that apart from a missing release. A 404 means "no release for this tag" and
builds from source; a sign-in page says so and suggests a token. Set `CORAL_TOKEN`
or `GITEA_TOKEN` and it is sent as `Authorization: token ...` for the release list
and the asset download.

**The store holds one version of each component**, so `install` replaces rather
than adds. The new binary lands first and only then is every other version, plus
every half-finished one, deleted, so a failed install leaves the working version
alone. If the version that was just dropped was the one `~/.coral/bin/kelpc` named,
the link is repointed at the stored version. There is no lock on the store: two
Coral processes installing different versions at once would fight over it. The
trade is deliberate, and it costs one reinstall per switch when two projects pin
different versions.

```text
$ coral toolchain kelp installed
v0.1.4
$ coral toolchain coral installed
v0.5.4
```

## Which compiler Coral runs

Coral resolves `kelpc` in this order, and stops at the first hit
([Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md)):

1. `$KELPC`, which is how a compiler built from source gets used;
2. the project's `[toolchain]` pin, installed on the spot if it is not there;
3. `~/.coral/bin/kelpc`, the machine-wide default;
4. `PATH`.

Because the compiler binary's bytes are part of the build fingerprint, changing the
pin rebuilds rather than replaying a cached artifact.

## Environment variables

| Variable | Effect |
| --- | --- |
| `KELPC` | the compiler to run, ahead of the pin, `~/.coral/bin` and `PATH` |
| `CORAL_HOME` | overrides `~/.coral` (used by Coral's own tests) |
| `CORAL_REGISTRY` | overrides the default Gitea registry that `owner/repo` resolves against |
| `CORAL_TOKEN`, `GITEA_TOKEN` | a Gitea token, sent as `Authorization: token ...` for the release list and the asset download |

## What is not here yet

Workspaces, `coral fmt`, `coral lint`, `coral bench`, and publishing. The last four
answer `unknown command`, which was checked; workspaces and publishing are absent
from the command list rather than refused by name.

Two consequences of the dependency model, both from
[Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md):
a folder dependency carries no manifest at all, so nothing can declare its own
dependencies, and a whole-repo dependency that carries its own `[dependencies]` is
not followed, so **nothing fetches a dependency of a dependency**. A per-target
cache to warm is still a sketch.

## Where the README and the binary disagree

| Claim in the README | What this binary does |
| --- | --- |
| "There is no `coral add` and no `coral update`" | both exist, both work, and both are in the command list above; `add` writes the manifest line and `update` re-fetches |
| "there was a `coral.lock`; both are gone" | `coral.lock` exists, is written by `add`/`update`/`sync`, and `--locked` reads it |
| a folder dependency lands flat, via a sparse clone | the folder is appended to the repository path and the clone fails; see [the folder section](#a-folder-dependency-is-broken-on-this-build) |

The rest of this page agrees with the README, and the README wins wherever the two
describe different versions.

## See also

- [`kelpc` CLI](/tooling/kelpc-cli)
- [Libraries (fpl)](/libraries) and [Writing a library](/libraries/writing-a-library)
- [Projects and coral.toml](/getting-started/projects)
- [Tooling](/tooling)
