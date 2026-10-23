---
title: "Working with Kelp memory"
description: "How a hosted Kelp program manages memory: owned values, borrows, moves and drops, the collector that reclaims memory values, the patterns and refusals you will meet, and the recorded cost of the 26.10.5 build."
isPublished: true
tags: "language, ownership, memory, performance"
---
This section is for a programmer who has read the [tutorial](/tutorial) or the
[ownership page](/language/ownership) and wants to write real programs. It covers
the rules, the patterns that follow from them, the compiler messages you will see
when a program breaks a rule, how memory is reclaimed, and what the hosted build
costs in time and memory.

## Owners, resources and memory

Every value has one owner, and the compiler refuses a program that would need two
owners of one value. The owner decides when a resource ends. A file, a socket, a
thread, a lock, or a value with a destructor is closed or dropped at the end of its
owner's scope, on every exit path, at a point the code shows. A destructor runs at
that point.

Memory values are handled differently in a hosted build, which is the default. On
current `main`, every hosted build links the collector, `kelp_gc`. It reclaims the
memory of a `String`, `Bytes`, `List`, `Map`, `Box` or closure environment once no
path reaches it. The owner's scope end does not free that memory, so the bytes of a
dead value can stay in the heap until the next collection.

- The collector is a non-moving mark-region tracing collector. It starts a collection
  when the bytes allocated since the last one reach a trigger. The first trigger is
  2.75 MiB: the midpoint of the two start guesses (1 MiB and 4 MiB) is 2.5 MiB, with 10
  percent headroom added. After each collection the next trigger is the larger of 8 MiB
  and the larger of the two latest live sizes plus 10 percent. That is the default
  `two-size` rule. `[tidepool] trigger_rule` can select `last-size` (the latest live size
  alone) or `gogc-style` (the latest live size plus the stack and global bytes scanned
  with it). No trigger is set above the heap region.
- The heap is capped by `[target] heap_max`, in MiB. The default is 256, and the
  range is 1 to 65536. When a collection cannot make room under the cap, the program
  stops with a fatal `out of memory` message.
- A value that a thread or a lock holds is collected like any other, because the
  runtime registers it as a collector root. A resource (a file, socket, process, thread
  handle, `Mutex` or `RwLock` record, condition variable, channel end or pool) is refused
  by name wherever it would enter the heap. See [Common refusals](/memory/refusals).

A freestanding build has no collector and no shared heap. See
[Freestanding](/language/freestanding).

The measured numbers on [Performance](/memory/performance) are for the 26.10.5
release, which had no collector. Current `main` has not been measured on that page.
Tidepool steps 1 and 2 are on `main`: the collector roots the values that threads and
locks hold, and `[tidepool]` in `coral.toml` sets the start guesses, the headroom and
the trigger rule. Manual block regions (`block name: T { ... }`) are on `main` too. See
[Tidepool](/memory/tidepool).

## Pages

In reading order:

- [The rules in one page](/memory/rules): one owner, borrows, moves, and drops
  at scope end, each with a program that compiles.
- [Patterns](/memory/patterns): trees built with `Box`, a growing `List`, a `Map`
  of owned values, text and views without copies, returning owned values, and
  passing borrows to functions.
- [Common refusals](/memory/refusals): the exact compiler messages for the
  mistakes everyone makes first, each with its fix.
- [Performance](/memory/performance): the recorded numbers for the 26.10.5 hosted
  build on four benchmarks, with their spread and the C reference, and what they show.
- [Tidepool](/memory/tidepool): the memory design. Steps 1 and 2 and the manual block
  regions are on `main`. Its pages describe what is built and cite the code for it.

The programs in this section were compiled with the 26.10.5 release compiler and
run, and the output shown is the output of that run. They have not been rerun on
current `main` for this section.

## See also

- [Ownership and borrowing](/language/ownership): the full rules, including
  cursors and partial moves
- [Drop](/language/drop): destructors and what a panic skips
- [Collections](/language/collections) and [Text](/language/text): the types the
  patterns use
