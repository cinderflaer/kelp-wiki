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
part by part once the language covers what it needs; a port is a long-term want
rather than a scheduled milestone (`kelp/plan/roadmap.md`, open item 72). This page follows
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
  sync [--dry-run] [--offline]
                            install the pinned toolchain and fetch dependencies, without building
                            --dry-run prints the plan and changes nothing
                            --offline refuses instead of fetching (or installing) anything
                            this is also what moves a dependency forward: a library has no
                            version, so a sync takes each remote's tip
  build [--release] [--offline]
                            compile the project's entry point with kelpc
  run [--release] [--offline] [-- args...]
                            build, then run the result, forwarding argv and the exit code
  check [--offline]         build without keeping the artifact
  clean                     remove build/
  docs get <file>.kp        one file's documentation comments, each with the
                            declaration it documents, and no code bodies
  docs list                 every documented thing in this project: where it is,
                            what it is called, and the first line of its prose
  docs search <query>       the entries whose key or prose match, prose included
                            ('fun:test' asks about that function and nothing else)
  task <name> [-- args...]  run a [tasks] entry
  task                      list the tasks declared in coral.toml
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
| `coral docs get <file>.kp` | print one file's documentation comments and the declarations they document |
| `coral docs list` | print every documented thing in the project, one line each |
| `coral docs search <query>` | print the entries whose key or prose match, prose included |
| `coral task` | list the `[tasks]` entries |
| `coral task <name>` | build and run one task |
| `coral clean` | remove `build/` |
| `coral toolchain kelp|coral ...` | list, installed, install, use, pin |

There is **no `coral --version`**: it is not a command, and the binary answers
`unknown command '--version'`. Ask the toolchain subcommand instead. `coral fmt`,
`coral lint`, `coral bench` and `coral publish` are also unknown commands today,
which is the "not here yet" list further down.

## `coral docs`

Three actions over one model: the documentation comments a project carries. The
language-side rules are [`syntax.md` §2.1](/language/lexical): `//!` and `///`
document the declaration below them, a `//!` that does not start a line is a
compiler error, and a block that documents something else names it with a
`[docs(<kind>: <name>)]` head.

| Command | What it does |
| --- | --- |
| `coral docs get <file>.kp` | one file's documentation, each block with the declaration it documents |
| `coral docs list` | every documented thing in this project, one line each |
| `coral docs search <query>` | the entries whose key or prose match, prose included |

### `coral docs get`

`coral docs get <file>.kp` needs no project, no manifest and no `kelpc`, so it
works on one file that is not part of a project yet:

```text
$ coral docs get std/str.kp
/// How many characters a `&str` has: bytes that do not continue a UTF-8
/// sequence.
fun char_count(s: &str).R: usize
```

The point is shape rather than content: a reader (or an agent) facing a
six-thousand-line module runs one command and sees what the file documents
instead of reading the source. What the render does, precisely:

- **A documentation block is printed verbatim**, marker and head included, so the
  output is the file's own words.
- **A headless block is followed by the declaration it documents**, with the body
  cut: a `{ ... }` body and an `= ...` expression body are both dropped, and a
  signature the author wrapped inside its own parentheses is joined onto one line.
- **A block with a head gets no signature printed under it**, because the head
  already names what the block is about.
- **A documented field or variant keeps its indentation**, so the render shows
  that the declaration is nested inside its `datac` or `enum` rather than
  pretending it is top level.
- **Only documented declarations appear.** A declaration with no documentation
  above it is left out, because the render is the documentation, not an outline.
- **A block with no declaration under it is printed alone** rather than dropped:
  `get` returns the file's documentation, it does not filter it.

```text
$ coral docs get buffer.kp
//! The buffer itself.
datac Buffer(val bytes: Bytes, val len: i32)

    /// The owned bytes.
    val bytes: Bytes

//! Appends one byte, growing the buffer if it is full.
fun push(b: &Buffer, v: u8)
```

It takes exactly one path, refuses a directory, and refuses anything that is not
a `.kp` file, so a mistyped argument is an error rather than an empty render.

### `coral docs list`

`coral docs list` walks the project's own sources, `src/` and `tests/`,
skipping a fetched `deps/` tree and a build directory, and prints one line per
documented thing: where it is, its key, and the first line of its prose. Paths
are relative to the project root.

```text
$ coral docs list
src/main.kp:1  module:main  A demo of documentation comments, which `coral docs` reads.
src/main.kp:6  title:"Error handling"  Every fallible call in this project returns a Result: there is no panic
src/main.kp:10  fun:test  The test function checks that a truncated frame is refused.
src/main.kp:16  const:HEADER  The frame we send first.
src/main.kp:19  fun:bump  Adds one to a count.
src/main.kp:23  field:len  How many bytes the frame carries.
```

An entry's key is what a reader searches for. A block below a declaration is
keyed by it (`fun:test`, `field:len`); a block at the top of a file is keyed
`module:<file stem>`; a `title:` head keys prose that belongs to no declaration.

### `coral docs search`

`coral docs search <query>` prints every matching entry with its prose, which is
the one command to reach for when the question is "what does this project say
about X". Both the key and the prose are searched, case-insensitively:

```text
$ coral docs search truncated
src/main.kp:10  fun:test
    The test function checks that a truncated frame is refused.
    It is kept next to the docs on purpose: a head can name a function that is
    declared somewhere else.

$ coral docs search fun:bump
src/main.kp:19  fun:bump
    Adds one to a count.
```

The first query matches prose, the second a restricted key: a query written
`<kind>:<text>` searches entries of that kind whose key or prose match, so
`fun:bump` asks about that function and nothing else, however many other blocks
mention it.

No match is an error rather than an empty success, so a script can ask whether
the project documents something (`coral docs search fun:parse` exits 1 when
nothing does). A head that cannot be read, or a block that documents no
declaration, is a warning on stderr naming the file and line; it does not stop
the rest of the index, because a reader should still get the documentation that
is well-formed.

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
| dev | `build/dev/demo`, `build/dev/demo.ll`, `build/dev/demo.o` |
| release | `build/release/demo`, `build/release/demo.ll`, `build/release/demo.o` |
| check | `build/check/demo`, `build/check/demo.ll`, `build/check/demo.o` (nothing is written to `dev/` or `release/`) |
| a task | `build/tasks/task-<name>`, `build/tasks/task-<name>.ll`, `build/tasks/task-<name>.o` |

The two files beside each binary are the backend's own: `llvm` writes the textual
IR and the object. They were `.c` while the C backend was what built a program,
and nothing but `kelpc` reads them.
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
build/tasks/task-hello.ll
build/tasks/task-hello.o
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

The line is written by hand, and `coral sync` is what fetches it:

```toml
[dependencies]
fpl = "Juniper/fpl"           # the whole repo
url = "Juniper/fpl/url"       # one folder inside it
```

`Juniper/fpl` is the whole repository, so its checkout lands at `src/deps/fpl/` and
the import names the folder inside it:

```kelp
impl "deps/fpl/json/lib"
```

`impl` paths are resolved against the project's `src/`, which is why fetched code
lands under `src/deps/` rather than a top-level `deps/`. A build fetches a
dependency that is missing; only `coral sync` refreshes one that is already there.

### A folder dependency lands flat

`owner/repo/folder` names one library inside a repository, and only that folder's
*contents* are downloaded. They land at `src/deps/<name>/` either way, so the
import is `impl "deps/<name>/lib"` no matter which repository or folder it came
from:
[Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md):
a folder dependency lands **flat**, so `Juniper/fpl/json` puts the contents of
`json/` at `src/deps/json/`, and the import is `impl "deps/json/lib"` no matter
which repository it came from. The clone behind it uses
`--filter=blob:none --sparse` so only the named folder comes down, and a server
that ignores the filter still works: git says so and does the slower thing.

```text
$ cat coral.toml
name = "coraldemo"
version = "0.26.9"
entry = "src/main.kp"

[dependencies]
url = "Juniper/fpl/url"

$ coral sync
coral: refreshing 'url' from ssh://gitea@thinkbox:2222/Juniper/fpl.git (url)
coral: 'url' is at 61f0b8b54c262eeee785038770d1a86a4509ac02
coral: 'coraldemo' synced (installed 0, fetched 1)

$ find src/deps -maxdepth 2
src/deps
src/deps/url
src/deps/url/lib.kp
```

A folder that is not in the repository is refused by name, with the list of
folders that are there, and a folder that names nothing useful cannot be written:
a `..` segment, a leading `/` or an empty name is an error in the manifest rather
than a path git is asked to check out.

### What the model promises, beyond those mechanics

- **A library has no version, on purpose.** There is no version constraint, no
  registry index, and no lockfile that pins a version. A dependency is a git
  remote, and what makes a build reproducible is that `src/deps/<name>/` **is** the
  tree it built with and stays that way until something refreshes it.
- **Only `coral sync` moves a dependency forward.** `coral build` fetches a
  dependency that is missing and leaves one that is present alone, which is why a
  warm tree builds offline and identically.
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

## There is no lockfile

A Kelp library has no version, so there is nothing for a lockfile to pin: a
dependency is a git remote, and what makes a build reproducible is that
`src/deps/<name>/` **is** the tree it built with and stays that way until a
`coral sync` refreshes it. `coral add` and `coral update` were removed, and so
were `coral.lock` and `--locked`: the binary refuses both of the commands by name
and `--locked` by name as well, rather than pretending to know them. A sync in CI
is `coral sync` after checkout, and a build that must not reach the network is
`coral build --offline`.

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

`coral docs` reads text and nothing else, so it resolves no name: a
`[docs(fun: nosuch)]` head is listed as written, and nothing reports that no such
function exists. It also lists documentation rather than the program, so a
function with no doc comment above it does not appear in `docs list` at all.

Two consequences of the dependency model, both from
[Coral's README](https://homelabone.xenoo.dev/gittea/Juniper/coral/src/branch/main/README.md):
a folder dependency carries no manifest at all, so nothing can declare its own
dependencies, and a whole-repo dependency that carries its own `[dependencies]` is
not followed, so **nothing fetches a dependency of a dependency**. A per-target
cache to warm is still a sketch.

## Where this page and the README could disagree

This page is written from the binary. The README is Coral's design sketch, and
wherever the two describe different versions the binary wins for command output
and the README wins for what a feature is meant to become. Two claims to watch:

| Claim | State |
| --- | --- |
| a folder dependency lands flat, via a sparse clone | shipped: `owner/repo/folder` lands the folder's contents at `src/deps/<name>/` |
| a library has no version, so there is no lockfile | shipped: `coral add`, `coral update`, `coral.lock` and `--locked` are gone |

## See also

- [`kelpc` CLI](/tooling/kelpc-cli)
- [Libraries (fpl)](/libraries) and [Writing a library](/libraries/writing-a-library)
- [Projects and coral.toml](/getting-started/projects)
- [Tooling](/tooling)
