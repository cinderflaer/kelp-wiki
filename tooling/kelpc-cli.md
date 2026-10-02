---
title: "`kelpc` CLI"
description: "The compiler's command line, quoted from runs against release builds: `build`, `run`, `check` (with `--json` and `--text`), `fmt`, `lint` and `--deny-outdated`."
isPublished: true
tags: "tooling, cli"
---
The compiler's command line. Everything on this page was run against a release
build on the machine that wrote it, and the outputs are quoted from those runs.
The bulk of it is the build tagged `v0.1.4`, whose binary was not rebuilt during
the rename, so `kelpc version` reported `kelpc 0.2.2` from that one. What shipped
after it (`kelpc lint` below, the comment-run and naming-case findings, the
`--deny-outdated` flag and the outdated-syntax section further down) comes from
`kelpc 26.09.0`.

```text
usage: kelpc build <file.kp> [-o <out>] [-O0|-O1|-O2|-O3|-Os] [--deny-outdated] [--incremental] [--timings]
       kelpc run <file.kp> [-O0|-O1|-O2|-O3|-Os] [--deny-outdated] [--incremental] [--timings]
       kelpc check <file.kp> [--json] [--deny-outdated] [--text]
       kelpc fmt <file.kp>
       kelpc fmt -w <path>...
       kelpc fmt --check <path>...
       kelpc lint <path>...
       kelpc cache stats|clear [--dir <dir>]
       kelpc version
```

There is no `--help` and no `--version`: each of those prints the usage block
above, and `kelpc version` is the version query.

## Subcommands

| Command | What it does | Exit status |
| --- | --- | --- |
| `kelpc build <file.kp>` | compiles to a binary and keeps the artifact | 0 on success, 1 on a diagnostic |
| `kelpc build <file.kp> -o <out>` | the same, naming the artifact | as above, 1 if `<out>.ll` cannot be written |
| `kelpc run <file.kp>` | compiles and executes, forwarding stdout, stderr and the program's exit code | the program's own status |
| `kelpc check <file.kp>` | runs the front end (load, type check, borrow check) with no code generation and writes no artifact; takes a project directory too | 0 on success, 1 on a diagnostic; an outdated finding on its own stays 0 |
| `kelpc check <file.kp> --json` | the same, with the findings as one JSON document on stdout | as above |
| `kelpc check <file.kp> --text` | the same, reading `<file.kp>`'s content from stdin instead of from disk; refused for a project directory | as above |
| `kelpc build <file.kp> --deny-outdated` | the same build, with a deprecation turned into an error | 1 if the program uses outdated syntax |
| `kelpc fmt <file.kp>` | prints the formatted source to stdout | 0, or 1 on a parse error |
| `kelpc fmt -w <path>...` | rewrites files in place | 1 if any input fails to parse |
| `kelpc fmt --check <path>...` | writes nothing, exits 1 if anything is not already formatted | 0 or 1 |
| `kelpc lint <path>...` | writes warnings to stderr for the style rules a formatter cannot enforce, and writes no file | 0 even when it warns; 1 only for a path it cannot read or a file it cannot lex |
| `kelpc cache stats` | prints the per-unit object cache's entry count and total size | 0 |
| `kelpc cache clear` | deletes every cached unit object | 0, or 1 when the directory cannot be removed |
| `kelpc version` | prints the release name the binary was built from: `kelpc 0.2.2` for the release tagged `v0.1.4`, and `kelpc 26.09.0` for the first release under the `YY.MM.N` scheme (`26.09.0`; the crate carries the semver-legal `26.9.0` and this command pads the month back) | 0 |

Two behaviours worth knowing:

- **`run` forwards the program's exit status.** A program that ends with
  `process.exit(3)` makes `kelpc run prog.kp` exit 3, which is what a shell script
  wants and what CI needs:

  ```text
  $ kelpc run exit3.kp; echo $?
  3
  ```

- **`run` takes no arguments of its own**, so a program that reads `argv` cannot
  be tested through it:

  ```text
  $ kelpc run src/main.kp extra
  error: unexpected argument 'extra'
  usage: kelpc build <file.kp> [-o <out>] [-O0|-O1|-O2|-O3|-Os] [--deny-outdated]
  ```

  Build first and run the binary, or use Coral, which does forward them
  (`coral run -- <args>`, see [Coral](/tooling/coral)).

## `check`

`kelpc check` runs everything a build runs except code generation: the same
modules, the same type check, the same borrow check. It answers whether a program
compiles without writing an artifact, and a project directory is one of the two
things it accepts, exactly as `build` accepts it.

```text
$ kelpc check /tmp/check/good.kp; echo $?
0
$ ls /tmp/check
 good.kp  main.kp
$ kelpc check /tmp/check/main.kp
error: the element type of 'ys' is still open: nothing said what 'List.empty()' holds, and 'xs.push(v)' is what decides it. Write it on the binding instead ('var xs: List<i32> = List.empty()')
  --> /tmp/check/main.kp:3:11
$ echo $?
1
```

The exit status is nonzero only for an error. An outdated-syntax finding exits
zero on its own, which is the rule `build` follows without `--deny-outdated`, and
`--deny-outdated` makes that finding an error exactly as it does there.

### `--json`

`kelpc check --json` writes the findings to stdout as one JSON document instead
of prose to stderr, so a program reads the answer instead of parsing a message.
Nothing else is written to either stream.

```json
{"schema":1,"ok":false,"diagnostics":[{"severity":"error","message":"the element type of 'ys' is still open: nothing said what 'List.empty()' holds, and 'xs.push(v)' is what decides it. Write it on the binding instead ('var xs: List<i32> = List.empty()')","module":"main","file":"/tmp/check/main.kp","line":3,"column":11,"end_line":3,"end_column":19,"notes":[]}]}
```

| Key | What it is |
| --- | --- |
| `schema` | `1` today, so a consumer can refuse a document it does not understand |
| `ok` | whether the program compiles: the same question the exit status answers |
| `severity` | `error`, `warning` or `outdated` |
| `module` | the module's canonical id: `main` for a loose file, `shapes/circle` for a module |
| `file` | the path as the compiler read it. Absent when there is no file to point at, which is a path the compiler could not read |
| `line`, `column` | 1-based, the first byte of the finding's span |
| `end_line`, `end_column` | exclusive, the byte after its last, so a reader can underline what the message is about |
| `notes` | secondary locations, each with `message`, `module` and the same location keys |

The front end stops at the first error, so `diagnostics` carries one `error` plus
whatever findings came before it: a `check` reports the first mistake, not every
mistake.

This is the interface [Lighthouse](/tooling/lighthouse)'s server was blocked on,
and the one Coral's design names as what a build tool reads instead of scraping
stderr. What Lighthouse also wants and does not have yet is whole-program
resolution, which is the compiler's own answer to keep or to publish.

### `--text`

`kelpc check <file.kp> --text` reads `<file.kp>`'s content from stdin instead of
from disk, while `<file.kp>` still names the real path: module resolution, the
`src/` layout rule, and every finding's `file`/`module` are the ones a caller
expects. It exists for an editor that wants to ask about an unsaved buffer
(`MISSING-b6Ytr`): a plain `kelpc check` can only ever see the last save, so a
mistake made since then reports nothing until the file is saved again.

```text
$ printf 'fun main() {\n    prin("broken")\n}\n' | kelpc check /tmp/check/main.kp --text --json
{"schema":1,"ok":false,"diagnostics":[{"severity":"error","message":"call to undefined function 'prin'","module":"main","file":"/tmp/check/main.kp","line":2,"column":5,"end_line":2,"end_column":19,"notes":[]}]}
$ cat /tmp/check/main.kp
fun main() {
    print("saved")
}
```

The file on disk is untouched by the call above: `--text` only changes what
`<file.kp>` is checked *as*, never what is written back. It is refused for a
project directory, since a buffer is always one open file, not a whole project.
[Lighthouse](/tooling/lighthouse)'s server uses it for the check that runs a
short debounce after a keystroke, with `didOpen`/`didSave` still reading from
disk.

## Where the artifacts land

| Invocation | Binary | Generated beside it |
| --- | --- | --- |
| `kelpc build src/main.kp` | `build/main` | `build/main.ll` and `build/main.o` |
| `kelpc build proj/` | `build/proj` | `build/proj.ll` and `build/proj.o` |
| `kelpc build proj` | `build/proj` | `build/proj.ll` and `build/proj.o` |
| `kelpc build src/main.kp -o app` | `app` | `app.ll` and `app.o` |
| `kelpc build .` | `build/a.out` | `build/a.ll` and `build/a.o` |

The generated files are `<out>.ll` (textual IR) and `<out>.o` (the object),
written beside the binary, and the object is linked with
`cc -o <out> <out>.o -lm` at the build's optimization level. A program that
reaches an `extern fun` also gets `<out>.externs.c`, the C source of its extern
object. Every `kelpc` links `libLLVM-21.so` and needs it at runtime. The `c`
oracle writes `<out>.c` where these land, and is one of the ways the `llvm`
artifact is checked.

- `build/` is relative to the **current working directory**, and the compiler
  creates it if it is missing.
- The name comes from the last path segment you passed, which is why a directory
  compiles to `build/<directory>` and a file to `build/<file stem>`.
- **A directory argument must hold a `coral.toml`.** A directory without one is
  refused, and neither `proj/` nor `.` is exempt:

  ```text
  $ kelpc build proj/
  error: '/tmp/proj' is a directory but has no coral.toml (pass a .kp file, or add a manifest)
  ```

- **Passing `.` gives the artifact the name `a.out`** (and `a.ll` and `a.o`),
  because the last segment has no stem. Name the directory (`kelpc build proj/`)
  or use `-o` when you care about the name, which a build script always should.
- With `-o`, the generated files are written beside the binary as `<out>.ll` and
  `<out>.o`. **The parent directory must already exist**:

  ```text
  $ kelpc build src/main.kp -o /tmp/missing/app
  error: could not write generated IR to '/tmp/missing/app.ll': No such file or directory (os error 2)
  ```

An `--incremental` build writes its artifacts somewhere else: see below.

## Incremental builds and the object cache

`kelpc` can split a program's **backend** into separate compilation units and
cache their objects, so a later build reuses everything whose IR did not change.
The front end (load, type check, borrow check) still runs whole-program; only
code generation is split. The mode is off by default and produces the same
program either way. [Incremental builds](/compiler/incremental) explains how it
works; this section is the command surface.

Turn it on one of three ways:

- `kelpc build <target> --incremental` and `kelpc run <target> --incremental`;
- `[build]` `incremental = true` in the project's `coral.toml`;
- leave it off, which is the default.

The C oracle (`KELPC_ORACLE=c`) ignores the flag and keeps its one translation
unit. A freestanding project is refused by name:

```text
$ kelpc build examples/kernel0 --incremental
error: '--incremental' is not implemented for a freestanding project yet: its image is one ELF with a single entry stub and one panic state, so the per-unit split is its own slice (plan/incremental-compilation.md)
```

One unit is written per source module id, plus one `_support` unit for the
compiler-generated helpers. A build with output `<out>` writes the units to
`<out>.units/<unit>.ll` and `<out>.units/<unit>.o` (a `/` in a module id is
written `+`, so `shapes/circle` is `shapes+circle.o`) and links them.

`--timings` adds per-phase wall times and, under `--incremental`, one line per
unit with `hit` or `miss`, all to stderr. `KELPC_CACHE_STATS=1` prints the
one-line build summary:

```text
$ KELPC_JOBS=2 KELPC_CACHE_DIR=cache KELPC_CACHE_STATS=1 kelpc build proj/ -o out/inc --incremental
kelpc cache: 0 hits, 4 misses, 4 stored
$ KELPC_JOBS=2 KELPC_CACHE_DIR=cache KELPC_CACHE_STATS=1 kelpc build proj/ -o out/inc --incremental
kelpc cache: 4 hits, 0 misses, 0 stored
```

Edit one module's source and run it again: the units whose IR did not change are
hits, and the edited module is the exception. On a three-module `shapes` project
(`main`, `geom`, `shapes/circle`) with a filled cache:

```text
$ KELPC_CACHE_DIR=cache KELPC_CACHE_STATS=1 kelpc build proj/ -o out/inc --incremental --timings
kelpc cache: 3 hits, 1 misses, 1 stored
kelpc timings:
  parse: 0.6 ms
  resolve: 0.1 ms
  infer: 0.7 ms
  borrowck: 0.1 ms
  codegen: 3.8 ms
  unit compile: 6.6 ms
  link: 106.9 ms
  unit geom: 0.9 ms hit
  unit main: 7.6 ms miss
  unit shapes/circle: 0.9 ms hit
  unit _support: 1.1 ms hit
```

`kelpc cache stats` and `kelpc cache clear` inspect and empty the directory. With
no `--dir` they use `KELPC_CACHE_DIR` when it is set and `build/.kelpc-cache`
otherwise, the same directory an `--incremental` build uses by default:

```text
$ kelpc cache stats --dir cache
kelpc cache: 4 entries, 9904 bytes in cache
$ kelpc cache clear --dir cache
kelpc cache: removed 4 files from cache
```

## Backends

`kelpc` builds every program with one backend, **`llvm`**. It lowers the typed IR
to LLVM IR, runs LLVM's own pass pipeline over the module at the build's
optimization level, emits an object and links it with `cc`.

There is no backend to choose. Whatever `--backend=` carries is refused with

```text
$ kelpc build src/main.kp --backend=asm2
error: --backend is gone: kelpc builds every program with the llvm backend, and the C backend is kept as the project's own oracle rather than as a user choice
```

and a set `KELPC_BACKEND` earns the same refusal, worded for the variable: the
choice is gone rather than the spelling changed, so a shell that still exports
one is told rather than silently ignored.

**The `c` backend is the project's own oracle**, kept in the tree, in the suite
and in CI. It transpiles to C and hands the file to `cc -fwrapv -lm` at the same
optimization level, and the fixture suite, the differential sweep and the fuzzer
measure every `llvm` build against its output. It is the reference backend rather
than a second opinion, and it is not a user surface: the project's own internal
switch is the only way to reach it.

The hand-written `asm` backend, which emitted x86-64 assembly itself and finished
with `as` and `ld`, was retired on 2026-09-20 and removed on 2026-09-21. Its plans,
its counts and its refusal ranking are history rather than a live measurement, and
the [Backends](/compiler/backends) page carries the current shape.

A *gated* item named as a function
value is refused by the compiler,
whether or not the naming module holds the domain, because the pattern check is
emitted from the call's own callee and an indirect call has none.

The **`llvm`** backend lowers the whole language the [Language](/language) pages
describe to LLVM IR and an object: the scalar types, `datac` records, `enum` and
`when`, `Bytes`/`String` and the drop plan, `List`/`Map`/`Box`/`[T; N]`,
references, closures and function values, the `extern fun` bodies, the `pd`
globals and the capability check. On the corpus it builds every target the C
backend builds and prints the same stdout with the same exit status, byte for
byte: `LLVM_BUILT_BASELINE` is 223 of the 223 targets and the refusal ranking is
empty. The gates that carry the slices are `kelpc/tests/run-llvm-scalar-subset.sh`,
`run-llvm-datac-subset.sh`, `run-llvm-strings-drops.sh`, `run-llvm-enum-subset.sh`,
`run-llvm-containers.sh`, `run-llvm-references.sh`, `run-llvm-closures.sh` (120
tests), `run-llvm-externs.sh` (138 tests) and `run-llvm-pd-caps.sh` (38 tests,
the `pd` globals, the capability check and the last three refusals, with the deny
text pinned against the C backend's own). One guard remains in the lowering, for
an owned temporary at a place it did not stage, and nothing in the corpus reaches
it. The `c` backend is the oracle this build is measured against. The object
carries DWARF
line locations, so a fault in an `llvm`-built binary names the `.kp` file and
line, where the C backend's `#line` was the only source of that before; it is a
line table, so no variables and no types. One optimization level is one level for
the whole build: it selects the LLVM pass pipeline and the target machine's
codegen level, and it is the `-O` flag the per-program C object and the final link
are given, so no performance parity with the C backend is claimed. See the MK7
record in
[`plan/done.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/done.md).

## `fmt`

`kelpc fmt` owns whitespace and nothing else. The rules it applies are the style
section of the plan
([syntax.md §19](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md)),
and the code that applies them is `kelpc/src/fmt.rs`.

What it enforces: indentation, spacing, trailing whitespace, the newline rules and
the comment rules. It caps a run of blank lines between top-level declarations at
one, never inserts a blank line the author did not write, and preserves the
author's line wrapping instead of re-wrapping.

Four invariants, which are the reason it is safe to run on any file:

| Invariant | Meaning |
| --- | --- |
| idempotent | formatting a formatted file changes nothing |
| token-faithful | no token's text is ever rewritten, so the formatted file is the same program |
| comment-preserving | every comment survives verbatim |
| refuses what it cannot read | a file that does not parse is reported and left alone |

What it does **not** enforce: the 100 column limit, the order of declarations
inside the final group, and the naming and case rules. Those are review
conventions that need a lint, and `kelpc lint` is that command. It is
warning-only, and it reports the comment run, the `else if` link and the naming
case below.

Path handling, as `--help` documents it:

- A path may be a `.kp` file or a directory, and a directory recurses.
- A **symbolic link given by name** is followed to the file it names, so `-w`
  rewrites that file and the link survives. A link **found inside a directory** is
  skipped and reported.
- A path that is not a regular file (a FIFO, a socket, a device) is refused before
  it is read, so `fmt` never waits on a node that has no data and never replaces
  one.
- A rewritten file is a **new inode**, so a hard link to it keeps the old bytes.
- A file that does not parse, by `fmt`'s own reading of it or by the compiler's
  when the project's aliases are needed, is reported as a parse error. **Other
  files in the same run are still formatted**, and the exit status is 1.

```text
$ kelpc fmt --check messy.kp
error: 'messy.kp' is not formatted
$ echo $?
1

$ kelpc fmt messy.kp
fun main() {
    print("hi")
}

$ kelpc fmt -w messy.kp && kelpc fmt --check messy.kp
$ echo $?
0

$ kelpc fmt broken.kp
error: expected identifier, found LBrace
  --> /tmp/tooling-fmt/broken.kp:1:11
```

That last run changed nothing. `--check` is the CI shape: it writes nothing and
fails on the first file that differs.

## `lint`

`kelpc lint` is the other half of the style section: what a formatter cannot
enforce. It is **warning-only by design**, so it is not a gate and it never
rewrites anything:

```sh
kelpc lint <path>...   # a .kp file, or a directory walked recursively
```

- Findings go to stderr as `warning: ...` with a `file:line:col` location, and
the exit status is **0** even when there are findings. A script tells "clean"
from "has findings" by the output, and "could not check" by the exit status:
only a path it cannot read or a file it cannot lex exits 1, reported with the
same shape `kelpc build` uses for the same file.
- It writes no file, so there is no `-w` and no `--check`.
- Paths are collected the way `fmt` collects them (a `.kp` file, or a directory
recursing `.kp` files, with a link inside a directory skipped and reported), so a
tree is named once.

The rules are the ones a formatter cannot enforce: the comment run, the `else if`
link, and the naming case, all three from [Style](/language/style).

### The comment run

Two or more consecutive `//` lines with no blank line and no code between them
suggest one `/* ... */` comment:

```text
$ kelpc lint notes.kp
warning: 3 consecutive '//' lines suggest one '/* ... */' comment
  --> /tmp/lintdemo/notes.kp:2:5
$ echo $?
0
```

What does **not** count as a run, each for a reason the rule would otherwise get
wrong: a blank line between the comments (two thoughts, which is how the author
separated them), any code between them, a block comment between them, a comment
that follows code on its own line (a run is *lines* of comments), and a doc
comment (`///` and `//!` are documentation the tooling reads as documentation,
so the block-comment suggestion does not apply). A `//` inside a string or a
block comment is not a comment either, because the rule reads tokens rather than
text.

### The `else if` link

`elif` is the preferred spelling of a chain link, so the longer one is reported:

```text
$ kelpc lint server.kp
warning: 'else if' compiles, but 'elif' is the preferred spelling
  --> /tmp/lintdemo/server.kp:14:7
$ echo $?
0
```

Both spellings stay legal and compile identically, and `kelpc fmt` never rewrites
one into the other.

### The naming case

The project's case is `coral.toml`'s `naming_case` (`0` = `camelCase`, the
default; `1` = `snake_case`), and a declared name in the other case is reported:

```text
$ kelpc lint io.kp
warning: function 'read_text' is snake_case, and this project asks for camelCase (coral.toml 'naming_case = 0'); write 'readText'
  --> /tmp/lintdemo/io.kp:7:5
$ echo $?
0
```

The setting is the project's, not the invocation's, so there is no `kelpc lint`
flag for it. The rule reads the names a file **declares** (a `fun` name, a
parameter, a `val`/`var`/`pd` binding, a `datac` or payload field, a loop binding,
a pattern binding), which is why a call into the standard library's locked
`snake_case` is never reported under either setting: a call is a use. A file with
no `coral.toml` to read gets the option's default, and a file under the
project's `src/deps/` gets no case rule at all.

## Outdated syntax

A spelling that is on its way out still compiles, and the compiler keeps a
register of them (`kelpc/src/deprecated.rs`, and `syntax.md` 23). **The register
is empty today**: the two entries it has carried, the `as name` clause on an
`impl` line and the `with` in front of a capability grant, were removed rather
than merely deprecated, so no program produces an `outdated:` finding any more.
The mechanism stays in place for the next spelling, and so does its vocabulary:
`kelpc build` and `kelpc run` print one `outdated:` finding per construct a
program uses when an entry is added.

- The label is **`outdated: `**, which is neither `error:` nor `warning: `. A
  lint's `warning: ` is a style opinion; this is a promise about a later version.
- An entry's old spelling **keeps working**, and the exit status is unchanged.
  Nothing is removed on the day its warning first appears: every entry goes on the
  next development cycle.
- **`--deny-outdated`** turns the findings into errors and stops before anything
  is generated. That is the gate for a project or a CI run that wants to hear
  about its own code. With the register empty it changes nothing, and it stays for
  the next entry.
- **`kelpc fmt`** never rewrites an old spelling into a new one: it copies tokens.
  **`kelpc lint`** does not report deprecations either, because a deprecation is a
  build's finding rather than a style pass's.

Both removed spellings are hard errors that name their fix rather than findings:

```text
$ kelpc build src/main.kp
error: `impl "..." with caps(...)` is gone: drop the `with`, so the grant is `impl "std/fs" caps(fs = ["/var/log/**"])`, and the patterns, the domains and the no-escalation rule are exactly the same
$ echo $?
1
```

The `as name` clause is refused the same way, and the module is reached by its own
name (see [Modules and imports](/language/modules)).

## The memory floor

`kelpc build` and `kelpc run` end themselves when the machine is nearly out of
memory, with one `error:` line and exit status **75**, instead of leaving the
kernel's OOM killer to choose a victim (on a small host the victim is often not
the compiler, and can be a whole login session).

A watchdog thread reads `MemAvailable` from `/proc/meminfo` every 200 ms. Below
the floor it kills the `cc`/`ld.lld`/`pkg-config` children the driver spawned
(they are the largest consumers and would outlive `kelpc`), prints the message
below and leaves with `_exit(75)` (`EX_TEMPFAIL`: the same input can succeed once
memory is free). The main thread is still inside LLVM at that point, so the exit
is `_exit` and not `std::process::exit`.

```text
$ KELPC_MIN_AVAILABLE_MB=999999999 kelpc build src/main.kp
error: kelpc stopped itself: only 4974 MiB of memory is available (floor 999999999 MiB). Free some memory and run it again, or lower the floor with KELPC_MIN_AVAILABLE_MB (0 turns the guard off).
$ echo $?
75
```

| Setting | Meaning |
| --- | --- |
| `KELPC_MIN_AVAILABLE_MB` | the floor in MiB, default **384**; `0` turns the guard off; an unparsable value is the default |

What it does not police: `kelpc run` stops the guard before it starts the
compiled program, so a program's own memory use is never limited by it. `fmt`,
`lint`, `check` and `version` do not start it at all, and only Linux is covered:
with no `/proc/meminfo` the guard does nothing. Disk space is not checked.

## Environment variables

| Variable | Effect |
| --- | --- |
| `LLVM_SYS_211_PREFIX` | where `llvm-sys` finds `libLLVM` and its headers; set by `shell.nix` |
| `KELPC_MIN_AVAILABLE_MB` | the compiler's memory floor; below it `build`/`run` exit 75, `0` disables it (see [above](#the-memory-floor)) |
| `KELPC_JOBS` | the `--incremental` unit-compilation worker count: a positive integer, default **2**, not the CPU count. A missing, unparsable or `0` value is the default, and more workers than units spawns one per unit |
| `KELPC_CACHE_DIR` | the object cache's directory; overrides the default `<out dir>/.kelpc-cache`, for a build and for a bare `kelpc cache` command |
| `KELPC_CACHE` | `off` turns lookups and stores off for one build; nothing is read and no directory is created |
| `KELPC_CACHE_STATS` | `1` prints the one-line `kelpc cache: <H> hits, <M> misses, <S> stored` summary to stderr at the end of a build |
| `KELPC_CACHE_MAX_MB` | the cache size cap in MiB, default **1024**. At the end of a build the oldest-modified entries are deleted until the total is under it (`0` empties the cache) |

Coral also reads `KELPC` to decide which compiler to run, which is a different
question from what the compiler does with its own environment (see
[Coral](/tooling/coral#which-compiler-coral-runs)).

## Projects

A project is a directory with a `coral.toml` in it. Compiling one rather than a
file changes three things:

1. **Module resolution follows the project, not the working directory.** A local
   `impl` path is relative to the project's `src/` and not to the file that
   contains the line, so `impl "shapes/circle"` means `<root>/src/shapes/circle.kp`
   from anywhere. `kelpc` refuses an `impl` path that steps outside `src/` (no
   `..` segments, no absolute paths).
2. **The entry point comes from the manifest.** `entry = "src/main.kp"` is the
   file that must hold `main`, and it does not have to be called `main.kp`.
3. **The compiler reads the flat keys and a few of its own sections.** It wants
   `name`, `version` and `entry` (plus `http_pool` and `naming_case`), and it
   reads `[build]`, `[target]`, `[caps]`, `[unsafe]` and `[extern."..."]`
   itself, because those change what it compiles: `[build] incremental = true`
   turns on the per-unit split. Every other section (`[tasks]`,
   `[dependencies]`, `[toolchain]`) is Coral's manifest surface, and the
   compiler skips its lines rather than rejecting them.

`kelpc` is lenient about flat keys it does not use: a manifest carrying
`http_pool = 8` compiles, because the compiler never looks at it. Coral validates
that key, and the two disagree about its type (see
[Coral's manifest section](/tooling/coral#the-manifest)).

```sh
kelpc build myproject/            # from the parent directory
kelpc build src/main.kp -o myproject/app   # from the project root: same module graph
```

## See also

- [Coral](/tooling/coral)
- [Tooling](/tooling)
- [Projects and coral.toml](/getting-started/projects)
- [Install and build](/getting-started/install)
- [Compiler](/compiler)
