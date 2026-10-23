---
title: "Tidepool: the allocation path"
description: "How one shared-pool allocation runs on main: the safepoint, the trigger check, the two spaces of the region, the header and the retry after a clearing. Each step names its source."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: the allocation path

This page follows one allocation of a shared-pool object on `main`, from the
compiled call to the header the collector reads later. It describes the
collector in `kelpc/gc`. The compiled program reaches it through the exported `kelp_gc_*`
functions. The compiler declares the ones it calls, for example
`kelp_gc_block_alloc`, in `kelpc/src/codegen_llvm/layout.rs`.

## Entry

`alloc_common` in `kelpc/gc/src/lib.rs` serves one object or one array. It runs
these steps in order:

1. `ensure_init` sets the collector up on the first call. If the program never
   called `kelp_gc_init`, it uses the default arguments: a 256 MiB cap, an 8 MiB
   floor, start guesses of 1 and 4 MiB and 10 percent headroom.
2. A thread that is not attached is a fatal error: `gc: allocation on a thread
   that is not attached (call kelp_gc_thread_attach before the first
   allocation)`.
3. Types with an alignment above 8 are refused with `gc: type alignment above 8
   is not supported in v1`. A descriptor with the no-scan flag and pointer slots
   is refused too.
4. An array's byte size is checked before anything else. The count must not
   exceed `u32::MAX`, and the product must not overflow. Neither check can be
   helped by a clearing, so both fail at once.

## Safepoint and trigger

Before the object is placed, the allocator calls `threads::safepoint()`. If
`KELP_GC_STRESS=n` is set, a clearing runs every `n` allocations. Otherwise a
clearing runs when the bytes allocated since the last one reach the trigger
(`bytes_since >= trigger`). The trigger rules are on
[Tidepool: the budget](/memory/tidepool/budget).

## Placement

The allocator takes the heap lock and calls `try_alloc` in `kelpc/gc/src/heap.rs`.
The region has two spaces:

- The line-hole space holds objects up to `LARGE_MIN`, which is 8192 bytes.
  Objects are bumped into the free lines of active blocks. A block is 32 KiB and a
  line is 128 bytes (`kelpc/gc/src/state.rs`), so an object lies inside one block.
- The run space holds larger objects. It takes runs of whole free blocks, so an
  object can cross a block boundary. Its objects are listed in the large table,
  which the sweep reads.

If `try_alloc` returns nothing, the allocator unlocks, runs one clearing with
`threads::collect()`, and tries again. When the second attempt fails too, it
prints `out of shared-pool memory` and stops the program. See
[Failure and recovery](/memory/tidepool/failure-recovery).

## Header and zeroing

A successful allocation writes one header word at the start of the object:

- the type id, in the bits from `HDR_TYPE_SHIFT`;
- `HDR_ARRAY` and the element count for an array;
- `HDR_NOSCAN` when the descriptor has the no-scan flag;
- `HDR_LARGE` when the total size is above `LARGE_MIN`;
- the unmarked value of the current epoch, which is the complement of the epoch.

The payload is then zeroed with `write_bytes`. The returned pointer is the
header address plus 8. `register_type` runs under the lock before placement, so
every header names a registered descriptor.

## What the collector reads later

The mark phase follows pointer slots from the roots, using the descriptor for
each header. It also scans thread stacks conservatively, as the crate header in
`kelpc/gc/src/lib.rs` says. `find_object` in `heap.rs` maps an interior pointer
back to its object, so a stack word that points into the middle of an object
keeps the whole object alive.

## Tests that cover this path

- `kelpc/tests/gc/mod.rs` has the allocation and clearing tests, including
  `a_dead_object_is_poisoned_in_verify_mode`, which checks the sweep.
- `kelpc/tests/gc/child_first.rs` checks that the first clearing lands in the pool
  block the trigger names (T40a): with a 3 MiB trigger, the 131041st 24-byte
  object is the first one in pool block 97.
- `kelpc/tests/gc/enum_tag.rs` checks that an allocation on an unattached thread
  fails loudly, that a cap of 256 MiB with no room reports `out of memory`, and
  that a thread which never reaches a safepoint is named after the timeout.
- `kelpc/tests/gc/large.rs` measures the waste of run-space objects (4 KiB and
  16 KiB arrays). It is a measurement, not a check.
