---
title: "Tidepool: build order"
description: "The parts of Tidepool in the order they landed on main, with the commits and tests that show each one. Each part names the file that holds its code."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: build order

Tidepool was built in parts. This page lists them in the order they landed on `main`,
with the commits and tests that show each one.

## Step 0: runtime and checker fixes

The fixes the block design depends on: a `static mut` of a heap type is refused by name,
a mutex of scalars checks clean, and a worker that panics leaves the collector. The tests
are in `kelpc/tests/tidepool_step0.rs`.

## Step 1: roots for threads and locks

The root table grows in chunks of 1024 slots (`ROOT_CHUNK` in `kelpc/gc/src/state.rs`).
Thread arguments and results, closure environments and lock values are roots. Commit
`3c5b726c` put the step 1 work on `main`, and `c2503916` lifted the refusals of channel
and lock values that step 1 made safe. The tests are in `kelpc/tests/tidepool_s1.rs`.

## Step 2: the `[tidepool]` section and the trigger

The manifest keys, the trigger arithmetic and the default headroom of 10 percent came in
these commits: `cdb9a349` (the trigger arithmetic in bytes), `2a2dbc69` (the reader and
its refusals), `b4b747a8` (the arithmetic wired into the collector), `b03c2cb3` (the
`trigger_rule` key), `0543a748` (the default headroom and the six `kelp_gc_init`
arguments), and `d167b1ee` (the start pair check). The settings are on
[settings](/memory/tidepool/settings). The arithmetic tests are in `kelpc/gc/src/trigger.rs`.

## Manual blocks (decision 139)

The block form was built in the order of its slices:

1. the parser accepts `block name: T { ... }` (`6183fe3b`);
2. the checker gives the block a `Result<T, BlockError>` type, a unique name and a
   `box()` that is valid only inside the block (`3bf79615`);
3. the collector gets the block runtime: one zeroed element per mapped chunk, charged
   against `heap_max` and rooted (`7c5b069c`), with its entry points
   `kelp_gc_block_alloc` and `kelp_gc_block_free` (`kelpc/gc/src/lib.rs`);
4. the lowering creates the element and frees it at the end of the region (`17850441`,
   `d82f6c96`);
5. the region is released on `return`, `break`, `continue` and `?` (`2396f0ff`);
6. the checker refuses a block value that leaves its block, by name (`c61ca741`), and a
   block value stored in a shared `List`, `Map` or `Box` (`76cdc449`).

The program of step 6 is `kelpc/tests/fixtures/block_end_to_end.kp`, and the tests are in
`kelpc/tests/compile_and_run/boxes_operators.rs`.

## Verify mode poisons dead objects

`da72af0b` makes verify mode fill each dead shared-pool object with `0xA5` at the sweep
(`kelpc/gc/src/heap.rs`). Verify mode is `KELP_GC_VERIFY=1`. The test is
`a_dead_object_is_poisoned_in_verify_mode` in `kelpc/tests/gc/mod.rs`.

## Channels, select and the pool

- `sync.rendezvous<T>()` and the fixed-arity `sync.select2` and `sync.select3` are on
  `main` (`kelpc/std/sync.kp`). The fixtures are `chan_rendezvous.kp`, `chan_select.kp`,
  `chan_select_blocks.kp` and `chan_select_mixed.kp`.
- The general `select { ... }` form, with send, timeout, closed and default arms, is parsed
  in `kelpc/src/parser/parser_select.rs` and lowered onto the waiter records in
  `kelpc/std/sync.kp`. Its fixtures are the `chan_select_*.kp` files, such as
  `chan_select_arms.kp` and `chan_select_send.kp`.
- `std/pool` is in `kelpc/std/pool.kp`, and its fixtures are `pool_sum.kp`, `pool_panics.kp`,
  `pool_drop_joins.kp`, `pool_spawn_after_join.kp` and `pool_zero_workers.kp`.

## The managed target is gone

Commit `d73b59f1` removed the `managed` target mode. Every hosted build has the shared
pool and can use blocks. A manifest that still says `mode = "managed"` is refused with a
message that asks for the line to be deleted (`kelpc/src/resolve/manifest_keys.rs`).

## The C code generator is gone

Commit `a66f3bcb` removed the C code generator, its link step and the backend selector.
The LLVM backend is the only one that lowers hosted programs.

## Escape analysis: compiled, not called

`kelpc/src/escape.rs` decides which shared-pool allocations could go into a block. It came
in `215eaea0` (step 2a) and `28f97940` (step 2b, for lists and maps of numbers). The module
is compiled (`mod escape;` in `kelpc/src/main.rs`), and its header says that nothing in a
build calls it. No other module of `kelpc/src` names it. The checks a build runs are in
`kelpc/src/infer/` and `kelpc/src/borrowck.rs`.

## Related

- [Tidepool memory design](/memory/tidepool): the index.
- [Test plan](/memory/tidepool/test-plan): where the tests for each part are.
- [Release tooling](/tooling/release-tooling): how a release is cut.
