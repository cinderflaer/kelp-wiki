---
title: "Tidepool: performance claims and how they are measured"
description: "What Tidepool's performance numbers measure, which scripts and tests produce them, what is recorded on main and what is not. No number is given here that main does not record."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: performance claims and how they are measured

This page says what Tidepool has measured, how, and what is on `main` to show
it. A claim about speed or memory should name one of the measurements below. A
claim that names none is not supported by the repository.

## What is recorded on main

- `bench/gc/RESULTS.md` is a table generated on 2026-10-10 by `bench/gc/run.sh`,
  for `kelpc 26.10.5`. Its rows for the managed variants show `NO-GC`, because the
  build at that commit did not link the collector. The file says so, and it says
  that no overhead can be read from those rows. Since commit `d73b59f1` removed the
  managed target, every hosted build links the collector, so that table does not
  measure the current collector.
- `memory/performance.md` records the 26.10.5 hosted build on four benchmarks. That
  build had no collector, so its numbers are for the program without Tidepool.

No recorded result on `main` measures the current collector. The measurements that
could show it are described in the next section. Each one prints its result when a
build queue job runs it.

## How the collector is measured

| Measurement | What it measures | Where |
| --- | --- | --- |
| M4 | the median pause of a forced clearing with a 1 MiB live set, for each of two caps (256 and 1024 MiB), and the ratio between them | `kelpc/tests/gc/bench_clear.rs` (`m4_clearing_cost_child`), run by `bench/gc-clear/run.sh` |
| M9 | refill tail and overshoot with 256 attached threads, one object each, and unrooted garbage | `m9_refill_tail_and_overshoot_256_threads` in `bench_clear.rs`, run by `bench/gc-clear/run.sh` |
| M5 | block creation and free time | `m5_block_create_and_free_ns` in `kelpc/tests/gc/mod.rs` |
| M1 | allocation time of the base collector against the step 1 collector | `bench/gc-alloc/run-m1.sh` with `run-m1.py` |
| the programs | wall time, spread, peak memory and collections for five programs (`binary-trees`, `heap-pressure`, `live-set`, `mixed-pool` and `strings`), managed against unmanaged | `bench/gc/run.sh` with `progs/` and `gate.sh` |

The M4 and M9 tests are ignored by default. Each runs in its own process, and the
script takes medians. The test comment says that nothing in these tests checks a
gate: the printed line is the measurement, and the pass line is in the design
record. The runner for M4 compares the ratio between the two caps against 1.5.

## Conditions

The measurement scripts follow these rules, which the script headers state:

- the collector's verifier is off (`KELP_GC_VERIFY` unset) and the stress mode is
  off, so the timings are those of a normal run;
- the build is release;
- `bench/gc-clear/run.sh` runs with core dumps off, as a build queue job at
  priority 1;
- `bench/gc/run.sh` runs each row once as a discarded warm-up and then three times
  (default), and reports the median and the spread.

## What is not claimed here

This page does not state a speed for Tidepool. It does not compare Tidepool with
the 26.10.5 build, because that build had no collector. A new number belongs on this
page only with the script, the machine and the date that produced it.
