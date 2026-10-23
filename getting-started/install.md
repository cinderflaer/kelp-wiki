---
title: "Install and build"
description: "Building `kelpc` from source and the requirements it has of the machine, installing Coral with its Nix flake, and the test suites."
isPublished: true
tags: "getting-started"
---
## Requirements

| Component | Needed for |
| --- | --- |
| Rust, 2024 edition (rustc 1.85 or newer) | building `kelpc` |
| `cc` | building `kelpc`: cargo links the Rust binaries with it. `kelpc` does not run it to compile or link a program |
| LLVM 21 development (`llvm-config`, `include/llvm-c`) | building `kelpc`: it depends on `llvm-sys`, whose build step locates `libLLVM`. The repository's `shell.nix` provides this and sets `LLVM_SYS_211_PREFIX` |
| `libLLVM-21.so` | running a `kelpc` built this way: the `llvm` backend links it dynamically and the binary does not start without it |
| OpenSSL libraries (`libssl`, `libcrypto`) | building a program that reaches [`std/tls`](/stdlib/tls), which `std/http` and `std/ws` do: `kelpc` puts `-lssl -lcrypto` on that program's link line |
| OpenSSL development output (the `libssl` and `libcrypto` link files) | the same programs: `ld.lld` links `-lssl -lcrypto`, so the development links must exist. No header is read. |
| glibc | `ld.lld` links the object the `llvm` backend emits, against glibc's start files and libraries. No C compiler is run. |
| `valgrind` (optional) | the memory gate test |
| [Coral](/tooling/coral) (recommended) | the build tool and package manager: projects, dependencies, tasks, and the compiler install. One `coral.toml`, and it calls `kelpc` for you |

A program that reaches neither `std/tls`, `std/http` nor `std/ws` needs no
OpenSSL at all: `hello` builds on a host without it. `nix-shell shell.nix`
provides the pair for the programs that do, and its `packages` list is the place
to copy it from.

## Build the compiler

```sh
git clone https://homelabone.xenoo.dev/gittea/Lilly/kelp
cd kelp
nix-shell shell.nix          # LLVM 21 dev, LLVM_SYS_211_PREFIX, OpenSSL dev
cargo build --release -p kelpc
```

The binary lands at `target/release/kelpc`.

A prebuilt release binary installs with the verifying `build/install.sh` instead
(see [Release tooling](/tooling/release-tooling)).

## Run a file

```sh
./target/release/kelpc run kelpc/tests/fixtures/examples/hello.kp
```

`run` compiles and executes in one step. To keep the artifact:

```sh
./target/release/kelpc build kelpc/tests/fixtures/examples/download.kp      # artifact in build/download
```

Through Coral the same two commands are `coral run` and `coral build`, run inside
a project directory. Worth starting there at the first program rather than the
first dependency, so the manifest is familiar before it has to be: `coral init`
scaffolds one, and [Projects and coral.toml](/getting-started/projects) explains
what lands in it.

With no `-o`, the binary and its generated files land in `build/` in the
**current working directory**, named after the last path segment compiled. The
backend leaves `<name>.ll` (textual IR) and `<name>.o` (the object) beside it.
So `kelpc build myproject/` writes `build/myproject`,
`build/myproject.ll` and `build/myproject.o`, and `kelpc build src/main.kp`
writes `build/main`. Pass `-o` when that is not where you want it, and pass
`-O0` for a cheap dev build (`-O2` is the default).

## Install Coral

Coral is a Kelp program with no dependencies, so the compiler builds it:

```sh
git clone https://homelabone.xenoo.dev/gittea/Lilly/coral
cd coral
kelpc build src/main.kp -o coral
./coral version
```

Coral's `main` branch has no Nix flake. The flake that builds Coral is on the
`v26.09.4` tag, which is the older Rust build, so it is not the way to get the Kelp
port. Once `coral` is on your `PATH`, `coral toolchain kelp update` installs the
newest Kelp compiler release into `~/.coral/toolchains/` and links
`~/.coral/bin/kelpc` to it (see [Toolchains](/tooling/coral#toolchains)). That is
how most people get `kelpc`, so the source build above is only needed to bootstrap
Coral itself.

## Backends

`kelpc` builds every program with one backend, **`llvm`**.
It lowers the typed IR to LLVM IR, runs LLVM's pass pipeline over the module at the build's optimization level, and writes an object.
`kelpc` then links that object with `ld.lld`.
No C compiler is used. The extern object a program needs for an `extern fun` or a capability-gated call is LLVM IR, written by the same target machine as the program.

There is no backend to choose.
The `--backend=` flag, `KELPC_BACKEND` and `KELPC_ORACLE` are refused by name, with a diagnostic that says the choice is gone.

The `llvm` backend lowers the whole language the [Language](/language) pages describe to LLVM IR and an object: the scalar types, `datac` records, `enum` and `when`, `Bytes`/`String` and the drop plan, `List`/`Map`/`Box`/`[T; N]`, references, closures and function values, the `extern fun` bodies, the `pd` globals and the capability check.
One guard remains in the lowering, for an owned temporary at a place it did not stage, and nothing in the corpus reaches it.

`build` and `run` take an optimization level: `-O0`, `-O1`, `-O2`, `-O3` or `-Os`, with `-O2` the default.
One level is one level for the whole build: it selects the LLVM pass pipeline and the target machine's codegen level, and it is the codegen level of the extern object as well.
`-Oz` is refused. `-Os` is the size level.

Every `kelpc` links `libLLVM-21.so` and needs it at runtime.

## Environment variables

| Variable | Effect |
| --- | --- |
| `LLVM_SYS_211_PREFIX` | where `llvm-sys` finds `libLLVM` and its headers; set by `shell.nix` |

## Tests

```sh
cargo test                                   # unit tests + the fixture suite
cargo test --test fmt                        # the formatter's corpus and properties
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

The fixture suite compiles each fixture, runs the result, and compares stdout.
The `run-llvm-*.sh` scripts are slice gates over parts of the fixture corpus.

Two heavier checks are `#[ignore]`d so the default run stays fast:

```sh
cargo test --test memory_gate      -- --ignored               # valgrind over the binaries
```

`bench/speed/run.sh` times four workloads written in four languages and checks
their checksums.

## See also

- [Set up your editor](/getting-started/editor)
- [Your first program](/getting-started/first-program)
- [`kelpc` CLI](/tooling/kelpc-cli)
- [Coral](/tooling/coral), including the `nix build` above
- [Compiler architecture](/compiler)
