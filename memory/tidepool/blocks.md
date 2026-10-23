---
title: "Tidepool: blocks at runtime"
description: "How a manual block's element is made, rooted, charged to heap_max and freed on every exit of its region, with the collector entry points and the source of each step."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: blocks at runtime

A manual block (`block name: T { ... }`, decision 139) gives one element its own
memory, freed when the block ends. This page covers what the runtime does for
that element. The language rules are on
[Tidepool: what the programmer writes, reads and sees](/memory/tidepool/programmer-view),
and the compile-time checks are on [Tidepool: the boundary](/memory/tidepool/boundary).

## Making the element

`name.box()` inside the block calls `kelp_gc_block_alloc`, which the compiler
emits in `emit_block_box` (`kelpc/src/codegen_llvm/frame.rs`). The entry point is
in `kelpc/gc/src/lib.rs` and calls `block::alloc` in `kelpc/gc/src/block.rs`:

1. The collector is initialised if it is not yet (`ensure_init`). A thread that
   is not attached is fatal, as it is for the shared pool.
2. A type with an alignment above 8 is fatal: `gc: type alignment above 8 is not
   supported in v1`.
3. The chunk size is the element size rounded up to 8 bytes, with a minimum of 8.
4. The budget check runs under the heap lock. If the chunk does not fit under
   `heap_max`, one clearing runs and the check is made again. See
   [Tidepool: the budget](/memory/tidepool/budget).
5. The chunk is mapped with `try_map`. A fresh anonymous mapping is zero, so the
   element starts zeroed.
6. The chunk is registered as a root in the same root table the pool's roots use
   (`threads::register_root`). A clearing therefore marks through the element.
   The handle returned is the root handle.

If step 4 or 5 or 6 fails, the charge and the mapping are undone before the status
is returned.

## Status codes

`block::alloc` returns one of four statuses. The compiled program receives the
status as an `i32`, and a status other than `BLOCK_OK` makes the block value
`Err(BlockError.Full)` (`emit_block_box` in `frame.rs`).

| Status | Constant | When |
| --- | --- | --- |
| 0 | `BLOCK_OK` | the element was made |
| 1 | `BLOCK_OVER_BUDGET` | the chunk would pass `heap_max`, even after a clearing |
| 2 | `BLOCK_ROOT_FULL` | the root table could not take another slot |
| 3 | `BLOCK_NO_MEMORY` | the chunk could not be mapped |

The constants are in `kelpc/gc/src/block.rs`.

## Freeing the element

Each block region has two slots, the base address and the root handle. The
compiler fills them at `name.box()` and reads them at the end of the region
(`emit_region`, `release_region`). `block::free` in `block.rs`:

1. unregisters the root, and returns false without doing anything if the handle
   is already stale;
2. unmaps the chunk;
3. gives the charge back to the budget.

The compiler frees a region on every way out of it. The commit that added this,
`2396f0ff`, names four exits: the end of the block, `return`, `break`, `continue`
and the `?` operator. The regions an exit leaves are freed innermost first, before
the drops and the jump.

## Tests

- `a_block_is_zeroed_rooted_and_charged_until_freed` in `kelpc/tests/gc/mod.rs`
  checks the zeroing, the root and the charge, and that the free returns the
  charge.
- `a_block_past_heap_max_runs_a_clearing_then_fails` in the same file checks the
  budget path.
- `kelpc/tests/compile_and_run/boxes_operators.rs`:
  `a_block_region_runs_and_releases_on_every_exit` runs `block_region_runs.kp`, which
  leaves a block by its end, a loop, a `return`, a `?` and a `defer` in the caller.
  `a_block_and_shared_pool_code_share_one_file` runs `block_end_to_end.kp`, which
  creates and frees a block a thousand times while shared-pool data stays intact.
- `m5_block_create_and_free_ns` in `kelpc/tests/gc/mod.rs` is a timing test for
  create and free. It prints a measurement and checks no gate.
