---
title: "Tidepool: the allocation path"
description: "One shared-pool allocation, from the compiled call to the header the collector reads later: the checks that run first, the safepoint and trigger, the two spaces, the retry after one clearing, and the zeroed payload."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: the allocation path

This page follows one allocation of a shared-pool object, from the compiled call to
the header the collector reads later. The compiled program reaches the collector
through the exported `kelp_gc_*` functions. The compiler declares the ones it calls,
for example `kelp_gc_block_alloc`, in `kelpc/src/codegen_llvm/layout.rs`.

## Entry

`alloc_common` in `kelpc/gc/src/lib.rs` serves one object or one array. It runs these
steps in order:

1. `ensure_init` sets the collector up on the first call. If the program never
   called `kelp_gc_init`, it uses the defaults: a 256 MiB cap, an 8 MiB floor, start
   guesses of 1 and 4 MiB, and 10 percent headroom (`init_once` in `lib.rs`).
2. A thread that is not attached is a fatal error: `gc: allocation on a thread that
   is not attached (call kelp_gc_thread_attach before the first allocation)`.
3. A type with an alignment above 8 is refused with `gc: type alignment above 8 is
   not supported in v1`. A descriptor with the no-scan flag and pointer slots is
   refused with `gc: noscan type descriptor has pointer slots`.
4. For an array, the byte size is computed first. A count whose byte size overflows
   is refused with `array size overflows`. A count above `u32::MAX` is refused with
   `array of <n> elements is too large`. Neither check can be helped by a clearing,
   so both fail at once (`array_overflows` and `array_too_large` in `lib.rs`).

## Safepoint and trigger

Before the object is placed, the allocator calls `threads::safepoint()`. Two checks
then decide whether a clearing runs first:

- If `KELP_GC_STRESS=n` is set, a clearing runs every `n` allocations.
- A clearing runs when the bytes allocated since the last one reach the trigger
  (`bytes_since >= trigger`). The trigger rules are on
  [the budget](/memory/tidepool/budget).

## Placement

The allocator takes the heap lock, registers the type if it is new, and calls
`try_alloc` in `kelpc/gc/src/heap.rs`. The region has two spaces:

- The line-hole space holds objects up to `LARGE_MIN`, which is 8192 bytes. Objects
  are bumped into the free lines of active blocks. A block is 32 KiB and a line is
  128 bytes (`kelpc/gc/src/state.rs`), so an object lies inside one block.
- The run space holds larger objects. It takes runs of whole free blocks, so an
  object can cross a block boundary. Its objects are listed in the large table, which
  the sweep reads.

If `try_alloc` returns nothing, the allocator unlocks, runs one clearing with
`threads::collect()`, and tries again. If the second attempt fails too, it prints
`out of shared-pool memory` and stops the program. See
[failure and recovery](/memory/tidepool/failure-recovery).

## Header and zeroing

A successful allocation writes one header word at the start of the object
(`kelpc/gc/src/types.rs` gives the bit positions):

- the type id, from bit `HDR_TYPE_SHIFT` (8);
- `HDR_ARRAY` and the element count, from bit `HDR_COUNT_SHIFT` (32), for an array;
- `HDR_NOSCAN` when the descriptor has the no-scan flag;
- `HDR_LARGE` when the total size is above `LARGE_MIN`;
- the unmarked value of the current epoch, which is the complement of the epoch.

The payload is then zeroed with `write_bytes`, and the returned pointer is the
header address plus 8. `register_type` runs under the lock before placement, so every
header names a registered descriptor.

## What the collector reads later

The mark phase follows pointer slots from the roots, using the descriptor for each
header. It also scans thread stacks conservatively, as the crate header in
`kelpc/gc/src/lib.rs` says. `find_object` in `heap.rs` maps an interior pointer back to
its object, so a stack word that points into the middle of an object keeps the whole
object alive.

## Tests

- `a_dead_object_is_poisoned_in_verify_mode` in `kelpc/tests/gc/mod.rs` checks the
  sweep under verify mode. See [tooling and release](/memory/tidepool/tooling-release)
  for `KELP_GC_VERIFY`.
- `kelpc/tests/gc/child_first.rs` checks that the first clearing lands in the pool
  block the trigger names. It is the `T40a` check of the budget.
- `allocation_without_attach_fails_loudly` in `kelpc/tests/gc/enum_tag.rs` checks step 2.
  `heap_cap_of_256_mib_fails_with_out_of_memory` in the same file checks a cap with no
  room.
- `measure_large_object_waste_4k_and_16k` in `kelpc/tests/gc/large.rs` prints the waste
  of run-space objects (4 KiB and 16 KiB arrays). It asserts nothing.

## Related

- [The budget](/memory/tidepool/budget): the cap and the triggers.
- [Blocks at runtime](/memory/tidepool/blocks): the same steps for a block's element.
- [Safety rules](/memory/tidepool/safety-rules): the rules the runtime checks.
- [Tidepool memory design](/memory/tidepool): the index.
