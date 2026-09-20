---
title: "`kelpc` CLI"
description: "The compiler's command line. Everything on this page was run against a release build on the machine that wrote it, and the outputs are quoted from those runs: the bulk of it against the build tagged `v0.1.4`, the `lint` section, the `--deny-outdated` flag, the outdated-syntax register and the `check` section against `kelpc 26.09.0` and the unreleased work after it."
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
usage: kelpc build <file.kp> [-o <out>] [--backend=<name>] [--deny-outdated]
       kelpc run <file.kp> [--deny-outdated]
       kelpc check <file.kp> [--json] [--deny-outdated]
       kelpc fmt <file.kp>
       kelpc fmt -w <path>...
       kelpc fmt --check <path>...
       kelpc lint <path>...
       kelpc version
```

There is no `--help` and no `--version`: each of those prints the usage block
above, and `kelpc version` is the version query.

## Subcommands

| Command | What it does | Exit status |
| --- | --- | --- |
| `kelpc build <file.kp>` | compiles to a binary and keeps the artifact | 0 on success, 1 on a diagnostic |
| `kelpc build <file.kp> -o <out>` | the same, naming the artifact | as above, 1 if `<out>.c` cannot be written |
| `kelpc run <file.kp>` | compiles and executes, forwarding stdout, stderr and the program's exit code | the program's own status |
| `kelpc check <file.kp>` | runs the front end (load, type check, borrow check) with no code generation and writes no artifact; takes a project directory too | 0 on success, 1 on a diagnostic; an outdated finding on its own stays 0 |
| `kelpc check <file.kp> --json` | the same, with the findings as one JSON document on stdout | as above |
| `kelpc build <file.kp> --deny-outdated` | the same build, with a deprecation turned into an error | 1 if the program uses outdated syntax |
| `kelpc fmt <file.kp>` | prints the formatted source to stdout | 0, or 1 on a parse error |
| `kelpc fmt -w <path>...` | rewrites files in place | 1 if any input fails to parse |
| `kelpc fmt --check <path>...` | writes nothing, exits 1 if anything is not already formatted | 0 or 1 |
| `kelpc lint <path>...` | writes warnings to stderr for the style rules a formatter cannot enforce, and writes no file | 0 even when it warns; 1 only for a path it cannot read or a file it cannot lex |
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
  usage: kelpc build <file.kp> [-o <out>] [--backend=<name>]
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

## Where the artifacts land

| Invocation | Binary | Generated C |
| --- | --- | --- |
| `kelpc build src/main.kp` | `build/main` | `build/main.c` |
| `kelpc build proj/` | `build/proj` | `build/proj.c` |
| `kelpc build proj` | `build/proj` | `build/proj.c` |
| `kelpc build src/main.kp -o app` | `app` | `app.c` |
| `kelpc build .` | `build/a.out` | `build/a.c` |

Under `--backend=asm` the generated file is the assembly text in place of the C:
`build/main.s` and `build/main.o`, or `<out>.s` and `<out>.o` with `-o`. That
backend is retired as a direction and goes when the LLVM backend lands; the planned
artifact then is LLVM IR (`.ll`) or an object, with a `libLLVM` requirement on
`kelpc` itself.

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

- **Passing `.` gives the artifact the name `a.out`** (and the C `a.c`), because
  the last segment has no stem. Name the directory (`kelpc build proj/`) or use
  `-o` when you care about the name, which a build script always should.
- With `-o`, the generated C is written beside the binary as `<out>.c`. **The
  parent directory must already exist**:

  ```text
  $ kelpc build src/main.kp -o /tmp/missing/app
  error: could not write generated C to '/tmp/missing/app.c': No such file or directory (os error 2)
  ```

## Backends

Two code generators, selected with `--backend=` or `KELPC_BACKEND`; an explicit
`--backend` wins over the variable, and the default is `c`.

| Backend | What it does | Toolchain it needs |
| --- | --- | --- |
| `c` (default) | transpiles to C | `cc -O2 -fwrapv -lm` |
| `asm` | emits x86-64 assembly itself | `as`, `ld` (no C compiler in the chain) |

```sh
kelpc build examples/hello.kp --backend=asm   # until `asm` is removed
KELPC_BACKEND=c kelpc run examples/hello.kp   # the oracle, and the default
```

A backend that does not exist is named in the error, so a typo is not a mystery:

```text
$ kelpc build src/main.kp --backend=asm2
error: unknown backend 'asm2'; expected one of: c, asm
```

**The C backend is the reference.** Every fixture in the test suite is built by
both backends and the two binaries' stdout is compared, so a construct the `asm`
backend cannot lower is **refused by name** rather than silently miscompiled.
Three real refusals, measured at compiler commit `926e33f`:

```text
error: the 'asm' backend does not support the `extern fun std.process.arg_count_raw` yet
error: the 'asm' backend does not support the method `List.clone` on a `List` yet
error: the 'asm' backend does not support a borrow of anything but a named local (a scalar, a `datac` or a heap type), a `datac` temporary, or a field of one yet
```

They are three lines and three mechanisms, measured at compiler commit `926e33f`: an `extern` whose body this backend has
no routine for (`std.process`'s argv and spawn family is the one left), which the plan
counts in its catch-all heap row; a `List` method over a `datac` or `enum` element;
and a borrow of a field chain. Scalars, `while`, `print!`, arithmetic, an aggregate
holding a float, a closure, a plain function value and a gated call all lower, so a
program made of those builds and runs under `asm` today. A *gated* item named as a
function value is not lowered at all: the compiler refuses it, in both backends
and whether or not the naming module holds the domain, because the pattern check
is emitted from the call's own callee and an indirect call has none.

The next backend is **LLVM IR**, and it is not a project: everything up to the
typed IR is reused, so only the emission layer is new, and LLVM supplies the
optimizer, the encoder, the ELF writer, the debug-info format, sanitizers and the
targets. It is roughly feature-complete with the fixture suite green in about 3 to
6 weeks of work. See
[`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md).

[`plan/asm-backend/plan.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/plan.md)
§0 and §5 hold the measured history of the retired `asm` track, and the
[Backends](/compiler/backends) page carries the current table. **205 of the 208
fixtures the C backend accepts build under `asm`, and 3 are refused**, measured at
compiler commit `926e33f`; the
suite figure measured the same way is **341 of 358** integration tests passing
under `--backend=asm`, with the C backend passing all 358, a larger denominator
because the suite counts multi-file projects and subprocess cases as well. Both
were measured at that commit rather than quoted from an earlier run. Re-measure
both before quoting them, because each moves with every slice. What the `asm`
backend lowers today, and the 3 refusals it still has, are on the
[Backends](/compiler/backends) page.

If the `asm` backend cannot find the library directory it links against, point
`KELPC_GLIBC_DIR` at the directory holding `crt1.o` and `libc.so`.

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

A spelling that is on its way out still compiles. The compiler keeps a register
of them (`kelpc/src/deprecated.rs`, and `syntax.md` 23), and `kelpc build` and
`kelpc run` print one finding per construct a program uses:

```text
$ kelpc build src/main.kp
outdated: `impl "..." with caps(...)` is outdated and will be removed in the next development cycle: drop the `with`: the grant is `impl "std/fs" caps(fs = ["/var/log/**"])`, and the patterns, the domains and the no-escalation rule are exactly the same
  --> src/main.kp:2:13
$ echo $?
0
```

- The label is **`outdated: `**, which is neither `error:` nor `warning: `. A
  lint's `warning: ` is a style opinion; this is a promise about a later version.
- The old spelling **keeps working**, and the exit status is unchanged. Nothing
  is removed on the day its warning first appears: every entry goes on the next
  development cycle.
- **`--deny-outdated`** turns the findings into errors and stops before anything
  is generated. That is the gate for a project or a CI run that wants to hear
  about its own code. A program with nothing on the list builds as it always did.
- **`kelpc fmt`** never rewrites an old spelling into a new one: it copies tokens.
  **`kelpc lint`** does not report deprecations either, because a deprecation is a
  build's finding rather than a style pass's.
- The register has one entry, the `with` in front of a capability grant
  (`impl "std/fs" with caps(fs = [...])`, where the grant itself is
  `impl "std/fs" caps(fs = [...])`). Its migration is a deletion: the `with`
  says nothing the `impl` line does not. The first entry, the `as name` clause on
  an `impl` line, is **retired**: it is gone from the parser, so a program that
  still writes it gets an error rather than a finding, and the module is reached
  by its own name (see [Modules and imports](/language/modules)).

## Environment variables

| Variable | Effect |
| --- | --- |
| `KELPC_BACKEND` | default backend (`c` or `asm`); an explicit `--backend=` wins over it |
| `KELPC_GLIBC_DIR` | where the `asm` backend finds `crt1.o` and `libc.so` |

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
3. **The compiler reads only the flat part.** It wants `name`, `version` and
   `entry`, and it **stops parsing at the first `[section]`**, so `[tasks]`,
   `[dependencies]` and `[toolchain]` are invisible to it. Coral is the program
   that reads those.

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
