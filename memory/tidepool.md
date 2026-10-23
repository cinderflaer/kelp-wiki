---
title: "Tidepool memory design"
description: "Index of the Tidepool memory pages: the shared pool cleared by a collector, manual blocks, one heap_max budget, the [tidepool] settings and the safety rules, with what is on main and what is not."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool memory design

Tidepool is the memory design for Kelp's hosted builds. Most memory values go into
a shared pool that a tracing collector clears. A manual block frees its element when
its region ends. One limit, `[target] heap_max`, covers both.

On `main`, every hosted build links the collector, a non-moving mark-region
collector, and caps its heap with `[target] heap_max`. The collector roots the values
that threads and locks hold, the root table grows in chunks of 1024 slots, and
`[tidepool]` in `coral.toml` sets the start guesses, the headroom and the trigger
rule. Manual blocks are on `main` as well: the parser, the checker, the lowering and
the collector's block entry points (`kelpc/gc/src/block.rs`).

A channel end crosses to a worker thread as a thread argument or result. The channel
records `Sender`, `Receiver`, `SendEnd` and `RecvEnd` are listed in
`CROSSING_CHANNEL_RECORDS` in `kelpc/src/managed.rs` (decision 125). A resource such
as a file, a socket or a `std/pool` value does not cross, and
[Common refusals](/memory/refusals) gives the messages.

The escape analysis in `kelpc/src/escape.rs` is not part of the build. Pages that
describe it say so.

## Pages

- [The idea](/memory/tidepool/idea): what the pieces are and how they fit.
- [Settings in `[tidepool]`](/memory/tidepool/settings): the keys in `coral.toml`.
- [The budget](/memory/tidepool/budget): the cap, the first clearing and the later triggers.
- [The allocation path](/memory/tidepool/allocation-path): one allocation, from the call to the header.
- [Blocks at runtime](/memory/tidepool/blocks): how a block's element is made, rooted, charged and freed.
- [The boundary](/memory/tidepool/boundary): the compile-time refusals for block values.
- [Safety rules](/memory/tidepool/safety-rules): the rules Tidepool enforces, and where.
- [Safety tests](/memory/tidepool/safety-tests): the tests for each rule.
- [What the programmer writes, reads and sees](/memory/tidepool/programmer-view): the block form and its result.
- [Failure and recovery](/memory/tidepool/failure-recovery): what returns a value and what stops the process.
- [Build order](/memory/tidepool/build-order): the parts in the order they landed on `main`.
- [Test plan](/memory/tidepool/test-plan): where the tests are and how each group runs.
- [Performance claims and how they are measured](/memory/tidepool/performance-claims): the measurements and what they record.
- [Tooling and release](/memory/tidepool/tooling-release): the environment variables, the archive and the benchmark scripts.

The pages cite the file or the test for each statement they make.
