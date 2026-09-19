---
title: "Tests"
description: "The suite is built on one idea - compile a program, run it, compare what it printed. Nothing asserts on generated C, so a test says what the language does rather than how a backend does it, and..."
isPublished: true
tags: "compiler, testing"
---
The suite is built on one idea: **compile a program, run it, compare what it
printed**. Nothing asserts on generated C, so a test says what the language does
rather than how a backend does it, and that is what lets the same suite validate
a second backend.

```sh
cargo test                                   # unit tests + the fixture suite
KELPC_BACKEND=asm cargo test --test compile_and_run
BACKENDS="c asm" ./kelpc/tests/run-all-backends.sh
```

## The fixture suite (`kelpc/tests/compile_and_run.rs`)

289 tests (measured 2026-09-19), driving the real `kelpc` binary over two corpora:

| Corpus | Count | Shape |
| --- | --- | --- |
| `kelpc/tests/fixtures/*.kp` | 302 files | one loose file per single-file test |
| `kelpc/tests/projects/<name>/` | 45 directories | multi-file: a module graph needs a directory, and a granted module needs an importer |

Every fixture lands in exactly one of three groups, because the harness does three
different things with them:

| Group | What the harness asserts |
| --- | --- |
| Compiled and run | stdout matches an exact expected value |
| Compiled and run, expected to fail | the program panics with a specific message: the panic texts are golden |
| Rejected by the compiler | specific compiler diagnostics: moves, borrows, escapes, unsupported types, a bad grant, a bad `impl` path |

The rejected group is the real proof that the move/borrow checker works rather
than merely that well-behaved programs compile. The multi-file projects carry the
capability cases: a granted path, a path outside the grant, a symlink escape, an
over-delegation that must be refused, a `..` pattern refused at the `impl` line,
the `net` host as written, a program path under `process`, and the HTTP projects
that exercise pooling and redirects against a loopback server the harness binds on
port 0 and passes to the program through argv.

Two gates run inside this file:

- **AddressSanitizer.** `heap_fixtures_are_double_free_and_leak_clean` rebuilds
  every fixture that owns memory with `-fsanitize=address -O1` and runs it, so a
  double free, a use-after-free or a leak fails the suite. This is what turns
  "drops happen" into a test result. It skips itself where `cc` has no
  AddressSanitizer, and a fixture that panics *on purpose* is excluded, because it
  is expected to leave its buffers behind.
- **A loopback HTTP server**, because an HTTP client blocks inside `send` and so
  cannot be both client and server in one process. The helper asserts how many
  connections were accepted, which is how "the pool reused the socket" becomes a
  direct assertion rather than a timing inference.

## Backend gates

| Test file | What it does | Default run |
| --- | --- | --- |
| `kelpc/tests/run-all-backends.sh` | runs the fixture suite once per backend (`BACKENDS`, default `c`) | a shell script, not a cargo test |
| `backend_coverage.rs` | the differential sweep: builds every fixture the C backend builds with `--backend=asm` too, runs both, and requires byte-identical stdout and exit status; a refusal must begin with the documented prefix; also records the refusal ranking so coverage numbers cannot drift silently | the sweep is ignored; one cheap baseline check runs |
| `memory_gate.rs` | valgrind (`--leak-check=full --show-leak-kinds=all`, diagnostics to `--log-file`) over both backends' binaries, asserting no findings in any process; a spawned child inherits valgrind, so it writes into the same log | ignored; the default run only checks that valgrind is discoverable |

```sh
cargo test --test backend_coverage -- --ignored --nocapture   # differential sweep + refusal ranking
cargo test --test memory_gate    -- --ignored                 # valgrind over both backends
```

The memory gate exists because the AddressSanitizer gate cannot cover the
assembly backend: it instruments the *generated C*, and there is none once
`kelpc` emits its own assembly. Valgrind runs an asm-generated binary like any
other.

## Differential corpora for the runtime

Two corpora pin the behaviour of the runtime pieces that moved from C to Kelp,
each comparing an old implementation against the new one over generated cases:

| Test file | Compares | Assertion |
| --- | --- | --- |
| `cap_matcher.rs` | `kelpc/runtime/cap_matcher_ref.c` against `std/rt.kp`'s matcher | identical verdict for every case, both drivers generated from one case list |
| `path_normalize.rs` | `kelpc/runtime/path_normalize_ref.c` against `std/rt.kp`'s `path_normalize` | identical bytes in the buffer *and* identical verdict, case by case |

The C files are kept as files rather than as `const`s inside the compiler so the
tests can compile them directly. See [Runtime](/compiler/runtime) for why the duplication
is deliberate.

```sh
cargo test --test cap_matcher   -- --ignored
cargo test --test path_normalize
```

## The formatter's corpus (`kelpc/tests/fmt.rs`)

29 tests, plus `kelpc/tests/fmt_corpus/` (28 input/expected pairs). `kelpc fmt` is a
token-level whitespace reformatter, so its interesting behaviour is a set of
**properties** rather than a set of hand-written outputs:

| Property | Meaning |
| --- | --- |
| Idempotence | `kelpc fmt --check` on a formatted file exits zero, i.e. `F(F(x)) == F(x)` |
| Token fidelity | the sequence of `(kind, source slice)` pairs is identical before and after, so identifiers, literals and operators are byte-equal rather than merely well-typed |
| Comment preservation | comments survive, which the AST cannot even represent |

The corpus covers the whitespace decisions, and the properties are asserted over
the repository's own Kelp sources.

## Benchmarks

Two benchmarks under `bench/`, each with a recorded `results.txt`:

| Benchmark | What it measures |
| --- | --- |
| `bench/speed/` | four CPU-bound workloads (`collatz`, `float`, `mix`, `fib`) with the same algorithm and op counts in Rust, Kelp, C++ and Python; every program times itself and prints a checksum, and the harness keeps the fastest of three trials |
| `bench/write_20gb/` | writing 20 GiB in the same four languages, which is entirely device-bound |

The checksums are the point: equal checksums are what make the timings comparable,
because they prove the four programs did the same work. In the recorded run Kelp,
C++ and Rust are level to within about 1% on all four workloads, and Python is 27x
to 87x slower depending on the workload, with one caveat the README records: an
unconstrained naive `fib` is rewritten into a loop by LLVM at 0.5 ns/op, so the
call-cost workload needs a side-effecting counter to measure anything at all.

The `bench/speed` gate is also where the assembly backend's numbers are measured,
and the plan's annex records the caveats: the asm backend compiled a subset of the
kernels at that measurement, and the follow-up list of what must be true before
the number is trustworthy is longer than the number itself.

## See also

- [Pipeline](/compiler/architecture)
- [Backends](/compiler/backends)
- [Runtime](/compiler/runtime)
- [Install and build](/getting-started/install): the commands, quoted from here
- [Known issues](/meta/known-issues): defects the suite does not cover
