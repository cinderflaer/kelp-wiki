---
title: "Tidepool: the idea"
description: "What Tidepool is: a shared pool cleared by a tracing collector, manual blocks that free their element at the end of a region, one heap_max cap for both, and a trigger that follows the live size. Each point names the code that makes it true."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: the idea

Tidepool is the memory design for hosted Kelp programs. A hosted program has two
places for memory values. Most values go into a shared pool that a collector
clears. A manual block gives one element its own memory, which the compiler frees
when the block ends. Both draw on one budget.

- **The shared pool.** Memory values such as a `String`, a `List`, a `Map`, a `Box`
  and a closure environment are allocated in the pool (`kelpc/gc/src/lib.rs`, the
  `alloc_common` function). The collector is a non-moving mark-region tracing
  collector. It clears the pool when the bytes allocated since the last clearing reach
  a trigger. It frees only the objects that no root reaches, because the mark phase
  starts from the roots (`kelpc/gc/src/mark.rs`).
- **Manual blocks.** `block name: T { ... }` makes one element and frees it when the
  block ends, on every exit. The compiler emits the free (`kelpc/src/codegen_llvm/frame.rs`,
  `release_region`). A value that could outlive the block is refused at build time.
  The refusals are on [the boundary](/memory/tidepool/boundary).
- **One budget.** `[target] heap_max` in `coral.toml` caps the pool and the block
  memory together. A block that does not fit gets one clearing first
  (`kelpc/gc/src/block.rs`, `alloc`).
- **The trigger.** The first clearing is set from two start guesses plus headroom.
  Later clearings follow the measured live size plus a headroom percentage
  (`kelpc/gc/src/trigger.rs`). The rules are on [the budget](/memory/tidepool/budget).
- **Roots for what threads hold.** A value that a thread or a lock holds is a
  collector root, so a clearing does not free it (`kelpc/tests/tidepool_s1.rs`).

The layout of each part is on [the allocation path](/memory/tidepool/allocation-path)
and [blocks at runtime](/memory/tidepool/blocks). The settings are on
[settings](/memory/tidepool/settings).

## Related

- [Tidepool memory design](/memory/tidepool): the index of these pages.
- [What the programmer writes, reads and sees](/memory/tidepool/programmer-view): the source form.
- [Working with Kelp memory](/memory): the owned values that Tidepool does not free.
