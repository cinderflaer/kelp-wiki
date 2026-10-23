---
title: "Tidepool: the budget"
description: "How heap_max caps the shared pool and the manual blocks together, how the first and later clearing triggers are computed, and what a program sees when the cap is reached. Each rule names its source."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: the budget

Every hosted program has one memory budget. The shared pool and the memory of
the manual blocks draw on it together. This page says how the budget is sized
and when the collector clears the pool. The settings are on
[Tidepool: settings in `[tidepool]`](/memory/tidepool/settings).

## The cap

`[target] heap_max` is a whole number of MiB from 1 to 65536, with a default of
256 (`kelpc/src/managed.rs`, `HEAP_MAX_MIB_RANGE` and `DEFAULT_HEAP_MAX_MIB`). The
compiler passes it to `kelp_gc_init` in bytes (`kelpc/src/codegen_llvm.rs`).

The collector turns the cap into a region (`do_init` in `kelpc/gc/src/lib.rs`):

- the number of 32 KiB blocks is `max(4, ceil(heap_max / 32 KiB))`;
- the region is that many blocks, so the cap is rounded up to a whole block and
  is never less than four blocks;
- the collector stores the region size as its `heap_max`. The budget checks below
  use this stored value, not the manifest number.

The collector reads `heap_max` once per process. A program cannot change it while
it runs (`kelpc/tests/gc/bench_clear.rs` runs one child process per cap).

## The first clearing

The first trigger is the midpoint of the two start guesses plus headroom, in bytes
(`first_trigger` in `kelpc/gc/src/trigger.rs`). With the defaults of 1 MiB, 4 MiB
and 10 percent, that is 2.75 MiB. The trigger is also capped at the region size
(`do_init` takes the smaller of the two). `heap_min` does not set the first
trigger.

## Later clearings

After a clearing, the next trigger is `max(heap_min, live * (100 + headroom) / 100)`
(`next_trigger` in `trigger.rs`). The value of `live` depends on the rule in
`[tidepool] trigger_rule`:

- `two-size` (the default): the larger of the last two measured live sizes;
- `last-size`: the last measured live size alone;
- `gogc-style`: the last measured live size plus the stack and global bytes
  scanned with it.

`heap_min` is the fixed 8 MiB floor (`DEFAULT_HEAP_MIN` in `kelpc/gc/src/state.rs`).
The `trigger.rs` tests pin the arithmetic for each rule, for example
`two_size_keeps_a_spike_one_clearing_longer_than_last_size`.

## What the cap covers

Two kinds of memory share the cap:

- Shared-pool blocks, counted in `used_blocks`. `budget_allows` in
  `kelpc/gc/src/heap.rs` refuses to take another pool block when it would pass the
  cap, given the live charge of the manual blocks.
- Manual block chunks, counted in `charged_bytes`. `fits` in
  `kelpc/gc/src/block.rs` checks `used_blocks * 32 KiB + charged_bytes + bytes <=
  heap_max` before a block is made. The chunk is one element, rounded up to 8
  bytes.

A block that does not fit gets one clearing, and then the check runs again
(`block::alloc`). If it still does not fit, the call returns `BLOCK_OVER_BUDGET`,
which the program sees as the `Full` case of `BlockError`
(`kelpc/src/codegen_llvm/frame.rs`). See [Failure and recovery](/memory/tidepool/failure-recovery).

## When the shared pool is full

When an allocation fails after a clearing, the collector prints three numbers and
stops. The format is this, with example numbers (`out_of_shared_pool` in `kelpc/gc/src/lib.rs`):

```text
out of shared-pool memory: heap_max is 256 MiB, 200 MiB was live at the last clearing, and 40 MiB is charged to live blocks
  note: keep less data live, or raise heap_max in coral.toml's [target] section
```

The numbers are the cap in MiB, the live size at the last clearing, and the bytes
charged to blocks. The program does not get a value back.

## Tests

- `a_block_past_heap_max_runs_a_clearing_then_fails` in `kelpc/tests/gc/mod.rs`:
  a block that does not fit runs one clearing and then fails.
- `a_pool_run_past_heap_max_is_refused_while_blocks_hold_the_budget` in the same
  file: while live blocks hold part of the cap, a pool run that would pass it is
  refused, and it is served once the blocks are freed.
- `t40a_first_trigger_is_3_mib_for_1_and_4_mib_at_headroom_20` in the `trigger_t40`
  module of `kelpc/tests/gc/mod.rs` checks the midpoint arithmetic.
  `t40e_first_clearing_happens_at_the_manifest_trigger` and
  `t40f_first_clearing_lands_in_the_pool_block_of_the_trigger` are in the same file.
- `kelpc/tests/gc/child_first.rs` checks that the first clearing lands in the pool
  block the trigger names: with a 3 MiB trigger, the 131041st 24-byte object is the
  first one in pool block 97.
- `two_size_keeps_a_spike_one_clearing_longer_than_last_size` in
  `kelpc/gc/src/trigger.rs` checks the `two-size` arithmetic for a spike.

## Related

- [Settings in `[tidepool]`](/memory/tidepool/settings): the keys that set the cap and the triggers.
- [The allocation path](/memory/tidepool/allocation-path): where the trigger is checked.
- [Failure and recovery](/memory/tidepool/failure-recovery): what a program sees at the cap.
- [Tidepool memory design](/memory/tidepool): the index.
