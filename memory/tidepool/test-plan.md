---
title: "Tidepool: test plan"
description: "Where Tidepool's tests live on main, which crate or command runs each group, which tests need the collector archive or a build queue job, and what the golden index adds. Each entry names its file."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: test plan

Tidepool's tests are in three places: the collector crate, the compiler crate and
the golden index. This page says what each group checks and how it is run. The
tests that check the rules are listed on [Tidepool: safety tests](/memory/tidepool/safety-tests).

## The collector crate

The collector is the crate `kelp_gc` in `kelpc/gc`. It is a separate workspace, and
`kelpc/gc/Cargo.toml` says it is "built by its own `cargo test`". Its unit tests live
under `kelpc/tests/gc/` and are included with a `#[path]` attribute in
`kelpc/gc/src/lib.rs`:

- `mod.rs` holds the allocation, clearing, block and budget tests, and the ABI
  tests. `c_layout_matches_the_abi` checks the C layout, and `abi_limits_are_pinned`
  pins the limits.
- `child_first.rs`, `enum_tag.rs`, `large.rs`, `panic_loc.rs` and `bench_clear.rs`
  are the other modules. `bench_clear.rs` holds the M4 and M9 measurements, which
  are ignored by default.
- `tidepool_step1_fixb.rs` holds step 1 tests on plain threads that attach to the
  collector: a foreign thread, a noscan type with pointers, array overflow and the
  descriptor layout against the Rust struct and the LLVM golden.
- The `trigger_t40` module of `mod.rs` checks the first clearing and later triggers.

Tests that need a fatal exit start a child process with `run_child` in `mod.rs`,
which returns the exit status and the output.

Trigger arithmetic has its own unit tests in `kelpc/gc/src/trigger.rs`.

## The compiler crate

These are integration tests in `kelpc/tests/`, run by `cargo test` in the `kelpc`
crate:

- `tidepool_step0.rs` checks the step 0 refusals and the run tests for threads.
- `tidepool_s1.rs` checks the step 1 run tests: the root table, spawn, lock and
  result roots, the counter line and the messages.
- `compile_and_run/` holds one file for each group of fixtures. The block tests are
  in `boxes_operators.rs`, the channel and thread tests in `atomics.rs`.
- `managed/tidepool_s0/`, `managed/tidepool_s1/` and `managed/tidepool_start/` are
  projects with a `coral.toml` and an `expected.txt`. The `[tidepool]` keys they use
  are on [settings](/memory/tidepool/settings).
- `projects/tidepool*` are projects whose manifest is refused by name, one per
  refusal (for example `tidepoolheapmax65537`, `tidepoolkeytypo` and
  `tidepoolsectionname`).

## Tests that need the collector archive

Some of the run tests build a program and link the collector archive. Those are
marked `#[ignore]`. The headers of `tidepool_step0.rs` and `tidepool_s1.rs` say to
set `KELP_GC_LIB` to `libkelp_gc.a` and to run them with `--ignored`. Their
comments still say "managed program", from the time the managed target existed.

## The golden index

`kelpc/tests/golden/index.tsv` lists each fixture with the outcome the test
expects (`ran`, or a refusal) and the printed output or message. Fixtures named
`fixture_block_*` and `fixture_closure_*` are there. The index is regenerated
with `regen_llvm.py`, which the commit `57c7987d` used for the Tidepool fixtures.

## Build queue

The measurement scripts run through the build queue, not on a developer's machine.
`bench/gc-clear/run.sh` names `buildq submit -p 1`. The scripts are described on
[Tidepool: tooling and release](/memory/tidepool/tooling-release).
