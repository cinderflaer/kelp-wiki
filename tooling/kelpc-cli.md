---
title: "`kelpc` CLI"
description: "The compiler's command line. Everything on this page was run against a release build of kelpc 0.1.4 on the machine that wrote it, and the outputs are quoted from those runs."
isPublished: true
tags: "tooling, cli"
---
The compiler's command line. Everything on this page was run against the release
build tagged `v0.1.4` on the machine that wrote it, and the outputs are quoted
from those runs. That binary was not rebuilt for the rename, so `kelpc version`
still reports `kelpc 0.2.2`.

```text
usage: kelpc build <file.kp> [-o <out>] [--backend=<name>]
       kelpc run <file.kp>
       kelpc fmt <file.kp>
       kelpc fmt -w <path>...
       kelpc fmt --check <path>...
       kelpc version
```

There is no `--help`, no `--version` and no `check` subcommand: each of those
prints the usage block above, and `kelpc version` is the version query.

## Subcommands

| Command | What it does | Exit status |
| --- | --- | --- |
| `kelpc build <file.kp>` | compiles to a binary and keeps the artifact | 0 on success, 1 on a diagnostic |
| `kelpc build <file.kp> -o <out>` | the same, naming the artifact | as above, 1 if `<out>.c` cannot be written |
| `kelpc run <file.kp>` | compiles and executes, forwarding stdout, stderr and the program's exit code | the program's own status |
| `kelpc fmt <file.kp>` | prints the formatted source to stdout | 0, or 1 on a parse error |
| `kelpc fmt -w <path>...` | rewrites files in place | 1 if any input fails to parse |
| `kelpc fmt --check <path>...` | writes nothing, exits 1 if anything is not already formatted | 0 or 1 |
| `kelpc version` | prints the build-time version string of the binary: `kelpc 0.2.2` for the release tagged `v0.1.4` | 0 |

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

## Where the artifacts land

| Invocation | Binary | Generated C |
| --- | --- | --- |
| `kelpc build src/main.kp` | `build/main` | `build/main.c` |
| `kelpc build proj/` | `build/proj` | `build/proj.c` |
| `kelpc build proj` | `build/proj` | `build/proj.c` |
| `kelpc build src/main.kp -o app` | `app` | `app.c` |
| `kelpc build .` | `build/a.out` | `build/a.c` |

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
kelpc build examples/hello.kp --backend=asm
KELPC_BACKEND=asm kelpc run examples/hello.kp
```

A backend that does not exist is named in the error, so a typo is not a mystery:

```text
$ kelpc build src/main.kp --backend=llvm
error: unknown backend 'llvm'; expected one of: c, asm
```

**The C backend is the reference.** Every fixture in the test suite is built by
both backends and the two binaries' stdout is compared, so a construct the `asm`
backend cannot lower is **refused by name** rather than silently miscompiled.
Three real refusals:

```text
error: the 'asm' backend does not support the `extern fun std.fs.exists_raw` yet
error: the 'asm' backend does not support the parameter `f: &closure(&Item)` of `each` yet
error: the 'asm' backend does not support the `extern fun std.time.now_unix_raw` yet
```

Those are three different categories: an `extern` whose body this backend has no
routine for, which is the `std/fs` call here and which the plan counts in its
catch-all heap row; a closure or a function value; and an `extern` refused for
its capability gate rather than for the symbol (`time.now_unix_raw`). Scalars,
`while`, `print!`, arithmetic and an aggregate holding a float all lower, so a
program made of those builds and runs under `asm` today.

`plan/mk7-own-backend.md` §0 and §5 own the current count. **154 of the 174
fixtures the C backend accepts build under `asm`, and 20 are refused**, and the
plan's status table records **250 of 295** integration tests passing under
`--backend=asm`, with the C backend passing all 295, a larger denominator,
because the suite counts multi-file projects and subprocess cases as well
([mk7-own-backend.md](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-own-backend.md)).
The fixture pair was re-measured for this page, and the suite figure is the
plan's, not a run here. Re-measure both before quoting them, because each moves
with every slice; the MK7 row of `plan/roadmap.md` carries the same figures.
What the `asm` backend lowers today, and
the 20 refusals it still has, are on the [Backends](/compiler/backends) page.

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
conventions that need a lint, and `kelpc` has no `lint` command.

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
