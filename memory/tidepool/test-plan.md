---
title: "Tidepool: test plan"
description: "Where Tidepool's tests live: the collector crate, the compiler crate, the managed projects, the manifest refusal projects and the golden index. Says what each group checks and how it is run."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: test plan

Tidepool's tests are in three places: the collector crate, the compiler crate and the
golden index. This page says what each group checks and how it is run. The tests that
check the rules are listed on [safety tests](/memory/tidepool/safety-tests).

## The collector crate

The collector is the crate `kelp_gc` in `kelpc/gc`. `kelpc/gc/Cargo.toml` says it is
"built by its own `cargo test`". Its unit tests live under `kelpc/tests/gc/`, and
`kelpc/tests/gc/mod.rs` includes the modules with `mod` and `#[path]` attributes:

- `mod.rs` holds the allocation, clearing, block and budget tests, the ABI tests and
  the `trigger_t40` module. `c_layout_matches_the_abi` checks the C layout, and
  `abi_limits_are_pinned` pins the limits.
- `child_first.rs`, `enum_tag.rs`, `large.rs` and `panic_loc.rs` are the other modules.
  `enum_tag.rs` holds the fatal-exit tests, which start a child process with `run_child`.
- `bench_clear.rs` holds the M4 and M9 measurements. They are ignored by default.
- `tidepool_step1_fixb.rs` holds step 1 tests on plain threads that attach to the
  collector: a foreign thread, a noscan type with pointers, array overflow, and the
  descriptor layout against the Rust struct.

Trigger arithmetic has its own unit tests in `kelpc/gc/src/trigger.rs`.

## The compiler crate

These are integration tests in `kelpc/tests/`, run by `cargo test` in the `kelpc` crate:

- `tidepool_step0.rs` checks the step 0 refusals and the run tests for threads.
- `tidepool_s1.rs` checks the step 1 run tests: the roots, the counter line and the
  fatal messages.
- `compile_and_run/` holds one file for each group of fixtures. The block tests are in
  `boxes_operators.rs`, and the channel, select and thread tests are in `atomics.rs`.
- `managed_run.rs` builds the managed projects `churn` and `enum_churn`, which allocate
  past the initial heap, collect, and print the right sums. These tests need the collector
  archive, so they are `#[ignore]`d.
- `managed/tidepool_s0/`, `managed/tidepool_s1/`, `managed/tidepool_start/` and
  `managed/tidepool_rule/` are projects with a `coral.toml`, a `src/main.kp` and an
  `expected.txt`. The `[tidepool]` keys they use are on
  [settings](/memory/tidepool/settings).
- `projects/tidepool*` are projects whose manifest is refused, one per refusal. Their
  messages are the `project_tidepool*` rows of the golden index.

## Tests that need the collector archive

Some of the run tests build a program and link the collector archive. Those are marked
`#[ignore]`. The headers of `tidepool_step0.rs` and `tidepool_s1.rs` say to set
`KELP_GC_LIB` to `libkelp_gc.a` and to run them with `--ignored`. `KELP_GC_LIB` is read
by `kelpc/src/driver.rs`, and a file that does not exist is an error.

## The golden index

`kelpc/tests/golden/index.tsv` lists each fixture with the outcome the test expects
(`ran`, or a refusal) and the printed output or message. The `fixture_block_*` rows hold
the block refusals, and the `fixture_chan_select*` rows hold the select fixtures. The
index is written by `kelpc/tests/golden/regen_llvm.py`, which commit `57c7987d` used for
the Tidepool fixtures.

## Measurement scripts

The measurement scripts run through the build queue, not on a developer's machine.
`bench/gc-clear/run.sh` names `buildq submit -p 1`. The scripts are described on
[tooling and release](/memory/tidepool/tooling-release).

## Related

- [Safety tests](/memory/tidepool/safety-tests): the rule-by-rule list.
- [Build order](/memory/tidepool/build-order): the parts these tests cover.
- [Tooling and release](/memory/tidepool/tooling-release): the environment variables and the scripts.
- [Tidepool memory design](/memory/tidepool): the index.
