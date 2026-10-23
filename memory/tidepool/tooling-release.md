---
title: "Tidepool: tooling and release"
description: "The parts of Tidepool a developer or a release touches: the collector archive that kelpc links, the environment variables the collector reads, and the benchmark scripts with their build queue priorities and known faults."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: tooling and release

This page covers the parts of Tidepool that a developer or a release touches: the archive
the compiler links, the environment variables the collector reads, and the scripts that run
the measurements. The tests are on [test plan](/memory/tidepool/test-plan).

## The collector archive

The collector is built as the crate `kelp_gc`, with the `staticlib` type
(`kelpc/gc/Cargo.toml`). `kelpc/build.rs` builds it as part of the compiler and copies
`libkelp_gc.a` to the build's output directory. `kelpc/src/driver.rs` embeds that file, so
every compiled hosted program is linked against the collector.

`KELP_GC_LIB` names a different archive for the link, and the run tests use it
(`kelpc/src/driver.rs`). A file that does not exist is an error.

## Environment variables

The collector reads these once, when it is set up (`do_init` in `kelpc/gc/src/lib.rs`).
A value that is not a whole number prints a notice and is ignored
([failure and recovery](/memory/tidepool/failure-recovery)).

| Variable | Effect | Source |
| --- | --- | --- |
| `KELP_GC_VERIFY=1` | runs the heap verifier after each collection, and poisons dead objects with `0xA5` at each sweep | `lib.rs`, `verify.rs`, `heap.rs` |
| `KELP_GC_STATS=1` | prints the counter line at exit, and before a fatal exit | `lib.rs`, `sys.rs` |
| `KELP_GC_STRESS=n` | runs a clearing every `n` allocations | `lib.rs` (`alloc_common`) |
| `KELP_GC_STOP_TIMEOUT_MS=n` | how long a collection waits for a thread to stop, in ms, at least 1; the default is 10000 | `lib.rs`, `threads.rs` |
| `KELP_GC_TEST_SPAWN_PAUSE=1` | a test hook: a spawn holds its worker before the worker attaches, and runs a clearing in that window | `lib.rs` (`spawn_pause`), `state.rs` |

Verify mode is the one to use when a program reads freed memory and gives a wrong answer.
A read through a stale pointer then sees `0xA5` bytes, not the old contents. The program
in [what the programmer writes](/memory/tidepool/programmer-view#checking-a-program-with-verify-mode)
shows the setting. The stress and verify modes are for testing, and the measurement
scripts unset them before they run.

## Benchmark scripts

| Script | What it runs | Where it runs |
| --- | --- | --- |
| `bench/gc-clear/run.sh` | builds the collector's test binary in release, and runs the M4 and M9 measurements, with medians | a build queue job at priority 1, with core dumps off (`prlimit --core=0:0`) |
| `bench/gc-alloc/run-m1.sh` | builds the base and step 1 collectors, and times them with `run-m1.py` | a build queue job at priority 1, exclusive |
| `bench/gc/run.sh` | builds the five programs in `bench/gc/progs/` as managed and unmanaged projects, and writes `raw.csv`, `results.csv` and `RESULTS.md` | a build queue job at priority 30 |
| `bench/gc/gate.sh` | compares `bench/gc/results.csv` with `bench/gc/baseline.csv`, and fails when a median is more than 5 percent above the baseline, or a pause median is above 50 ms | after `run.sh` |

The benchmark headers name the job commands. `bench/gc/run.sh` writes `mode = "hosted"`
into every project it builds. The managed row is the one with a `heap_max` line
(`make_project` in the script).

## Release

`kelpc` builds the collector archive with the rest of the compiler, so a release carries the
collector in every hosted build. Nothing on this page gives a separate release step for
Tidepool. The release procedure for the compiler is on [release tooling](/tooling/release-tooling).

## Related

- [Performance claims](/memory/tidepool/performance-claims): what the scripts measure.
- [Settings in `[tidepool]`](/memory/tidepool/settings): the keys the variables sit beside.
- [Test plan](/memory/tidepool/test-plan): the tests that use these variables.
- [Tidepool memory design](/memory/tidepool): the index.
