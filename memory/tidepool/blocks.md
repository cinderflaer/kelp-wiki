---
title: "Tidepool: blocks at runtime"
description: "How a manual block's element is made, rooted, charged to the budget and freed: the four status codes, the zeroed chunk, the free on every exit of the region, and the box made again in a loop."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: blocks at runtime

A manual block (`block name: T { ... }`) gives one element its own memory, freed when
the block ends. This page covers what the runtime does for that element. The language
rules are on [what the programmer writes, reads and sees](/memory/tidepool/programmer-view),
and the compile-time checks are on [the boundary](/memory/tidepool/boundary).

## Making the element

`name.box()` inside the block calls `kelp_gc_block_alloc`, which the compiler emits in
`emit_block_box` (`kelpc/src/codegen_llvm/frame.rs`). The entry point is in
`kelpc/gc/src/lib.rs` and calls `block::alloc` in `kelpc/gc/src/block.rs`:

1. The collector is initialised if it is not yet (`ensure_init`). A thread that is not
   attached is fatal: `gc: block allocation on a thread that is not attached`.
2. A type with an alignment above 8 is fatal: `gc: type alignment above 8 is not
   supported in v1`.
3. The chunk size is the element size rounded up to 8 bytes, with a minimum of 8
   (`chunk_bytes`).
4. The budget check runs under the heap lock. If the chunk does not fit under
   `heap_max`, one clearing runs and the check is made again. See
   [the budget](/memory/tidepool/budget).
5. The chunk is mapped with `try_map`. A fresh anonymous mapping is zero, so the
   element starts zeroed.
6. The chunk is registered as a root in the same root table the pool's roots use
   (`threads::register_root`). A clearing therefore marks through the element. The
   handle returned is the root handle.

If step 4, 5 or 6 fails, the charge and the mapping are undone before the status is
returned.

## Status codes

`block::alloc` returns one of four statuses. The compiled program receives the status
as an `i32`. A status other than `BLOCK_OK` makes the block value
`Err(BlockError.Full)` (`emit_block_box` in `frame.rs`).

| Status | Constant | When |
| --- | --- | --- |
| 0 | `BLOCK_OK` | the element was made |
| 1 | `BLOCK_OVER_BUDGET` | the chunk would pass `heap_max`, even after a clearing |
| 2 | `BLOCK_ROOT_FULL` | the root table could not take another slot |
| 3 | `BLOCK_NO_MEMORY` | the chunk could not be mapped |

The constants are in `kelpc/gc/src/block.rs`.

## A box made again in a loop

A block makes at most one box in its source text (see
[the boundary](/memory/tidepool/boundary)). A loop body can run `name.box()` more than
once. Each call first frees the element the previous call made, because that `let` is
dead by then and the region holds one element (the comment on `emit_block_box`). The
fixture `block_region_runs.kp` has this shape in its `looped` function, which returns 3.

## Freeing the element

Each block region has two slots, the base address and the root handle. The compiler
fills them at `name.box()` and reads them at the end of the region (`emit_region`,
`release_region`). `block::free` in `block.rs`:

1. unregisters the root, and returns false without doing anything if the handle is
   already stale;
2. unmaps the chunk;
3. gives the charge back to the budget.

The compiler frees a region on every way out of it. The commit that added this,
`2396f0ff`, names four exits: the end of the block, `return`, `break`, `continue` and
the `?` operator. The regions an exit leaves are freed innermost first
(`release_regions_from` in `frame.rs`).

## Tests

- `a_block_is_zeroed_rooted_and_charged_until_freed` in `kelpc/tests/gc/mod.rs` checks
  the zeroing, the root and the charge, and that the free returns the charge.
- `a_block_past_heap_max_runs_a_clearing_then_fails` in the same file checks the budget
  path.
- `kelpc/tests/compile_and_run/boxes_operators.rs`:
  `a_block_region_runs_and_releases_on_every_exit` runs `block_region_runs.kp`, which
  leaves a block by its end, a loop, a `return`, a `?` and a `defer` in the caller.
  `a_block_and_shared_pool_code_share_one_file` runs `block_end_to_end.kp`, which
  creates and frees a block a thousand times while shared-pool data stays intact.
- `m5_block_create_and_free_ns` in `kelpc/tests/gc/mod.rs` times create and free. It
  prints a measurement and checks no gate.

## Related

- [The boundary](/memory/tidepool/boundary): the refusals for block values.
- [What the programmer writes, reads and sees](/memory/tidepool/programmer-view): the source form.
- [The allocation path](/memory/tidepool/allocation-path): the shared-pool path for comparison.
- [Failure and recovery](/memory/tidepool/failure-recovery): what a `Full` means.
