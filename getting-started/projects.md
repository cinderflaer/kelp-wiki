---
title: "Projects and `coral.toml`"
description: "A loose .kp file compiles on its own, and is then its own module root. A project is a directory with a coral.toml in it, sources under src/, and optionally an alias.kpconf -"
isPublished: true
tags: "getting-started"
---
A loose `.kp` file compiles on its own, and is then its own module root. A
**project** is a directory with a `coral.toml` in it, sources under `src/`, and
optionally an `alias.kpconf`:

```
myproject/
    coral.toml
    src/main.kp              # the entry module
    src/shapes/circle.kp     # impl "shapes/circle"
    src/deps/json/           # fetched by `coral sync`, gitignored
    src/tasks/report.kp      # a `[tasks]` entry
    alias.kpconf             # optional, see below
```

```sh
kelpc build myproject/       # builds the project
coral build                  # the same, through Coral, plus dependencies
```

## The manifest

```toml
name = "myproject"
version = "0.1.0"
entry = "src/main.kp"

[tasks]
report = "src/tasks/report.kp"

[dependencies]
util      = "Juniper/kelp-util"          # a whole repo
json      = "Juniper/fpl/json"           # one folder inside a repo
local     = "file:///srv/git/fpl#other"  # a full URL, folder after '#'

[toolchain]
kelp = "v0.1.1"
```

`kelpc` reads only the flat part (`name`, `version`, `entry`) and stops at the
first `[section]`, so the sections below belong to Coral.

## What a project buys you

- **`impl` paths are relative to `src/`**, not to the working directory or to the
  importing file. `impl "shapes/circle"` is always `<root>/src/shapes/circle.kp`,
  however deep the importer sits.
- **The entry module may be somewhere other than `src/main.kp`**: the manifest
  names it.
- **Dependencies** land under `src/`, because `kelpc` resolves every `impl` path
  against the project's `src/` and refuses one that steps outside it.

Compiling a file *inside* a project finds the manifest by walking up, so
`kelpc build src/main.kp` from the project root is the same module graph as
building the directory.

## Dependencies

A dependency is a line you write. `owner/repo` resolves against your Gitea over
SSH; anything containing `://` or `@` is taken as a full URL and used as written.

**A folder dependency lands flat**: `Juniper/fpl/json` puts the *contents* of
`json/` at `src/deps/json/`, so the import is

```kelp
impl "deps/json/lib"
```

no matter which repo or folder it came from. A sibling library in the same repo is
neither fetched nor importable.

| Command | What it does |
| --- | --- |
| `coral sync` | installs the pinned toolchain and fetches every dependency: **the only command that moves a dependency forward** |
| `coral build` | fetches a dependency that is missing, and nothing else; never refreshes one that is present |
| `coral run` | build, then run, forwarding argv and the exit code |
| `coral check` | build without keeping the artifact |
| `coral clean` | remove `build/` |
| `coral task <name>` | run a `[tasks]` entry |
| `coral task` | list the tasks declared in the manifest |
| `coral toolchain kelp …` | `list`, `installed`, `install <ver>`, `use <ver>`, `pin <ver>`, `pin --clear` |

`--offline` refuses instead of fetching, and `--dry-run` prints the plan.
`coral build --offline` after a sync is the assertion "this build did no I/O".

There is **no version, no lockfile and no registry index**: a dependency is a git
remote, and what makes a build reproducible is that `src/deps/<name>/` *is* the
tree it built with until something refreshes it.

## Pinning the compiler

```toml
[toolchain]
kelp = "v0.1.1"
```

A pin makes the project build with the compiler it was written against instead of
whatever `coral toolchain kelp use` last set machine-wide. `coral toolchain kelp
pin v0.1.1` writes it; `pin --clear` removes it. The store holds **one** version at
a time, so two projects pinned to different versions cost one reinstall per
switch.

## `alias.kpconf`

Alias substitution is textual and runs before parsing, so it can rewrite an import
path:

```kelp
// alias.kpconf, one name="replacement text" per line
db="storage/postgres"
```

```kelp
impl %*db*%
```

An inline `alias %*name*% = <raw text to end of line>` works too. There is no
scoping and no hygiene.

## See also

- [Install and build](/getting-started/install)
- [Testing what you write](/getting-started/testing): a `[tasks]` entry that checks your code
- [When it does not work](/getting-started/troubleshooting): manifest and capability failures
- [`kelpc` CLI](/tooling/kelpc-cli) and [Coral](/tooling/coral)
- [Libraries (fpl)](/libraries) and [Writing a library](/libraries/writing-a-library)
- [Capabilities](/language/capabilities): why a gated dependency needs a grant
