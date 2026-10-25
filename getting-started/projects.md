---
title: "Projects and `coral.toml`"
description: "A loose .kp file compiles on its own. A project is a directory with a coral.toml in it, sources under src/, and optional aliases in its [alias] section."
isPublished: true
tags: "getting-started"
---
A loose `.kp` file compiles on its own, and is then its own module root. A
**project** is a directory with a `coral.toml` in it, sources under `src/`, and
optional aliases in its `[alias]` section:

```
myproject/
    coral.toml
    src/main.kp              # the entry module
    src/shapes/circle.kp     # impl "shapes/circle"
    src/deps/json/           # fetched by `coral sync`, gitignored
    src/tasks/report.kp      # a `[tasks]` entry
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
util      = "Lilly/kelp-util"          # a whole repo
json      = "Lilly/fpl/json"           # one folder inside a repo
local     = "file:///srv/git/fpl#other"  # a full URL, folder after '#'
```

`kelpc` reads the flat keys (`name`, `version`, `entry`, `http_pool` and
`naming_case`) and the sections that change what it compiles, such as `[alias]`,
`[caps]` and `[target]`. A `[run]` table, which names the QEMU machine and the lines
`kelpc boot` checks, is read by that command only (see [`kelpc` CLI](/tooling/kelpc-cli)). It skips the sections that belong to Coral, such as
`[tasks]` and `[dependencies]`.

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

A dependency is a line you write. `owner/repo` resolves against the registry in
Coral's configuration, the Gitea base URL set by `CORAL_REGISTRY` or the config
file (see [Coral](/tooling/coral#configuration)); anything containing `://` or `@`
is taken as a full URL and used as written.

**A folder dependency lands flat**: `Lilly/fpl/json` puts the *contents* of
`json/` at `src/deps/json/`, so the import is

```kelp
impl "deps/json/lib"
```

no matter which repo or folder it came from. A sibling library in the same repo is
neither fetched nor importable.

| Command | What it does |
| --- | --- |
| `coral sync` | installs the newest Kelp release if the store lacks it, and fetches every dependency: **the only command that moves a dependency forward** |
| `coral build` | fetches a dependency that is missing, and nothing else; never refreshes one that is present |
| `coral run` | build, then run, forwarding argv and the exit code |
| `coral check` | build without keeping the artifact |
| `coral clean` | remove `build/` |
| `coral task <name>` | run a `[tasks]` entry |
| `coral task` | list the tasks declared in the manifest |
| `coral toolchain kelp …` | `latest`, `installed`, `update`: the compiler is always the newest release |

`--offline` refuses instead of fetching, and `--dry-run` prints the plan.
`coral build --offline` after a sync is the assertion "this build did no I/O".

There is **no dependency version and no registry index**: a dependency is a git
remote. `coral sync` refreshes each dependency to its remote tip and records the
commit it checked out in `coral.lock`.

## The compiler

There are no per-project compiler pins. Coral builds every project with the newest
Kelp release it has installed, and `coral toolchain kelp update` installs that
release. A `[toolchain]` section in `coral.toml` is refused: delete it.
`[package] kelp` records the release a project was last built with, which Coral
writes itself.

## Aliases in `coral.toml`

Alias substitution is textual and runs before parsing, so it can rewrite an import
path.
Declare the alias in the `[alias]` section of `coral.toml`, one `_name = "path"` per line:

```toml
[alias]
_db = "storage/postgres"
```

Use the alias inside a string, because the value is a plain module path:

```kelp
impl "_db"
```

The path must be relative, with no leading `/` and no `..` component.
The project-root `alias.kpconf` file is no longer read.

An inline `alias _name = <raw text to end of line>` works too.
There is no scoping and no hygiene.

## See also

- [Install and build](/getting-started/install)
- [Testing what you write](/getting-started/testing): a `[tasks]` entry that checks your code
- [When it does not work](/getting-started/troubleshooting): manifest and capability failures
- [`kelpc` CLI](/tooling/kelpc-cli) and [Coral](/tooling/coral)
- [Libraries (fpl)](/libraries) and [Writing a library](/libraries/writing-a-library)
- [Capabilities](/language/capabilities): why a gated dependency needs a grant
