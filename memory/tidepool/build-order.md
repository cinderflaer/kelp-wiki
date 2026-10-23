---
title: "Tidepool: build order"
description: "What was built for Tidepool, in what order, and what each part of main now contains. Each part names the commits and the tests that show it landed, and says which parts are not in the build."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: build order

Tidepool was built in parts. This page lists the parts in the order they landed on
`main`, with the commits and tests that show each one. A part marked "not in the
build" has code in the repository that no build runs.

## Step 0: runtime and checker fixes

The fixes the block design depends on: a `static mut` of a heap type is refused by
name, a mutex of scalars checks clean, and a worker that panics leaves the
collector. The tests are in `kelpc/tests/tidepool_step0.rs`.

## Step 1: roots for threads and locks

The root table grows in chunks of 1024 slots (`ROOT_CHUNK` in `kelpc/gc/src/state.rs`).
Thread arguments and results, closure environments and lock values are roots.
Commit `3c5b726c` put the step 1 work on current `main`, and `c2503916` lifted the
refusals of channel and lock values that step 1 made safe. The tests are in
`kelpc/tests/tidepool_s1.rs`.

## Step 2: the `[tidepool]` section and the trigger

The manifest keys, the trigger arithmetic and the default headroom of 10 percent
came in these commits: `cdb9a349` (the trigger arithmetic in bytes), `2a2dbc69`
(the reader and its refusals), `b4b747a8` (the arithmetic wired into the
collector), `b03c2cb3` (the `trigger_rule` key), `0543a748` (the default headroom
and the six `kelp_gc_init` arguments), and `d167b1ee` (the start pair check). The
settings are on [Tidepool: settings in `[tidepool]`](/memory/tidepool/settings).
The arithmetic tests are in `kelpc/gc/src/trigger.rs`.

## Step 2a and 2b: escape analysis (not in the build)

`kelpc/src/escape.rs` decides which shared-pool allocations could go into a block.
It came in `215eaea0` (step 2a) and `28f97940` (step 2b, for lists and maps of
numbers). Its own header says that nothing in a build calls it, and no other
module of `kelpc/src` names it. The checks a build runs are in `kelpc/src/infer/`
and `kelpc/src/borrowck.rs`.

## Manual blocks (decision 139)

The block form was built in the order of its slices:

1. the parser accepts `block name: T { ... }` and refuses it until blocks are built
   (`6183fe3b`);
2. the checker gives the block a `Result<T, BlockError>` type, a unique name and a
   `box()` that is valid only inside the block (`3bf79615`);
3. the collector gets the block runtime: one zeroed element per mapped chunk,
   charged against `heap_max` and rooted (`7c5b069c`), with its entry points
   `kelp_gc_block_alloc` and `kelp_gc_block_free` (`kelpc/gc/src/lib.rs`);
4. the lowering creates the element and frees it at the end of the region
   (`17850441`, `d82f6c96`);
5. the region is released on `return`, `break`, `continue` and `?` (`2396f0ff`);
6. the checker refuses a block value that leaves its block, by name (`c61ca741`),
   and a block value stored in a shared `List`, `Map` or `Box` (`76cdc449`).

The programs of step 6 are in `kelpc/tests/fixtures/block_end_to_end.kp` and the
tests are in `kelpc/tests/compile_and_run/boxes_operators.rs`.

## Verify mode poisons dead objects

`da72af0b` makes verify mode fill each dead shared-pool object with `0xA5` at the
sweep (`kelpc/gc/src/heap.rs`). Verify mode is `KELP_GC_VERIFY=1`. The test is
`a_dead_object_is_poisoned_in_verify_mode` in `kelpc/tests/gc/mod.rs`.

## The managed target is gone

Commit `d73b59f1` removed the `managed` target mode. Every hosted build has the
shared pool and can use blocks. The `[target] heap_max` key applies to every hosted
build that sets it.

## Not on main

- The parts of the design that this page does not name are not claimed as built.
- The C code generator was removed in `a66f3bcb`.
