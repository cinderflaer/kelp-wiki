---
title: "Tidepool memory design"
description: "Index of the Tidepool pages: the shared pool a tracing collector clears, manual blocks that free their element, one heap_max cap for both, the [tidepool] settings, and the channel, select and pool rules that touch memory."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool memory design

Tidepool is the memory design for hosted Kelp programs. Most memory values go into
a shared pool that a tracing collector clears. A manual block frees its element when
its region ends. One limit, `[target] heap_max` in `coral.toml`, covers both.

What a hosted program gets today:

- **A collector in every hosted build.** The compiler links `libkelp_gc.a`, a
  non-moving mark-region collector built from `kelpc/gc` (`kelpc/build.rs` and
  `kelpc/src/driver.rs`). The `managed` target mode was removed in `d73b59f1`, so
  `mode = "managed"` is refused (`kelpc/src/resolve/manifest_keys.rs`).
- **A capped heap.** `[target] heap_max` is a whole number of MiB from 1 to 65536,
  with a default of 256 (`kelpc/src/managed.rs`). The cap is passed to
  `kelp_gc_init` (`kelpc/src/codegen_llvm.rs`).
- **Tuned clearing.** The `[tidepool]` section sets the start guesses, the headroom
  and the trigger rule (`kelpc/src/resolve/manifest.rs`). See
  [settings](/memory/tidepool/settings).
- **Roots for threads and locks.** Thread arguments and results, closure
  environments and lock values are roots (commit `3c5b726c`,
  `kelpc/tests/tidepool_s1.rs`).
- **Manual blocks.** `block name: T { ... }` makes one element, frees it on every exit
  from the block, and yields `Result<T, BlockError>` (`kelpc/tests/fixtures/block_end_to_end.kp`).
  See [what the programmer writes](/memory/tidepool/programmer-view).
- **Channel ends and select.** A channel end may cross to a worker as a thread argument
  or result (`CROSSING_CHANNEL_RECORDS` in `kelpc/src/managed.rs`). The `select` form
  is in `kelpc/src/parser/parser_select.rs`. See [channels and select](/stdlib/sync#select).
- **A worker pool.** [`std/pool`](/stdlib/pool) is written in Kelp over `Mutex`,
  `Condvar` and `thread.spawn` (`kelpc/std/pool.kp`).

Two parts of the design are not in any build. `kelpc/src/escape.rs` is compiled as a
module (`kelpc/src/main.rs`), but no other module calls it. See
[build order](/memory/tidepool/build-order).

## Pages

- [The idea](/memory/tidepool/idea): what the pieces are and how they fit.
- [Settings in `[tidepool]`](/memory/tidepool/settings): the keys in `coral.toml`, their defaults and their refusals.
- [The budget](/memory/tidepool/budget): the cap, the first clearing and the later triggers.
- [The allocation path](/memory/tidepool/allocation-path): one shared-pool allocation, from the call to the header.
- [Blocks at runtime](/memory/tidepool/blocks): how a block's element is made, rooted, charged and freed.
- [The boundary](/memory/tidepool/boundary): the compile-time refusals for block values.
- [Safety rules](/memory/tidepool/safety-rules): the rules Tidepool enforces, and where.
- [Safety tests](/memory/tidepool/safety-tests): the tests for each rule.
- [What the programmer writes, reads and sees](/memory/tidepool/programmer-view): blocks, select, the pool and verify mode.
- [Failure and recovery](/memory/tidepool/failure-recovery): what returns a value and what stops the process.
- [Build order](/memory/tidepool/build-order): the parts in the order they landed on `main`.
- [Test plan](/memory/tidepool/test-plan): where the tests are and how each group runs.
- [Performance claims and how they are measured](/memory/tidepool/performance-claims): the measurements and what they record.
- [Tooling and release](/memory/tidepool/tooling-release): the environment variables, the archive and the benchmark scripts.

The pages cite the file, test or commit for each statement they make.

## Related

- [Working with Kelp memory](/memory): the ownership rules and the patterns Tidepool sits under.
- [Common refusals](/memory/refusals): the messages a hosted build prints.
- [Ownership and borrowing](/language/ownership) and [Drop](/language/drop): the owned values the pool does not free.
- [Concurrency in v1](/language/concurrency): threads, the panic policy and the cell a thread shares.
- [`std/sync`](/stdlib/sync) and [`std/pool`](/stdlib/pool): the channels, select and pool built on the collector.
- [Limits in v1](/language/limits): what is left out.
