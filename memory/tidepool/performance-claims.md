---
title: "Tidepool: performance claims and how they are measured"
description: "What Tidepool has measured, how, and which file holds each result. A claim about speed or memory names one of the measurements listed here. Shows the recorded 26.10.5 table and the measurements that run on the build queue."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: performance claims and how they are measured

This page says what Tidepool has measured, how, and what is on `main` to show it. A claim
about speed or memory should name one of the measurements below.

## What is recorded on main

- `bench/gc/RESULTS.md` is a table generated on 2026-10-10 by `bench/gc/run.sh`, for
  `kelpc 26.10.5`. Its managed rows show `NO-GC`. `run.sh` defines that status as a
  binary without the collector, whose numbers are not overhead, so the ratio is not
  printed (the comment at the top of `bench/gc/run.sh`).
- [`memory/performance.md`](/memory/performance) records the 26.10.5 hosted build on four
  benchmarks. That build linked no collector, so its numbers are for the program without
  Tidepool.

No recorded result on `main` measures the current collector. The measurements that could
show it are in the next section. Each one prints its result when a build queue job runs it.

## How the collector is measured

| Measurement | What it measures | Where |
| --- | --- | --- |
| M4 | the median pause of a forced clearing with a 1 MiB live set, for each of two caps (256 and 1024 MiB), and the ratio between them | `m4_clearing_cost_child` in `kelpc/tests/gc/bench_clear.rs`, run by `bench/gc-clear/run.sh` |
| M9 | refill tail and overshoot with 256 attached threads, one object each, and unrooted garbage | `m9_refill_tail_and_overshoot_256_threads` in `bench_clear.rs`, run by `bench/gc-clear/run.sh` |
| M5 | block creation and free time | `m5_block_create_and_free_ns` in `kelpc/tests/gc/mod.rs` |
| M1 | allocation time of the base collector against the step 1 collector | `bench/gc-alloc/run-m1.sh` with `run-m1.py` |
| the programs | wall time, spread, peak memory and collections for five programs (`binary-trees`, `heap-pressure`, `live-set`, `mixed-pool` and `strings`), managed against unmanaged | `bench/gc/run.sh` with `bench/gc/progs/` and `bench/gc/gate.sh` |

The M4 and M9 tests are ignored by default. M4 runs one child process per `heap_max`,
because the collector reads the cap once per process, and the script takes medians.
`bench/gc-clear/run.sh` compares the ratio between the two caps with the limit of 1.5.
The M5 test prints its figures and asserts nothing.

## Conditions

The measurement scripts follow these rules, which the script headers state:

- the collector's verifier is off, and the stress and stats modes are unset, so the
  timings are those of a normal run (`unset KELP_GC_VERIFY KELP_GC_STRESS KELP_GC_STATS`
  in `bench/gc-clear/run.sh` and `bench/gc-alloc/run-m1.sh`);
- the build is release;
- `bench/gc-clear/run.sh` runs with core dumps off, as a build queue job at priority 1;
- `bench/gc/run.sh` runs each row once as a discarded warm-up and then three times by
  default (`RUNS=3`), and reports the median and the spread.

## What is not claimed here

This page states no speed for Tidepool. It does not compare Tidepool with the 26.10.5 build,
because that build had no collector. A new number belongs on this page only with the script,
the machine and the date that produced it.

## Related

- [Tooling and release](/memory/tidepool/tooling-release): the scripts and their job priority.
- [Performance](/memory/performance): the recorded 26.10.5 table.
- [Test plan](/memory/tidepool/test-plan): the tests that run the measurements.
- [Tidepool memory design](/memory/tidepool): the index.
