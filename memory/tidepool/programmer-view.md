---
title: "Tidepool: what the programmer writes, reads and sees"
description: "How a hosted program uses Tidepool: manual blocks with a complete example and the rules for their values, channel select, the thread pool, and verify mode with KELP_GC_VERIFY=1. Each rule cites the fixture or test that shows it."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: what the programmer writes, reads and sees

A hosted program has two kinds of memory value. Most values are in the shared pool,
and the collector frees them once nothing reaches them. A manual block gives one element
its own memory, and frees it when the block ends. This page shows how a program writes
each, what it gets back, and what it sees when something cannot be made. The rules the
compiler checks are on [the boundary](/memory/tidepool/boundary).

## Writing a block

A block is an expression. It names the block, gives the element type, and holds the
statements that use it:

```kelp
impl "std/result"

datac Node(val value: i32)

fun doubled(n: i32) => result.Result<i32, BlockError> {
    val v = block request: Node {
        val cell = request.box()?
        Node(value = n * 2)
    }?
    return result.Result.Ok<i32, BlockError>(value = v.value)
}
```

This is `kelpc/tests/fixtures/block_end_to_end.kp`. The test
`a_block_and_shared_pool_code_share_one_file` runs it, and the program prints `doubled(5)`
as `10`.

- `block request: Node { ... }` declares a block named `request` whose element is a
  `Node`. The name is unique in its function, and a `let` in the same function may not
  use it (`block_name_twice.kp`, `block_name_shadowed_by_let.kp`).
- `request.box()` makes the element. It returns a `Result`, so it is used with `?`. The
  `?` sends a failure out of the function, so the function must return a `Result`
  (`block_try_in_unit_function.kp`).
- The box must be bound by a `let` inside the block (`block_box_not_bound_by_let.kp`).
  A block makes at most one box in its source (`block_box_twice.kp`).
- The last expression of the block is its value, here `Node(value = n * 2)`.

## What the block returns

The type of a block is `Result<T, BlockError>`, where `T` is the type written after the
name. `BlockError` is a built-in enum with one variant, `Full`
(`kelpc/src/infer/generics.rs`). It needs no import. The block's result is used either
with `?`, as above, or with `when`. A result that is not used at all is refused
(`block_region_not_built.kp`).

`Full` means the collector could not make the element under `heap_max`, even after one
clearing. See [the budget](/memory/tidepool/budget) and
[failure and recovery](/memory/tidepool/failure-recovery).

## Reading the element

The element is read through `get()` on the box, or through a field of its value inside
the block:

```kelp
val cell = request.box()?
Node(value = cell.get().value + n)
```

`cell.value` without `get()` is refused (`block_box_field_without_get.kp`). A new element
is zeroed. The fixture `block_box_get_reads_field.kp` depends on this: it prints `7` for
`make(7)`, because the element's `value` starts at 0.

## A box in a loop

A loop body can make the box more than once. Each call frees the element the previous
call made, so the region holds one element at a time. The fixture `block_region_runs.kp`
has this in its `looped` function, which prints `3`.

## Leaving the block

The element is freed when the block ends, on every exit: the end of the block, a
`return`, a `break`, a `continue` and a `?` (commit `2396f0ff`). The fixture
`block_region_runs.kp` covers the end of a block, a loop, a `return`, a `?` that leaves
the function, and a `defer` in the caller. Its output is `5`, `3`, `7`, `0`, `1`, `2`
and `5`, one per line (`kelpc/tests/golden/fixture_block_region_runs.out`).

The element may not leave the block. It cannot be returned, stored outside, put in a
`List`, or passed to a call (see [the boundary](/memory/tidepool/boundary)). A `List` or a
`String` made inside a block is refused for the same reason.

## What the element may hold

The element is a scalar or a `datac` of scalars. A block cannot hold a `String`
(`block_element_not_scalar.kp`).

## The shared pool next to a block

Ordinary code that allocates a `List` or a `String` outside a block uses the shared
pool, as in `block_end_to_end.kp`. The block and the pool use the same `heap_max`. The
program in that fixture creates and frees a block a thousand times while a `List` made
outside the block keeps its element. The settings are on
[settings](/memory/tidepool/settings).

## Channels and select

Channel ends may cross to a worker as a thread argument or result (see
[`std/sync`](/stdlib/sync)). The `select` form waits on several cases and runs the arm of
the first case that is ready:

```kelp
impl "std/option"
impl "std/result"
impl "std/sync"

fun main() {
    val (tx, rx) = sync.bounded<i64>(1)
    val sent = select {
        send(tx, 7) -> "sent",
        recv(rx) as v -> "received",
        closed -> "closed",
    }
    print(sent)
}
```

The fixture `chan_select_send.kp` runs this shape and prints `sent`, `7` and
`received`. The fixture `chan_select_default.kp` prints `-1` for a `default` arm when
nothing is queued, and `4` once a value is queued. The fixture `chan_select_arms.kp`
shows a `timeout(20)` arm and a `closed` arm.

The rules a program meets:

- A select with a receive arm needs a `closed -> e` arm
  (`chan_select_no_closed.kp`).
- A value can be sent in one case only (`chan_select_moved.kp`).
- A case names its channel as a variable or a field, not a call such as `recv(make_rx())`.
- At most one `timeout`, one `closed` and one `default` arm, and not both `default` and
  `timeout`.

The arms, their ready rules and the refusal texts are on
[`std/sync`, Select](/stdlib/sync#select). The form is parsed and lowered in
`kelpc/src/parser/parser_select.rs`.

## The thread pool

`std/pool` runs closures on a fixed set of workers (see [`std/pool`](/stdlib/pool)). The
fixture `pool_sum.kp` queues 1000 jobs on four workers, adds to an atomic, and prints
`499500` and then `0`, the number of panicked jobs. The test
`a_pool_runs_a_thousand_jobs` in `kelpc/tests/compile_and_run/atomics.rs` runs it.

- `pool.new(0)` panics with `pool.new: a pool needs at least one worker`.
- `spawn` after `join` panics with `Pool.spawn: the pool has been joined`.
- A `Pool` value is a resource. It stays in the thread that made it and does not cross
  to a worker.

## Checking a program with verify mode

`KELP_GC_VERIFY=1` turns on two checks when the program runs. After each collection the
collector walks the heap and checks every object header. At each sweep it fills each dead
shared-pool object with the byte `0xA5`. A read through a stale pointer then sees that
pattern and not the old contents. The test `a_dead_object_is_poisoned_in_verify_mode` in
`kelpc/tests/gc/mod.rs` checks the poisoning. The collector reads the variable once, at
start-up (`kelpc/gc/src/lib.rs`). The other environment variables are on
[tooling and release](/memory/tidepool/tooling-release).

```text
KELP_GC_VERIFY=1 ./program
```

Verify mode is for tests and debugging. The variable is read by the collector only, so
a program that does not set it runs without the checks.

## Related

- [Tidepool memory design](/memory/tidepool): the index.
- [Blocks at runtime](/memory/tidepool/blocks): how the element is made and freed.
- [The boundary](/memory/tidepool/boundary): the refusals for block values.
- [Settings in `[tidepool]`](/memory/tidepool/settings): the cap and the triggers.
- [Failure and recovery](/memory/tidepool/failure-recovery): what stops the process.
- [Working with Kelp memory](/memory): the rules for owned values.
- [`std/sync`](/stdlib/sync), [`std/pool`](/stdlib/pool) and [Concurrency in v1](/language/concurrency).
