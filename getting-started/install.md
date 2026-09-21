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

With no `-o`, the binary and the generated C land in `build/` in the
**current working directory**, named after the last path segment compiled. So
`kelpc build myproject/` writes `build/myproject` and `build/myproject.c`, and
`kelpc build src/main.kp` writes `build/main`. Pass `-o` when that is not where
you want it.

## Backends

One code generator is selectable with `--backend=` or the `KELPC_BACKEND`
environment variable:

| Backend | What it does | Chain |
| --- | --- | --- |
| `c` (default) | transpiles to C | `cc -O2 -fwrapv -lm` |

The hand-written `asm` backend was retired on 2026-09-20 and removed on
2026-09-21, so `--backend=asm` now reports `unknown backend 'asm'; expected one
of: c`. Its history is in
[`plan/asm-backend/`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/).

The next backend is **LLVM IR**
([`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md)):
`kelpc` will emit LLVM IR and let LLVM optimize and generate the object, the way
`rustc` does. Everything up to the typed IR is reused, so it is weeks of
emission-layer work rather than a project, and LLVM supplies the optimizer, the
encoder, the ELF writer, the debug-info format, sanitizers and the targets. The
repository's `shell.nix` provides the LLVM development output that `llvm-sys`
needs to build against: `nix-shell` puts `llvm-config` and the C API headers on
the path and sets `LLVM_SYS_211_PREFIX`.

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
| `KELPC_BACKEND` | default backend (`c` today, `llvm` once it lands); an explicit `--backend=` wins |
| `LLVM_SYS_211_PREFIX` | where `llvm-sys` finds `libLLVM` and its headers; set by `shell.nix` |

## Tests

```sh
cargo test                                   # unit tests + the fixture suite
cargo test --test fmt                        # the formatter's corpus and properties
./kelpc/tests/run-all-backends.sh            # the suite once per implemented backend
```

The fixture suite is backend-agnostic by construction: it compiles a fixture,
runs the result, and compares stdout, so pointing `KELPC_BACKEND` at a backend
validates it with no test edits. Two heavier checks are `#[ignore]`d so the
default run stays fast:

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
