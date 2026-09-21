---
title: "Tests"
description: "The suite is built on one idea - compile a program, run it, compare what it printed. Nothing asserts on generated C, so a test says what the language does rather than how a backend does it, and..."
isPublished: true
tags: "compiler, testing"
---
The suite is built on one idea: **compile a program, run it, compare what it
printed**. Nothing in the language suite asserts on generated C, so a test says
what the language does rather than how a backend does it, and that is what lets
the same suite validate a second backend. Three tests read the generated file on
purpose, because the property under test *is* the generated C: the capability
check has to call the Kelp matcher (`cap_matcher.rs`), every statement has to be
mapped back to its `.kp` line (`compile_and_run.rs`'s
`the_generated_c_maps_statements_back_to_their_kp_lines`), and a build with no
`-o` has to leave the generated C beside the artifact
(`a_build_with_no_output_path_lands_in_build`).

```sh
cargo test                                   # unit tests + the fixture suite
cargo test --test fmt                        # the formatter's corpus and properties
./kelpc/tests/run-all-backends.sh            # the suite once per implemented backend
```

## The fixture suite (`kelpc/tests/compile_and_run.rs`)

353 tests (measured 2026-09-21, after the `asm` backend was removed), driving the
real `kelpc` binary over two corpora:

| Corpus | Count | Shape |
| --- | --- | --- |
| `kelpc/tests/fixtures/*.kp` | 363 files | one loose file per single-file test |
| `kelpc/tests/projects/<name>/` | 61 directories | multi-file: a module graph needs a directory, and a granted module needs an importer |

The C backend passes every one of them. The `llvm` backend passes the fixtures
that stay inside the MK7 S1 scalar subset, the S2A `datac` slice, the S2B heap
slice, the S2C tagged-union slice or the S2D container slice, and refuses the rest
by name, so the whole suite is not yet green on it:
`KELPC_BACKEND=llvm` runs the fixtures, and the gates below name the closed
subsets that must pass.
The `asm` rows left the suite with the backend on 2026-09-21: its counts, its
refusal ranking and the fixture-by-fixture detail stay frozen in
[`plan/asm-backend/plan.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/plan.md)
§0, as history rather than a live measurement.
One of them,
`the_host_port_denial_names_the_host_as_written_and_its_own_port`, is a loopback
test that fails intermittently in a full run: a run that includes it reads 340 and
18, and it passes in isolation and on a re-run.

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
port 0 and passes to the program through argv. The four capability-gate bypasses
the compiler closed this round each have a project of their own: a gated module's
`extern fun` primitive, a gated item named as a function value, a receiver method
and a `pd` initializer, each refused in a module that holds no grant and exercised
in one that does (`caps_raw_ungranted`, `caps_raw_granted`, `caps_raw_positions`,
`caps_raw_denied`, `caps_value_ungranted`, `caps_raw_value_ungranted`,
`caps_method_*`, `pd_gated_*`). The granted-function-value route is a test file of
its own (`cap_function_value.rs`, four tests, because the construct is refused at
inference, before any backend) and the project it replaced,
`caps_raw_value_granted`, went with it.

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
| `kelpc/tests/run-all-backends.sh` | runs the fixture suite once per backend (`BACKENDS`, default `c`; `BACKENDS="c llvm"` runs both) | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-scalar-subset.sh` | the MK7 S1 gate: runs the closed scalar-subset fixtures with `KELPC_BACKEND=llvm` and asserts byte-identical stdout | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-datac-subset.sh` | the MK7 S2A gate: runs the S1 fixtures and the closed `datac` slice (28 tests) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-strings-drops.sh` | the MK7 S2B gate: runs the S1 and S2A fixtures and the heap slice (`Bytes`/`String` through the runtime, an owned field, the drop plan, `panic`/`assert`) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout (40 tests) | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-enum-subset.sh` | the MK7 S2C gate: runs the S1, S2A and S2B fixtures and the tagged-union slice (`enum` at the C `{ tag, union }` layout, `when`, `if let`, `?`) with `KELPC_BACKEND=llvm`, asserts byte-identical stdout (58 tests), and reads the tag and payload offsets back out of the `<out>.ll` the backend wrote to assert three SysV layouts | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-containers.sh` | the MK7 S2D gate: runs the S1, S2A, S2B and S2C fixtures and the container slice (`List`, `Map`, `Box` and `[T; N]` at the C backend's header layouts, construction, the method surfaces, `for` over a list, a container as a field and an element, the bounds checks and one drop per container type) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout (103 tests); it also reads the container header and entry layouts back out of the `<out>.ll` the backend wrote and asserts no runtime declaration passes a container header by value | a shell script, not a cargo test |
| `memory_gate.rs` | valgrind (`--leak-check=full --show-leak-kinds=all`, diagnostics to `--log-file`) over the built binaries, asserting no findings in any process; a spawned child inherits valgrind, so it writes into the same log | ignored; the default run only checks that valgrind is discoverable |

The differential sweep is `backend_coverage.rs`, rebuilt after the `asm` rows went
with the backend on 2026-09-21. It is the sweep the project had been missing: it
always builds *both* backends, so the C backend is an oracle rather than a second
opinion. Every target the C backend builds is built with `llvm` too; for every
target both build, both binaries are run and their stdout and exit status must be
byte-identical. A target the `llvm` backend cannot build is recorded with its
refusal message rather than failed, and a crash or a diagnostic that is not a
named refusal fails the run. It also ratchets a coverage count, `LLVM_BUILT_BASELINE`,
which may only rise: **124 of the 219 targets** at the S2D tip, with **95 refused
by name**, and the ranking report prints those refusals grouped by their exact
message so the slice each one waits on is visible. The sweep compiles the whole
corpus twice, so it is `#[ignore]`d:

```sh
cargo test --release --test backend_coverage -- --ignored --nocapture
```

It is what caught the silent miscompile in `borrow_returned.kp` (a borrow returned
through the value position of an `if`, and a returned `&String`) that the container
slice's reference-place handling closed.

```sh
cargo test --test memory_gate    -- --ignored                 # valgrind over the binaries
```

The memory gate exists because the AddressSanitizer gate cannot cover a backend
that writes its own object: it instruments the *generated C*, and there is none
once `kelpc` emits code itself. Valgrind runs any binary.

## Differential corpora for the runtime

Four corpora pin the behaviour of the runtime pieces that moved from C to Kelp,
and each one
compares one implementation against another over generated cases:

| Test file | Compares | Assertion |
| --- | --- | --- |
| `cap_matcher.rs` | `kelpc/runtime/cap_matcher_ref.c` against `std/rt.kp`'s matcher | identical verdict for every case, both drivers generated from one case list |
| `path_normalize.rs` | `kelpc/runtime/path_normalize_ref.c` against `std/rt.kp`'s `path_normalize` | identical bytes in the buffer *and* identical verdict, case by case |
| `dns_parse.rs` | `kelpc/runtime/dns_parse_ref.c` against `kelpc/runtime/dns_parse.kp` | identical verdict for every case, one line per case, both drivers generated from one case list (1990 cases) |
| `resolver_conf.rs` | `kelpc/runtime/resolver_conf_ref.c` against `kelpc/runtime/resolver_conf.kp` | identical verdict for every case, one line per case, both drivers generated from one case list (2612 cases) |

The C files are kept as files rather than as `const`s inside the compiler so the
tests can compile them directly. See [Runtime](/compiler/runtime) for why the duplication
is deliberate.

```sh
cargo test --test cap_matcher   -- --ignored
cargo test --test path_normalize
cargo test --test dns_parse
cargo test --test resolver_conf
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

The `bench/speed` gate is also where the retired hand-written backend's numbers
were measured, and the plan's annex records the caveats: it compiled a subset of
the kernels at that measurement, and the follow-up list of what must be true
before the number is trustworthy is longer than the number itself. The retired
track's call-cost measurement is
[`plan/asm-backend/call-overhead.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/call-overhead.md),
and it is the measurement the LLVM decision rests on.

## See also

- [Pipeline](/compiler/architecture)
- [Backends](/compiler/backends)
- [Runtime](/compiler/runtime)
- [Install and build](/getting-started/install): the commands, quoted from here
