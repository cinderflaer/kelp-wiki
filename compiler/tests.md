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
`-o` has to leave the running backend's own intermediate beside the artifact
(`.c` for `c`, `.ll` for `llvm`; `a_build_with_no_output_path_lands_in_build`).

```sh
cargo test                                   # unit tests + the fixture suite
cargo test --test fmt                        # the formatter's corpus and properties
./kelpc/tests/run-all-backends.sh            # the suite once per implemented backend
```

## The fixture suite (`kelpc/tests/compile_and_run.rs`)

357 tests (measured 2026-09-21, after the `asm` backend was removed), driving the
real `kelpc` binary over two corpora:

| Corpus | Count | Shape |
| --- | --- | --- |
| `kelpc/tests/fixtures/*.kp` | 367 files | one loose file per single-file test |
| `kelpc/tests/projects/<name>/` | 61 directories | multi-file: a module graph needs a directory, and a granted module needs an importer |

The C backend passes every one of them, and so does the `llvm` backend: it lowers
the whole language, so `BACKENDS="c llvm" ./kelpc/tests/run-all-backends.sh` runs
the whole suite under both, which it could not do while one test asserted the C
backend's own `.c` sat beside the artifact. The differential sweep below finds no
target the C backend builds that it does not.
The per-slice gates that follow still name the fixtures they carry.
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
| `kelpc/tests/run-llvm-scalar-subset.sh` | the scalar-subset gate: runs the closed scalar-subset fixtures with `KELPC_BACKEND=llvm` and asserts byte-identical stdout | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-datac-subset.sh` | the datac gate: runs the S1 fixtures and the closed `datac` slice (28 tests) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-strings-drops.sh` | the heap gate: runs the S1 and S2A fixtures and the heap slice (`Bytes`/`String` through the runtime, an owned field, the drop plan, `panic`/`assert`) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout (40 tests) | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-enum-subset.sh` | the tagged-union gate: runs the S1, S2A and S2B fixtures and the tagged-union slice (`enum` at the C `{ tag, union }` layout, `when`, `if let`, `?`) with `KELPC_BACKEND=llvm`, asserts byte-identical stdout (58 tests), and reads the tag and payload offsets back out of the `<out>.ll` the backend wrote to assert three SysV layouts | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-containers.sh` | the container gate: runs the S1, S2A, S2B and S2C fixtures and the container slice (`List`, `Map`, `Box` and `[T; N]` at the C backend's header layouts, construction, the method surfaces, `for` over a list, a container as a field and an element, the bounds checks and one drop per container type) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout (103 tests); it also reads the container header and entry layouts back out of the `<out>.ll` the backend wrote and asserts no runtime declaration passes a container header by value | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-references.sh` | the reference gate: runs the S1, S2A, S2B, S2C and S2D fixtures and the reference slice (`&T` to a scalar, a borrow of a field, the read, the write, a `&T` parameter and a `&T` return) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout (109 tests); it also reads the borrowed-parameter signatures back out of the `<out>.ll` the backend wrote to assert they take `kelp_origin(ptr)`-style pointers, and asserts a `panic` tail ends in `unreachable` | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-closures.sh` | the closure gate: runs the S1, S2A, S2B, S2C, S2D and S2F fixtures and the closure and function-value slice (a declared `fun` as a value, a `fun` literal with and without captures, a call through a value, a closure's heap environment and its drop, and the two widening shapes) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout (120 tests); it also reads the fat pointer's shape back out of the `<out>.ll` the backend wrote as `{ ptr, ptr, ptr }`, that a `fun` parameter and a `fun` return are both `ptr`, that a call through a closure passes the environment first, and the shape of a two-field environment | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-externs.sh` | the extern fun gate: runs the S1, S2A, S2B, S2C, S2D, S2F and S2E fixtures and the `extern fun` slice (the raw allocator, `str`'s byte reads, the `malloc`-shaped `String`/`Bytes` construction, `sqrt`, `clock_gettime` and a raw `read`) with `KELPC_BACKEND=llvm` and asserts byte-identical stdout (138 tests); it also reads each extern's declaration back out of the `<out>.ll` the backend wrote to assert it matches its body's C signature, and asserts that no `declare %kelp_(Bytes|String)` line exists | a shell script, not a cargo test |
| `kelpc/tests/run-llvm-pd-caps.sh` | the `pd` globals, the capability check and the last three refusals (38 tests); it pins the exact deny text and exit status against the C backend's own and asserts the owned `pd` is freed at exit | a shell script, not a cargo test |
| `llvm_debug_info.rs` | the debug-info gate: builds `kelpc/tests/llvm-debug/fault.kp` with `--backend=llvm`, reads the decoded line table back out of the binary with `readelf` and asserts it names the fixture's `.kp` file and statement lines, then runs the binary, whose run-time division by zero traps, and asserts `gdb` places the fault at `fault.kp:16` with its caller at `fault.kp:21`. The fixture sits outside `tests/fixtures/` on purpose: the coverage sweep treats a run that dies from a signal as a failure, which is right for the corpus and wrong for the one program whose job is to crash | a cargo test, and it fails by name when `gdb` or `readelf` is missing |
| `kelpc/tests/differential_fuzz.rs` | the differential fuzzer and the conformance corpus: one seed generates one valid Kelp program (SplitMix64, no new dependency), written to a file before it is built, built with both backends and compared byte for byte on stdout and exit status. The default run pins one seed and asserts every corpus file byte-equals the generator's output for its seed; the 256-seed run and the corpus run are `#[ignore]`d | the default run is cheap; the heavy runs are ignored |
| `memory_gate.rs` | valgrind (`--leak-check=full --show-leak-kinds=all`, diagnostics to `--log-file`) over the built binaries, asserting no findings in any process; a spawned child inherits valgrind, so it writes into the same log | ignored; the default run only checks that valgrind is discoverable |

The differential sweep is `backend_coverage.rs`, rebuilt after the `asm` rows went
with the backend on 2026-09-21. It is the sweep the project had been missing: it
always builds *both* backends, so the C backend is an oracle rather than a second
opinion. Every target the C backend builds is built with `llvm` too; for every
target both build, both binaries are run and their stdout and exit status must be
byte-identical. A target the `llvm` backend cannot build is recorded with its
refusal message rather than failed, and a crash or a diagnostic that is not a
named refusal fails the run. It also ratchets a coverage count, `LLVM_BUILT_BASELINE`,
which may only rise: **223 of the 223 targets** at the MK7 S5 tip, so **no target
is refused** and the ranking is empty, which is the plan's §4.1 gate. The ranking
report still prints any refusal grouped by its exact message, so a refusal that
arrived with a new fixture names the slice it waits on. The sweep compiles the
whole corpus twice, so it is `#[ignore]`d:

```sh
cargo test --release --test backend_coverage -- --ignored --nocapture
```

It is what caught the silent miscompile in `borrow_returned.kp` (a borrow returned
through the value position of an `if`, and a returned `&String`) that the container
slice's reference-place handling closed.

A curated corpus only covers the shapes its author thought of, so
`kelpc/tests/differential_fuzz.rs` generates programs instead. One seed is one
valid program over the landed surface, drawn by a hand-written SplitMix64 PRNG
(no new dependency), so the same seed always produces the same text and a
mismatch has a name a reader can quote. Each program is written to a file *before*
it is built, then built with both backends and compared byte for byte on stdout
and exit status, with the failing seed, the file and both outputs printed.
`FUZZ_SEED_START` and `FUZZ_SEED_COUNT` select the seed list; the default run pins
one seed and the 256-seed run is `#[ignore]`d. 256 seeds were generated and 256
built by both backends and agreed, 0 refused and 0 mismatches, and a 512-seed run
agreed too. `kelpc/tests/fuzz-corpus/` holds a conformance corpus of 24 frozen
seeds, union-covering all sixteen shapes, run differentially by an ignored test; a
default-suite test asserts every file byte-equals the generator's own output for
its seed, so it cannot drift. **A mismatch is a defect in a backend and is
diagnosed, never answered by deleting a shape from the generator.** The fuzzer
found two real defects, both `llvm`-confined and each now a fixture: a float
`List`'s
`contains` fell through to an integer compare, which is invalid IR
(`list_float_element.kp`), and an unread owned `pd` made the generated `atexit`
drop reference a container set that was never declared (`pd_owned_container.kp`).

```sh
cargo test --release --test differential_fuzz -- --ignored --nocapture  # the fuzzer and the corpus
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
