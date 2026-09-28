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
| LLVM 21 development (`llvm-config`, `include/llvm-c`) | building `kelpc`: it depends on `llvm-sys`, whose build step locates `libLLVM`. The repository's `shell.nix` provides this and sets `LLVM_SYS_211_PREFIX` |
| `libLLVM-21.so` | running a `kelpc` built this way: the `llvm` backend links it dynamically and the binary does not start without it |
| a C compiler and glibc | linking: `cc` links the object the `llvm` backend emits, and it is the compiler the C oracle's own path uses |
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

With no `-o`, the binary and its generated files land in `build/` in the
**current working directory**, named after the last path segment compiled. The
backend leaves `<name>.ll` (textual IR) and `<name>.o` (the object) beside it.
So `kelpc build myproject/` writes `build/myproject`,
`build/myproject.ll` and `build/myproject.o`, and `kelpc build src/main.kp`
writes `build/main`. Pass `-o` when that is not where you want it, and pass
`-O0` for a cheap dev build (`-O2` is the default).

## Install Coral with Nix

Coral carries an official `flake.nix` at its repository root, so a machine with
flakes enabled needs no Rust toolchain to build it:

```sh
nix run git+https://homelabone.xenoo.dev/gittea/Juniper/coral -- version
nix build git+https://homelabone.xenoo.dev/gittea/Juniper/coral
./result/bin/coral version
```

A tag is a flake ref like any other, and the file fetches the source it is built
from: `nix build git+https://homelabone.xenoo.dev/gittea/Juniper/coral?ref=v26.09.4`
builds that release. From a checkout, `.` is the same flake:

```sh
nix build .#coral              # result/bin/coral
nix run . -- version
nix develop                    # cargo and rustc, at the revision the flake pins
```

The flake pins `nixos-26.05`. It reads the package version from `Cargo.toml`
rather than repeating it, so a release bump moves the package with it, and it
runs Coral's unit tests as part of the build.

`kelpc` is deliberately **not** part of it. Coral manages the compiler itself,
and `coral toolchain kelp install <ver>` is how one arrives, so pinning a second
compiler in the flake would be a second answer to the same question. Build the
compiler from source with the steps above, or let Coral fetch a release asset
(see [Toolchains](/tooling/coral#toolchains)).

## Backends

`kelpc` builds every program with one backend, **`llvm`**: it lowers the typed IR
to LLVM IR, runs LLVM's own pass pipeline over the module at the build's
optimization level, emits an object and hands it to `cc`. There is no backend to
choose, and no `--backend=` flag and no `KELPC_BACKEND`: both are refused, with a
diagnostic that says the choice is gone.

```text
error: --backend is gone: kelpc builds every program with the llvm backend, and the C backend is kept as the project's own oracle rather than as a user choice
```

The **`c` backend** ([Backends](/compiler/backends)) is kept, maintained and run
in the suite as the **project's own oracle**. It
transpiles to C and hands the file to `cc -O2 -fwrapv -lm`, and the fixture
suite, the differential sweep and the fuzzer compare every `llvm` build against
it. It is the reference backend rather than a second opinion, and it is not a
user surface: no flag and no environment variable selects it, and the project's
own suite reaches it through an internal switch.

The `llvm` backend lowers the whole language the [Language](/language) pages
describe to LLVM IR and an object: the scalar types, `datac` records, `enum` and
`when`, `Bytes`/`String`
and the drop plan, `List`/`Map`/`Box`/`[T; N]`, references, closures and function
values, the `extern fun` bodies, the `pd` globals and the capability check. It
builds every target the C backend builds and its stdout and exit status match the
C backend's byte for byte over the corpus (223 of 223 targets, the refusal ranking
empty). One guard remains in the lowering, for an owned temporary at a place it
did not stage, and nothing in the corpus reaches it.

`build` and `run` take an optimization level: `-O0`, `-O1`, `-O2`, `-O3` or `-Os`,
with `-O2` the default. One level is one level for the whole build: it selects the
LLVM pass pipeline and the target machine's codegen level, and it is the `-O` flag
the per-program C object and the final link are given. `-Oz` is refused because it
is a clang-only spelling and the linking `cc` may be gcc; `-Os` is the size level.

Every `kelpc` links `libLLVM-21.so` and needs it at runtime.

```sh
./target/release/kelpc build -O3 examples/hello.kp
```

`kelpc version` prints the compiler version. `kelpc check` answers whether a
program compiles without writing an artifact (`kelpc check --json` answers with a
document instead of prose). `kelpc fmt` formats sources (see
[`kelpc` CLI](/tooling/kelpc-cli)).

## Environment variables

| Variable | Effect |
| --- | --- |
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
runs the result, and compares stdout, so the suite exercises any backend by being
pointed at it. It runs `llvm` by default and the C oracle through the project's
internal switch, which is not a user surface, and both are green.
`run-all-backends.sh` runs both by default (its `BACKENDS` list is `c llvm`). The
byte-identical gates are the separate `run-llvm-scalar-subset.sh`,
`run-llvm-datac-subset.sh`, `run-llvm-strings-drops.sh`,
`run-llvm-enum-subset.sh`, `run-llvm-containers.sh`,
`run-llvm-references.sh`, `run-llvm-closures.sh`,
`run-llvm-externs.sh` and `run-llvm-pd-caps.sh`. The differential sweep,
`kelpc/tests/backend_coverage.rs`, is `#[ignore]`d because it compiles the whole
corpus twice; it is the check that the `llvm` backend builds every target the C
backend builds and prints the same stdout with the same exit status; at the MK7 S5
tip it builds all 223 targets the C backend builds, with an empty refusal ranking:

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
- [Coral](/tooling/coral), including the `nix build` above
- [Compiler architecture](/compiler)
