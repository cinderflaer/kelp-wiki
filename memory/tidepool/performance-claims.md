---
title: "Tidepool: performance claims and how they are measured"
description: "What Tidepool has measured, how, and which file holds each result. Shows the recorded 26.10.5 table, two single-run laptop results from 2026-10-23, and the measurements that run on the build queue."
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

The two laptop runs of 2026-10-23, below, are the first results on `main` that run the
current collector. Each is one run on one machine, so treat them as a first sample, not
as a baseline. The measurements that could show more are in the next section. Each one
prints its result when a build queue job runs it.

## Laptop runs, 2026-10-23

Both runs were made on one laptop, an Intel Core i5-10310U at 1.70 GHz with 15.3 GB of
memory. Each is **one run on one machine**. They are not medians of repeated runs, and
they are not a baseline. Do not compare them with `bench/RESULTS.md` or `bench/gc/RESULTS.md`,
which were measured on other machines.

### Tidepool programs

Source: [`bench/results-tidepool-laptop-2026-10-23.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/bench/results-tidepool-laptop-2026-10-23.md),
from `bench/gc/run.sh` with `RUNS=1`, on kelp `a7bb7585` and kelpc `26.10.6`, built with
`kelpc build -O2` on the LLVM backend. Times are wall seconds of the one recorded run.

| bench | managed wall s | unmanaged wall s | managed / unmanaged |
| --- | ---: | ---: | ---: |
| binary-trees | 2.920 | 2.890 | 1.01x |
| live-set | 0.920 | 0.920 | 1.00x |
| strings | 1.950 | 1.950 | 1.00x |
| mixed-pool | 6.370 | 6.390 | 1.00x |
| heap-pressure, managed-64 | 1.460 | 1.450 | 1.01x |
| heap-pressure, managed-256 | 1.460 | 1.450 | 1.01x |

**heap-pressure, managed-16 did not produce a result.** It failed by design. Its live set
(about 11 MiB) is larger than its 16 MiB `heap_max`, so the program stopped with the
out-of-shared-pool-memory panic after 0.03 s. The bench sizes were not changed to make the
row pass. This row is not a measurement, and it gives no ratio.

`mixed-pool` used more than one thread: its user time (about 22.9 s) is well above its wall
time (about 6.4 s) in both variants. This was recorded and not analysed.

### Manual blocks (M1)

Source: [`bench/results-manual-blocks-laptop-2026-10-23.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/bench/results-manual-blocks-laptop-2026-10-23.md),
from `bench/gc-alloc/run-m1.sh` with `run-m1.py`. The base arm is kelp `bf655a60` and the
s1 arm is kelp `a7bb7585`. The run used nine interleaved blocks, with one run per arm in
each block. It was pinned to one core.

| arm | median ns per allocation (cell16, 24 B, the gate row) |
| --- | ---: |
| base (`bf655a60`) | 16.66 |
| s1 (`a7bb7585`) | 16.87 |

- The mean of the per-block ratio s1 / base is 1.0127.
- The one-sided 95% upper bound on that ratio is 1.0227. The gate is 1.05.
- **Verdict: pass.** s1 is at most 5 percent slower than base, to the 95% bound. This is one
  measurement on one machine.

Other rows, reported but not gated (mean ratio s1 / base):

- array8x8 (72 B): 1.025
- obj200 (208 B): 1.063. **This is a single run and needs a repeat** before it is read as a
  regression. The gate applies to the cell16 row only.

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

The laptop runs are the only speeds for Tidepool on this page, and each is one run. They
are not compared with the 26.10.5 build, because that build had no collector. A new number
belongs on this page only with the script, the machine and the date that produced it.

## Related

- [Tooling and release](/memory/tidepool/tooling-release): the scripts and their job priority.
- [Performance](/memory/performance): the recorded 26.10.5 table.
- [Test plan](/memory/tidepool/test-plan): the tests that run the measurements.
- [Tidepool memory design](/memory/tidepool): the index.
