# `kelpc` CLI

The compiler's command line. Everything on this page was run against a release
build of `kelpc 0.2.2` on the machine that wrote it, and the outputs are quoted
from those runs.

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
| `kelpc version` | prints the compiler version (`kelpc 0.2.2`) | 0 |

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
  (`coral run -- <args>`, see [Coral](coral.md)).

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
error: the 'asm' backend does not support the enum `E` yet
error: the 'asm' backend does not support the `extern fun std.fs.exists_raw` yet
error: the 'asm' backend does not support the parameter `f: &closure(&Item)` of `each` yet
```

Those are three different categories: a tagged union, a capability-gated call
(the `extern` body behind `std/fs`), and a closure parameter typed with a
module-declared type. Scalars, `while`, `print!` and arithmetic do lower; a
program made of those builds and runs under `asm` today.

The roadmap keeps the current count, and it is the authority for the numbers:
`plan/roadmap.md` records MK7 stage 1 as past halfway, with 193 of 266 integration
tests passing on the `asm` backend, 266 of 266 on the C one, and 97 of the 145
fixtures the C backend builds built and compared byte for byte
([roadmap](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/roadmap.md)).
Those figures come from the roadmap, not from a run here. What the `asm` backend
lowers today, and the 48 refusals it still has, are on the
[Backends](../compiler/backends.md) page.

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
[Coral](coral.md#which-compiler-coral-runs)).

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
[Coral's manifest section](coral.md#the-manifest)).

```sh
kelpc build myproject/            # from the parent directory
kelpc build src/main.kp -o myproject/app   # from the project root: same module graph
```

## See also

- [Coral](coral.md)
- [Tooling](index.md)
- [Projects and coral.toml](../getting-started/projects.md)
- [Install and build](../getting-started/install.md)
- [Compiler](../compiler/index.md)
