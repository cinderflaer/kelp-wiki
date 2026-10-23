---
title: "Tidepool: the idea"
description: "What Tidepool is: a shared pool that is cleared by a tracing collector, manual blocks that free their element at the end of a region, one heap_max cap for both, and a trigger that follows the live size. Each point names the code that makes it true."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: the idea

Tidepool is the memory design for Kelp's hosted builds. A hosted program has two
places for memory values. Most values go into a shared pool that a collector
clears. A manual block gives one element its own memory, which the compiler frees
when the block ends. Both draw on one budget.

- **The shared pool.** Most memory values, such as a `String`, a `List`, a `Map`,
  a `Box` and a closure environment, are allocated in the pool. The collector is a
  non-moving mark-region tracing collector (`kelpc/gc/src/lib.rs`). It clears the
  pool when the bytes allocated since the last clearing reach a trigger. It frees
  only the objects that no root reaches, because the mark phase starts from the
  roots (`kelpc/gc/src/mark.rs`).
- **Manual blocks.** `block name: T { ... }` makes one element and frees it when the
  block ends, on every exit. The compiler writes the free. A value that could outlive
  the block is refused at build time, and the refusals are on
  [the boundary](/memory/tidepool/boundary).
- **One budget.** `[target] heap_max` in `coral.toml` caps the pool and the block
  memory together. A block that does not fit gets one clearing first (`kelpc/gc/src/block.rs`).
- **The trigger.** The first clearing is set from two start guesses, and later
  clearings follow the measured live size plus a headroom percentage. The rules are
  in `kelpc/gc/src/trigger.rs` and on [the budget](/memory/tidepool/budget).

What is on `main` is listed on [Tidepool: build order](/memory/tidepool/build-order),
and the parts that are not on `main` are not claimed here. See
[Tidepool](/memory/tidepool) for the index.
