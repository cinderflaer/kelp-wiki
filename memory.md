---
title: "Working without the garbage collector"
description: "Writing Kelp with manual memory: ownership, borrows, moves and drops, the patterns they make, the refusals you will meet, and the measured cost of the hosted build."
isPublished: true
tags: "language, ownership, memory, performance"
---
This section is for a programmer who has read the [tutorial](/tutorial) or the
[ownership page](/language/ownership) and wants to write real programs with
Kelp's manual memory: every value has one owner, and its owner frees it. It
covers the rules, the patterns that follow from them, the compiler messages you
will see when a program breaks a rule, and what the hosted build costs in time
and memory.

## Why manual memory

Kelp has no garbage collector. A value lives exactly as long as its one owner,
and the owner's scope end frees it on every exit path, so there is no collector
pausing the program, no tracing pass, and no moment at which a dead value
lingers until the collector gets to it. A destructor runs at a known point in
the code. The price is that the compiler refuses a program that would need two
owners of one value, so the program is shaped around single ownership up front,
where a garbage-collected language would let the shared value stay shared.

## Pages

In reading order:

- [The rules in one page](/memory/rules): one owner, borrows, moves, and drops
  at scope end, each with a program that compiles.
- [Patterns](/memory/patterns): trees built with `Box`, a growing `List`, a `Map`
  of owned values, text and views without copies, returning owned values, and
  passing borrows to functions.
- [Common refusals](/memory/refusals): the exact compiler messages for the
  mistakes everyone makes first, each with its fix.
- [Performance](/memory/performance): the measured numbers for the hosted build
  on four benchmarks, with their spread and the C reference, and what they show.
- [Managed comparison](/memory/managed): a placeholder. The managed build is not
  finished, so there are no numbers for it yet.

Every program in this section was compiled with the 26.10.5 release compiler and
run. The output shown is the output of that run.

## See also

- [Ownership and borrowing](/language/ownership): the full rules, including
  cursors and partial moves
- [Drop](/language/drop): destructors and what a panic skips
- [Collections](/language/collections) and [Text](/language/text): the types the
  patterns use
