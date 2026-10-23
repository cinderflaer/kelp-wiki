---
title: "Tidepool: what the programmer writes, reads and sees"
description: "The manual block form on main, with a complete example: how a block is written, what its value type is, what BlockError.Full means, and what the program prints. Each rule cites the fixture or test that shows it."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: what the programmer writes, reads and sees

A manual block gives one element its own memory, and frees it when the block
ends. This page shows how to write one, what it returns, and what the program
sees when the block cannot be made. The rules that the compiler checks are on
[Tidepool: the boundary](/memory/tidepool/boundary).

## Writing a block

A block is an expression. It names the block, gives the element type and holds
the statements that use it:

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

This is `kelpc/tests/fixtures/block_end_to_end.kp`, which the test
`a_block_and_shared_pool_code_share_one_file` runs.

- `block request: Node { ... }` declares a block named `request` whose element is
  a `Node`. The name is unique in its function, and a `let` in the same function
  may not use it (`block_name_twice.kp`, `block_name_shadowed_by_let.kp`).
- `request.box()` makes the element. It returns a `Result`, so it is used with
  `?`. The `?` sends a failure out of the function, so the function must return a
  `Result` (`block_try_in_unit_function.kp`).
- The box must be bound by a `let` inside the block (`block_box_not_bound_by_let.kp`).
  A block makes at most one box (`block_box_twice.kp`).
- `Node(value = n * 2)` is the value of the block. The block's value is wrapped in
  `Ok`.

## What the block returns

The type of a block is `Result<T, BlockError>`, where `T` is the type written
after the name. `BlockError` is a built-in enum with one variant, `Full`
(`kelpc/src/infer/program/program_types.rs`). It needs no import. The block's
result is used either with `?`, as above, or with `when`. A result that is not
used at all is refused (`block_region_not_built.kp`).

`Full` means the collector could not make the element under `heap_max`, even
after one clearing. See [Tidepool: the budget](/memory/tidepool/budget).

## Reading the element

The element is read through `get()` on the box, or through a field of its value
inside the block:

```kelp
val cell = request.box()?
Node(value = cell.get().value + n)
```

`cell.value` without `get()` is refused: `block box 'cell' has no field 'value':
its element is read through 'get()'` (`block_box_field_without_get.kp`).

A new element is zeroed. The fixture `block_box_get_reads_field.kp` depends on
this: its result is the argument `n`, because the element's `value` starts at 0.

## Leaving the block

The element is freed when the block ends, on every exit: the end of the block, a
`return`, a `break`, a `continue` and a `?` (commit `2396f0ff`). The fixture
`block_region_runs.kp` covers the end of a block, a loop, a `return`, a `?` that
leaves the function, and a `defer` in the caller. Its expected output is
`5`, `3`, `7`, `0`, `1`, `2` and `5`, one per line.

The element may not leave the block: it cannot be returned, stored outside, put in
a `List` or passed to a call (see [the boundary](/memory/tidepool/boundary)).
A `List` or a `String` made inside a block is refused for the same reason.

## What the element may hold

The element is a scalar or a `datac` of scalars. A block cannot hold a `String`
(`block_element_not_scalar.kp`).

## Settings

The block uses the same budget as the shared pool. `[target] heap_max` in
`coral.toml` sets the cap for both. The `[tidepool]` section does not change the
block itself. The keys are on [Tidepool: settings in `[tidepool]`](/memory/tidepool/settings).

## When the element cannot be made

A block that cannot be made returns `Err(BlockError.Full)`, so the program decides
what to do. A shared-pool allocation that fails after a clearing stops the program
instead, with the message in [Failure and recovery](/memory/tidepool/failure-recovery).
