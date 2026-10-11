---
title: "Tests"
description: "The compiler test suite compiles programs, runs them and compares their output. Covers the fixture harness, the backend gates, the fuzzers, and which tests are ignored by default."
isPublished: true
tags: "compiler, testing"
---
Most compiler tests compile a program, run it and compare what it printed.
A test therefore states what the language does, not how a backend does it.
The tests run against the LLVM backend, the only code generator.

```sh
cargo test                                   # unit tests and the fixture suite
cargo test --test fmt                        # the formatter's corpus and properties
./kelpc/tests/run-all-backends.sh            # the fixture suite once per backend
```

`run-all-backends.sh` reads `BACKENDS`, which defaults to `c llvm`.

## The fixture suite (`tests/compile_and_run.rs`)

The harness runs the real `kelpc` binary on two sets of inputs.

| Input | Shape |
| --- | --- |
| `tests/fixtures/*.kp` | One loose file for each single-file test. |
| `tests/projects/<name>/` | A directory for each multi-file test, such as a module graph or a grant. |

Each fixture falls into one of three groups.

| Group | What the harness checks |
| --- | --- |
| Compiled and run | The output on stdout matches an exact value. |
| Compiled and run, expected to fail | The program panics with a specific message. |
| Rejected by the compiler | The compiler reports a specific diagnostic. |

The rejected group is what shows that the move and borrow checker works.
The projects cover the capability cases: a granted path, a path outside the grant, a symlink that leads outside it, an over-delegation that must be refused, and a `..` pattern refused at the `impl` line.

Two checks run inside this file:

- **A loopback HTTP server.** The HTTP tests bind a server on port 0 in the harness and pass the port to the program.
  The server counts the accepted connections, so a test can check that a pool reused a socket.

## Backend gates

Each `run-llvm-*.sh` script runs one slice of the fixtures on the LLVM backend, and compares stdout with the expected output.
Some of them also read the generated `.ll` file to check an instruction or a layout.
The scripts are `run-llvm-scalar-subset.sh`, `run-llvm-datac-subset.sh`, `run-llvm-strings-drops.sh`, `run-llvm-enum-subset.sh`, `run-llvm-containers.sh`, `run-llvm-references.sh`, `run-llvm-closures.sh`, `run-llvm-externs.sh`, `run-llvm-pd-caps.sh` and `run-llvm-abi.sh`.

`llvm_debug_info.rs` builds `tests/llvm-debug/fault.kp`, which divides by a run-time zero.
It reads the line table of the binary and checks that the fault is reported at the `.kp` line.

## The backend coverage sweep (`backend_coverage.rs`)

`backend_coverage.rs` was written to build every fixture with two backends and compare them.
The C backend has been removed, so the test no longer has a second side to compare against.
The golden outputs in `kelpc/tests/golden/` are the record that remains.

## Fuzzing (`differential_fuzz.rs`, `frontend_fuzz.rs`)

`differential_fuzz.rs` generates a Kelp program from a seed.
The generator uses a fixed pseudo-random number generator, so the same seed always gives the same program.
Each program is written to a file and built. There is no second backend to compare it with.
`FUZZ_SEED_START` and `FUZZ_SEED_COUNT` choose the seeds.
The default run uses one seed, and the larger runs are ignored.
`tests/fuzz-corpus/` holds frozen seeds that are run the same way.

A mismatch is a defect in a backend.
The fix is in the backend, not in the generator.

`frontend_fuzz.rs` mutates fixtures and runs `kelpc check` on them.
It checks that nothing panics, aborts or hangs.

## Memory checks (`memory_gate.rs`)

`memory_gate.rs` runs valgrind over the built binaries and checks the log for findings.
It is ignored by default.
Valgrind runs on any binary.

## Runtime reference tests

Older tests compared a Kelp port with a C reference file, using the same generated cases on both sides.
The C reference files are not in the tree, and `kelpc/runtime/` holds no `*_ref.c` file.
So these comparisons have no second side now.
The `kelpc/runtime/` folder keeps `dns_parse.kp` and `resolver_conf.kp`.

## The formatter and the linter

`fmt.rs` tests the formatter with the corpus in `tests/fmt_corpus/` and with properties.
Formatting an already formatted file changes nothing.
The token kinds and their text are the same before and after.
Comments survive.

`lint.rs` and `doc.rs` test the linter and the documentation generator.
`check.rs` tests the output of `kelpc check`, including the JSON form.

## Benchmarks

The speed and write benchmarks are described on the [Benchmarks](/compiler/benchmarks) page.

## See also

- [Pipeline](/compiler/architecture)
- [Backends](/compiler/backends)
- [Runtime](/compiler/runtime)
- [Install and build](/getting-started/install)
