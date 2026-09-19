# `kelpc` CLI

The compiler's own command line, as `kelpc --help` prints it:

```text
usage: kelpc build <file.kp> [-o <out>] [--backend=<name>]
       kelpc run <file.kp>
       kelpc fmt <file.kp>
       kelpc fmt -w <path>...
       kelpc fmt --check <path>...
       kelpc version
```

## Subcommands

| Command | What it does |
| --- | --- |
| `kelpc build <file.kp>` | compiles to a binary, keeping the artifact |
| `kelpc build <file.kp> -o <out>` | the same, naming the output |
| `kelpc run <file.kp>` | compiles and executes, forwarding the program's output |
| `kelpc fmt <file.kp>` | prints the formatted source to stdout |
| `kelpc fmt -w <path>...` | rewrites files in place |
| `kelpc fmt --check <path>...` | exits nonzero if anything is not already formatted |
| `kelpc version` | prints the compiler version |

`kelpc version` on this checkout prints `kelpc 0.2.2`.

## Where the artifacts land

| Invocation | Binary | Generated C |
| --- | --- | --- |
| `kelpc build hello.kp` | `build/hello` | `build/hello.c` |
| `kelpc build proj/` | `build/proj` | `build/proj.c` |
| `kelpc build hello.kp -o out/hello` | `out/hello` | `out/hello.c` |

`build/` is relative to the **current working directory** and the compiler creates
it if it is missing. The name comes from the last path segment you passed, so a
project directory compiles to `build/<project>` — the same place a file does.

With `-o`, the generated C is written beside the binary as `<out>.c`. The
parent directory of `-o` must already exist; the compiler does not create it:

```sh
$ kelpc build hello.kp -o /tmp/nope/hello
error: could not write generated C to '/tmp/nope/hello.c': No such file or directory (os error 2)
```

## Backends

Two code generators are selectable with `--backend=` or the `KELPC_BACKEND`
environment variable; an explicit `--backend` wins over the variable, and the
default is `c`.

| Backend | What it does | Chain |
| --- | --- | --- |
| `c` (default) | transpiles to C | `cc -O2 -fwrapv -lm` |
| `asm` | emits x86-64 assembly itself | `as`, `ld` — no C compiler |

```sh
kelpc build examples/hello.kp --backend=asm
KELPC_BACKEND=asm kelpc run examples/hello.kp
```

The C backend is the reference: every fixture in the test suite is built by both
backends and the two binaries' stdout is compared, so a construct the `asm`
backend does not lower yet is refused **by name** rather than silently
miscompiled:

```
error: the 'asm' backend does not support the enum `Maybe` yet
```

If the `asm` backend cannot find the library directory it links against, point
`KELPC_GLIBC_DIR` at the directory holding `crt1.o` and `libc.so`.

## `fmt`

`kelpc fmt` owns whitespace and nothing else. Its rules and its refusals are data
in `kelpc/src/fmt.rs`, and the style section of the plan
([syntax.md §19](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md))
is what they implement.

What it enforces: indentation, spacing, trailing whitespace, the newline rules
and the comment rules. It caps a run of blank lines between top-level
declarations at one but never inserts a blank line the author did not write, and
it preserves the author's own line wrapping instead of re-wrapping.

Four invariants:

| Invariant | Meaning |
| --- | --- |
| idempotent | formatting a formatted file changes nothing |
| token-faithful | no token's text is ever rewritten, so the formatted file is the same program |
| comment-preserving | every comment survives verbatim |
| never writes a file it refuses | a file that does not parse is reported, not reformatted |

What it does **not** enforce: the 100-column limit, the order inside the final
declaration group, and the naming/case rules. Those are review conventions that
need a lint, and `kelpc` has no `lint` command.

Path handling, as `--help` documents it:

- A path may be a `.kp` file or a directory, and a directory recurses.
- A **symbolic link given by name** is followed to the file it names, so `-w`
  rewrites that file and the link survives. A link **found inside a directory** is
  skipped and reported.
- A path that is not a regular file (a FIFO, a socket, a device) is refused before
  it is read, so `fmt` never waits on a node that has no data and never replaces
  one.
- A rewritten file is a **new inode** — a hard link to it keeps the old bytes.
- A file that does not parse — by `fmt`'s own reading of it, or by the compiler's
  when the project's aliases are needed — is reported as a parse error and left
  alone.

```
$ kelpc fmt bad.kp                 # prints the formatted source
fun main() {
    print("hi")
}

$ kelpc fmt --check bad.kp
error: 'bad.kp' is not formatted    # exit status 1

$ kelpc fmt -w bad.kp
$ kelpc fmt --check bad.kp          # exit status 0
```

`--check` is the CI shape: it writes nothing and exits nonzero on the first file
that differs.

## Environment variables

| Variable | Effect |
| --- | --- |
| `KELPC_BACKEND` | default backend (`c` or `asm`); an explicit `--backend=` wins |
| `KELPC_GLIBC_DIR` | where the `asm` backend finds `crt1.o` and `libc.so` |

## Projects

`kelpc` compiles a loose `.kp` file as its own module root, and a directory with a
`coral.toml` as a project — see
[Projects and coral.toml](../getting-started/projects.md). Coral drives the same
binary as a subprocess, so anything you can do here you can also do from a
`[tasks]` entry.

## See also

- [Install and build](../getting-started/install.md)
- [Coral](coral.md) — the project layer on top
- [Tooling](index.md) — how the three pieces divide the work
