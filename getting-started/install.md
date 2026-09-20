---
title: "Install and build"
description: "The binary lands at target/release/kelpc."
isPublished: true
tags: "getting-started"
---
## Requirements

| Component | Needed for |
| --- | --- |
| Rust, 2024 edition (rustc 1.85 or newer) | building `kelpc`, which has no third-party dependencies |
| a C compiler and glibc | the default `c` backend |
| `as`, `ld` (binutils) and the glibc they link against | the `asm` backend |
| `valgrind` (optional) | the memory gate test |
| [Coral](/tooling/coral) (recommended) | the build tool and package manager: projects, dependencies, tasks, toolchain pins. One `coral.toml`, and it calls `kelpc` for you |

## Build the compiler

```sh
git clone https://homelabone.xenoo.dev/gittea/Juniper/kelp
cd kelp
cargo build --release -p kelpc
```

The binary lands at `target/release/kelpc`.

## Run a file

```sh
./target/release/kelpc run examples/hello.kp
```

`run` compiles and executes in one step. To keep the artifact:

```sh
./target/release/kelpc build examples/download.kp      # artifact in build/download
```

Through Coral the same two commands are `coral run` and `coral build`, run inside
a project directory. Worth starting there at the first program rather than the
first dependency, so the manifest is familiar before it has to be: `coral init`
scaffolds one, and [Projects and coral.toml](/getting-started/projects) explains
what lands in it.

With no `-o`, the binary and the generated C (or assembly) land in `build/` in the
**current working directory**, named after the last path segment compiled. So
`kelpc build myproject/` writes `build/myproject` and `build/myproject.c`, and
`kelpc build src/main.kp` writes `build/main`. Pass `-o` when that is not where
you want it.

## Backends

Two code generators are selectable with `--backend=` or the `KELPC_BACKEND`
environment variable:

| Backend | What it does | Chain |
| --- | --- | --- |
| `c` (default) | transpiles to C | `cc -O2 -fwrapv -lm` |
| `asm` | emits x86-64 assembly itself | `as`, `ld`: no C compiler |

```sh
./target/release/kelpc build examples/hello.kp --backend=asm
KELPC_BACKEND=asm ./target/release/kelpc run examples/hello.kp
```

The C backend is the reference: every fixture is built by both and the two
binaries' stdout is compared, so a construct the `asm` backend does not lower yet
is **refused by name** rather than silently miscompiled:

```
error: the 'asm' backend does not support the `extern fun std.process.arg_count_raw` yet
```

`kelpc version` prints the compiler version. `kelpc check` answers whether a
program compiles without writing an artifact (`kelpc check --json` answers with a
document instead of prose). `kelpc fmt` formats sources (see
[`kelpc` CLI](/tooling/kelpc-cli)).

If the `asm` backend cannot find the library directory it needs, point
`KELPC_GLIBC_DIR` at the directory holding `crt1.o` and `libc.so`.

## Environment variables

| Variable | Effect |
| --- | --- |
| `KELPC_BACKEND` | default backend (`c` or `asm`); an explicit `--backend=` wins |
| `KELPC_GLIBC_DIR` | where the `asm` backend finds `crt1.o` and `libc.so` |

## Tests

```sh
cargo test                                   # unit tests + the fixture suite
cargo test --test fmt                        # the formatter's corpus and properties
KELPC_BACKEND=asm cargo test --test compile_and_run
BACKENDS="c asm" ./kelpc/tests/run-all-backends.sh
```

The fixture suite is backend-agnostic by construction: it compiles a fixture,
runs the result, and compares stdout, so pointing `KELPC_BACKEND` at a backend
validates it with no test edits. Three heavier checks are `#[ignore]`d so the
default run stays fast:

```sh
cargo test --test backend_coverage -- --ignored --nocapture   # differential sweep
cargo test --test memory_gate      -- --ignored               # valgrind, both backends
cargo test --test cap_matcher      -- --ignored               # capability matcher vs C
```

`bench/speed/run.sh` times four workloads written in four languages and checks
their checksums.

## See also

- [Set up your editor](/getting-started/editor)
- [Your first program](/getting-started/first-program)
- [`kelpc` CLI](/tooling/kelpc-cli)
- [Compiler architecture](/compiler)
