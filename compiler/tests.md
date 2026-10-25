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
```

There is one backend, so there is no script that runs the suite once per backend.

## The fixture suite (`tests/compile_and_run/`)

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

A compiled-and-run fixture keeps its expected stdout at the end of the file, in a trailer of comment lines:

```
// stdout-begin
// stdout: hello, world
// stdout:
// stdout:  an indented line keeps its extra space
```

`// stdout-begin` starts the trailer. Each `// stdout:` line after it is one line of output: the text after the single space that follows the colon is printed as written, and a bare `// stdout:` is an empty line. A fixture with no output has `// stdout-begin` and nothing after it. The Rust test names the file only, with `assert_fixture_runs("tests/fixtures/name.kp")`, and the harness reads the trailer.

The rejected group is what shows that the move and borrow checker works.
The projects cover the capability cases: a granted path, a path outside the grant, a symlink that leads outside it, an over-delegation that must be refused, and a `..` pattern refused at the `impl` line.

Two checks run inside this file:

- **A loopback HTTP server.** The HTTP tests bind a server on port 0 in the harness and pass the port to the program.
  The server counts the accepted connections, so a test can check that a pool reused a socket.

## Backend gates

Each `run-llvm-*.sh` script runs one slice of the fixtures on the LLVM backend, and compares stdout with the expected output.
Some of them also read the generated `.ll` file to check an instruction or a layout.
The scripts are `run-llvm-scalar-subset.sh`, `run-llvm-datac-subset.sh`, `run-llvm-strings-drops.sh`, `run-llvm-enum-subset.sh`, `run-llvm-containers.sh`, `run-llvm-references.sh`, `run-llvm-closures.sh`, `run-llvm-externs.sh` and `run-llvm-pd-caps.sh`.
`run-llvm-levels.sh` builds each corpus target at `-O0` and at each higher level, and requires the same output at every level. Its full sweep is an ignored test in `level_differential.rs`.

The ABI check for by-value aggregates is a Rust witness, `abi_aggregate.rs`. It links a Rust caller and callee with `repr(C)` structs against the Kelp object. It replaces the C fixture that was compiled before.

`llvm_debug_info.rs` builds `tests/llvm-debug/fault.kp`, which divides by a run-time zero.
It reads the line table of the binary and checks that the fault is reported at the `.kp` line.

## The backend coverage sweep (`backend_coverage.rs`)

`backend_coverage.rs` covers the `llvm` backend alone: the coverage of the fixtures, the refusal ranking and the crash check.
It was written to compare two backends. The C backend that was the second side was removed on 2026-10-10, so the comparison is gone.
The frozen golden set in `kelpc/tests/golden/` is the reference for the corpus that remains (`golden_corpus.rs`).

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

Older runtime tests compared a Kelp port with a C reference file. No C file is in the tree, so those comparisons have no second side now.
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


## Compile-time scaling

Moved here from the retired `plan/scaling.md`. The text is kept as the record it was.

`kelpc/tests/scaling.rs` generates large programs (method chains, nested
calls, nested generics, nested blocks and function literals, long `+`/`&&`
chains, a 5,000-element list literal, long templates, a 300-arm `elif` ladder,
a 200-field datac, 300 statements) and runs `check`, `fmt`, `lint`, `doc` and
`build` on both backends over each, then runs both binaries. A step over 20 s
fails the test.

### The bug that was fixed

Type checking a method call inferred its receiver twice: once with no
expectation, to learn the receiver's type for method lookup, and again as the
`self` argument. In `a.f().f().f()...` each link therefore doubled the work of
the link below it (0.4 s at 16 links, 21 s at 22, a chain of 400 never ended).
Calls of generic functions and generic `datac`/`enum` constructions did the
same with their arguments (arguments probed for type inference, then checked
again against the instantiated signature), so `id(id(id(...)))` and
`W(v = W(v = ...))` were exponential too.

`Ctx::probes` now keeps the first result; `check_call_arg` reuses it when the
type is exactly the type the argument is expected to have, and checks again
(the old behaviour) otherwise. Entries are keyed by expression address and
span, consumed on use, and dropped whenever the checking that made them fails,
so a retry (the scoped-block exclusive-capture retry, a swallowed error) never
sees a stale one. No accepted or refused program and no diagnostic changed.

### Measured after the fix (debug build, this machine)

Nothing else was super-linear in `check`, `fmt`, `lint`, `doc`, or the C
backend. Every shape finishes each step in about a second or less except:

| input | step | time |
| --- | --- | --- |
| list literal, 5,000 elements | `build`, LLVM, -O2 | 4.0-4.6 s |
| list literal, 2,500 elements | `build`, LLVM, -O2 | 1.0 s |
| list literal, 1,250 elements | `build`, LLVM, -O2 | 0.5 s |
| 150 chained closures `val f_i = fun(x) = f_(i-1)(x) + 1` | `build`, C oracle | 1.6-2.2 s |
| 50 nested generic enum constructions | `build`, LLVM | 1.1-1.5 s |
| 150 chained closures | `build`, LLVM | 1.0 s |

Only the first row is super-linear: the time is quadratic in the length and
sits inside LLVM's optimizer, which is given the literal as one first-class
`[N x i32]` aggregate value (-O0 takes 0.85 s for 5,000 elements). The all
constant literal is now emitted as a single constant array instead of N
`insertvalue`s, which halved -O0 and left -O2 unchanged. Emitting a constant
array as a private global plus a copy would remove the rest; it was left alone
because it changes the shape of the IR every array literal produces.

The other rows scale linearly (the 150-closure and generic-enum timings double
when the size does).

### Limits that bound the rest

The parser refuses more than 800 links in a chain and more than 200 levels of
nesting ([`tooling/fuzzing.md`](/tooling/fuzzing)), so a 400-link chain, 90 nested calls and 60 nested
`if` blocks are about the largest shapes a program can reach; both limits were
kept.
