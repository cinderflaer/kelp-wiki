---
title: "Install and build"
description: "The binary lands at target/release/kelpc."
isPublished: true
tags: "getting-started"
---
## Requirements

| Component | Needed for |
| --- | --- |
| Rust, 2024 edition (rustc 1.85 or newer) | building `kelpc` |
| LLVM 21 development (`llvm-config`, `include/llvm-c`) | building `kelpc`: it depends on `llvm-sys`, whose build step locates `libLLVM`. The repository's `shell.nix` provides this and sets `LLVM_SYS_211_PREFIX` |
| `libLLVM-21.so` | running a `kelpc` built this way: the `llvm` backend links it dynamically and the binary does not start without it |
| a C compiler and glibc | both backends: `c` compiles the generated C, and `llvm` links its object with `cc` |
| `valgrind` (optional) | the memory gate test |
| [Coral](/tooling/coral) (recommended) | the build tool and package manager: projects, dependencies, tasks, toolchain pins. One `coral.toml`, and it calls `kelpc` for you |

## Build the compiler

```sh
git clone https://homelabone.xenoo.dev/gittea/Juniper/kelp
cd kelp
nix-shell shell.nix          # LLVM 21 development output, and LLVM_SYS_211_PREFIX
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

With no `-o`, the binary and its generated file land in `build/` in the
**current working directory**, named after the last path segment compiled. The
file is `<name>.c` for the default `c` backend, and `<name>.ll` plus `<name>.o`
for `llvm`. So `kelpc build myproject/` writes `build/myproject` and
`build/myproject.c`, and `kelpc build src/main.kp` writes `build/main`. Pass `-o`
when that is not where you want it.

## Backends

A code generator is selectable with `--backend=` or the `KELPC_BACKEND`
environment variable:

| Backend | What it does | Chain |
| --- | --- | --- |
| `c` (default) | transpiles to C | `cc -O2 -fwrapv -lm` |
| `llvm` | lowers the whole language to LLVM IR and an object | `cc -O2 -o <out> <out>.o -lm` |

The hand-written `asm` backend was retired on 2026-09-20 and removed on
2026-09-21, so `--backend=asm` now reports `unknown backend 'asm'; expected one
of: c, llvm`. Its history is in
[`plan/asm-backend/`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/).

The **`llvm`** backend
([`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md))
lowers the whole language the [Language](/language) pages describe to LLVM IR and
an object: the scalar types, `datac` records, `enum` and `when`, `Bytes`/`String`
and the drop plan, `List`/`Map`/`Box`/`[T; N]`, references, closures and function
values, the `extern fun` bodies, the `pd` globals and the capability check. It
builds every target the C backend builds and its stdout and exit status match the
C backend's byte for byte over the corpus (221 of 221 targets, the refusal ranking
empty). One guard remains in the lowering, for an owned temporary at a place it
did not stage, and nothing in the corpus reaches it. `c` stays the default, the
oracle and the way out. There is no IR optimization pass pipeline yet, so no
performance parity with the C backend is claimed, and the default has not moved.
Every `kelpc` links `libLLVM-21.so` and needs it at
runtime, whichever backend it is run with.

```sh
KELPC_BACKEND=c ./target/release/kelpc run examples/hello.kp   # the default, spelled out
```

`kelpc version` prints the compiler version. `kelpc check` answers whether a
program compiles without writing an artifact (`kelpc check --json` answers with a
document instead of prose). `kelpc fmt` formats sources (see
[`kelpc` CLI](/tooling/kelpc-cli)).

## Environment variables

| Variable | Effect |
| --- | --- |
| `KELPC_BACKEND` | default backend (`c`; `llvm` is selectable too); an explicit `--backend=` wins |
| `LLVM_SYS_211_PREFIX` | where `llvm-sys` finds `libLLVM` and its headers; set by `shell.nix` |

## Tests

```sh
cargo test                                   # unit tests + the fixture suite
cargo test --test fmt                        # the formatter's corpus and properties
./kelpc/tests/run-all-backends.sh            # the suite once per implemented backend
./kelpc/tests/run-llvm-scalar-subset.sh      # the llvm scalar subset
./kelpc/tests/run-llvm-datac-subset.sh       # the datac slice
./kelpc/tests/run-llvm-strings-drops.sh      # the heap slice
./kelpc/tests/run-llvm-enum-subset.sh        # the tagged-union slice
./kelpc/tests/run-llvm-containers.sh         # the container slice (103 tests)
./kelpc/tests/run-llvm-references.sh         # the reference slice (109 tests)
./kelpc/tests/run-llvm-closures.sh           # the closure and function-value slice (120 tests)
./kelpc/tests/run-llvm-externs.sh            # the extern fun slice (138 tests)
./kelpc/tests/run-llvm-pd-caps.sh            # the pd globals and capability slice (38 tests)
```

The fixture suite is backend-agnostic by construction: it compiles a fixture,
runs the result, and compares stdout, so pointing `KELPC_BACKEND` at a backend
validates it with no test edits. `run-all-backends.sh` is still `BACKENDS=c` by
default, so `BACKENDS="c llvm" ./kelpc/tests/run-all-backends.sh` runs both. The
byte-identical gates are the separate `run-llvm-scalar-subset.sh`,
`run-llvm-datac-subset.sh`, `run-llvm-strings-drops.sh`,
`run-llvm-enum-subset.sh`, `run-llvm-containers.sh`,
`run-llvm-references.sh`, `run-llvm-closures.sh`,
`run-llvm-externs.sh` and `run-llvm-pd-caps.sh`. The differential sweep,
`kelpc/tests/backend_coverage.rs`, is `#[ignore]`d because it compiles the whole
corpus twice; it is the check that the `llvm` backend builds every target the C
backend builds and prints the same stdout with the same exit status; at the S3 tip
it builds all 221 targets the C backend builds, with an empty refusal ranking:

```sh
cargo test --release --test backend_coverage -- --ignored --nocapture
```

Two heavier checks are `#[ignore]`d so the default run stays fast:

```sh
cargo test --test memory_gate      -- --ignored               # valgrind over the binaries
cargo test --test cap_matcher      -- --ignored               # capability matcher vs C
```

`bench/speed/run.sh` times four workloads written in four languages and checks
their checksums.

## See also

- [Set up your editor](/getting-started/editor)
- [Your first program](/getting-started/first-program)
- [`kelpc` CLI](/tooling/kelpc-cli)
- [Compiler architecture](/compiler)
